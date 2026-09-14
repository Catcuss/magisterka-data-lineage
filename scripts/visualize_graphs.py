"""
Wizualizacja grafów DLG-DG-23.
Generuje osobne PNG dla każdego grafu (małe: pełne, duże: próbka).
"""

import json
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# Konfiguracja kolorów
NODE_COLORS = {
    "Data Table": "#4C72B0",   # niebieski
    "Data Field": "#55A868",   # zielony
    "Data Job":   "#C44E52",   # czerwony
}
EDGE_COLORS = {
    "PARENT_CHILD": "#AAAAAA",  # szary
    "DATA_FLOW":    "#DD8800",  # pomarańczowy
}

BASE = "C:/Users/Maria/Desktop/MAGISTERKA/data/raw/extracted"
OUT_DIR = "C:/Users/Maria/Desktop/MAGISTERKA/docs/graphs"
os.makedirs(OUT_DIR, exist_ok=True)

# Próg: grafy większe niż MAX_NODES wizualizowane jako próbka
MAX_NODES = 500
SAMPLE_SEED = 42


def load_graph(i: int) -> nx.DiGraph:
    with open(f"{BASE}/Node/DLG{i}-node.json") as f:
        nodes = json.load(f)["nodes"]
    with open(f"{BASE}/Edge/DLG{i}-edge.json") as f:
        edges = json.load(f)["edges"]

    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["asset_id"], asset_type=n["asset_type"])
    for e in edges:
        G.add_edge(e["source"], e["target"],
                   relation_type=e["relation_type"],
                   relation_id=e["relation_id"])
    return G


def sample_subgraph(G: nx.DiGraph, max_nodes: int, seed: int) -> nx.DiGraph:
    """Losuje spójny podgraf: zaczyna od losowego węzła, BFS do max_nodes."""
    import random
    rng = random.Random(seed)
    nodes = list(G.nodes())
    start = rng.choice(nodes)
    visited = []
    queue = [start]
    seen = {start}
    while queue and len(visited) < max_nodes:
        cur = queue.pop(0)
        visited.append(cur)
        neighbors = list(G.successors(cur)) + list(G.predecessors(cur))
        rng.shuffle(neighbors)
        for nb in neighbors:
            if nb not in seen:
                seen.add(nb)
                queue.append(nb)
    return G.subgraph(visited).copy()


def draw_graph(G: nx.DiGraph, title: str, out_path: str, is_sample: bool = False):
    n = G.number_of_nodes()
    # Dobierz rozmiar figury i layout w zależności od wielkości
    if n <= 100:
        figsize = (12, 9)
        k = 2.5 / math.sqrt(n)
        layout = nx.spring_layout(G, k=k, seed=42, iterations=80)
        node_size = 200
        font_size = 0
        edge_width = 1.2
        arrows = True
        arrowsize = 10
    elif n <= 300:
        figsize = (16, 12)
        k = 2.0 / math.sqrt(n)
        layout = nx.spring_layout(G, k=k, seed=42, iterations=60)
        node_size = 80
        font_size = 0
        edge_width = 0.7
        arrows = True
        arrowsize = 7
    else:
        figsize = (20, 15)
        layout = nx.kamada_kawai_layout(G)
        node_size = 30
        font_size = 0
        edge_width = 0.4
        arrows = True
        arrowsize = 5

    fig, ax = plt.subplots(figsize=figsize, facecolor="#F8F8F8")
    ax.set_facecolor("#F8F8F8")

    node_color_list = [
        NODE_COLORS.get(G.nodes[n].get("asset_type", ""), "#888888")
        for n in G.nodes()
    ]

    # Rysuj krawędzie osobno według typu
    for rel_type, color in EDGE_COLORS.items():
        edge_list = [
            (u, v) for u, v, d in G.edges(data=True)
            if d.get("relation_type") == rel_type
        ]
        if edge_list:
            nx.draw_networkx_edges(
                G, layout,
                edgelist=edge_list,
                edge_color=color,
                width=edge_width,
                alpha=0.7,
                arrows=arrows,
                arrowsize=arrowsize,
                ax=ax,
                connectionstyle="arc3,rad=0.05",
            )

    nx.draw_networkx_nodes(
        G, layout,
        node_color=node_color_list,
        node_size=node_size,
        alpha=0.9,
        ax=ax,
    )

    node_patches = [
        mpatches.Patch(color=c, label=t)
        for t, c in NODE_COLORS.items()
    ]
    edge_patches = [
        mpatches.Patch(color=c, label=t)
        for t, c in EDGE_COLORS.items()
    ]

    ax.legend(
        handles=node_patches + edge_patches,
        loc="upper left",
        fontsize=10,
        framealpha=0.85,
    )

    sample_info = f" (próbka {G.number_of_nodes()} węzłów)" if is_sample else ""
    ax.set_title(
        f"{title}{sample_info}\n"
        f"{G.number_of_nodes()} węzłów · {G.number_of_edges()} krawędzi",
        fontsize=14, fontweight="bold", pad=12,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Zapisano: {out_path}")


def main():
    for i in range(1, 19):
        G_full = load_graph(i)
        n_full = G_full.number_of_nodes()
        is_sample = n_full > MAX_NODES

        if is_sample:
            G_vis = sample_subgraph(G_full, MAX_NODES, SAMPLE_SEED)
        else:
            G_vis = G_full

        out_path = f"{OUT_DIR}/DLG{i:02d}.png"
        print(f"DLG{i:2d}: {n_full:5d} wezlow, {G_full.number_of_edges():5d} krawedzi"
              + (" -> probka" if is_sample else " -> pelny"))
        draw_graph(G_vis, f"DLG {i}", out_path, is_sample=is_sample)

    # Stwórz też panel 3x6 z miniaturkami wszystkich grafów
    print("\nGeneruję panel zbiorczy...")
    fig, axes = plt.subplots(3, 6, figsize=(36, 18), facecolor="white")
    axes = axes.flatten()

    for idx, i in enumerate(range(1, 19)):
        img_path = f"{OUT_DIR}/DLG{i:02d}.png"
        img = plt.imread(img_path)
        axes[idx].imshow(img)
        axes[idx].axis("off")
        axes[idx].set_title(f"DLG {i}", fontsize=11, fontweight="bold")

    plt.suptitle("DLG-DG-23 — wszystkie 18 grafów data lineage", fontsize=18, fontweight="bold", y=1.01)
    plt.tight_layout()
    panel_path = f"{OUT_DIR}/all_graphs_panel.png"
    plt.savefig(panel_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Panel: {panel_path}")


if __name__ == "__main__":
    main()
