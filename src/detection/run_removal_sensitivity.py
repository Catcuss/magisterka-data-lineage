"""
Analiza wrażliwości — czy wynik detekcji zależy od odsetka usuwanych jobów?

Uruchamia protokół indukcyjny (leave-one-graph-out, exclude_isolated) dla kilku
wartości removal_ratio i pokazuje średni AUC-ROC per algorytm. Stabilny wynik =
metoda nie jest artefaktem doboru ratio (argument anty-podważeniowy w pracy).

Użycie:
    python src/detection/run_removal_sensitivity.py --all --repeats 3
"""

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph
from detection.run_detection_experiments import (
    build_datasets, run_seed, aggregate, ALL_ALGOS,
)

ALL_DLGS = list(range(1, 19))
DEFAULT_RATIOS = [0.05, 0.10, 0.20, 0.30]
KEY_ALGOS = ["LineageDetector", "LightGBM", "RandomForest", "completeness", "rule_root"]


def mean_auc_per_algo(agg: list[dict]) -> dict:
    out = {}
    for alg in ALL_ALGOS:
        aucs = [r["auc_roc"] for r in agg
                if r["algorithm"] == alg and r["reliable"]
                and not np.isnan(r["auc_roc"])]
        out[alg] = (float(np.mean(aucs)), len(aucs)) if aucs else (float("nan"), 0)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="Wrażliwość detekcji na removal_ratio")
    p.add_argument("--all", action="store_true")
    p.add_argument("--dlg", nargs="+", type=int)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--ratios", nargs="+", type=float, default=DEFAULT_RATIOS)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    dlg_ids = args.dlg if args.dlg else (ALL_DLGS if args.all else [1, 2, 3, 4, 5, 6])
    seeds = [args.seed + i for i in range(max(1, args.repeats))]
    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in dlg_ids}

    print(f"Grafy: {sorted(graphs)} | ratios: {args.ratios} | powtórzenia: {len(seeds)}")
    print("Protokół: indukcyjny leave-one-graph-out, exclude_isolated=True\n")

    t0 = time.time()
    results = {}  # ratio -> {alg: (auc, n)}
    for rr in args.ratios:
        print(f"removal_ratio={rr}...", flush=True)
        all_rows = []
        for seed in seeds:
            datasets = build_datasets(graphs, rr, seed, "both", exclude_isolated=True)
            if len(datasets) >= 2:
                all_rows.extend(run_seed(datasets, seed))
        results[rr] = mean_auc_per_algo(aggregate(all_rows)) if all_rows else {}

    print(f"\n{'='*80}")
    print("ŚREDNI AUC-ROC per algorytm wg removal_ratio (grafy wiarygodne)")
    print(f"{'='*80}")
    header = f"{'Algorytm':<22}" + "".join(f"{f'r={rr}':>10}" for rr in args.ratios)
    print(header)
    print("-" * len(header))
    for alg in KEY_ALGOS:
        row = f"{alg:<22}"
        for rr in args.ratios:
            auc, n = results[rr].get(alg, (float("nan"), 0))
            row += f"{(f'{auc:.3f}' if not np.isnan(auc) else 'nan'):>10}"
        print(row)
    print(f"\nStabilność = małe wahania w wierszu → wynik nie jest artefaktem ratio.")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
