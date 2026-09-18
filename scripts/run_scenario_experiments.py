"""
Eksperymenty na scenariuszach broken lineage (strukturalny podział krawędzi).

W przeciwieństwie do losowego podziału krawędzi 80/20, tutaj krawędzie
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

# Minimalna liczba pozytywów w teście, by metryki uznać za wiarygodne.
# Poniżej tej wartości AUROC/Hits@k mają zbyt duży rozrzut, by je interpretować.
MIN_TEST_POS = 10

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


def run_one(dlg_id: int, scenario: str, seed: int, run_ml: bool,
            val_ratio: float = 0.2, neg_ratio: float = 5.0) -> list[dict]:
    label = f"DLG{dlg_id}"
    G = load_graph(label)

    try:
        splits = scenario_split(G, scenario=scenario, val_ratio=val_ratio,
                                neg_ratio=neg_ratio, seed=seed)
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


_AGG_METRICS = ["precision", "recall", "f1", "auc_roc", "auc_pr", "hits_at_k"]


def _trimmed_mean(values: list[float]) -> float:
    """Średnia po odrzuceniu nan oraz (gdy ≥3 próbek) jednego min i max."""
    vals = sorted(v for v in values if v is not None and not np.isnan(v))
    if not vals:
        return float("nan")
    if len(vals) >= 3:
        vals = vals[1:-1]
    return float(np.mean(vals))


def run_repeated(dlg_id: int, scenario: str, seeds: list[int], run_ml: bool,
                 val_ratio: float, neg_ratio: float) -> list[dict]:
    """
    Uruchamia run_one dla każdego seeda i agreguje metryki per algorytm.

    Protokół powtórzeń (za Dutkiewicz, Misiorek, Wrembel 2026): powtórz N razy,
    odrzuć skrajne (min/max) wartości metryki, raportuj średnią z pozostałych.
    Dodaje pole 'reliable' (test_pos ≥ MIN_TEST_POS) oraz 'n_runs'.
    """
    by_alg: dict[str, list[dict]] = {}
    order: list[str] = []
    for seed in seeds:
        for r in run_one(dlg_id, scenario, seed, run_ml, val_ratio, neg_ratio):
            alg = r["algorithm"]
            if alg not in by_alg:
                by_alg[alg] = []
                order.append(alg)
            by_alg[alg].append(r)

    aggregated = []
    for alg in order:
        runs = by_alg[alg]
        first = runs[0]
        test_pos = float(np.mean([r["test_pos"] for r in runs]))
        agg = {
            "graph": first["graph"], "scenario": scenario,
            "nodes": first["nodes"],
            "train_pos": int(np.mean([r["train_pos"] for r in runs])),
            "val_pos":   int(np.mean([r.get("val_pos", 0) for r in runs])),
            "test_pos":  int(round(test_pos)),
            "algorithm": alg,
            "n_runs":    len(runs),
            "reliable":  test_pos >= MIN_TEST_POS,
        }
        for m in _AGG_METRICS:
            agg[m] = _trimmed_mean([r.get(m, float("nan")) for r in runs])
        aggregated.append(agg)
    return aggregated


def print_table(all_results: list[dict], scenarios: list[str]):
    if not all_results:
        print("Brak wyników.")
        return

    for sc in scenarios:
        rows = [r for r in all_results if r["scenario"] == sc]
        if not rows:
            continue

        print(f"\n{'='*108}")
        print(f"SCENARIUSZ {sc}: {SCENARIO_LABELS[sc]}")
        print(f"{'='*108}")
        print(f"{'Graf':<8} {'Węzły':>6} {'Tr+':>5} {'Va+':>4} {'Te+':>5}  "
              f"{'Algorytm':<24}  {'AUC-ROC':>8} {'AUC-PR':>7} {'Hits@k':>7} "
              f"{'F1':>6}")
        print("-" * 108)

        def fmt(v):
            return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "  nan"

        prev = None
        for r in rows:
            if r["graph"] != prev and prev is not None:
                print()
            prev = r["graph"]
            mark = "" if r.get("reliable", True) else " !"  # mały zbiór testowy
            print(
                f"{r['graph']:<8} {r['nodes']:>6} {r['train_pos']:>5} "
                f"{r.get('val_pos', 0):>4} {r['test_pos']:>5}{mark:<2} "
                f"{r['algorithm']:<24}  "
                f"{fmt(r['auc_roc']):>8} {fmt(r['auc_pr']):>7} "
                f"{fmt(r.get('hits_at_k', float('nan'))):>7} {fmt(r['f1']):>6}"
            )

    print(f"\n  ! = test_pos < {MIN_TEST_POS}: metryki o dużym rozrzucie, wyłączone z agregacji.")

    # Podsumowanie: średni AUC-ROC / Hits@k per algorytm.
    # Liczone tylko na grafach wiarygodnych (test_pos ≥ MIN_TEST_POS).
    print(f"\n{'='*108}")
    print("PODSUMOWANIE — średni AUC-ROC i Hits@k per algorytm (tylko grafy wiarygodne)")
    print(f"{'='*108}")
    algorithms = []
    for r in all_results:
        if r["algorithm"] not in algorithms:
            algorithms.append(r["algorithm"])

    for sc in scenarios:
        print(f"\nScenariusz {sc}:")
        print(f"  {'Algorytm':<24} {'avg AUC-ROC':>12} {'avg Hits@k':>12} {'n grafów':>9}")
        print("  " + "-" * 60)
        for alg in algorithms:
            cells = [r for r in all_results
                     if r["scenario"] == sc and r["algorithm"] == alg
                     and r.get("reliable", True)]
            aucs = [r["auc_roc"] for r in cells if not np.isnan(r.get("auc_roc", float("nan")))]
            hits = [r["hits_at_k"] for r in cells if not np.isnan(r.get("hits_at_k", float("nan")))]
            if aucs:
                print(f"  {alg:<24} {np.mean(aucs):>12.3f} "
                      f"{(np.mean(hits) if hits else float('nan')):>12.3f} {len(aucs):>9}")
            else:
                print(f"  {alg:<24} {'—':>12} {'—':>12} {0:>9}")


_DEFAULT_CSV = _PROJECT_ROOT / "results" / "wyniki_scenariusze.csv"

_CSV_FIELDS = [
    "graph", "scenario", "nodes",
    "train_pos", "val_pos", "test_pos",
    "algorithm", "n_runs", "reliable",
    "auc_roc", "auc_pr", "hits_at_k",
    "precision", "recall", "f1",
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
            for k in ("precision", "recall", "f1", "auc_roc", "auc_pr",
                      "hits_at_k", "threshold"):
                v = row.get(k)
                if isinstance(v, float) and np.isnan(v):
                    row[k] = ""
            writer.writerow(row)


def main():
    # Wymuś UTF-8 na stdout — inaczej polskie znaki/symbole psują się w konsoli
    # Windows (cp1250) i przekierowanie do pliku daje mojibake.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Eksperymenty scenariuszowe — broken lineage")
    parser.add_argument("--all",      action="store_true")
    parser.add_argument("--dlg",      nargs="+", type=int)
    parser.add_argument("--scenario", nargs="+", choices=["A","B","C"],
                        default=SCENARIOS)
    parser.add_argument("--no-ml",    action="store_true")
    parser.add_argument("--seed",     type=int, default=42)
    parser.add_argument("--repeats",  type=int, default=5,
                        help="Liczba powtórzeń z różnymi seedami; metryki "
                             "uśredniane po odrzuceniu skrajnych (min/max).")
    parser.add_argument("--neg-ratio", type=float, default=5.0,
                        help="Stosunek negatywów do pozytywów (TGD: 50, "
                             "realny broken lineage to silna nierównowaga).")
    parser.add_argument("--csv",      type=Path, default=_DEFAULT_CSV,
                        help="Ścieżka pliku CSV z wynikami (UTF-8).")
    args = parser.parse_args()

    dlg_ids  = args.dlg if args.dlg else (ALL_DLGS if args.all else DEFAULT_DLGS)
    run_ml   = not args.no_ml
    scenarios = args.scenario
    seeds    = [args.seed + i for i in range(max(1, args.repeats))]

    print(f"Grafy:      {[f'DLG{i}' for i in dlg_ids]}")
    print(f"Scenariusze:{scenarios}")
    print(f"Modele ML:  {'tak' if run_ml else 'nie'}")
    print(f"Powtórzenia:{len(seeds)} (seedy {seeds[0]}–{seeds[-1]}), neg_ratio={args.neg_ratio}")
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
            results = run_repeated(dlg_id, sc, seeds=seeds, run_ml=run_ml,
                                   val_ratio=0.2, neg_ratio=args.neg_ratio)
            all_results.extend(results)

    print_table(all_results, scenarios)
    save_csv(all_results, args.csv)
    print(f"\nWyniki zapisane: {args.csv}")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
