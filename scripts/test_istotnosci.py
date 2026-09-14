"""
Test istotności statystycznej różnic między metodami detekcji (sekcja 4.4 pracy).

Protokół zgodny z zaleceniem Demšara (2006) dla porównania klasyfikatorów
na wielu zbiorach: test kolejności par Wilcoxona (signed-rank), sparowany po
GRAFACH testowych, z poprawką Holma na wielokrotne porównania w obrębie metryki.

Jednostką obserwacji jest graf wiarygodny (reliable=True) z biegu kanonicznego,
a nie pojedynczy węzeł — pary są zależne (te same grafy, ten sam podział).

Użycie:
    python scripts/test_istotnosci.py
    python scripts/test_istotnosci.py --csv results/wyniki_detekcja_canon.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

REFERENCE = "LineageDetector"

# metryka -> czy wyższa wartość jest lepsza
METRICS = {
    "auc_roc": True,
    "auc_pr": True,
    "precision_at_k": True,
    "brier": False,
}

METRIC_LABELS = {
    "auc_roc": "AUC-ROC",
    "auc_pr": "AUC-PR",
    "precision_at_k": "P@k",
    "brier": "Brier",
}

# Rodziny hipotez. Poprawkę Holma stosujemy w obrębie rodziny, a nie na wszystkich
# ośmiu porównaniach naraz, bo przy 8 parach dokładny test Wilcoxona daje minimalne
# osiągalne p = 2/2^8 = 0,0078, więc korekta na 8 porównaniach podnosi próg do
# 8 x 0,0078 = 0,0625 i żadna różnica nie mogłaby wyjść istotna, niezależnie od
# danych. Podział na dwie rodziny odpowiada
# dwóm odrębnym pytaniom badawczym pracy: (1) czy uczenie bije heurystyki,
# (2) czy autorski detektor bije klasyczne klasyfikatory.
FAMILIES = {
    "heurystyki": ["degree_anomaly", "boundary", "low_job_connectivity",
                   "rule_root", "completeness"],
    "metody uczone": ["RandomForest", "RUSBoost", "LightGBM"],
}
ALGO_ORDER = [a for algos in FAMILIES.values() for a in algos]

ALGO_LABELS = {
    "degree_anomaly": "Anomalia stopnia",
    "boundary": "Brzeg (root/leaf)",
    "low_job_connectivity": "Niska łączność jobów",
    "rule_root": "Reguła korzenia",
    "completeness": "Score kompletności",
    "RandomForest": "Random Forest",
    "RUSBoost": "RUSBoost",
    "LightGBM": "LightGBM",
    # warianty ablacyjne (results/wyniki_ablacja.csv)
    "bez_kalibracji": "bez kalibracji",
    "bez_kompletnosci": "bez score'u kompletności",
    "bez_obu": "bez obu składników",
}

# Tryb ablacyjny: odniesieniem jest pełny detektor, jedna rodzina hipotez.
ABLATION = {
    "reference": "pelny",
    "families": {"warianty ablacyjne":
                 ["bez_kalibracji", "bez_kompletnosci", "bez_obu"]},
}


def holm(pvals: list[float]) -> list[float]:
    """Poprawka Holma–Bonferroniego. Zwraca p skorygowane w kolejności wejściowej."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)          # wymuszenie monotoniczności
        adjusted[idx] = min(1.0, running)
    return adjusted


def rank_biserial(diffs: np.ndarray) -> float:
    """
    Wielkość efektu dla testu Wilcoxona: korelacja rangowo-dwuseryjna
    r = (W+ - W-) / (W+ + W-), w zakresie [-1, 1]. Pary zerowe pomijane.
    """
    d = diffs[diffs != 0]
    if d.size == 0:
        return 0.0
    ranks = pd.Series(np.abs(d)).rank().to_numpy()
    w_plus = ranks[d > 0].sum()
    w_minus = ranks[d < 0].sum()
    total = w_plus + w_minus
    return float((w_plus - w_minus) / total) if total else 0.0


