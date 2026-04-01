"""
Wizualizacja grafów DLG-DG-23 z czytelnymi etykietami dla promotora.

Problem: węzły w DLG-DG-23 mają UUID jako identyfikatory (anonimizacja).
Rozwiązanie: zastąpienie UUID pseudonimami T1/T2/... (Tables), J1/J2/... (Jobs).
             Pola (Fields) są pomijane — skupiamy się na podgrafie DATA_FLOW.

Generowane pliki:
    relabeled_DLG1.png  — kompletny mały graf z etykietami
    relabeled_DLG4.png  — kompletny mały graf z etykietami
    broken_lineage_demo.png — porównanie: pełny vs broken lineage (DLG4)
    panel_small_graphs.png  — panel DLG1–DLG4 z etykietami

Uruchomienie:
    python docs/relabeled_graphs/generate_relabeled_viz.py
"""

import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# Ścieżki
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(SCRIPT_DIR, "..", "..", "data", "raw", "extracted")
OUT_DIR = SCRIPT_DIR
os.makedirs(OUT_DIR, exist_ok=True)

# Kolory — identyczne z visualize_graphs.py dla spójności
NODE_COLORS  = {"Data Table": "#4C72B0", "Data Job": "#C44E52"}
EDGE_COLOR   = "#DD8800"
REMOVED_COLOR = "#CC0000"   # brakujące krawędzie (broken lineage)
REMOVED_STYLE = "dashed"


# ---------------------------------------------------------------------------
# Wczytywanie i relabeling
# ---------------------------------------------------------------------------

def load_graph_raw(dlg_id: int) -> nx.DiGraph:
    with open(f"{BASE}/Node/DLG{dlg_id}-node.json", encoding="utf-8") as f:
        nodes = json.load(f)["nodes"]
    with open(f"{BASE}/Edge/DLG{dlg_id}-edge.json", encoding="utf-8") as f:
        edges = json.load(f)["edges"]

    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["asset_id"], asset_type=n["asset_type"])
    for e in edges:
        G.add_edge(e["source"], e["target"],
                   relation_type=e["relation_type"])
    return G


def relabel_graph(G: nx.DiGraph) -> tuple[nx.DiGraph, dict]:
    """
    Zastępuje UUID czytelną etykietą (T1, T2, J1, J2, F1...).
    Zwraca (nowy_graf, słownik_mapowania).
    """
    counters = {"Data Table": 0, "Data Job": 0, "Data Field": 0}
    prefix   = {"Data Table": "T", "Data Job": "J", "Data Field": "F"}

    mapping = {}
    for node, data in G.nodes(data=True):
        t = data.get("asset_type", "Data Table")
        counters[t] += 1
        mapping[node] = f"{prefix.get(t, 'X')}{counters[t]}"

    return nx.relabel_nodes(G, mapping), mapping


def dataflow_subgraph(G: nx.DiGraph) -> nx.DiGraph:
    """Zwraca podgraf zawierający tylko węzły Table/Job i krawędzie DATA_FLOW."""
    keep_nodes = {n for n, d in G.nodes(data=True)
                  if d.get("asset_type") in ("Data Table", "Data Job")}
    keep_edges = [(u, v) for u, v, d in G.edges(data=True)
                  if d.get("relation_type") == "DATA_FLOW"
                  and u in keep_nodes and v in keep_nodes]
    sub = G.subgraph(keep_nodes).copy()
    # usuń krawędzie nie-DATA_FLOW (np. PARENT_CHILD przez Field)
    to_remove = [(u, v) for u, v, d in sub.edges(data=True)
                 if d.get("relation_type") != "DATA_FLOW"]
    sub.remove_edges_from(to_remove)
    return sub


# ---------------------------------------------------------------------------
# Rysowanie
# ---------------------------------------------------------------------------

def _layout(G: nx.DiGraph) -> dict:
    n = G.number_of_nodes()
    if n <= 30:
        return nx.spring_layout(G, k=3.0 / math.sqrt(max(n, 1)), seed=42, iterations=100)
    elif n <= 100:
        return nx.kamada_kawai_layout(G)
    else:
        return nx.spring_layout(G, k=2.0 / math.sqrt(n), seed=42, iterations=60)


