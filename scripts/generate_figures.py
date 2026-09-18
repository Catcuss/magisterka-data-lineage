"""
Generacja rysunków do rozdz. 3 i 4 pracy magisterskiej (detekcja chorych węzłów).

Wyjście: docs/thesis_draft_new/thesis/figures/*.pdf (+ .png do podglądu).
Źródła liczb: bieg kanoniczny (results/agregat_detekcja*.csv) oraz sweep
removal_ratio z results/_faza2_runs.txt.

Uruchomienie:
    python scripts/generate_figures.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGDIR = ROOT / "docs" / "thesis_draft_new" / "thesis" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

# Styl spójny dla wszystkich rysunków.
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "figure.dpi": 150,
})

# paleta czytelna też w skali szarości: heurystyki szare, ML niebieskie,
# detektor wyróżniony pomarańczowym.
C_HEUR = "#9aa3ad"
C_ML = "#4c78a8"
C_DET = "#e4761b"
C_INFECTED = "#d1495b"
C_CLEAN = "#6c8ebf"
C_JOB = "#f0f0f0"

PL_NAMES = {
    "degree_anomaly": "Anomalia stopnia",
    "boundary": "Brzeg (korzeń/liść)",
    "low_job_connectivity": "Niska łączność zadań",
    "rule_root": "Reguła korzenia",
    "completeness": "Kompletność*",
    "RandomForest": "Random Forest",
    "RUSBoost": "RUSBoost",
    "LightGBM": "LightGBM",
    "LineageDetector": "LineageDetector*",
}
HEUR = {"degree_anomaly", "boundary", "low_job_connectivity",
        "rule_root", "completeness"}


def _save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIGDIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  zapisano  figures/{name}.pdf (+.png)")


# RYSUNEK 1 — schemat potoku przetwarzania
def fig_pipeline():
    # Wymiary w calach dobrane tak, by rysunek skladany na szerokosc kolumny
    # tekstu (ok. 6,1 cala) mial czcionke ok. 7 pt.
    fig, ax = plt.subplots(figsize=(6.3, 3.5))
    ax.set_xlim(0, 6.3)
    ax.set_ylim(0, 3.5)
    ax.axis("off")
    fs = 7.5
    w, h = 1.3, 0.72

    def box(x, y, label, color=C_JOB, dashed=False):
        ax.add_patch(FancyBboxPatch(
            (x, y - h / 2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            linewidth=1.0, edgecolor="#333333", facecolor=color,
            linestyle="--" if dashed else "-"))
        ax.text(x + w / 2, y, label, ha="center", va="center", fontsize=fs,
                linespacing=1.3)

    def arrow(p, q):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9,
                                     linewidth=1.0, color="#333333",
                                     shrinkA=2.5, shrinkB=2.5))

    def line(p, q):
        ax.plot([p[0], q[0]], [p[1], q[1]], color="#333333", linewidth=1.0)

    y_top, y_bot = 2.95, 1.35
    top = [0.05, 1.65, 3.35, 4.95]
    box(top[0], y_top, "Zbiór DLG-DG-23\n18 grafów\n(pliki JSON)")
    box(top[1], y_top, "Wczytanie\ngrafów\n(loader.py)")
    box(top[2], y_top, "Benchmark\nDutkiewicza et al.\n(Northwind, CSV)",
        dashed=True)
    box(top[3], y_top, "Adapter DUT\nagregacja do\ntabela–zadanie")
    arrow((top[0] + w, y_top), (top[1], y_top))
    arrow((top[2] + w, y_top), (top[3], y_top))

    bot = [0.05, 1.65, 3.25, 4.85]
    labels = [
        ("Symulacja\nusunięcia zadań\n(etykiety)", C_JOB),
        ("Ekstrakcja cech\n13 cech pozycji\n+ 3 kompletności", C_JOB),
        ("Detektor\nheurystyki, ML,\nLineageDetector", C_DET),
        ("Metryki\nAUC-ROC, AUC-PR,\nP@k, Brier", C_JOB),
    ]
    for x, (lab, col) in zip(bot, labels):
        box(x, y_bot, lab, col)
    for a, b in zip(bot[:-1], bot[1:]):
        arrow((a + w, y_bot), (b, y_bot))

    # Zbieg obu źródeł do wspólnego potoku
    y_bus = (y_top - h / 2 + y_bot + h / 2) / 2
    x_in = bot[0] + w / 2
    line((top[1] + w / 2, y_top - h / 2), (top[1] + w / 2, y_bus))
    line((top[3] + w / 2, y_top - h / 2), (top[3] + w / 2, y_bus))
    line((x_in, y_bus), (top[3] + w / 2, y_bus))
    arrow((x_in, y_bus), (x_in, y_bot + h / 2))

    ax.text(3.15, 0.42,
            "DLG-DG-23: protokół indukcyjny leave-one-graph-out "
            "(trening na 17 grafach, test na 1)\n"
            "DUT: wyłącznie test modeli wytrenowanych na DLG-DG-23",
            ha="center", va="center", fontsize=fs, style="italic",
            color="#555555", linespacing=1.5)
    _save(fig, "rys_potok")


# RYSUNEK 2 — mały graf przed i po usunięciu jobu (infected)
def _draw_lineage(ax, removed):
    """Rysuje przykładowy podgraf lineage; removed=True → job J1 usunięty."""
    T = {
        "T1": (0.6, 3.2), "T2": (0.6, 1.4),
        "T3": (3.4, 2.3),
        "T4": (6.2, 2.3),
    }
    J = {"J1": (2.0, 2.3), "J2": (4.8, 2.3)}

    infected = {"T1", "T2", "T3"} if removed else set()

    # krawędzie DATA_FLOW
    edges = [("T1", "J1"), ("T2", "J1"), ("J1", "T3"),
             ("T3", "J2"), ("J2", "T4")]
    for u, v in edges:
        pu = T.get(u, J.get(u))
        pv = T.get(v, J.get(v))
        dead = removed and ("J1" in (u, v))
        style = dict(arrowstyle="-|>", mutation_scale=12, linewidth=1.4)
        if dead:
            style.update(color="#cccccc", linestyle=(0, (3, 3)))
        else:
            style.update(color="#555555")
        ax.add_patch(FancyArrowPatch(pu, pv, shrinkA=15, shrinkB=15, **style))

    # węzły-tabele (koła)
    for name, (x, yy) in T.items():
        fc = C_INFECTED if name in infected else C_CLEAN
        ax.add_patch(Circle((x, yy), 0.34, facecolor=fc,
                            edgecolor="#333333", linewidth=1.3, zorder=3))
        ax.text(x, yy, name, ha="center", va="center", color="white",
                fontsize=9, fontweight="bold", zorder=4)

    # węzły-joby (kwadraty)
    for name, (x, yy) in J.items():
        gone = removed and name == "J1"
        fc = "#ffffff" if gone else C_JOB
        ec = "#cccccc" if gone else "#333333"
        ax.add_patch(FancyBboxPatch((x - 0.32, yy - 0.32), 0.64, 0.64,
                     boxstyle="round,pad=0.0,rounding_size=0.06",
                     facecolor=fc, edgecolor=ec, linewidth=1.3,
                     linestyle="--" if gone else "-", zorder=3))
        ax.text(x, yy, name, ha="center", va="center",
                color="#bbbbbb" if gone else "#333333",
                fontsize=9, fontweight="bold", zorder=4)

    ax.set_xlim(-0.2, 7.0)
    ax.set_ylim(0.4, 4.2)
    ax.axis("off")


def fig_before_after():
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.4))
    _draw_lineage(axes[0], removed=False)
    axes[0].set_title("(a) Graf oryginalny", fontsize=10)
    _draw_lineage(axes[1], removed=True)
    axes[1].set_title("(b) Po usunięciu zadania J1", fontsize=10)

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor=C_CLEAN, edgecolor="#333", label="Tabela czysta"),
        Patch(facecolor=C_INFECTED, edgecolor="#333", label="Tabela zainfekowana (infected)"),
        Patch(facecolor=C_JOB, edgecolor="#333", label="Zadanie (job)"),
        Line2D([0], [0], color="#cccccc", linestyle="--",
               label="Krawędź utracona"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=4,
               frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "rys_graf_przed_po")


# RYSUNEK 3 — AUC-ROC per algorytm: uczciwy vs zawyżony
def fig_auc_bars():
    honest = pd.read_csv(RESULTS / "agregat_detekcja.csv").set_index("algorithm")
    infl = pd.read_csv(RESULTS / "agregat_detekcja_napompowany.csv").set_index("algorithm")

    order = honest.sort_values("auc_roc_mean").index.tolist()
    labels = [PL_NAMES[a] for a in order]
    y = np.arange(len(order))
    hgt = 0.38

    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    ax.barh(y + hgt / 2, infl.loc[order, "auc_roc_mean"], height=hgt,
            xerr=infl.loc[order, "auc_roc_std"], error_kw=dict(lw=0.8, alpha=0.5),
            color="#c9c9c9", edgecolor="#888", label="Wariant zawyżony (n=10)")
    ax.barh(y - hgt / 2, honest.loc[order, "auc_roc_mean"], height=hgt,
                   xerr=honest.loc[order, "auc_roc_std"],
                   error_kw=dict(lw=0.8, alpha=0.6),
                   color=[C_DET if a == "LineageDetector"
                          else (C_ML if a not in HEUR else C_HEUR) for a in order],
                   edgecolor="#333", label="Wariant uczciwy (n=8)")

    ax.axvline(0.5, color="#333", linestyle=":", linewidth=1.1)
    ax.text(0.5, len(order) - 0.3, "  losowo (0,5)", fontsize=8,
            color="#333", va="center")

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("AUC-ROC (średnia po grafach wiarygodnych)")
    ax.set_xlim(0, 1.0)
    ax.set_title("Skuteczność detekcji zainfekowanych tabel – protokół indukcyjny")

    # wartości wariantu uczciwego na słupkach
    for yi, a in zip(y, order):
        v = honest.loc[a, "auc_roc_mean"]
        ax.text(v + 0.012, yi - hgt / 2, f"{v:.3f}".replace(".", ","),
                va="center", fontsize=7.5)

    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend = [
        Patch(facecolor=C_DET, edgecolor="#333",
              label="Wariant uczciwy (n=8) – autorski detektor"),
        Patch(facecolor=C_ML, edgecolor="#333",
              label="Wariant uczciwy (n=8) – klasyczne ML"),
        Patch(facecolor=C_HEUR, edgecolor="#333",
              label="Wariant uczciwy (n=8) – heurystyki"),
        Patch(facecolor="#c9c9c9", edgecolor="#888",
              label="Wariant zawyżony (n=10) – wszystkie metody"),
        Line2D([0], [0], color="#333", lw=0.8,
               label="Odchylenie standardowe"),
    ]
    ax.legend(handles=legend, loc="upper center", frameon=False, fontsize=8,
              ncol=2, bbox_to_anchor=(0.5, -0.13))
    fig.tight_layout()
    _save(fig, "rys_auc_uczciwy_napompowany")


# RYSUNEK 4 — wrażliwość na removal_ratio (sweep)
def fig_sensitivity():
    # dane wprost ze sweepu w results/_faza2_runs.txt
    ratios = [0.05, 0.10, 0.20, 0.30]
    series = {
        "LineageDetector*": ([0.761, 0.771, 0.755, 0.754], C_DET, "o"),
        "Random Forest":    ([0.760, 0.749, 0.755, 0.756], C_ML, "s"),
        "LightGBM":         ([0.706, 0.720, 0.742, 0.761], "#72b7b2", "^"),
        "Reguła korzenia":  ([0.562, 0.574, 0.592, 0.586], C_HEUR, "D"),
        "Kompletność*":     ([0.554, 0.559, 0.560, 0.532], "#b0b0b0", "v"),
    }
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for name, (vals, col, mk) in series.items():
        lw = 2.4 if name.startswith("Lineage") else 1.4
        ax.plot(ratios, vals, marker=mk, color=col, linewidth=lw,
                markersize=6, label=name,
                zorder=5 if name.startswith("Lineage") else 3)
    ax.axhline(0.5, color="#333", linestyle=":", linewidth=1.0)
    ax.text(0.30, 0.505, "losowo", fontsize=8, color="#333",
            ha="right", va="bottom")
    ax.set_xlabel("removal_ratio (odsetek usuwanych zadań)")
    ax.set_ylabel("AUC-ROC (grafy wiarygodne)")
    ax.set_xticks(ratios)
    ax.set_ylim(0.45, 0.85)
    ax.set_title("Wrażliwość skuteczności na odsetek usuwanych zadań")
    ax.legend(loc="center right", frameon=True, fontsize=8.5)
    fig.text(0.01, -0.02,
             "* wkład własny. Wynik LineageDetectora niemal stały (0,754–0,771), "
             "nie jest artefaktem wyboru removal_ratio.",
             fontsize=7.2, color="#555")
    fig.tight_layout()
    _save(fig, "rys_wrazliwosc_removal_ratio")


if __name__ == "__main__":
    print(f"Rysunki → {FIGDIR}")
    fig_pipeline()
    fig_before_after()
    fig_auc_bars()
    fig_sensitivity()
    print("Gotowe.")
