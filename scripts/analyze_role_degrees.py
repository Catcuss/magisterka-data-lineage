"""
Analiza stopni węzłów per rola ETL w grafach DLG-DG-23.

Generuje:
  results/figures/role_degree_boxplot.png  — box plot stopni per rola
  results/figures/role_counts_per_graph.png — liczba węzłów per rola per graf
  results/role_degree_stats.csv            — statystyki opisowe

Użycie:
  python scripts/analyze_role_degrees.py
  python scripts/analyze_role_degrees.py --dlg 1 2 3   # wybrane grafy
"""

import argparse
import csv
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph, DLG_IDS

_FIGURES_DIR = _PROJECT_ROOT / "results" / "figures"
_RESULTS_DIR = _PROJECT_ROOT / "results"

_ROLE_COLORS = {
    "source":       "#2196F3",   # niebieski
    "intermediate": "#F44336",   # czerwony — najważniejszy (broken lineage)
    "sink":         "#4CAF50",   # zielony
    "isolated":     "#9E9E9E",   # szary
}

_ROLE_ORDER = ["source", "intermediate", "sink", "isolated"]


def classify_role(G, node) -> str:
    df_in  = sum(1 for _, _, d in G.in_edges(node,  data=True)
                 if d.get("relation_type") == "DATA_FLOW")
    df_out = sum(1 for _, _, d in G.out_edges(node, data=True)
                 if d.get("relation_type") == "DATA_FLOW")
    if df_in > 0 and df_out > 0:    return "intermediate"
    elif df_in == 0 and df_out > 0: return "source"
    elif df_in > 0 and df_out == 0: return "sink"
    return "isolated"


def collect_data(dlg_ids: list[str]) -> tuple[dict, list[dict]]:
    """
    Zbiera stopnie węzłów per rola i per graf.

    Returns
    -------
    role_degrees : dict[role, list[int]]
        Wszystkie stopnie węzłów danej roli (łącznie ze wszystkich grafów).
    per_graph : list[dict]
        Statystyki per graf dla CSV.
    """
    role_degrees: dict = defaultdict(list)
    per_graph: list[dict] = []

    for dlg_id in dlg_ids:
        G = load_graph(dlg_id)
        graph_roles: dict = defaultdict(list)

        for n in G.nodes():
            role = classify_role(G, n)
            deg  = G.degree(n)
            role_degrees[role].append(deg)
            graph_roles[role].append(deg)

        for role in _ROLE_ORDER:
            vals = graph_roles.get(role, [])
            per_graph.append({
                "graph":  dlg_id,
                "role":   role,
                "count":  len(vals),
                "mean":   round(np.mean(vals), 2)   if vals else 0,
                "median": round(np.median(vals), 2) if vals else 0,
                "max":    max(vals)                  if vals else 0,
                "min":    min(vals)                  if vals else 0,
            })

        counts = {r: len(graph_roles.get(r, [])) for r in _ROLE_ORDER}
        print(f"  {dlg_id:<6}  "
              f"source={counts['source']:4d}  "
              f"intermediate={counts['intermediate']:4d}  "
              f"sink={counts['sink']:4d}  "
              f"isolated={counts['isolated']:5d}")

    return dict(role_degrees), per_graph


