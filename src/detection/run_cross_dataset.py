"""
Eksperyment cross-dataset: TEST NA GRAFIE SPOZA ZBIORU DLG-DG-23.

Zachowuje schemat generalizacji do skali (run_scale_generalization):
    trening  = grafy MAŁE + ŚREDNIE z DLG-DG-23,
    test     = grafy DUŻE z DLG-DG-23  ORAZ  zewnętrzny graf Dutkiewicza (DUT).

Pytanie badawcze: czy detektor nauczony na jednym zbiorze (produkcyjny Huawei
Cloud) przenosi się na graf z ZUPEŁNIE INNEGO źródła — bazy Northwind
z syntetycznymi scenariuszami SQL (github.com/dudenzz/lineage)? To mocniejszy
sprawdzian przenośności niż leave-one-graph-out wewnątrz jednego zbioru.

Graf DUT buduje adapter (src/data/dutkiewicz_adapter.py). Jest mały (~21 tabel),
dlatego domyślnie zwiększono liczbę powtórzeń dla stabilności oszacowań.

Użycie:
    python src/detection/run_cross_dataset.py
    python src/detection/run_cross_dataset.py --repeats 15 --removal-ratio 0.2
    python src/detection/run_cross_dataset.py --exclude-isolated
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
from data.dutkiewicz_adapter import build_dutkiewicz_graph, summary
from detection.job_removal import build_node_dataset
from detection.node_metrics import node_detection_metrics
from detection.node_classifier import HEURISTICS, ML_MODELS
from detection.run_scale_generalization import size_class
from detection.run_detection_experiments import (
    _heuristic_score, _make_model, _trimmed_mean, _METRICS, MIN_POS,
    HEUR_NAMES, FIT_MODELS,
)

ALL_DLGS = list(range(1, 19))
DUT_ID = "DUT"


def build_all_datasets(graphs: dict, removal_ratio: float, seed: int,
                       exclude_isolated: bool) -> dict:
    datasets = {}
    for gid, G in graphs.items():
        try:
            datasets[gid] = build_node_dataset(
                G, removal_ratio, seed, "both", exclude_isolated=exclude_isolated)
        except ValueError:
            pass
    return datasets


def run_seed(graphs: dict, seed: int, removal_ratio: float,
             exclude_isolated: bool) -> list[dict]:
    """Trening na małych+średnich DLG; test na dużych DLG + DUT."""
    datasets = build_all_datasets(graphs, removal_ratio, seed, exclude_isolated)

    # Podział wg schematu scale; DUT zawsze do testu (jest spoza DLG-DG-23).
    train_ids = [g for g in datasets
                 if g != DUT_ID and size_class(graphs[g].number_of_nodes()) != "duży"]
    test_ids = [g for g in datasets
                if g == DUT_ID or size_class(graphs[g].number_of_nodes()) == "duży"]
    if not train_ids or not test_ids:
        return []

    train_pool = [datasets[g] for g in train_ids]
    fitted = {}
    for name in FIT_MODELS:
        try:
            fitted[name] = _make_model(name, seed).fit(train_pool)
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
            "external": (test_g == DUT_ID),
        }
        for name in HEUR_NAMES:
            m = node_detection_metrics(ds["labels"], _heuristic_score(name, ds))
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
            "external": f["external"],
            "reliable": all(r["reliable"] for r in runs), "n_runs": len(runs),
        }
        for m in _METRICS:
            rec[m] = _trimmed_mean([r.get(m, float("nan")) for r in runs])
        agg.append(rec)
    return agg


def _fmt(v):
    return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "  nan"


def print_report(agg: list[dict], algorithms: list[str]):
    graphs = sorted({r["graph"] for r in agg},
                    key=lambda g: (g == DUT_ID, g))  # DUT na końcu

    print(f"\n{'='*94}")
    print("CROSS-DATASET — trening: małe+średnie DLG; test: duże DLG + graf Dutkiewicza (DUT)")
    print(f"{'='*94}")
    print(f"{'Graf':<8} {'Kand.':>6} {'Inf.':>5}  {'Algorytm':<22} "
          f"{'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6} {'Brier':>7}")
    print("-" * 94)
    for g in graphs:
        rows = [r for r in agg if r["graph"] == g]
        tag = "  (ZEWN.)" if rows and rows[0]["external"] else ""
        rel = "" if rows and rows[0]["reliable"] else " !"
        for i, r in enumerate(rows):
            head = (f"{g:<8}{tag[:0]:<0}{r['n_candidates']:>6} {r['n_infected']:>4}{rel:<2}"
                    if i == 0 else " " * 22)
            print(f"{head} {r['algorithm']:<22} {_fmt(r['auc_roc']):>8} "
                  f"{_fmt(r['auc_pr']):>7} {_fmt(r['precision_at_k']):>6} "
                  f"{_fmt(r['brier']):>7}")
        if rows:
            print(f"   ^ {g}{tag}  (! = #infected<{MIN_POS})\n")

    # Wyróżniony blok: sam graf zewnętrzny.
    print(f"{'='*94}")
    print("WYNIK NA GRAFIE ZEWNĘTRZNYM (DUT) — przenośność poza DLG-DG-23")
    print(f"{'='*94}")
    print(f"  {'Algorytm':<22} {'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6} {'Brier':>7}")
    print("  " + "-" * 55)
    for alg in algorithms:
        cells = [r for r in agg if r["algorithm"] == alg and r["graph"] == DUT_ID]
        if not cells:
            continue
        r = cells[0]
        print(f"  {alg:<22} {_fmt(r['auc_roc']):>8} {_fmt(r['auc_pr']):>7} "
              f"{_fmt(r['precision_at_k']):>6} {_fmt(r['brier']):>7}")

    print(f"\n{'='*94}")
    print("PODSUMOWANIE — średnia po DUŻYCH grafach DLG (odniesienie wewnątrz zbioru)")
    print(f"{'='*94}")
    print(f"  {'Algorytm':<22} {'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6} {'n graf':>7}")
    print("  " + "-" * 60)
    for alg in algorithms:
        cells = [r for r in agg if r["algorithm"] == alg
                 and not r["external"] and r["reliable"]]
        aucs = [r["auc_roc"] for r in cells if not np.isnan(r["auc_roc"])]
        if not aucs:
            print(f"  {alg:<22} {'—':>8}")
            continue
        def mean_of(m):
            xs = [r[m] for r in cells if not np.isnan(r[m])]
            return np.mean(xs) if xs else float("nan")
        print(f"  {alg:<22} {np.mean(aucs):>8.3f} {mean_of('auc_pr'):>7.3f} "
              f"{mean_of('precision_at_k'):>6.3f} {len(aucs):>7}")


_CSV_FIELDS = ["graph", "algorithm", "n_candidates", "n_infected", "external",
               "reliable", "n_runs", "auc_roc", "auc_pr", "precision_at_k",
               "recall_at_k", "hits_at_k", "brier"]


def save_csv(agg, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in agg:
            row = {k: r.get(k, "") for k in _CSV_FIELDS}
            for k in ("auc_roc", "auc_pr", "precision_at_k", "recall_at_k",
                      "hits_at_k", "brier"):
                if isinstance(row.get(k), float) and np.isnan(row[k]):
                    row[k] = ""
            w.writerow(row)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Test cross-dataset (DLG-DG-23 → graf Dutkiewicza)")
    p.add_argument("--repeats", type=int, default=15,
                   help="Liczba powtórzeń (więcej dla stabilności małego grafu DUT).")
    p.add_argument("--removal-ratio", type=float, default=0.2)
    p.add_argument("--exclude-isolated", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_cross_dataset.csv")
    args = p.parse_args()

    seeds = [args.seed + i for i in range(max(1, args.repeats))]
    algorithms = HEUR_NAMES + FIT_MODELS

    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in ALL_DLGS}
    graphs[DUT_ID] = build_dutkiewicz_graph()

    small = [g for g in graphs if g != DUT_ID and size_class(graphs[g].number_of_nodes()) == "mały"]
    med = [g for g in graphs if g != DUT_ID and size_class(graphs[g].number_of_nodes()) == "średni"]
    large = [g for g in graphs if g != DUT_ID and size_class(graphs[g].number_of_nodes()) == "duży"]
    print("GRAF ZEWNĘTRZNY (DUT):", summary(graphs[DUT_ID]))
    print(f"Trening: {len(small)} małych + {len(med)} średnich = {sorted(small+med)}")
    print(f"Test:    {len(large)} dużych DLG {sorted(large)} + DUT (zewnętrzny)")
    print(f"Powtórzenia: {len(seeds)}, removal_ratio={args.removal_ratio}, "
          f"exclude_isolated={args.exclude_isolated}, MIN_POS={MIN_POS}\n")

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