def compare(df: pd.DataFrame, metric: str, higher_better: bool) -> pd.DataFrame:
    """Porównuje REFERENCE z każdą inną metodą na tej samej metryce."""
    wide = df.pivot(index="graph", columns="algorithm", values=metric)
    if REFERENCE not in wide.columns:
        raise SystemExit(f"Brak metody odniesienia '{REFERENCE}' w danych.")

    rows = []
    algos = [a for a in ALGO_ORDER if a in wide.columns]
    for algo in algos:
        pair = wide[[REFERENCE, algo]].dropna()
        ref = pair[REFERENCE].to_numpy(dtype=float)
        other = pair[algo].to_numpy(dtype=float)
        # Różnica dodatnia = LineageDetector lepszy (Brier odwracamy).
        diff = (ref - other) if higher_better else (other - ref)

        if np.allclose(diff, 0):
            stat, p = np.nan, 1.0
        else:
            stat, p = wilcoxon(diff, alternative="two-sided",
                               zero_method="wilcox", method="exact")
        rows.append({
            "metryka": metric,
            "rodzina": next(f for f, a in FAMILIES.items() if algo in a),
            "porownanie": algo,
            "n_par": len(pair),
            "mediana_ref": float(np.median(ref)),
            "mediana_alt": float(np.median(other)),
            "mediana_roznicy": float(np.median(diff)),
            "n_wygranych_ref": int((diff > 0).sum()),
            "W": float(stat) if stat == stat else np.nan,
            "p": float(p),
            "r_rangowo_dwuseryjne": rank_biserial(diff),
        })

    out = pd.DataFrame(rows)
    out["p_holm"] = np.nan
    for family in FAMILIES:                      # korekta w obrębie rodziny
        mask = out["rodzina"] == family
        out.loc[mask, "p_holm"] = holm(out.loc[mask, "p"].tolist())
    out["istotne_005"] = out["p_holm"] < 0.05
    return out


def fmt_p(p: float) -> str:
    if p < 0.001:
        return "<0,001"
    return f"{p:.3f}".replace(".", ",")


def _num(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}".replace(".", "{,}")