def draw_labeled_graph(
    G: nx.DiGraph,
    title: str,
    out_path: str,
    removed_edges: list[tuple] | None = None,
    figsize: tuple = (14, 10),
):
    """
    Rysuje graf z czytelnymi etykietami węzłów (T1, J3, ...).
    Opcjonalnie zaznacza brakujące krawędzie (broken lineage) na czerwono przerywane.
    """
    pos = _layout(G)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#F8F8F8")
    ax.set_facecolor("#F8F8F8")

    node_colors = [
        NODE_COLORS.get(G.nodes[n].get("asset_type", ""), "#888888")
        for n in G.nodes()
    ]
    node_sizes = [
        320 if G.nodes[n].get("asset_type") == "Data Table" else 220
        for n in G.nodes()
    ]

    # Krawędzie istniejące (DATA_FLOW)
    existing = list(G.edges())
    nx.draw_networkx_edges(
        G, pos, edgelist=existing,
        edge_color=EDGE_COLOR, width=1.8, alpha=0.8,
        arrows=True, arrowsize=14, ax=ax,
        connectionstyle="arc3,rad=0.06",
    )

    # Brakujące krawędzie — czerwone przerywane
    if removed_edges:
        # Dodaj je tymczasowo do grafu tylko do rysowania
        G_tmp = G.copy()
        G_tmp.add_edges_from(removed_edges)
        nx.draw_networkx_edges(
            G_tmp, pos, edgelist=removed_edges,
            edge_color=REMOVED_COLOR, width=2.2, alpha=0.9,
            style="dashed", arrows=True, arrowsize=14, ax=ax,
            connectionstyle="arc3,rad=0.06",
        )

    # Węzły
    nx.draw_networkx_nodes(
        G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.95, ax=ax
    )

    # Etykiety
    font_size = max(6, min(10, 130 // max(G.number_of_nodes(), 1)))
    nx.draw_networkx_labels(G, pos, font_size=font_size, font_weight="bold", ax=ax)

    # Legenda
    patches = [
        mpatches.Patch(color=NODE_COLORS["Data Table"], label="Data Table (T)"),
        mpatches.Patch(color=NODE_COLORS["Data Job"],   label="Data Job (J)"),
        mpatches.Patch(color=EDGE_COLOR,                label="DATA_FLOW (istniejący)"),
    ]
    if removed_edges:
        patches.append(
            mpatches.Patch(color=REMOVED_COLOR, label="DATA_FLOW (brakujący – broken lineage)")
        )
    ax.legend(handles=patches, loc="upper left", fontsize=9, framealpha=0.9)

    n_removed = len(removed_edges) if removed_edges else 0
    info = f"\n({n_removed} brakujących krawędzi zaznaczonych)" if n_removed else ""
    ax.set_title(
        f"{title}{info}\n"
        f"{G.number_of_nodes()} węzłów · {G.number_of_edges()} krawędzi DATA_FLOW",
        fontsize=13, fontweight="bold", pad=10,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Zapisano: {out_path}")


# ---------------------------------------------------------------------------
# Generowanie demo broken lineage (pełny vs broken)
# ---------------------------------------------------------------------------

def draw_broken_lineage_comparison(dlg_id: int, n_remove: int = 3):
    """
    Tworzy obraz porównawczy: lewy panel — pełny graf,
    prawy panel — ten sam graf z usuniętymi krawędziami (broken lineage).
    """
    G_raw = load_graph_raw(dlg_id)
    G_labeled, _ = relabel_graph(G_raw)
    G_df = dataflow_subgraph(G_labeled)

    # Wybierz krawędzie do "usunięcia" (symulacja broken lineage)
    all_edges = list(G_df.edges())
    import random
    rng = random.Random(42)
    removed = rng.sample(all_edges, min(n_remove, len(all_edges)))

    G_broken = G_df.copy()
    G_broken.remove_edges_from(removed)

    pos = _layout(G_df)  # ten sam układ dla obu paneli

    fig, (ax_full, ax_broken) = plt.subplots(1, 2, figsize=(22, 10), facecolor="white")

    def _draw_panel(ax, G, extra_edges, title):
        ax.set_facecolor("#F8F8F8")
        node_colors = [NODE_COLORS.get(G.nodes[n].get("asset_type", ""), "#888")
                       for n in G.nodes()]
        node_sizes  = [320 if G.nodes[n].get("asset_type") == "Data Table" else 220
                       for n in G.nodes()]
        nx.draw_networkx_edges(G, pos, edge_color=EDGE_COLOR, width=1.8,
                               alpha=0.8, arrows=True, arrowsize=14, ax=ax,
                               connectionstyle="arc3,rad=0.06")
        if extra_edges:
            G_tmp = G.copy()
            G_tmp.add_edges_from(extra_edges)
            nx.draw_networkx_edges(G_tmp, pos, edgelist=extra_edges,
                                   edge_color=REMOVED_COLOR, width=2.2,
                                   alpha=0.9, style="dashed", arrows=True,
                                   arrowsize=14, ax=ax,
                                   connectionstyle="arc3,rad=0.06")
        nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                               node_size=node_sizes, alpha=0.95, ax=ax)
        font_sz = max(7, min(11, 140 // max(G.number_of_nodes(), 1)))
        nx.draw_networkx_labels(G, pos, font_size=font_sz, font_weight="bold", ax=ax)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=8)
        ax.axis("off")

    _draw_panel(ax_full,   G_df,    [],      f"DLG{dlg_id} — pełny graf lineage\n({G_df.number_of_edges()} krawędzi DATA_FLOW)")
    _draw_panel(ax_broken, G_broken, removed, f"DLG{dlg_id} — broken lineage\n({G_broken.number_of_edges()} krawędzi widocznych, {len(removed)} brakujących)")

    # Wspólna legenda pod wykresami
    patches = [
        mpatches.Patch(color=NODE_COLORS["Data Table"], label="Data Table (T)"),
        mpatches.Patch(color=NODE_COLORS["Data Job"],   label="Data Job (J)"),
        mpatches.Patch(color=EDGE_COLOR,                label="DATA_FLOW — widoczny"),
        mpatches.Patch(color=REMOVED_COLOR,             label="DATA_FLOW — brakujący (tymczasowa tabela usunięta)"),
    ]
    fig.legend(handles=patches, loc="lower center", ncol=4, fontsize=10,
               framealpha=0.9, bbox_to_anchor=(0.5, -0.03))

    plt.suptitle(
        f"Problem broken lineage — DLG{dlg_id} (etykiety: T=Data Table, J=Data Job)",
        fontsize=15, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"broken_lineage_demo_DLG{dlg_id}.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Zapisano: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # 1. Pojedyncze grafy DLG1 i DLG4 z etykietami
    for dlg_id in [1, 4]:
        print(f"\nDLG{dlg_id} — relabeled...")
        G_raw = load_graph_raw(dlg_id)
        G_labeled, mapping = relabel_graph(G_raw)
        G_df = dataflow_subgraph(G_labeled)
        out = os.path.join(OUT_DIR, f"relabeled_DLG{dlg_id}.png")
        draw_labeled_graph(
            G_df,
            title=f"DLG{dlg_id} — podgraf DATA_FLOW (etykiety: T=Table, J=Job)",
            out_path=out,
        )

    # 2. Demo broken lineage: pełny vs broken (DLG4 — dobry rozmiar)
    print("\nBroken lineage demo (DLG4)...")
    draw_broken_lineage_comparison(dlg_id=4, n_remove=4)

    # 3. Panel 2×2: DLG1–DLG4 z etykietami
    print("\nPanel DLG1–DLG4...")
    fig, axes = plt.subplots(2, 2, figsize=(24, 18), facecolor="white")
    axes = axes.flatten()

    for idx, dlg_id in enumerate([1, 2, 3, 4]):
        G_raw = load_graph_raw(dlg_id)
        G_labeled, _ = relabel_graph(G_raw)
        G_df = dataflow_subgraph(G_labeled)
        pos = _layout(G_df)
        ax = axes[idx]
        ax.set_facecolor("#F8F8F8")
        nc = [NODE_COLORS.get(G_df.nodes[n].get("asset_type", ""), "#888") for n in G_df.nodes()]
        ns = [300 if G_df.nodes[n].get("asset_type") == "Data Table" else 200 for n in G_df.nodes()]
        nx.draw_networkx_edges(G_df, pos, edge_color=EDGE_COLOR, width=1.5,
                               alpha=0.8, arrows=True, arrowsize=12, ax=ax,
                               connectionstyle="arc3,rad=0.06")
        nx.draw_networkx_nodes(G_df, pos, node_color=nc, node_size=ns, alpha=0.95, ax=ax)
        fs = max(6, min(10, 130 // max(G_df.number_of_nodes(), 1)))
        nx.draw_networkx_labels(G_df, pos, font_size=fs, font_weight="bold", ax=ax)
        ax.set_title(
            f"DLG{dlg_id}  ({G_df.number_of_nodes()} węzłów, {G_df.number_of_edges()} krawędzi)",
            fontsize=12, fontweight="bold",
        )
        ax.axis("off")

    patches = [
        mpatches.Patch(color=NODE_COLORS["Data Table"], label="Data Table (T)"),
        mpatches.Patch(color=NODE_COLORS["Data Job"],   label="Data Job (J)"),
        mpatches.Patch(color=EDGE_COLOR,                label="DATA_FLOW"),
    ]
    fig.legend(handles=patches, loc="lower center", ncol=3, fontsize=11,
               framealpha=0.9, bbox_to_anchor=(0.5, -0.02))
    plt.suptitle(
        "DLG-DG-23 — grafy DLG1–DLG4 (podgraf DATA_FLOW, etykiety T/J zamiast UUID)",
        fontsize=15, fontweight="bold",
    )
    plt.tight_layout()
    panel_out = os.path.join(OUT_DIR, "panel_small_graphs.png")
    plt.savefig(panel_out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Zapisano: {panel_out}")

    print("\nGotowe. Pliki:")
    for f in sorted(os.listdir(OUT_DIR)):
        if f.endswith(".png"):
            print(f"  {os.path.join(OUT_DIR, f)}")


if __name__ == "__main__":
    main()
