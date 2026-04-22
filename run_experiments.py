"""
Uruchamia wszystkie algorytmy na grafach DLG-DG-23 i drukuje tabelę wyników.

Użycie:
    python run_experiments.py              # DLG1–DLG4, losowy split
    python run_experiments.py --all        # wszystkie 18 grafów, losowy split
    python run_experiments.py --dlg 4 7    # wybrane grafy
    python run_experiments.py --scenarios  # dodatkowo scenariusze A/B/C
    python run_experiments.py --all --scenarios --no-ml  # szybko, bez ML

Opcje:
    --all          uruchom na wszystkich 18 grafach
    --dlg N [N...] uruchom tylko na wybranych grafach (np. --dlg 1 4)
    --no-ml        pomiń modele ML (RF, RUSBoost, LightGBM, Node2Vec)
    --scenarios    dodatkowo uruchom strukturalne scenariusze A/B/C
    --seed N       ziarno losowości (domyślnie 42)
"""

import argparse
import sys
import time
import warnings

import numpy as np

warnings.filterwarnings("ignore")

sys.path.insert(0, "src")
from data.loader import load_graph
from data.splitter import split_edges
from data.scenario_splitter import scenario_split
from algorithms.heuristics import score_all_methods
from algorithms.classical_ml import (
    GraphMLClassifier, RUSBoostGraphClassifier, LightGBMGraphClassifier,
)
from algorithms.node2vec_ml import Node2VecMLPClassifier
from evaluation.metrics import evaluate_split, best_threshold_f1


# ---------------------------------------------------------------------------
# Konfiguracja
# ---------------------------------------------------------------------------

DEFAULT_DLGS = [1, 2, 3, 4]   # małe grafy — szybki podgląd
ALL_DLGS     = list(range(1, 19))

HEURISTICS = [
    "common_neighbors",
    "jaccard",
    "adamic_adar",
    "preferential_attachment",
    "l3",
    "katz",
    "ppr",
]

ML_MODELS = {
    "RandomForest":  GraphMLClassifier,
    "RUSBoost":      RUSBoostGraphClassifier,
    "LightGBM":      LightGBMGraphClassifier,
    "Node2Vec+MLP":  Node2VecMLPClassifier,
}


# ---------------------------------------------------------------------------
# Uruchomienie jednego grafu
# ---------------------------------------------------------------------------

def run_one(dlg_id: int, seed: int, run_ml: bool) -> list[dict]:
    """
    Wczytuje DLG{dlg_id}, dzieli krawędzie 80/20, ocenia wszystkie algorytmy.
    Zwraca listę słowników wyników.
    """
    label = f"DLG{dlg_id}"
    G = load_graph(label)

    try:
        splits = split_edges(G, edge_type="DATA_FLOW", test_ratio=0.2, seed=seed)
    except ValueError as e:
        print(f"  [{label}] Pominięto: {e}")
        return []

    n_nodes = G.number_of_nodes()
    n_train = len(splits["pos_train"])
    n_test  = len(splits["pos_test"])

    algo_results = _run_algorithms(splits["G_train"], splits, run_ml, seed)
    return [
        {"graph": label, "nodes": n_nodes,
         "train_pos": n_train, "test_pos": n_test, **r}
        for r in algo_results
    ]


# ---------------------------------------------------------------------------
# Drukowanie tabeli
# ---------------------------------------------------------------------------