def to_latex(results: pd.DataFrame, n_graphs: int) -> str:
    """
    Tabela LaTeX do sekcji o istotności: wiersze = porównania (grupowane
    w rodziny hipotez), kolumny = metryki, w każdej mediana różnicy i p_Holm.
    """
    metrics = list(METRICS)
    header_groups = " & ".join(
        rf"\multicolumn{{2}}{{c}}{{\textbf{{{METRIC_LABELS[m]}}}}}" for m in metrics)
    cmidrules = " ".join(
        rf"\cmidrule(lr){{{2 + 2 * i}-{3 + 2 * i}}}" for i in range(len(metrics)))

    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Istotność statystyczna różnic między LineageDetectorem "
        r"a~pozostałymi metodami. Test kolejności par Wilcoxona (dokładny, "
        f"dwustronny), sparowany po~{n_graphs}~grafach wiarygodnych; poprawka "
        r"Holma w~obrębie rodziny hipotez i~metryki. $\Delta$~—~mediana różnicy "
        r"na~korzyść LineageDetectora.}",
        r"\label{tab:istotnosc}",
        r"\small",
        r"\begin{tabular}{l" + "cc" * len(metrics) + "}",
        r"\toprule",
        r"\textbf{Porównanie z} & " + header_groups + r" \\",
        cmidrules,
        " & " + " & ".join(r"$\Delta$ & $p$" for _ in metrics) + r" \\",
        r"\midrule",
    ]

    for family, algos in FAMILIES.items():
        lines.append(rf"\multicolumn{{{1 + 2 * len(metrics)}}}{{l}}"
                     rf"{{\emph{{{family.capitalize()}}}}} \\")
        for algo in algos:
            cells = []
            for m in metrics:
                row = results[(results["metryka"] == m)
                              & (results["porownanie"] == algo)]
                if row.empty:
                    cells += ["—", "—"]
                    continue
                r = row.iloc[0]
                star = "^{*}" if r["istotne_005"] else ""
                cells.append(f"${_num(r['mediana_roznicy'])}$")
                cells.append(f"${fmt_p(r['p_holm']).replace(',', '{,}')}{star}$")
            lines.append(f"{ALGO_LABELS.get(algo, algo)} & "
                         + " & ".join(cells) + r" \\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"

    lines += [
        r"\end{tabular}",
        r"",
        r"\vspace{0.5em}",
        r"\footnotesize $^{*}$ różnica istotna na~poziomie $\alpha = 0{,}05$ "
        r"po~poprawce Holma. Różnica dodatnia oznacza przewagę "
        r"LineageDetectora (dla~Brier score — wartość niższą). Przy~"
        + f"{n_graphs}~parach najniższe osiągalne $p$ wynosi "
        + f"{2 / 2 ** n_graphs:.4f}".replace(".", "{,}")
        + r", co~ogranicza moc testu.",
        r"\end{table}",
    ]
    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Test istotności różnic między metodami")
    ap.add_argument("--csv", type=Path,
                    default=_PROJECT_ROOT / "results" / "wyniki_detekcja_canon.csv")
    ap.add_argument("--out-csv", type=Path,
                    default=_PROJECT_ROOT / "results" / "istotnosc_wilcoxon.csv")
    ap.add_argument("--out-tex", type=Path,
                    default=_PROJECT_ROOT / "results" / "tabela_istotnosc.tex")
    ap.add_argument("--ablacja", action="store_true",
                    help="Tryb ablacyjny: porównuje pełny detektor z wariantami "
                         "z results/wyniki_ablacja.csv.")
    args = ap.parse_args()

    if args.ablacja:
        global REFERENCE, FAMILIES, ALGO_ORDER
        REFERENCE = ABLATION["reference"]
        FAMILIES = ABLATION["families"]
        ALGO_ORDER = [a for algos in FAMILIES.values() for a in algos]
        if args.csv == _PROJECT_ROOT / "results" / "wyniki_detekcja_canon.csv":
            args.csv = _PROJECT_ROOT / "results" / "wyniki_ablacja.csv"
            args.out_csv = _PROJECT_ROOT / "results" / "istotnosc_ablacja.csv"
            args.out_tex = _PROJECT_ROOT / "results" / "tabela_ablacja_istotnosc.tex"

    df = pd.read_csv(args.csv)
    df = df[df["reliable"] == True]  # noqa: E712 — kolumna bywa wczytana jako obiekt
    graphs = sorted(df["graph"].unique())
    n_graphs = len(graphs)

    print(f"Źródło:  {args.csv.name}")
    print(f"Grafy wiarygodne ({n_graphs}): {', '.join(graphs)}")
    print(f"Metoda odniesienia: {REFERENCE}")
    print(f"Test: Wilcoxon signed-rank (dokładny, dwustronny), poprawka Holma\n")

    p_min = 2 / 2 ** n_graphs
    print(f"Moc testu: przy {n_graphs} parach minimalne osiągalne p (dokładne, "
          f"dwustronne) = {p_min:.4f}.")
    for family, algos in FAMILIES.items():
        print(f"  rodzina '{family}' ({len(algos)} porównania): "
              f"najniższe możliwe p_Holm = {len(algos) * p_min:.4f}"
              f"{'  — próg 0,05 OSIĄGALNY' if len(algos) * p_min < 0.05 else '  — próg 0,05 NIEOSIĄGALNY'}")
    print()

    all_results = []
    for metric, higher_better in METRICS.items():
        res = compare(df, metric, higher_better)
        all_results.append(res)

        kierunek = "wyżej = lepiej" if higher_better else "niżej = lepiej"
        print(f"{'=' * 78}")
        print(f"{METRIC_LABELS[metric]}  ({kierunek})")
        print(f"{'=' * 78}")
        for family in FAMILIES:
            block = res[res["rodzina"] == family]
            print(f"  -- rodzina: {family} --")
            print(f"  {'Porównanie z':<24}{'med. Δ':>9}{'wygrane':>9}"
                  f"{'p':>9}{'p Holm':>9}{'r':>7}  ")
            print("  " + "-" * 68)
            for _, r in block.iterrows():
                mark = " *" if r["istotne_005"] else "  "
                print(f"  {ALGO_LABELS.get(r['porownanie'], r['porownanie']):<24}"
                      f"{r['mediana_roznicy']:>+9.3f}"
                      f"{r['n_wygranych_ref']:>6}/{r['n_par']:<3}"
                      f"{r['p']:>9.4f}{r['p_holm']:>9.4f}"
                      f"{r['r_rangowo_dwuseryjne']:>+7.2f}{mark}")
        print()

    results = pd.concat(all_results, ignore_index=True)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.out_csv, index=False, encoding="utf-8")
    args.out_tex.write_text(to_latex(results, n_graphs), encoding="utf-8")

    print(f"{'=' * 78}")
    print("WNIOSEK")
    print(f"{'=' * 78}")
    for family in FAMILIES:
        print(f"\n  Rodzina: {family}")
        for metric in METRICS:
            block = results[(results["metryka"] == metric)
                            & (results["rodzina"] == family)]
            sig = [ALGO_LABELS.get(a, a)
                   for a in block[block["istotne_005"]]["porownanie"]]
            label = METRIC_LABELS[metric]
            if sig:
                print(f"    {label:<10} istotna przewaga nad: {', '.join(sig)}")
            else:
                print(f"    {label:<10} brak istotnej przewagi "
                      f"(najniższe p_Holm = {block['p_holm'].min():.3f})")

    print(f"\nZapisano: {args.out_csv}")
    print(f"Zapisano: {args.out_tex}")


if __name__ == "__main__":
    main()
