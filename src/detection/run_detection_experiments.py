"""
Eksperymenty detekcji zainfekowanych węzłów — protokół INDUKCYJNY (cross-graph).

Dla każdego powtórzenia (seed) i każdego grafu testowego g:
  - usuwamy podzbiór jobów w KAŻDYM grafie (symulacja broken lineage),
  - trenujemy klasyfikator na PULI pozostałych grafów (leave-one-graph-out),
  - oceniamy ranking węzłów grafu g (niewidzianego w treningu).
Metryki uśredniane po powtórzeniach (trim min/max), potem po grafach (per model).

Użycie:
    python src/detection/run_detection_experiments.py            # DLG1-6
    python src/detection/run_detection_experiments.py --all      # 18 grafów
    python src/detection/run_detection_experiments.py --repeats 5 --removal-ratio 0.3
"""

import argparse
import csv
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")  # m.in. LightGBM "valid feature names"

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph
from detection.job_removal import build_node_dataset
from detection.node_classifier import (
    HeuristicNodeScorer, NodeMLClassifier, HEURISTICS, ML_MODELS,
)
from detection.node_metrics import node_detection_metrics

ALL_DLGS = list(range(1, 19))
DEFAULT_DLGS = [1, 2, 3, 4, 5, 6]
MIN_POS = 5  # minimalna liczba zainfekowanych w teście, by metryki były wiarygodne
_METRICS = ["auc_roc", "auc_pr", "precision_at_k", "recall_at_k", "hits_at_k"]


def _trimmed_mean(values: list[float]) -> float:
    vals = sorted(v for v in values if v is not None and not np.isnan(v))
    if not vals:
        return float("nan")
    if len(vals) >= 3:
        vals = vals[1:-1]
    return float(np.mean(vals))


def build_datasets(graphs: dict, removal_ratio: float, seed: int, side: str) -> dict:
    """Buduje instancję (usunięcie jobów) dla każdego grafu przy danym seed."""
    datasets = {}
    for gid, G in graphs.items():
        try:
            datasets[gid] = build_node_dataset(G, removal_ratio, seed, side)
        except ValueError:
            pass  # graf bez jobów łączących — pomijamy
    return datasets


def run_seed(datasets: dict, seed: int) -> list[dict]:
    """Leave-one-graph-out dla jednego seeda. Zwraca wiersze metryk."""
    rows = []
    gids = list(datasets.keys())

    # Scorery (heurystyki bez treningu; ML trenowane per fold)
    heur = {name: HeuristicNodeScorer(name) for name in HEURISTICS}

    for test_g in gids:
        ds_test = datasets[test_g]
        train_pool = [datasets[g] for g in gids if g != test_g]
        n_pos = ds_test["n_infected"]
        reliable = (n_pos >= MIN_POS) and (n_pos < len(ds_test["candidates"]))
        base = {
            "graph": test_g, "seed": seed,
            "n_candidates": len(ds_test["candidates"]),
            "n_infected": n_pos, "reliable": reliable,
        }

        # Heurystyki
        for name, scorer in heur.items():
            scores = scorer.score(ds_test)
            m = node_detection_metrics(ds_test["labels"], scores)
            rows.append({**base, "algorithm": name, **m})

        # ML — trening na puli pozostałych grafów
        for name in ML_MODELS:
            try:
                clf = NodeMLClassifier(name, seed=seed).fit(train_pool)
                scores = clf.score(ds_test)
                m = node_detection_metrics(ds_test["labels"], scores)
                rows.append({**base, "algorithm": name, **m})
            except (ValueError, ImportError) as e:
                print(f"  [{test_g}] {name} pominięto: {e}")
    return rows


def aggregate(all_rows: list[dict]) -> list[dict]:
    """Agreguje po seedach (trim) → jeden wiersz per (graf, algorytm)."""
    by_key: dict = {}
    order: list = []
    for r in all_rows:
        key = (r["graph"], r["algorithm"])
        if key not in by_key:
            by_key[key] = []
            order.append(key)
        by_key[key].append(r)

    agg = []
    for key in order:
        runs = by_key[key]
        first = runs[0]
        rec = {
            "graph": first["graph"], "algorithm": first["algorithm"],
            "n_candidates": first["n_candidates"],
            "n_infected": int(np.mean([r["n_infected"] for r in runs])),
            "reliable": all(r["reliable"] for r in runs),
            "n_runs": len(runs),
        }
        for m in _METRICS:
            rec[m] = _trimmed_mean([r.get(m, float("nan")) for r in runs])
        agg.append(rec)
    return agg


