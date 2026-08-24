"""
Generator Dodatku B: pełne wyniki biegu kanonicznego dla wszystkich 18 grafów.

Główna tabela rozdziału 4 podaje średnie po ośmiu grafach wiarygodnych.
Tutaj raportowane są wszystkie grafy i wszystkie metryki, także te odrzucone
z agregacji progiem MIN_POS — dzięki temu czytelnik może samodzielnie ocenić,
co próg odsiewa.

Użycie:
    python scripts/dodatek_wyniki.py
"""

import sys
from pathlib import Path

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

ALGOS = [
    "degree_anomaly", "boundary", "low_job_connectivity", "rule_root",
    "completeness", "RandomForest", "RUSBoost", "LightGBM", "LineageDetector",
]

SHORT = {
    "degree_anomaly": "Stopień",
    "boundary": "Brzeg",
    "low_job_connectivity": "Łączn.",
    "rule_root": "Korzeń",
    "completeness": "Kompl.",
    "RandomForest": "RF",
    "RUSBoost": "RUSB",
    "LightGBM": "LGBM",
    "LineageDetector": "LD*",
}

METRICS = {
    "auc_roc": ("AUC-ROC", True),
    "auc_pr": ("AUC-PR", True),
    "precision_at_k": ("Precision@k", True),
    "brier": ("Brier score", False),
}


def pl(v) -> str:
    if pd.isna(v):
        return "---"
    return f"{v:.3f}".replace(".", "{,}")


def table_for(df: pd.DataFrame, metric: str, label: str, higher: bool) -> str:
    wide = df.pivot(index="graph", columns="algorithm", values=metric)
    info = df.groupby("graph")[["n_candidates", "n_infected", "reliable"]].first()
    order = sorted(wide.index, key=lambda g: int(g.replace("DLG", "")))

    kierunek = "wyżej — lepiej" if higher else "niżej — lepiej"
    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        rf"\caption{{{label} dla~wszystkich 18~grafów zbioru DLG-DG-23 "
        rf"({kierunek}). Gwiazdka przy~identyfikatorze grafu — graf odrzucony "
        rf"z~agregacji progiem $\mathrm{{MIN\_POS}} = 5$.}}",
        rf"\label{{tab:dodb-{metric.replace('_', '-')}}}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"\begin{tabular}{lrr" + "c" * len(ALGOS) + "}",
        r"\toprule",
        r"\textbf{Graf} & \textbf{Kand.} & \textbf{Zainf.} & "
        + " & ".join(rf"\textbf{{{SHORT[a]}}}" for a in ALGOS) + r" \\",
        r"\midrule",
    ]
    for g in order:
        mark = "" if info.loc[g, "reliable"] else r"$^{*}$"
        cells = [pl(wide.loc[g, a]) if a in wide.columns else "---" for a in ALGOS]
        lines.append(
            f"{g}{mark} & {int(info.loc[g, 'n_candidates'])} & "
            f"{int(info.loc[g, 'n_infected'])} & " + " & ".join(cells) + r" \\"
        )

    rel = df[df["reliable"] == True]                                # noqa: E712
    means = rel.groupby("algorithm")[metric].mean()
    lines += [
        r"\midrule",
        r"\emph{średnia} & & & "
        + " & ".join(pl(means.get(a)) for a in ALGOS) + r" \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"",
        r"\vspace{0.4em}",
        r"\footnotesize Skróty metod: Stopień — anomalia stopnia, Brzeg — "
        r"root/leaf, Łączn.\ — niska łączność jobów, Korzeń — reguła korzenia, "
        r"Kompl.\ — score kompletności, RF — Random Forest, RUSB — RUSBoost, "
        r"LGBM — LightGBM, LD\textsuperscript{*} — LineageDetector (wkład "
        r"własny). Średnia liczona wyłącznie po~grafach wiarygodnych.",
        r"\end{table}",
    ]
    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    src = _PROJECT_ROOT / "results" / "wyniki_detekcja_canon.csv"
    df = pd.read_csv(src)
    n_rel = df[df["reliable"] == True]["graph"].nunique()           # noqa: E712
    print(f"Źródło: {src.name} — {df['graph'].nunique()} grafów, "
          f"{n_rel} wiarygodnych")

    blocks = [table_for(df, m, label, higher)
              for m, (label, higher) in METRICS.items()]
    out = _PROJECT_ROOT / "results" / "dodatek_b_wyniki.tex"
    out.write_text("\n\n\\clearpage\n\n".join(blocks), encoding="utf-8")
    print(f"Zapisano {len(blocks)} tabel: {out}")


if __name__ == "__main__":
    main()
