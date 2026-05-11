"""
Eksperymenty na scenariuszach broken lineage (strukturalny podział krawędzi).

W przeciwieństwie do run_experiments.py (losowy 80/20 split), tutaj krawędzie
testowe są wybierane według roli węzła — symulując realne przyczyny broken lineage:

  Scenariusz A — tabela staging usunięta
                 (krawędzie wyjściowe intermediate Tables)
  Scenariusz B — zależność ukryta przez UDF
                 (krawędzie wyjściowe source Tables)
  Scenariusz C — zależność do data martu ukryta
                 (krawędzie wejściowe sink Tables)

Użycie:
    python run_scenario_experiments.py              # DLG1–DLG4, scenariusze A+B+C
    python run_scenario_experiments.py --all        # wszystkie 18 grafów
    python run_scenario_experiments.py --dlg 4 7    # wybrane grafy
    python run_scenario_experiments.py --scenario A # tylko jeden scenariusz
    python run_scenario_experiments.py --no-ml      # pomiń ML
"""

import argparse
import csv
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))
from data.loader import load_graph
from data.scenario_splitter import scenario_split, scenario_summary, classify_table_roles
from algorithms.heuristics import score_all_methods
from algorithms.classical_ml import (
    GraphMLClassifier, RUSBoostGraphClassifier, LightGBMGraphClassifier,
)
from algorithms.node2vec_ml import Node2VecMLPClassifier
from evaluation.metrics import tune_and_evaluate

DEFAULT_DLGS = [1, 2, 3, 4]
ALL_DLGS     = list(range(1, 19))
SCENARIOS    = ["A", "B", "C"]

HEURISTICS = [
    "preferential_attachment",
    "l3",
    "katz",
    "ppr",
]

ML_MODELS = {
    "RandomForest": GraphMLClassifier,
    "RUSBoost":     RUSBoostGraphClassifier,
    "LightGBM":     LightGBMGraphClassifier,
    "Node2Vec+MLP": Node2VecMLPClassifier,
}

SCENARIO_LABELS = {
    "A": "Staging table removed  (intermediate->Job edges hidden)",
    "B": "UDF hidden source      (source Table->Job edges hidden)",
    "C": "Sink dependency hidden (Job->sink Table edges hidden)",
}


# ---------------------------------------------------------------------------

def run_one(dlg_id: int, scenario: str, seed: int, run_ml: bool,
            val_ratio: float = 0.2) -> list[dict]:
    label = f"DLG{dlg_id}"
    G = load_graph(label)

    try:
        splits = scenario_split(G, scenario=scenario,
                                val_ratio=val_ratio, seed=seed)
    except ValueError as e:
        print(f"  [{label}/S{scenario}] Pominięto: {e}")
        return []

    G_train    = splits["G_train"]
    pos_train  = splits["pos_train"]
    neg_train  = splits["neg_train"]
    pos_val    = splits["pos_val"]
    neg_val    = splits["neg_val"]
    pos_test   = splits["pos_test"]
    neg_test   = splits["neg_test"]

    if len(pos_test) == 0 or len(neg_test) == 0:
        return []

    val_edges  = pos_val + neg_val
    test_edges = pos_test + neg_test
    y_val  = np.array([1] * len(pos_val)  + [0] * len(neg_val))
    y_test = np.array([1] * len(pos_test) + [0] * len(neg_test))

    results = []
    base = {
        "graph": label, "scenario": scenario,
        "nodes": G.number_of_nodes(),
        "train_pos": len(pos_train), "val_pos": len(pos_val),
        "test_pos": len(pos_test),
        "roles": splits["roles_summary"],
    }

    # Heurystyki — próg dobierany na walidacji, metryki raportowane na teście
    val_scores_dict  = score_all_methods(G_train, val_edges)  if val_edges  else {}
    test_scores_dict = score_all_methods(G_train, test_edges)
    for method in HEURISTICS:
        sc_val  = val_scores_dict.get(method, np.array([]))
        sc_test = test_scores_dict[method]
        m = tune_and_evaluate(y_val, sc_val, y_test, sc_test)
        results.append({**base, "algorithm": method, **m})

    if not run_ml:
        return results

    for name, Cls in ML_MODELS.items():
        try:
            clf = Cls(seed=seed)
            clf.fit(G_train, pos_train, neg_train)
            sc_val  = (clf.predict_proba(G_train, val_edges)
                       if val_edges else np.array([]))
            sc_test = clf.predict_proba(G_train, test_edges)
            m = tune_and_evaluate(y_val, sc_val, y_test, sc_test)
            results.append({**base, "algorithm": name, **m})
        except Exception as e:
            print(f"  [{label}/S{scenario}] {name} błąd: {e}")

    return results


# ---------------------------------------------------------------------------

