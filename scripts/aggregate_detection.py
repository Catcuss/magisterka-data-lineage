"""
Agregacja wyników detekcji chorych węzłów do tabeli rozdziału 4.

Wejście : results/wyniki_detekcja_canon.csv (kanoniczny bieg — patrz _det_canon.txt:
          removal_ratio=0.10, side=both, exclude_isolated=True, seedy 42-44,
          protokół indukcyjny leave-one-out, MIN_POS=5).
Wyjście : 1) results/agregat_detekcja.csv  — średnia±std per algorytm (tylko
             grafy wiarygodne, reliable=True),
          2) results/tabela_detekcja.tex    — gotowa tabela LaTeX (booktabs),
             do wstawienia przez \\input w rozdziale 4; pogrubia najlepszą
             wartość w każdej kolumnie.

Uruchomienie:
    python scripts/aggregate_detection.py
    python scripts/aggregate_detection.py --csv results/inny_bieg.csv --reliable-only
"""

import argparse
import csv
import statistics
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Metryki i czy wyższa wartość jest lepsza (do pogrubiania w LaTeX).
METRICS = ["auc_roc", "auc_pr", "precision_at_k", "recall_at_k", "hits_at_k", "brier"]
HIGHER_BETTER = {
    "auc_roc": True, "auc_pr": True, "precision_at_k": True,
    "recall_at_k": True, "hits_at_k": True, "brier": False,  # Brier: niżej = lepiej
}

# Kolejność wierszy: heurystyki → klasyczne ML → detektor autorski.
ALGO_ORDER = [
    "degree_anomaly", "boundary", "low_job_connectivity", "rule_root", "completeness",
    "RandomForest", "RUSBoost", "LightGBM",
    "LineageDetector",
]
# Ładne etykiety do tabeli.
ALGO_LABELS = {
    "degree_anomaly":       "Anomalia stopnia",
    "boundary":             "Brzeg (root/leaf)",
    "low_job_connectivity": "Niska łączność jobów",
    "rule_root":            "Reguła korzenia",
    "completeness":         "Kompletność (peer-consistency)*",
    "RandomForest":         "Random Forest",
    "RUSBoost":             "RUSBoost",
    "LightGBM":             "LightGBM",
    "LineageDetector":      "LineageDetector*",
}
METRIC_LABELS = {
    "auc_roc": "AUC-ROC", "auc_pr": "AUC-PR",
    "precision_at_k": "P@k", "recall_at_k": "R@k",
    "hits_at_k": "Hits@k", "brier": "Brier",
}


def read_rows(path: Path, reliable_only: bool) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if reliable_only:
        rows = [r for r in rows if str(r.get("reliable", "")).strip().lower() == "true"]
    return rows


def aggregate(rows: list[dict]) -> dict:
    """algorithm -> {metric -> (mean, std, n)}. Puste komórki pomijane."""
    by_algo: dict = {}
    for r in rows:
        by_algo.setdefault(r["algorithm"], []).append(r)

    out: dict = {}
    for algo, recs in by_algo.items():
        stats = {}
        for m in METRICS:
            vals = []
            for r in recs:
                v = r.get(m, "")
                if v is None or str(v).strip() == "":
                    continue
                try:
                    vals.append(float(v))
                except ValueError:
                    continue
            if vals:
                mean = statistics.fmean(vals)
                std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
                stats[m] = (mean, std, len(vals))
            else:
                stats[m] = (float("nan"), float("nan"), 0)
        out[algo] = stats
    return out


def _ordered(agg: dict) -> list[str]:
    known = [a for a in ALGO_ORDER if a in agg]
    extra = [a for a in agg if a not in ALGO_ORDER]
    return known + sorted(extra)


def best_per_metric(agg: dict) -> dict:
    """metric -> algorithm z najlepszą średnią (do pogrubienia)."""
    best = {}
    for m in METRICS:
        candidates = [(a, s[m][0]) for a, s in agg.items()
                      if s[m][2] > 0 and s[m][0] == s[m][0]]  # nie-NaN
        if not candidates:
            continue
        best[m] = (max if HIGHER_BETTER[m] else min)(candidates, key=lambda x: x[1])[0]
    return best


