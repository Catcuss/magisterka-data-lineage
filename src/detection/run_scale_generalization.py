"""
Eksperyment porównawczy 1: GENERALIZACJA DO SKALI.

Trenujemy WYŁĄCZNIE na grafach małych i średnich, testujemy na DUŻYCH.
Pytanie: czy wzorce nauczone na małych grafach przenoszą się na duże
(realny scenariusz: model uczony na tańszych, małych bazach, wdrażany na dużej).

Podział wg liczby węzłów: mały <1000, średni 1000-5000, duży >5000.
Trening = małe + średnie; test = każdy duży graf osobno (indukcyjnie).

Użycie:
    python src/detection/run_scale_generalization.py
    python src/detection/run_scale_generalization.py --exclude-isolated --repeats 5
"""

import argparse
import csv
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph
from detection.job_removal import build_node_dataset
from detection.node_classifier import (
    HeuristicNodeScorer, NodeMLClassifier, HEURISTICS, ML_MODELS,
)
from detection.node_metrics import node_detection_metrics
from detection.run_detection_experiments import _trimmed_mean, _METRICS, MIN_POS

ALL_DLGS = list(range(1, 19))


def size_class(n_nodes: int) -> str:
    if n_nodes > 5000:
        return "duży"
    if n_nodes >= 1000:
        return "średni"
    return "mały"


def run_seed(graphs: dict, seed: int, removal_ratio: float,
             exclude_isolated: bool) -> list[dict]:
    """Trening na małych+średnich, test na każdym dużym."""
    datasets = {}
    for gid, G in graphs.items():
        try:
            datasets[gid] = build_node_dataset(
                G, removal_ratio, seed, "both", exclude_isolated=exclude_isolated)
        except ValueError:
            pass

    train_ids = [g for g in datasets if size_class(graphs[g].number_of_nodes()) != "duży"]
    test_ids = [g for g in datasets if size_class(graphs[g].number_of_nodes()) == "duży"]
    if not train_ids or not test_ids:
        return []

    train_pool = [datasets[g] for g in train_ids]
    heur = {name: HeuristicNodeScorer(name) for name in HEURISTICS}
    fitted = {}
    for name in ML_MODELS:
        try:
            fitted[name] = NodeMLClassifier(name, seed=seed).fit(train_pool)
        except (ValueError, ImportError) as e:
            print(f"  {name} pominięto: {e}")

    rows = []
    for test_g in test_ids:
        ds = datasets[test_g]
        n_pos = ds["n_infected"]
        base = {
            "graph": test_g, "seed": seed,
            "n_candidates": len(ds["candidates"]), "n_infected": n_pos,
            "reliable": (n_pos >= MIN_POS) and (n_pos < len(ds["candidates"])),
            "n_train_graphs": len(train_ids),
        }
        for name, scorer in heur.items():
            m = node_detection_metrics(ds["labels"], scorer.score(ds))
            rows.append({**base, "algorithm": name, **m})
        for name, clf in fitted.items():
            m = node_detection_metrics(ds["labels"], clf.score(ds))
            rows.append({**base, "algorithm": name, **m})
    return rows


def aggregate(all_rows: list[dict]) -> list[dict]:
    by_key, order = {}, []
    for r in all_rows:
        key = (r["graph"], r["algorithm"])
        if key not in by_key:
            by_key[key] = []
            order.append(key)
        by_key[key].append(r)
    agg = []
    for key in order:
        runs = by_key[key]
        f = runs[0]
        rec = {
            "graph": f["graph"], "algorithm": f["algorithm"],
            "n_candidates": f["n_candidates"],
            "n_infected": int(np.mean([r["n_infected"] for r in runs])),
            "n_train_graphs": f["n_train_graphs"],
            "reliable": all(r["reliable"] for r in runs), "n_runs": len(runs),
        }
        for m in _METRICS:
            rec[m] = _trimmed_mean([r.get(m, float("nan")) for r in runs])
        agg.append(rec)
    return agg