def print_table(all_results: list[dict], scenarios: list[str]):
    if not all_results:
        print("Brak wyników.")
        return

    for sc in scenarios:
        rows = [r for r in all_results if r["scenario"] == sc]
        if not rows:
            continue

        print(f"\n{'='*100}")
        print(f"SCENARIUSZ {sc}: {SCENARIO_LABELS[sc]}")
        print(f"{'='*100}")
        print(f"{'Graf':<8} {'Węzły':>6} {'Tr+':>5} {'Va+':>4} {'Te+':>5}  "
              f"{'Algorytm':<24}  {'P':>6} {'R':>6} {'F1':>6} {'AUC-ROC':>8} {'AUC-PR':>7}")
        print("-" * 105)

        def fmt(v):
            return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "  nan"

        prev = None
        for r in rows:
            if r["graph"] != prev and prev is not None:
                print()
            prev = r["graph"]
            print(
                f"{r['graph']:<8} {r['nodes']:>6} {r['train_pos']:>5} "
                f"{r.get('val_pos', 0):>4} {r['test_pos']:>5}  "
                f"{r['algorithm']:<24}  "
                f"{fmt(r['precision']):>6} {fmt(r['recall']):>6} "
                f"{fmt(r['f1']):>6} {fmt(r['auc_roc']):>8} {fmt(r['auc_pr']):>7}"
            )

    # Zbiorcze podsumowanie: najlepszy F1 per (scenariusz, graf)
    print(f"\n{'='*100}")
    print("PODSUMOWANIE — najlepszy AUC-ROC per (scenariusz, graf)")
    print(f"{'='*100}")
    print(f"{'Graf':<8}", end="")
    for sc in scenarios:
        print(f"  {'S'+sc+' best alg':<26} {'AUC':>6}", end="")
    print()
    print("-" * 100)

    graphs = sorted(set(r["graph"] for r in all_results))
    for g in graphs:
        print(f"{g:<8}", end="")
        for sc in scenarios:
            subset = [r for r in all_results
                      if r["graph"] == g and r["scenario"] == sc
                      and not np.isnan(r.get("auc_roc", float("nan")))]
            if subset:
                best = max(subset, key=lambda x: x["auc_roc"])
                alg  = best["algorithm"][:24]
                print(f"  {alg:<26} {best['auc_roc']:>6.3f}", end="")
            else:
                print(f"  {'—':<26} {'—':>6}", end="")
        print()

    # Porównanie scenariuszy: czy A/B/C są trudniejsze od siebie?
    print(f"\n{'='*100}")
    print("TRUDNOŚĆ SCENARIUSZY — średni AUC-ROC per scenariusz (wszystkie grafy, najlepszy alg)")
    print(f"{'='*100}")
    for sc in scenarios:
        aucs = []
        for g in graphs:
            subset = [r for r in all_results
                      if r["graph"] == g and r["scenario"] == sc
                      and not np.isnan(r.get("auc_roc", float("nan")))]
            if subset:
                aucs.append(max(r["auc_roc"] for r in subset))
        if aucs:
            print(f"  Scenariusz {sc}: avg AUC-ROC = {np.mean(aucs):.3f}  "
                  f"(min={min(aucs):.3f}, max={max(aucs):.3f}, n={len(aucs)} grafów)")


# ---------------------------------------------------------------------------

_DEFAULT_CSV = _PROJECT_ROOT / "results" / "wyniki_scenariusze.csv"

_CSV_FIELDS = [
    "graph", "scenario", "nodes",
    "train_pos", "val_pos", "test_pos",
    "algorithm",
    "precision", "recall", "f1",
    "auc_roc", "auc_pr",
    "threshold",
]


def save_csv(all_results: list[dict], path: Path) -> None:
    """Zapis wyników w UTF-8 CSV — niezależnie od kodowania terminala."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in all_results:
            row = {k: r.get(k, "") for k in _CSV_FIELDS}
            for k in ("precision", "recall", "f1", "auc_roc", "auc_pr", "threshold"):
                v = row.get(k)
                if isinstance(v, float) and np.isnan(v):
                    row[k] = ""
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Eksperymenty scenariuszowe — broken lineage")
    parser.add_argument("--all",      action="store_true")
    parser.add_argument("--dlg",      nargs="+", type=int)
    parser.add_argument("--scenario", nargs="+", choices=["A","B","C"],
                        default=SCENARIOS)
    parser.add_argument("--no-ml",    action="store_true")
    parser.add_argument("--seed",     type=int, default=42)
    parser.add_argument("--csv",      type=Path, default=_DEFAULT_CSV,
                        help="Ścieżka pliku CSV z wynikami (UTF-8).")
    args = parser.parse_args()

    dlg_ids  = args.dlg if args.dlg else (ALL_DLGS if args.all else DEFAULT_DLGS)
    run_ml   = not args.no_ml
    scenarios = args.scenario

    print(f"Grafy:      {[f'DLG{i}' for i in dlg_ids]}")
    print(f"Scenariusze:{scenarios}")
    print(f"Modele ML:  {'tak' if run_ml else 'nie'}")
    print()

    # Pokaż strukturę ról węzłów dla każdego grafu
    print("Role węzłów Data Table w podgrafie DATA_FLOW:")
    print(f"  {'Graf':<8} {'interm':>7} {'source':>7} {'sink':>7} {'isolated':>9}")
    for dlg_id in dlg_ids:
        G = load_graph(f"DLG{dlg_id}")
        roles = classify_table_roles(G)
        print(f"  DLG{dlg_id:<4} {len(roles['intermediate']):>7} "
              f"{len(roles['source']):>7} {len(roles['sink']):>7} "
              f"{len(roles['isolated']):>9}")
    print()

    all_results = []
    t0 = time.time()

    for dlg_id in dlg_ids:
        for sc in scenarios:
            print(f"DLG{dlg_id} / Scenariusz {sc}...", flush=True)
            results = run_one(dlg_id, sc, seed=args.seed, run_ml=run_ml)
            all_results.extend(results)

    print_table(all_results, scenarios)
    save_csv(all_results, args.csv)
    print(f"\nWyniki zapisane: {args.csv}")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
