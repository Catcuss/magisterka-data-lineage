"""
Badanie ablacyjne detektora LineageHealthDetector (sekcja 4.8 pracy).

Izoluje wkład dwóch autorskich składników detektora przez ich wyłączanie:
  - relacyjnego score'u kompletności peer-consistency (use_completeness),
  - kalibracji izotonicznej prawdopodobieństw (calibrate).

Cztery warianty w pełnym planie 2x2. Konfiguracja identyczna z biegiem
kanonicznym rozdziału 4 (18 grafów, removal_ratio=0.10, 3 seedy, wariant
uczciwy, protokół indukcyjny leave-one-graph-out), żeby wiersz „pełny"
odtwarzał liczby z tabeli głównej.

Użycie:
    python src/detection/run_ablation.py                 # bieg kanoniczny
    python src/detection/run_ablation.py --repeats 5
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph
from detection.lineage_detector import LineageHealthDetector
from detection.run_detection_experiments import (
    ALL_DLGS, MIN_POS, _METRICS, _avg_metrics_over, aggregate,
    build_datasets, save_csv,
)

# nazwa wariantu -> (use_completeness, calibrate)
VARIANTS = {
    "pelny":              (True,  True),
    "bez_kalibracji":     (True,  False),
    "bez_kompletnosci":   (False, True),
    "bez_obu":            (False, False),
}

VARIANT_LABELS = {
    "pelny": "Pełny detektor",
    "bez_kalibracji": "bez kalibracji izotonicznej",
    "bez_kompletnosci": "bez score'u kompletności",
    "bez_obu": "bez obu składników",
}


def run_seed_ablation(datasets: dict, seed: int) -> list[dict]:
    """Leave-one-graph-out dla jednego seeda, dla każdego wariantu detektora."""
    rows = []
    gids = list(datasets.keys())

    for test_g in gids:
        ds_multi = datasets[test_g]
        train_pool = [datasets[g] for g in gids if g != test_g]
        n_pos = ds_multi["n_infected"]
        base = {
            "graph": test_g, "seed": seed,
            "n_candidates": len(ds_multi["candidates"]),
            "n_infected": n_pos,
            "reliable": (n_pos >= MIN_POS) and (n_pos < len(ds_multi["candidates"])),
        }

        for variant, (use_completeness, calibrate) in VARIANTS.items():
            try:
                clf = LineageHealthDetector(
                    seed=seed, calibrate=calibrate,
                    use_completeness=use_completeness,
                ).fit(train_pool)
            except (ValueError, ImportError) as e:
                print(f"  [{test_g}] {variant} pominięto: {e}")
                continue
            m = _avg_metrics_over([ds_multi], clf.score)
            if m:
                rows.append({**base, "algorithm": variant, **m})
    return rows


def print_report(agg: list[dict]):
    print(f"\n{'=' * 84}")
    print("BADANIE ABLACYJNE — średnie po grafach wiarygodnych (wariant uczciwy)")
    print(f"{'=' * 84}")
    print(f"  {'Wariant':<32}{'AUC-ROC':>9}{'AUC-PR':>9}{'P@k':>8}"
          f"{'Brier':>9}{'n graf':>8}")
    print("  " + "-" * 76)

    full = None
    for variant in VARIANTS:
        cells = [r for r in agg if r["algorithm"] == variant and r["reliable"]]
        if not cells:
            print(f"  {VARIANT_LABELS[variant]:<32}{'—':>9}")
            continue

        def mean_of(m):
            xs = [r[m] for r in cells if not np.isnan(r[m])]
            return float(np.mean(xs)) if xs else float("nan")

        vals = {m: mean_of(m) for m in _METRICS}
        if variant == "pelny":
            full = vals
        print(f"  {VARIANT_LABELS[variant]:<32}{vals['auc_roc']:>9.3f}"
              f"{vals['auc_pr']:>9.3f}{vals['precision_at_k']:>8.3f}"
              f"{vals['brier']:>9.3f}{len(cells):>8}")

    if full is None:
        return
    print("\n  Ubytek względem pełnego detektora (ujemny = wariant gorszy):")
    print("  " + "-" * 76)
    for variant in VARIANTS:
        if variant == "pelny":
            continue
        cells = [r for r in agg if r["algorithm"] == variant and r["reliable"]]
        if not cells:
            continue

        def mean_of(m):
            xs = [r[m] for r in cells if not np.isnan(r[m])]
            return float(np.mean(xs)) if xs else float("nan")

        # Brier: niżej lepiej, więc ubytek liczymy z odwrotnym znakiem.
        print(f"  {VARIANT_LABELS[variant]:<32}"
              f"{mean_of('auc_roc') - full['auc_roc']:>+9.3f}"
              f"{mean_of('auc_pr') - full['auc_pr']:>+9.3f}"
              f"{mean_of('precision_at_k') - full['precision_at_k']:>+8.3f}"
              f"{full['brier'] - mean_of('brier'):>+9.3f}")
    print("\n  (dla Brier score znak odwrócono, aby '-' zawsze oznaczał pogorszenie)")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    p = argparse.ArgumentParser(description="Ablacja LineageHealthDetector")
    p.add_argument("--dlg", nargs="+", type=int, default=ALL_DLGS)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--removal-ratio", type=float, default=0.10)
    p.add_argument("--side", choices=["both", "pred", "succ"], default="both")
    p.add_argument("--no-exclude-isolated", action="store_true",
                   help="Wariant napompowany (domyślnie liczymy uczciwy).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_ablacja.csv")
    args = p.parse_args()

    exclude_isolated = not args.no_exclude_isolated
    seeds = [args.seed + i for i in range(max(1, args.repeats))]

    print(f"Grafy:        {[f'DLG{i}' for i in args.dlg]}")
    print(f"Powtórzenia:  {len(seeds)} (seedy {seeds[0]}-{seeds[-1]})")
    print(f"removal_ratio={args.removal_ratio}, side={args.side}, "
          f"exclude_isolated={exclude_isolated}, MIN_POS={MIN_POS}")
    print(f"Warianty:     {', '.join(VARIANTS)}\n")

    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in args.dlg}

    t0 = time.time()
    all_rows = []
    for seed in seeds:
        print(f"Seed {seed}...", flush=True)
        datasets = build_datasets(graphs, args.removal_ratio, seed, args.side,
                                  exclude_isolated=exclude_isolated)
        if len(datasets) < 2:
            print("  Za mało grafów z jobami łączącymi — pomijam seed.")
            continue
        all_rows.extend(run_seed_ablation(datasets, seed))

    if not all_rows:
        print("Brak wyników.")
        return

    agg = aggregate(all_rows)
    print_report(agg)
    save_csv(agg, args.csv)
    print(f"\nWyniki zapisane: {args.csv}")
    print(f"Czas: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