def save_csv(agg: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["algorithm"] + [f"{m}_mean" for m in METRICS] + \
             [f"{m}_std" for m in METRICS] + ["n_graphs"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for algo in _ordered(agg):
            s = agg[algo]
            row = {"algorithm": algo, "n_graphs": max(s[m][2] for m in METRICS)}
            for m in METRICS:
                row[f"{m}_mean"] = round(s[m][0], 4) if s[m][2] else ""
                row[f"{m}_std"] = round(s[m][1], 4) if s[m][2] else ""
            w.writerow(row)


def save_latex(agg: dict, path: Path, caption: str, label: str):
    best = best_per_metric(agg)
    cols = "l" + "c" * len(METRICS)
    lines = [
        "% Wygenerowane przez scripts/aggregate_detection.py — nie edytuj ręcznie.",
        "% Wstaw w rozdziale 4 przez: \\input{tabela_detekcja}",
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{cols}}}",
        "\\toprule",
        "\\textbf{Metoda} & " + " & ".join(f"\\textbf{{{METRIC_LABELS[m]}}}"
                                            for m in METRICS) + " \\\\",
        "\\midrule",
    ]
    prev_group = None
    for algo in _ordered(agg):
        # Separator między grupami (heurystyki / ML / detektor).
        group = ("h" if algo in ("degree_anomaly", "boundary", "low_job_connectivity",
                                 "rule_root", "completeness")
                 else "ml" if algo in ("RandomForest", "RUSBoost", "LightGBM")
                 else "det")
        if prev_group is not None and group != prev_group:
            lines.append("\\midrule")
        prev_group = group

        s = agg[algo]
        cells = [ALGO_LABELS.get(algo, algo)]
        for m in METRICS:
            mean, std, n = s[m]
            if n == 0 or mean != mean:
                cells.append("--")
                continue
            txt = f"{mean:.3f}"
            if best.get(m) == algo:
                txt = f"\\textbf{{{txt}}}"
            cells.append(txt)
        lines.append(" & ".join(cells) + " \\\\")

    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_console(agg: dict):
    hdr = f"{'Metoda':<28}" + "".join(f"{METRIC_LABELS[m]:>9}" for m in METRICS) + "   n"
    print(hdr)
    print("-" * len(hdr))
    for algo in _ordered(agg):
        s = agg[algo]
        n = max(s[m][2] for m in METRICS)
        cells = f"{ALGO_LABELS.get(algo, algo):<28}"
        for m in METRICS:
            mean = s[m][0]
            cells += f"{mean:>9.3f}" if s[m][2] else f"{'--':>9}"
        print(cells + f"   {n}")


def main():
    p = argparse.ArgumentParser(description="Agregacja wyników detekcji do tabeli rozdz. 4")
    p.add_argument("--csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "wyniki_detekcja_canon.csv")
    p.add_argument("--out-csv", type=Path,
                   default=_PROJECT_ROOT / "results" / "agregat_detekcja.csv")
    p.add_argument("--out-tex", type=Path,
                   default=_PROJECT_ROOT / "results" / "tabela_detekcja.tex")
    p.add_argument("--reliable-only", action="store_true", default=True,
                   help="Uśredniaj tylko po grafach wiarygodnych (reliable=True). Domyślnie tak.")
    p.add_argument("--all-graphs", dest="reliable_only", action="store_false",
                   help="Uśredniaj po wszystkich grafach (także niewiarygodnych).")
    p.add_argument("--caption", default="Średnie metryki detekcji chorych węzłów per "
                   "metoda (protokół indukcyjny, wariant uczciwy z wykluczeniem izolowanych; "
                   "gwiazdka -- wkład własny; najlepsza wartość w kolumnie pogrubiona).")
    p.add_argument("--label", default="tab:wyniki-detekcja")
    args = p.parse_args()

    if not args.csv.exists():
        raise SystemExit(f"Brak pliku: {args.csv}. Najpierw uruchom bieg kanoniczny.")

    rows = read_rows(args.csv, args.reliable_only)
    agg = aggregate(rows)
    n_graphs = max((max(s[m][2] for m in METRICS) for s in agg.values()), default=0)

    print(f"Źródło: {args.csv.name}   grafy wiarygodne: {'tak' if args.reliable_only else 'nie'}"
          f"   (n={n_graphs} na algorytm)\n")
    print_console(agg)

    save_csv(agg, args.out_csv)
    save_latex(agg, args.out_tex, args.caption, args.label)
    print(f"\nZapisano:\n  {args.out_csv}\n  {args.out_tex}")


if __name__ == "__main__":
    main()