def print_table(all_results: list[dict]):
    if not all_results:
        print("Brak wyników.")
        return

    # Nagłówek
    COL = 24
    print()
    print("=" * 100)
    print(f"{'Graf':<8} {'Węzły':>6} {'Tr+':>5} {'Te+':>5}  "
          f"{'Algorytm':<{COL}}  {'P':>6} {'R':>6} {'F1':>6} {'AUC-ROC':>8} {'AUC-PR':>7}")
    print("-" * 100)

    prev_graph = None
    for r in all_results:
        if r["graph"] != prev_graph and prev_graph is not None:
            print()
        prev_graph = r["graph"]

        def fmt(v):
            return f"{v:.3f}" if not (isinstance(v, float) and np.isnan(v)) else "  nan"

        print(
            f"{r['graph']:<8} {r['nodes']:>6} {r['train_pos']:>5} {r['test_pos']:>5}  "
            f"{r['algorithm']:<{COL}}  "
            f"{fmt(r['precision']):>6} {fmt(r['recall']):>6} "
            f"{fmt(r['f1']):>6} {fmt(r['auc_roc']):>8} {fmt(r['auc_pr']):>7}"
        )

    print("=" * 100)

    # Podsumowanie: najlepszy F1 per graf
    from itertools import groupby
    print("\nNajlepszy F1 per graf:")
    graphs = sorted(set(r["graph"] for r in all_results))
    for g in graphs:
        subset = [r for r in all_results if r["graph"] == g
                  and not np.isnan(r["f1"])]
        if subset:
            best = max(subset, key=lambda x: x["f1"])
            print(f"  {g}: {best['algorithm']:<24}  F1={best['f1']:.3f}  AUC-ROC={best['auc_roc']:.3f}")


# ---------------------------------------------------------------------------
# Eksperymenty scenariuszowe A / B / C
# ---------------------------------------------------------------------------

def _run_algorithms(G_train, splits, run_ml, seed) -> list[dict]:
    """
    Wspólna logika: heurystyki + (opcjonalnie) modele ML na gotowym splicie.
    Zwraca listę słowników z metrykami, bez pól 'graph' / 'nodes' / etc.
    """
    pos_test  = splits["pos_test"]
    neg_test  = splits["neg_test"]
    pos_train = splits["pos_train"]
    neg_train = splits["neg_train"]
    test_edges = pos_test + neg_test
    y_true = np.array([1] * len(pos_test) + [0] * len(neg_test))

    results = []

    # --- Heurystyki ---
    scores_dict = score_all_methods(G_train, test_edges)
    for method in HEURISTICS:
        scores = scores_dict[method]
        t = best_threshold_f1(y_true, scores) if len(np.unique(scores)) > 1 else 0.5
        m = evaluate_split(splits, scores, threshold=t)
        results.append({"algorithm": method, **m})

    if not run_ml:
        return results

    # --- Modele ML ---
    for model_name, ModelClass in ML_MODELS.items():
        try:
            clf = ModelClass(seed=seed)
            clf.fit(G_train, pos_train, neg_train)
            scores = clf.predict_proba(G_train, test_edges)
            m = evaluate_split(splits, scores, threshold=0.5)
            results.append({"algorithm": model_name, **m})
        except Exception as e:
            print(f"    {model_name} błąd: {e}")

    return results


def run_scenarios(dlg_id: int, seed: int, run_ml: bool) -> list[dict]:
    """
    Dla DLG{dlg_id} uruchamia scenariusze A, B, C.
    Zwraca listę wyników z polem 'scenario'.
    """
    label = f"DLG{dlg_id}"
    G = load_graph(label)
    n_nodes = G.number_of_nodes()

    results = []
    for sc in ("A", "B", "C"):
        try:
            splits = scenario_split(G, scenario=sc, seed=seed)
        except ValueError as e:
            print(f"  [{label}] Scenariusz {sc} pominięty: {e}")
            continue

        G_train   = splits["G_train"]
        n_train   = len(splits["pos_train"])
        n_test    = len(splits["pos_test"])

        print(f"  [{label}] Scenariusz {sc}: train_pos={n_train} test_pos={n_test}", flush=True)
        algo_results = _run_algorithms(G_train, splits, run_ml, seed)

        for r in algo_results:
            results.append({
                "graph":     label,
                "scenario":  sc,
                "nodes":     n_nodes,
                "train_pos": n_train,
                "test_pos":  n_test,
                **r,
            })

    return results


