"""
Generuje wykresy do prezentacji z wyników wyniki_random_split.csv.

Wyniki:
  results/figures/prezentacja_auc_barplot.png     — mean AUC-ROC per algorytm
  results/figures/prezentacja_auc_heatmap.png     — AUC-ROC algorytmy x grafy
  results/figures/prezentacja_feature_importance.png — feature importance RF-11

Użycie:
  python scripts/generate_presentation_charts.py
"""

import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_FIGURES_DIR  = _PROJECT_ROOT / "results" / "figures"
_CSV_PATH     = _PROJECT_ROOT / "results" / "wyniki_random_split.csv"

_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Kolejność algorytmów w wykresach (logiczna, nie alfabetyczna)
ALGO_ORDER = [
    "common_neighbors", "jaccard", "adamic_adar",
    "preferential_attachment", "rwpa",
    "l3", "katz", "ppr",
    "RandomForest", "RUSBoost", "LightGBM",
    "RF-18(ETL)", "RUSBoost-18(ETL)",
    "Node2Vec+MLP",
]

ALGO_LABELS = {
    "common_neighbors":        "CN",
    "jaccard":                 "Jaccard",
    "adamic_adar":             "Adamic-Adar",
    "preferential_attachment": "PA",
    "rwpa":                    "RWPA",
    "l3":                      "L3",
    "katz":                    "Katz",
    "ppr":                     "PPR",
    "RandomForest":            "RF-11",
    "RUSBoost":                "RUSBoost-11",
    "LightGBM":                "LightGBM",
    "RF-18(ETL)":              "RF-18(ETL)",
    "RUSBoost-18(ETL)":        "RUSBoost-18(ETL)",
    "Node2Vec+MLP":            "Node2Vec+MLP",
}

# Kolory grup
_COLORS = {
    "common_neighbors":        "#BDBDBD",
    "jaccard":                 "#BDBDBD",
    "adamic_adar":             "#BDBDBD",
    "preferential_attachment": "#1976D2",
    "rwpa":                    "#90CAF9",
    "l3":                      "#1976D2",
    "katz":                    "#1976D2",
    "ppr":                     "#1976D2",
    "RandomForest":            "#388E3C",
    "RUSBoost":                "#388E3C",
    "LightGBM":                "#388E3C",
    "RF-18(ETL)":              "#A5D6A7",
    "RUSBoost-18(ETL)":        "#A5D6A7",
    "Node2Vec+MLP":            "#E64A19",
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(_CSV_PATH)
    df["auc_roc"] = pd.to_numeric(df["auc_roc"], errors="coerce")
    df["f1"]      = pd.to_numeric(df["f1"],      errors="coerce")
    return df


# Wykres 1: mean AUC-ROC per algorytm (bar chart poziomy)

def plot_auc_barplot(df: pd.DataFrame) -> None:
    means = (
        df.groupby("algorithm")["auc_roc"]
        .mean()
        .reindex([a for a in ALGO_ORDER if a in df["algorithm"].unique()])
    )

    algos  = [ALGO_LABELS.get(a, a) for a in means.index]
    values = means.values
    colors = [_COLORS.get(a, "#999") for a in means.index]

    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.barh(algos, values, color=colors, edgecolor="white", height=0.65)

    # Linia bazowa 0.5 (random)
    ax.axvline(0.5, color="black", linestyle="--", linewidth=1.2, alpha=0.6)
    ax.text(0.501, -0.7, "AUC=0.5\n(losowe)", fontsize=7.5, color="black",
            alpha=0.7, va="top")

    for bar, val in zip(bars, values):
        if not np.isnan(val):
            ax.text(val + 0.004, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", ha="left", fontsize=8.5)

    ax.set_xlabel("Mean AUC-ROC (18 grafów DLG-DG-23)", fontsize=11)
    ax.set_xlim(0, 0.72)
    ax.set_title("Porównanie algorytmów — mean AUC-ROC\n"
                 "(losowy split 60/20/20, seed=42)", fontsize=12)
    ax.grid(axis="x", alpha=0.3)

    # Legenda pod wykresem (nie zasłania słupków)
    legend_patches = [
        mpatches.Patch(color="#BDBDBD", label="CN / Jaccard / AA — nieskuteczne"),
        mpatches.Patch(color="#1976D2", label="Heurystyki (PA, L3, Katz, PPR)"),
        mpatches.Patch(color="#90CAF9", label="RWPA (własna)"),
        mpatches.Patch(color="#388E3C", label="Klasyczne ML"),
        mpatches.Patch(color="#A5D6A7", label="ML + cechy ETL (-18)"),
        mpatches.Patch(color="#E64A19", label="Node2Vec + MLP"),
    ]
    ax.legend(handles=legend_patches, loc="upper center",
              bbox_to_anchor=(0.5, -0.13), ncol=3,
              fontsize=8.5, framealpha=0.9)

    plt.tight_layout(rect=[0, 0.1, 1, 1])
    out = _FIGURES_DIR / "prezentacja_auc_barplot.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Zapisano: {out}")


# Wykres 2: heatmap AUC-ROC algorytmy x grafy

def plot_auc_heatmap(df: pd.DataFrame) -> None:
    # Tylko sensowne algorytmy (pomijamy CN/Jaccard/AA — zawsze NaN)
    algos_show = [a for a in ALGO_ORDER
                  if a not in ("common_neighbors", "jaccard", "adamic_adar")
                  and a in df["algorithm"].unique()]

    graphs = sorted(df["graph"].unique(),
                    key=lambda x: int(x.replace("DLG", "")))

    pivot = df[df["algorithm"].isin(algos_show)].pivot_table(
        index="algorithm", columns="graph", values="auc_roc", aggfunc="mean"
    ).reindex(index=algos_show, columns=graphs)

    labels_y = [ALGO_LABELS.get(a, a) for a in algos_show]

    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto",
                   vmin=0.2, vmax=0.85)

    ax.set_xticks(range(len(graphs)))
    ax.set_yticks(range(len(algos_show)))
    ax.set_xticklabels(graphs, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels_y, fontsize=9)

    for i in range(len(algos_show)):
        for j in range(len(graphs)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                color = "white" if val < 0.45 or val > 0.72 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, color=color)
            else:
                ax.text(j, i, "—", ha="center", va="center",
                        fontsize=8, color="gray")

    # Separator grup (po PPR i po RUSBoost-18)
    sep_after = {
        "ppr":              (3.5, "Heurystyki / ML"),
        "RUSBoost-18(ETL)": (10.5, "ML / Node2Vec"),
    }
    for algo, (y_pos, _) in sep_after.items():
        if algo in algos_show:
            idx = algos_show.index(algo)
            ax.axhline(idx + 0.5, color="white", linewidth=2)

    plt.colorbar(im, ax=ax, label="AUC-ROC", shrink=0.8)
    ax.set_title("AUC-ROC: algorytmy × grafy DLG-DG-23\n"
                 "(zielony = lepszy, czerwony = gorszy, — = brak ścieżek)",
                 fontsize=11)
    plt.tight_layout()
    out = _FIGURES_DIR / "prezentacja_auc_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Zapisano: {out}")