def plot_boxplot(role_degrees: dict, out_path: Path) -> None:
    """Box plot stopni węzłów per rola (bez isolated — dominuje skalę)."""
    roles_shown = ["source", "intermediate", "sink"]
    data   = [role_degrees.get(r, [0]) for r in roles_shown]
    colors = [_ROLE_COLORS[r] for r in roles_shown]
    labels = [
        f"source\n(n={len(role_degrees.get('source',[]))})",
        f"intermediate\n(n={len(role_degrees.get('intermediate',[]))})",
        f"sink\n(n={len(role_degrees.get('sink',[]))})",
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Lewy panel: pełna skala
    bp = axes[0].boxplot(data, patch_artist=True, notch=False,
                         medianprops={"color": "black", "linewidth": 2})
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    axes[0].set_xticks(range(1, len(roles_shown) + 1))
    axes[0].set_xticklabels(labels)
    axes[0].set_ylabel("Stopień węzła (degree)")
    axes[0].set_title("Rozkład stopni per rola ETL\n(pełna skala)")
    axes[0].grid(axis="y", alpha=0.3)

    # Prawy panel: percentyl 95 — bez outlierów
    p95 = max(np.percentile(d, 95) for d in data if d)
    bp2 = axes[1].boxplot(data, patch_artist=True, notch=False,
                          medianprops={"color": "black", "linewidth": 2},
                          showfliers=False)
    for patch, color in zip(bp2["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    axes[1].set_xticks(range(1, len(roles_shown) + 1))
    axes[1].set_xticklabels(labels)
    axes[1].set_ylabel("Stopień węzła (degree)")
    axes[1].set_ylim(0, p95 * 1.1)
    axes[1].set_title("Rozkład stopni per rola ETL\n(bez outlierów, do p95)")
    axes[1].grid(axis="y", alpha=0.3)

    for ax, bp_obj in [(axes[0], bp), (axes[1], bp2)]:
        for i, d in enumerate(data):
            med = np.median(d)
            ax.text(i + 1, med, f" {med:.1f}", va="center",
                    fontsize=8, color="black", fontweight="bold")

    fig.suptitle("DLG-DG-23: Stopień węzłów per rola ETL\n"
                 "(source=niebieskie, intermediate=czerwone, sink=zielone)",
                 fontsize=11)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nWykres zapisany: {out_path}")


def plot_counts(per_graph: list[dict], out_path: Path) -> None:
    """Stacked bar chart: liczba węzłów per rola per graf."""
    graphs = sorted(set(r["graph"] for r in per_graph),
                    key=lambda x: int(x.replace("DLG", "")))

    counts = {role: [] for role in _ROLE_ORDER}
    for g in graphs:
        rows = {r["role"]: r["count"] for r in per_graph if r["graph"] == g}
        for role in _ROLE_ORDER:
            counts[role].append(rows.get(role, 0))

    x = np.arange(len(graphs))
    width = 0.6
    fig, ax = plt.subplots(figsize=(14, 5))

    bottom = np.zeros(len(graphs))
    for role in _ROLE_ORDER:
        vals = np.array(counts[role], dtype=float)
        ax.bar(x, vals, width, bottom=bottom,
               color=_ROLE_COLORS[role], label=role, alpha=0.85)
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels(graphs, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Liczba węzłów")
    ax.set_title("DLG-DG-23: Liczba węzłów per rola ETL per graf")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Wykres zapisany: {out_path}")


def save_csv(per_graph: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["graph", "role", "count", "mean", "median", "min", "max"]
    with out_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(per_graph)
    print(f"CSV zapisany:    {out_path}")


def print_summary(role_degrees: dict) -> None:
    print("\n" + "=" * 60)
    print(f"{'Rola':<14} {'n':>6} {'mediana':>8} {'mean':>8} {'max':>6}")
    print("-" * 60)
    for role in _ROLE_ORDER:
        vals = role_degrees.get(role, [])
        if not vals:
            continue
        print(f"{role:<14} {len(vals):>6} "
              f"{np.median(vals):>8.1f} "
              f"{np.mean(vals):>8.1f} "
              f"{max(vals):>6}")
    print("=" * 60)

    # Wniosek o wagach RWPA
    med_interm = np.median(role_degrees.get("intermediate", [1]))
    med_source = np.median(role_degrees.get("source", [1]))
    med_sink   = np.median(role_degrees.get("sink",   [1]))
    print("\nWniosek dla wag RWPA:")
    if med_source > med_interm:
        print(f"  UWAGA: source (mediana={med_source:.1f}) > intermediate (mediana={med_interm:.1f})")
        print("  PA już implicite preferuje source. Wagi RWPA mogą być redundantne.")
        print("  Rozważ: zmień uzasadnienie RWPA lub dostosuj wagi.")
    else:
        print(f"  OK: intermediate (mediana={med_interm:.1f}) NIE dominuje stopniem.")
        print(f"  source={med_source:.1f}, sink={med_sink:.1f}")
        print("  Wagi RWPA (3.0/1.5/1.0) mają uzasadnienie — intermediate nie jest")
        print("  automatycznie premiowany przez PA. RWPA dodaje realny sygnał.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dlg", nargs="+", type=int,
                        help="wybrane numery grafów (domyślnie wszystkie 18)")
    args = parser.parse_args()

    if args.dlg:
        dlg_ids = [f"DLG{i}" for i in args.dlg]
    else:
        dlg_ids = DLG_IDS

    print(f"Analizuję {len(dlg_ids)} grafów...")
    role_degrees, per_graph = collect_data(dlg_ids)

    print_summary(role_degrees)
    plot_boxplot(role_degrees,  _FIGURES_DIR / "role_degree_boxplot.png")
    plot_counts(per_graph,      _FIGURES_DIR / "role_counts_per_graph.png")
    save_csv(per_graph,         _RESULTS_DIR / "role_degree_stats.csv")


if __name__ == "__main__":
    main()
