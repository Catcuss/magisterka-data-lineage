"""
Czysta wizualizacja grafu lineage dla promotora.
Pokazuje tylko węzły Data Table i Data Job połączone krawędziami DATA_FLOW.
Układ hierarchiczny (warstwy topologiczne).
"""

import json
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import networkx as nx


BASE = "C:/Users/Maria/Desktop/MAGISTERKA/data/raw/extracted"
OUT_DIR = "C:/Users/Maria/Desktop/MAGISTERKA/docs/graphs"

COLORS = {
    "Data Table": "#4C72B0",   # niebieski
    "Data Job":   "#C44E52",   # czerwony
}
EDGE_COLOR = "#444444"


def load_high_level_graph(graph_id: int) -> nx.DiGraph:
    """Ładuje graf z tylko Data Table i Data Job węzłami i DATA_FLOW krawędziami."""
    with open(f"{BASE}/Node/DLG{graph_id}-node.json") as f:
        nodes = json.load(f)["nodes"]
    with open(f"{BASE}/Edge/DLG{graph_id}-edge.json") as f:
        edges = json.load(f)["edges"]

    allowed_types = {"Data Table", "Data Job"}
    node_type = {
        n["asset_id"]: n["asset_type"]
        for n in nodes
        if n["asset_type"] in allowed_types
    }

    G = nx.DiGraph()
    for nid, ntype in node_type.items():
        G.add_node(nid, asset_type=ntype)
    for e in edges:
        if (e["relation_type"] == "DATA_FLOW"
                and e["source"] in node_type
                and e["target"] in node_type):
            G.add_edge(e["source"], e["target"])

    # Usuń izolowane węzły (brak krawędzi DATA_FLOW)
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    return G


def assign_layers(G: nx.DiGraph) -> dict:
    """Przypisuje warstwę każdemu węzłowi via najdłuższa ścieżka od źródeł."""
    layer = {}
    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        if not preds:
            layer[node] = 0
        else:
            layer[node] = max(layer[p] for p in preds) + 1
    return layer


def hierarchical_layout(G: nx.DiGraph, vertical: bool = True) -> dict:
    """Hierarchiczny układ węzłów według warstw topologicznych."""
    # Dla grafów z cyklami użyj spring_layout
    if not nx.is_directed_acyclic_graph(G):
        return nx.spring_layout(G, k=2.5 / math.sqrt(max(len(G), 1)), seed=42)

    layer = assign_layers(G)

    # Grupuj węzły po warstwach
    from collections import defaultdict
    layers_dict = defaultdict(list)
    for node, lyr in layer.items():
        layers_dict[lyr].append(node)

    # Sortuj w każdej warstwie: najpierw Data Table, potem Data Job
    for lyr in layers_dict:
        layers_dict[lyr].sort(key=lambda n: (G.nodes[n].get("asset_type", ""), n))

    pos = {}
    max_layer = max(layers_dict.keys()) if layers_dict else 0
    for lyr, nodes_in_layer in sorted(layers_dict.items()):
        n = len(nodes_in_layer)
        for i, node in enumerate(nodes_in_layer):
            x = lyr / max(max_layer, 1)
            y = (i - (n - 1) / 2) / max(n, 1)
            if vertical:
                pos[node] = (x, -y)
            else:
                pos[node] = (y, -x)
    return pos


def short_label(node_id: str, node_type: str, index: int) -> str:
    prefix = "T" if node_type == "Data Table" else "J"
    return f"{prefix}{index}"


def draw_clean_graph(G: nx.DiGraph, title: str, out_path: str):
    n = G.number_of_nodes()
    if n == 0:
        print(f"  Pusty graf (brak węzłów po filtracji): {title}")
        return

    pos = hierarchical_layout(G)

    # Numerowanie węzłów
    table_idx = {}
    job_idx = {}
    t_cnt, j_cnt = 1, 1
    for node in G.nodes():
        t = G.nodes[node].get("asset_type", "")
        if t == "Data Table":
            table_idx[node] = t_cnt
            t_cnt += 1
        else:
            job_idx[node] = j_cnt
            j_cnt += 1

    labels = {}
    for node in G.nodes():
        t = G.nodes[node].get("asset_type", "")
        if t == "Data Table":
            labels[node] = f"T{table_idx[node]}"
        else:
            labels[node] = f"J{job_idx[node]}"

    node_colors = [COLORS.get(G.nodes[n].get("asset_type", ""), "#888") for n in G.nodes()]

    figsize = (max(14, n // 2), max(8, n // 3))
    node_size = max(400, 1200 - n * 20)
    font_size = max(7, 11 - n // 10)

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    ax.set_facecolor("white")

    nx.draw_networkx_edges(
        G, pos,
        edge_color=EDGE_COLOR,
        width=1.8,
        alpha=0.75,
        arrows=True,
        arrowsize=18,
        arrowstyle="-|>",
        node_size=node_size,
        ax=ax,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=15,
        min_target_margin=15,
    )

    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=node_size,
        alpha=0.92,
        ax=ax,
    )

    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=font_size,
        font_color="white",
        font_weight="bold",
        ax=ax,
    )

    patches = [
        mpatches.Patch(color=COLORS["Data Table"], label="Data Table (T)"),
        mpatches.Patch(color=COLORS["Data Job"],   label="Data Job (J)"),
    ]
    ax.legend(handles=patches, loc="upper left", fontsize=11, framealpha=0.9)

    ax.set_title(
        f"{title}  —  graf zależności (tylko DATA_FLOW)\n"
        f"{t_cnt-1} tabel · {j_cnt-1} zadań · {G.number_of_edges()} krawędzi",
        fontsize=14, fontweight="bold", pad=14,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Zapisano: {out_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Czysta wizualizacja grafów lineage")
    parser.add_argument(
        "graphs", nargs="*", type=int, default=list(range(1, 19)),
        help="Numery grafów do wygenerowania (domyślnie: wszystkie 1-18)"
    )
    parser.add_argument("--outdir", default=OUT_DIR)
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    for i in args.graphs:
        G = load_high_level_graph(i)
        print(f"DLG{i:2d}: {G.number_of_nodes()} węzłów, {G.number_of_edges()} krawędzi (po filtracji)")
        out_path = f"{args.outdir}/DLG{i:02d}_clean.png"
        draw_clean_graph(G, f"DLG {i}", out_path)


if __name__ == "__main__":
    main()
