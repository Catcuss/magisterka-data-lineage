"""
Eksperyment porównawczy 2: PODEJŚCIE TRANSDUKTYWNE (w obrębie jednego grafu).

Dla każdego grafu (średniego/dużego) dzielimy JEGO węzły na train/test
(podział stratyfikowany). Model uczy się na części węzłów tego samego grafu
i przewiduje pozostałe. To paradygmat transduktywny — w przeciwieństwie do
indukcyjnego cross-graph (run_detection_experiments.py), gdzie test to graf
NIGDY niewidziany.

Pytanie: czy znajomość części etykiet tego samego grafu (transdukcja) poprawia
detekcję względem indukcji? Skrypt drukuje obok siebie wynik transduktywny i
indukcyjny (wczytany z wyniki_detekcja_honest.csv, jeśli istnieje).

Tylko grafy średnie i duże (≥1000 węzłów) — małe mają za mało chorych węzłów
na sensowny podział wewnątrzgrafowy.

Użycie:
    python src/detection/run_transductive.py
    python src/detection/run_transductive.py --exclude-isolated --repeats 5
"""

import argparse
import csv
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

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
MIN_NODES = 1000  # tylko średnie i duże


def _subset(ds: dict, nodes: list, labels: list) -> dict:
    """Pod-dataset współdzielący G_obs, z wybranym podzbiorem węzłów."""
    return {"G_obs": ds["G_obs"], "candidates": nodes, "labels": labels}


def run_graph(G, gid: str, seed: int, removal_ratio: float,
              test_size: float, exclude_isolated: bool) -> list[dict]:
    try:
        ds = build_node_dataset(G, removal_ratio, seed, "both",
                                exclude_isolated=exclude_isolated)
    except ValueError:
        return []

    cand = np.array(ds["candidates"], dtype=object)
    y = np.array(ds["labels"])
    n_pos = int(y.sum())
    # Potrzebujemy ≥2 pozytywów po obu stronach podziału stratyfikowanego.
    if n_pos < 4 or (len(y) - n_pos) < 4:
        return []

    idx = np.arange(len(cand))
    tr_idx, te_idx = train_test_split(
        idx, test_size=test_size, random_state=seed, stratify=y)

    ds_tr = _subset(ds, list(cand[tr_idx]), list(y[tr_idx]))
    ds_te = _subset(ds, list(cand[te_idx]), list(y[te_idx]))
    y_te = list(y[te_idx])
    n_pos_te = int(sum(y_te))

    base = {
        "graph": gid, "seed": seed,
        "n_test": len(te_idx), "n_infected_test": n_pos_te,
        "reliable": (n_pos_te >= MIN_POS) and (0 < n_pos_te < len(y_te)),
    }
    rows = []
    for name in HEURISTICS:
        m = node_detection_metrics(y_te, HeuristicNodeScorer(name).score(ds_te))
        rows.append({**base, "algorithm": name, **m})
    for name in ML_MODELS:
        try:
            clf = NodeMLClassifier(name, seed=seed).fit([ds_tr])
            m = node_detection_metrics(y_te, clf.score(ds_te))
            rows.append({**base, "algorithm": name, **m})
        except (ValueError, ImportError) as e:
            print(f"  [{gid}] {name} pominięto: {e}")
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
            "n_test": int(np.mean([r["n_test"] for r in runs])),
            "n_infected_test": int(np.mean([r["n_infected_test"] for r in runs])),
            "reliable": all(r["reliable"] for r in runs), "n_runs": len(runs),
        }
        for m in _METRICS:
            rec[m] = _trimmed_mean([r.get(m, float("nan")) for r in runs])
        agg.append(rec)
    return agg


def load_inductive(path: Path) -> dict:
    """Wczytuje AUC-ROC indukcyjny {(graf, alg): auc} do porównania."""
    out = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                out[(row["graph"], row["algorithm"])] = float(row["auc_roc"])
            except (ValueError, KeyError):
                pass
    return out