def print_scenario_table(all_results: list[dict]):
    """Tabela wyników dla eksperymentów scenariuszowych."""
    if not all_results:
        print("Brak wyników scenariuszowych.")
        return

    COL = 24
    print()
    print("=" * 110)
    print("WYNIKI SCENARIUSZOWE (A=staging, B=UDF/source, C=sink/data-mart)")
    print("=" * 110)
    print(f"{'Graf':<8} {'Sc':>3} {'Węzły':>6} {'Tr+':>5} {'Te+':>5}  "
          f"{'Algorytm':<{COL}}  {'P':>6} {'R':>6} {'F1':>6} {'AUC-ROC':>8} {'AUC-PR':>7}")
    print("-" * 110)

    prev_key = None
    for r in all_results:
        key = (r["graph"], r["scenario"])
        if key != prev_key and prev_key is not None:
            print()
        prev_key = key

        def fmt(v):
            return f"{v:.3f}" if not (isinstance(v, float) and np.isnan(v)) else "  nan"

        print(
            f"{r['graph']:<8} {r['scenario']:>3} {r['nodes']:>6} "
            f"{r['train_pos']:>5} {r['test_pos']:>5}  "
            f"{r['algorithm']:<{COL}}  "
            f"{fmt(r['precision']):>6} {fmt(r['recall']):>6} "
            f"{fmt(r['f1']):>6} {fmt(r['auc_roc']):>8} {fmt(r['auc_pr']):>7}"
        )

    print("=" * 110)

    # Najlepszy F1 per (graf, scenariusz)
    print("\nNajlepszy F1 per (graf, scenariusz):")
    keys = sorted(set((r["graph"], r["scenario"]) for r in all_results))
    for g, sc in keys:
        subset = [r for r in all_results
                  if r["graph"] == g and r["scenario"] == sc
                  and not np.isnan(r["f1"])]
        if subset:
            best = max(subset, key=lambda x: x["f1"])
            print(f"  {g} [{sc}]: {best['algorithm']:<24}  F1={best['f1']:.3f}  AUC-ROC={best['auc_roc']:.3f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Eksperymenty link prediction — DLG-DG-23")
    parser.add_argument("--all",       action="store_true", help="wszystkie 18 grafów")
    parser.add_argument("--dlg",       nargs="+", type=int,  help="wybrane numery grafów, np. --dlg 1 4")
    parser.add_argument("--no-ml",     action="store_true", help="pomiń modele ML")
    parser.add_argument("--scenarios", action="store_true", help="uruchom scenariusze A/B/C")
    parser.add_argument("--seed",      type=int, default=42, help="ziarno losowości")
    args = parser.parse_args()

    if args.dlg:
        dlg_ids = args.dlg
    elif args.all:
        dlg_ids = ALL_DLGS
    else:
        dlg_ids = DEFAULT_DLGS

    run_ml = not args.no_ml

    print(f"Grafy: {[f'DLG{i}' for i in dlg_ids]}")
    print(f"Modele ML: {'tak' if run_ml else 'nie (--no-ml)'}")
    print(f"Scenariusze A/B/C: {'tak' if args.scenarios else 'nie'}")
    print(f"Seed: {args.seed}")
    print()

    t0 = time.time()

    # --- Losowy split (zawsze) ---
    print(">>> Losowy split 80/20")
    all_results = []
    for dlg_id in dlg_ids:
        print(f"DLG{dlg_id}...", flush=True)
        all_results.extend(run_one(dlg_id, seed=args.seed, run_ml=run_ml))
    print_table(all_results)

    # --- Scenariusze (opcjonalnie) ---
    if args.scenarios:
        print("\n>>> Scenariusze strukturalne A/B/C")
        sc_results = []
        for dlg_id in dlg_ids:
            print(f"DLG{dlg_id} — scenariusze:", flush=True)
            sc_results.extend(run_scenarios(dlg_id, seed=args.seed, run_ml=run_ml))
        print_scenario_table(sc_results)

    print(f"\nCzas łączny: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