# Wykres 3: feature importance RF-11 (dane z implementation_summary)

def plot_feature_importance() -> None:
    # Dane z wytrenowanego RF na DLG-DG-23 (agregacja)
    features = [
        "shortest_path",
        "has_path",
        "tgt_in_deg",
        "tgt_out_deg",
        "src_out_deg",
        "src_in_deg",
        "src_type / tgt_type",
        "CN / Jaccard / AA",
    ]
    importances = [0.526, 0.261, 0.081, 0.070, 0.046, 0.010, 0.007, 0.000]

    colors = ["#E64A19" if imp > 0.1 else
              "#FF8A65" if imp > 0.04 else
              "#BDBDBD"
              for imp in importances]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(features[::-1], importances[::-1],
                   color=colors[::-1], edgecolor="white", height=0.6)

    for bar, val in zip(bars, importances[::-1]):
        ax.text(val + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.1%}", va="center", fontsize=9)

    ax.set_xlabel("Feature importance (Random Forest)", fontsize=11)
    ax.set_xlim(0, 0.65)
    ax.set_title("Ważność cech — Random Forest (RF-11)\n"
                 "Model kieruje się głównie odległością topologiczną",
                 fontsize=11)
    ax.axvline(0.05, color="gray", linestyle=":", linewidth=1, alpha=0.6)
    ax.grid(axis="x", alpha=0.3)

    ax.annotate("cechy ETL-aware\n(flow_depth, role)\ndodano tutaj",
                xy=(0.046, 3.5), xytext=(0.25, 3.5),
                arrowprops=dict(arrowstyle="->", color="navy"),
                fontsize=8.5, color="navy", va="center")

    plt.tight_layout()
    out = _FIGURES_DIR / "prezentacja_feature_importance.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Zapisano: {out}")


def main():
    print("Wczytuję wyniki...")
    df = load_data()
    print(f"  Wczytano {len(df)} wierszy, {df['graph'].nunique()} grafów, "
          f"{df['algorithm'].nunique()} algorytmów\n")

    print("Generuję wykresy do prezentacji...")
    plot_auc_barplot(df)
    plot_auc_heatmap(df)
    plot_feature_importance()

    print(f"\nWszystkie wykresy w: {_FIGURES_DIR}")
    print("Gotowe.")


if __name__ == "__main__":
    main()