def print_report(agg, algorithms, inductive):
    print(f"\n{'='*100}")
    print("TRANSDUKTYWNY (podział węzłów w obrębie grafu) vs INDUKCYJNY (cross-graph)")
    print(f"{'='*100}")
    print(f"{'Graf':<8} {'Test':>6} {'Inf.':>5}  {'Algorytm':<22} "
          f"{'AUC transd.':>12} {'AUC indukc.':>12} {'Δ':>7}")
    print("-" * 100)

    def fmt(v):
        return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "  nan"

    graphs = sorted({r["graph"] for r in agg}, key=lambda g: int(g.replace("DLG", "")))
    for g in graphs:
        rows = [r for r in agg if r["graph"] == g]
        for i, r in enumerate(rows):
            ind = inductive.get((g, r["algorithm"]), float("nan"))
            delta = r["auc_roc"] - ind if not np.isnan(ind) else float("nan")
            head = (f"{g:<8} {r['n_test']:>6} {r['n_infected_test']:>5}"
                    if i == 0 else " " * 21)
            print(f"{head}  {r['algorithm']:<22} {fmt(r['auc_roc']):>12} "
                  f"{fmt(ind):>12} {fmt(delta):>7}")
        print()

    print(f"{'='*100}")
    print("PODSUMOWANIE — średni AUC-ROC per algorytm (grafy wiarygodne)")
    print(f"{'='*100}")
    print(f"  {'Algorytm':<22} {'transd.':>9} {'indukc.':>9} {'Δ (transd-ind)':>16}")
    print("  " + "-" * 58)
    for alg in algorithms:
        cells = [r for r in agg if r["algorithm"] == alg and r["reliable"]]
        tr = [r["auc_roc"] for r in cells if not np.isnan(r["auc_roc"])]
        ind = [inductive[(r["graph"], alg)] for r in cells
               if (r["graph"], alg) in inductive]
        if not tr:
            print(f"  {alg:<22} {'—':>9}")
            continue
        tr_m = np.mean(tr)
        ind_m = np.mean(ind) if ind else float("nan")
        d = tr_m - ind_m if not np.isnan(ind_m) else float("nan")
        ds = f"{d:+.3f}" if not np.isnan(d) else "  nan"
        print(f"  {alg:<22} {tr_m:>9.3f} "
              f"{(ind_m if not np.isnan(ind_m) else float('nan')):>9.3f} {ds:>16}")


_CSV_FIELDS = ["graph", "algorithm", "n_test", "n_infected_test", "reliable",
               "n_runs", "auc_roc", "auc_pr", "precision_at_k", "recall_at_k",
               "hits_at_k"]


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
    p = argparse.ArgumentParser(description="Transduktywny podział węzłów vs indukcyjny")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--removal-ratio", type=float, default=0.2)
    p.add_argument("--test-size", type=float, default=0.4)
    p.add_argument("--exclude-isolated", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_transduktywny.csv")
    p.add_argument("--inductive-csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_detekcja_honest.csv",
                   help="CSV z wynikami indukcyjnymi do kolumny porównawczej.")
    args = p.parse_args()

    seeds = [args.seed + i for i in range(max(1, args.repeats))]
    algorithms = HEURISTICS + ML_MODELS
    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in ALL_DLGS}
    selected = {g: G for g, G in graphs.items() if G.number_of_nodes() >= MIN_NODES}

    print(f"Grafy (średnie+duże, ≥{MIN_NODES} węzłów): {sorted(selected)}")
    print(f"Powtórzenia: {len(seeds)}, test_size={args.test_size}, "
          f"removal_ratio={args.removal_ratio}, exclude_isolated={args.exclude_isolated}\n")

    t0 = time.time()
    all_rows = []
    for seed in seeds:
        print(f"Seed {seed}...", flush=True)
        for gid, G in selected.items():
            all_rows.extend(run_graph(G, gid, seed, args.removal_ratio,
                                      args.test_size, args.exclude_isolated))

    if not all_rows:
        print("Brak wyników (za mało chorych węzłów na podział).")
        return
    agg = aggregate(all_rows)
    inductive = load_inductive(args.inductive_csv)
    print_report(agg, algorithms, inductive)
    save_csv(agg, args.csv)
    print(f"\nWyniki zapisane: {args.csv}")
    print(f"(porównanie indukcyjne z: {args.inductive_csv})")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