def print_report(agg: list[dict], algorithms: list[str]):
    print(f"\n{'='*96}")
    print("DETEKCJA ZAINFEKOWANYCH WĘZŁÓW — wyniki per graf (indukcyjny, leave-one-out)")
    print(f"{'='*96}")
    print(f"{'Graf':<7} {'Kand.':>6} {'Inf.':>5}  {'Algorytm':<22} "
          f"{'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6} {'R@k':>6} {'Hits@k':>7}")
    print("-" * 96)

    def fmt(v):
        return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "  nan"

    graphs = sorted({r["graph"] for r in agg}, key=lambda g: int(g.replace("DLG", "")))
    for g in graphs:
        rows = [r for r in agg if r["graph"] == g]
        if not rows:
            continue
        rel = "" if rows[0]["reliable"] else " !"
        for i, r in enumerate(rows):
            head = (f"{g:<7} {r['n_candidates']:>6} {r['n_infected']:>4}{rel:<2}"
                    if i == 0 else " " * 21)
            print(f"{head} {r['algorithm']:<22} "
                  f"{fmt(r['auc_roc']):>8} {fmt(r['auc_pr']):>7} "
                  f"{fmt(r['precision_at_k']):>6} {fmt(r['recall_at_k']):>6} "
                  f"{fmt(r['hits_at_k']):>7}")
        print()

    print(f"  ! = #infected < {MIN_POS}: metryki niewiarygodne, wyłączone z agregacji.\n")
    print(f"{'='*96}")
    print("PODSUMOWANIE — średnie metryki per algorytm (tylko grafy wiarygodne)")
    print(f"{'='*96}")
    print(f"  {'Algorytm':<22} {'AUC-ROC':>8} {'AUC-PR':>7} {'P@k':>6} {'R@k':>6} "
          f"{'Hits@k':>7} {'n graf':>7}")
    print("  " + "-" * 70)
    for alg in algorithms:
        cells = [r for r in agg if r["algorithm"] == alg and r["reliable"]]
        aucs = [r["auc_roc"] for r in cells if not np.isnan(r["auc_roc"])]
        if not aucs:
            print(f"  {alg:<22} {'—':>8}")
            continue
        def mean_of(m):
            xs = [r[m] for r in cells if not np.isnan(r[m])]
            return np.mean(xs) if xs else float("nan")
        print(f"  {alg:<22} {np.mean(aucs):>8.3f} {mean_of('auc_pr'):>7.3f} "
              f"{mean_of('precision_at_k'):>6.3f} {mean_of('recall_at_k'):>6.3f} "
              f"{mean_of('hits_at_k'):>7.3f} {len(aucs):>7}")


_CSV_FIELDS = ["graph", "algorithm", "n_candidates", "n_infected", "reliable",
               "n_runs", "auc_roc", "auc_pr", "precision_at_k", "recall_at_k",
               "hits_at_k"]


def save_csv(agg: list[dict], path: Path):
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

    p = argparse.ArgumentParser(description="Detekcja zainfekowanych węzłów (indukcyjny)")
    p.add_argument("--all", action="store_true")
    p.add_argument("--dlg", nargs="+", type=int)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--removal-ratio", type=float, default=0.2)
    p.add_argument("--side", choices=["both", "pred", "succ"], default="both")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_detekcja.csv")
    args = p.parse_args()

    dlg_ids = args.dlg if args.dlg else (ALL_DLGS if args.all else DEFAULT_DLGS)
    seeds = [args.seed + i for i in range(max(1, args.repeats))]
    algorithms = HEURISTICS + ML_MODELS

    print(f"Grafy:        {[f'DLG{i}' for i in dlg_ids]}")
    print(f"Powtórzenia:  {len(seeds)} (seedy {seeds[0]}-{seeds[-1]})")
    print(f"removal_ratio={args.removal_ratio}, side={args.side}, MIN_POS={MIN_POS}")
    print()

    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in dlg_ids}

    t0 = time.time()
    all_rows = []
    for seed in seeds:
        print(f"Seed {seed}...", flush=True)
        datasets = build_datasets(graphs, args.removal_ratio, seed, args.side)
        if len(datasets) < 2:
            print("  Za mało grafów z jobami łączącymi — pomijam seed.")
            continue
        all_rows.extend(run_seed(datasets, seed))

    if not all_rows:
        print("Brak wyników (żaden graf nie miał jobów łączących).")
        return

    agg = aggregate(all_rows)
    print_report(agg, algorithms)
    save_csv(agg, args.csv)
    print(f"\nWyniki zapisane: {args.csv}")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