def print_report(agg: list[dict], algorithms: list[str]):
    print(f"\n{'='*92}")
    print("GENERALIZACJA DO SKALI — trening na małych+średnich, test na dużych")
    print(f"{'='*92}")
    print(f"{'Graf (duży)':<12} {'Kand.':>6} {'Inf.':>5}  {'Algorytm':<22} "
          f"{'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6}")
    print("-" * 92)

    def fmt(v):
        return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "  nan"

    graphs = sorted({r["graph"] for r in agg}, key=lambda g: int(g.replace("DLG", "")))
    for g in graphs:
        rows = [r for r in agg if r["graph"] == g]
        for i, r in enumerate(rows):
            head = (f"{g:<12} {r['n_candidates']:>6} {r['n_infected']:>5}"
                    if i == 0 else " " * 25)
            print(f"{head}  {r['algorithm']:<22} {fmt(r['auc_roc']):>8} "
                  f"{fmt(r['auc_pr']):>7} {fmt(r['precision_at_k']):>6}")
        print()

    print(f"{'='*92}")
    print("PODSUMOWANIE — średnia po dużych grafach testowych")
    print(f"{'='*92}")
    print(f"  {'Algorytm':<22} {'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6} {'n graf':>7}")
    print("  " + "-" * 55)
    for alg in algorithms:
        cells = [r for r in agg if r["algorithm"] == alg and r["reliable"]]
        aucs = [r["auc_roc"] for r in cells if not np.isnan(r["auc_roc"])]
        if not aucs:
            print(f"  {alg:<22} {'—':>8}")
            continue
        prs = [r["auc_pr"] for r in cells if not np.isnan(r["auc_pr"])]
        pks = [r["precision_at_k"] for r in cells if not np.isnan(r["precision_at_k"])]
        print(f"  {alg:<22} {np.mean(aucs):>8.3f} {np.mean(prs):>7.3f} "
              f"{np.mean(pks):>6.3f} {len(aucs):>7}")


_CSV_FIELDS = ["graph", "algorithm", "n_candidates", "n_infected", "n_train_graphs",
               "reliable", "n_runs", "auc_roc", "auc_pr", "precision_at_k",
               "recall_at_k", "hits_at_k"]


def save_csv(agg, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in agg:
            row = {k: r.get(k, "") for k in _CSV_FIELDS}
            for k in ("auc_roc", "auc_pr", "precision_at_k", "recall_at_k", "hits_at_k"):
                if isinstance(row.get(k), float) and np.isnan(row[k]):
                    row[k] = ""
            w.writerow(row)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Generalizacja do skali (małe+średnie → duże)")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--removal-ratio", type=float, default=0.2)
    p.add_argument("--exclude-isolated", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_skala.csv")
    args = p.parse_args()

    seeds = [args.seed + i for i in range(max(1, args.repeats))]
    algorithms = HEURISTICS + ML_MODELS
    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in ALL_DLGS}

    small = [g for g in graphs if size_class(graphs[g].number_of_nodes()) == "mały"]
    med = [g for g in graphs if size_class(graphs[g].number_of_nodes()) == "średni"]
    large = [g for g in graphs if size_class(graphs[g].number_of_nodes()) == "duży"]
    print(f"Trening: {len(small)} małych + {len(med)} średnich = {sorted(small+med)}")
    print(f"Test (duże): {sorted(large)}")
    print(f"Powtórzenia: {len(seeds)}, removal_ratio={args.removal_ratio}, "
          f"exclude_isolated={args.exclude_isolated}\n")

    t0 = time.time()
    all_rows = []
    for seed in seeds:
        print(f"Seed {seed}...", flush=True)
        all_rows.extend(run_seed(graphs, seed, args.removal_ratio, args.exclude_isolated))

    if not all_rows:
        print("Brak wyników.")
        return
    agg = aggregate(all_rows)
    print_report(agg, algorithms)
    save_csv(agg, args.csv)
    print(f"\nWyniki zapisane: {args.csv}")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
