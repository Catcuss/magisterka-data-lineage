"""
Wizualizacja problemu Broken Lineage do prezentacji.
Wynik: results/figures/broken_lineage_diagram.png
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

_OUT = Path(__file__).resolve().parent.parent / "results" / "figures"
_OUT.mkdir(parents=True, exist_ok=True)

# Paleta
C_TABLE   = "#1565C0"
C_JOB     = "#388E3C"
C_STAGING = "#E65100"
C_RED     = "#C62828"
C_GREY    = "#546E7A"
C_BG      = "#F8F9FA"

NODE_W, NODE_H = 1.8, 0.65
XS = [0.9, 3.0, 5.1, 7.2, 9.3]   # pozycje x węzłów
Y  = 0.0                           # wspólna linia y


def _box(ax, x, label, sub, color, alpha=1.0, dashed=False):
    ls = (0, (5, 4)) if dashed else "-"
    p = FancyBboxPatch((x - NODE_W/2, Y - NODE_H/2), NODE_W, NODE_H,
                       boxstyle="round,pad=0.08",
                       facecolor=color, edgecolor="white",
                       linewidth=2.5, linestyle=ls,
                       alpha=alpha, zorder=3)
    ax.add_patch(p)
    ax.text(x, Y + 0.07, label, ha="center", va="center",
            fontsize=8.5, fontweight="bold", color="white",
            alpha=alpha, zorder=4)
    ax.text(x, Y - 0.17, sub, ha="center", va="center",
            fontsize=6.5, color="white", alpha=alpha * 0.80, zorder=4)


def _pill(ax, x, label, color, alpha=1.0):
    e = mpatches.Ellipse((x, Y), 1.65, NODE_H,
                         facecolor=color, edgecolor="white",
                         linewidth=2.5, alpha=alpha, zorder=3)
    ax.add_patch(e)
    ax.text(x, Y, label, ha="center", va="center",
            fontsize=8.5, fontweight="bold", color="white",
            alpha=alpha, zorder=4)


def _arrow(ax, x1, x2, color=C_GREY, lw=2.2, alpha=1.0, dashed=False):
    ls = "dashed" if dashed else "solid"
    ax.annotate("", xy=(x2, Y), xytext=(x1, Y),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, alpha=alpha, linestyle=ls),
                zorder=2)


def _gap(x1, x2):
    """Zwraca x końca lewego węzła i x początku prawego."""
    return x1 + NODE_W/2 + 0.06, x2 - NODE_W/2 - 0.06


def setup_ax(ax, title, title_color):
    ax.set_xlim(-0.2, 10.4)
    ax.set_ylim(-1.1, 0.9)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(C_BG)
    ax.text(5.1, 0.72, title, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=title_color)


# ---------------------------------------------------------------------------
# Panel górny — graf pełny
# ---------------------------------------------------------------------------
def draw_full(ax):
    setup_ax(ax, "Graf pełny", "#1A237E")

    _box  (ax, XS[0], "Table_A",  "source",   C_TABLE)
    _pill (ax, XS[1], "Job_X",                C_JOB)
    _box  (ax, XS[2], "Staging",  "tymczasowa", C_STAGING)
    _pill (ax, XS[3], "Job_Y",                C_JOB)
    _box  (ax, XS[4], "Table_B",  "wynik",    C_TABLE)

    for i in range(4):
        a, b = _gap(XS[i], XS[i+1])
        _arrow(ax, a, b)

    # Adnotacja — staging znika
    ax.annotate("znika po ETL", xy=(XS[2], Y - NODE_H/2),
                xytext=(XS[2], -0.72),
                arrowprops=dict(arrowstyle="-|>", color=C_STAGING,
                                lw=1.5, linestyle="dashed"),
                ha="center", fontsize=9, color=C_STAGING,
                style="italic", zorder=5)


# ---------------------------------------------------------------------------
# Panel dolny — broken lineage
# ---------------------------------------------------------------------------
def draw_broken(ax):
    setup_ax(ax, "Graf po Broken Lineage", C_RED)

    _box  (ax, XS[0], "Table_A", "source", C_TABLE)
    _pill (ax, XS[1], "Job_X",             C_JOB,  alpha=0.45)
    _pill (ax, XS[3], "Job_Y",             C_JOB,  alpha=0.45)
    _box  (ax, XS[4], "Table_B", "wynik",  C_TABLE)

    # Węzeł brakujący
    p = FancyBboxPatch((XS[2] - NODE_W/2, Y - NODE_H/2), NODE_W, NODE_H,
                       boxstyle="round,pad=0.08",
                       facecolor="#FFEBEE", edgecolor=C_RED,
                       linewidth=2.5, linestyle=(0, (5, 3)), zorder=3)
    ax.add_patch(p)
    ax.text(XS[2], Y + 0.06, "???", ha="center", va="center",
            fontsize=13, fontweight="bold", color=C_RED, zorder=4)
    ax.text(XS[2], Y - 0.20, "brakująca tabela", ha="center",
            fontsize=6.5, color=C_RED, style="italic", zorder=4)

    # Krawędź Table_A → Job_X (normalna)
    a, b = _gap(XS[0], XS[1])
    _arrow(ax, a, b, alpha=0.45)

    # Krawędzie do/od ??? (urwane, czerwone)
    a, b = _gap(XS[1], XS[2])
    _arrow(ax, a, b, color=C_RED, lw=2.0, alpha=0.5, dashed=True)
    a, b = _gap(XS[2], XS[3])
    _arrow(ax, a, b, color=C_RED, lw=2.0, alpha=0.5, dashed=True)

    # Krawędź Job_Y → Table_B (normalna)
    a, b = _gap(XS[3], XS[4])
    _arrow(ax, a, b, alpha=0.45)

    # Etykieta braku połączenia
    ax.text(5.1, -0.78, "brak ciągłości lineage",
            ha="center", fontsize=8.5, fontweight="bold",
            color=C_RED,
            bbox=dict(boxstyle="round,pad=0.3", fc="#FFEBEE",
                      ec=C_RED, lw=1.5, alpha=0.9))


# ---------------------------------------------------------------------------
# Legenda typów węzłów (wspólna, pod wykresem)
# ---------------------------------------------------------------------------
def draw_legend(fig):
    items = [
        (C_TABLE,   "Data Table"),
        (C_JOB,     "Data Job"),
        (C_STAGING, "Tabela tymczasowa (staging)"),
    ]
    y = 0.025
    starts = [0.22, 0.44, 0.63]
    for (color, label), x in zip(items, starts):
        fig.add_artist(mpatches.Ellipse((x, y), 0.018, 0.028,
                                        facecolor=color, edgecolor="white",
                                        linewidth=1.5,
                                        transform=fig.transFigure))
        fig.text(x + 0.013, y, label, va="center",
                 fontsize=7.5, color="#37474F",
                 transform=fig.transFigure)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), facecolor=C_BG)
    fig.subplots_adjust(hspace=0.10, left=0.01, right=0.99,
                        top=0.97, bottom=0.08)

    draw_full(axes[0])
    draw_broken(axes[1])
    draw_legend(fig)

    # Linia podziału
    fig.add_artist(plt.Line2D([0.05, 0.95], [0.505, 0.505],
                              transform=fig.transFigure,
                              color="#CFD8DC", linewidth=1.2))

    out = _OUT / "broken_lineage_diagram.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor=C_BG)
    plt.close()
    print(f"Zapisano: {out}")


if __name__ == "__main__":
    main()
