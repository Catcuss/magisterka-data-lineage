"""
Wizualizacja broken lineage na prawdziwym grafie DLG-DG-23.

Generuje PNG dla wybranego grafu (domyslnie DLG4) pokazujac:
  1. Pelny podgraf DATA_FLOW (wszystkie krawedzie)
  2. Symulacje broken lineage: 80% krawedzi widocznych (train),
     20% ukrytych (test) -- zielone przerywane = do odtworzenia

Wezly maja etykiety T1/T2.../J1/J2... zamiast UUID.

Uruchomienie:
    python docs/real_graph_demo/real_graph_viz.py
    python docs/real_graph_demo/real_graph_viz.py DLG7
"""

import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# Dodaj katalog projektu do sciezki
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.data.loader import load_graph
from src.data.splitter import split_edges

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT_DIR, exist_ok=True)

NODE_COLORS = {
    "Data Table": "#4C72B0",
    "Data Job":   "#C44E52",
    "Data Field": "#55A868",
}
EDGE_TRAIN_COLOR  = "#DD8800"   # pomaranczowy -- krawedzie widoczne (train)
EDGE_TEST_COLOR   = "#22AA44"   # zielony -- krawedzie ukryte (do odtworzenia)
EDGE_NEG_COLOR    = "#AAAAAA"   # szary -- przykladowe pary negatywne


def build_short_labels(G):
    """Przypisuje krotkie etykiety: T1..Tn dla tabel, J1..Jn dla jobow."""
    t_count, j_count, f_count = 0, 0, 0
    labels = {}
    for node, data in G.nodes(data=True):
        t = data.get("asset_type", "")
        if t == "Data Table":
            t_count += 1
            labels[node] = f"T{t_count}"
        elif t == "Data Job":
            j_count += 1
            labels[node] = f"J{j_count}"
        else:
            f_count += 1
            labels[node] = f"F{f_count}"
    return labels


def extract_dataflow_subgraph(G):
    """Zwraca podgraf zawierajacy tylko wezly i krawedzie DATA_FLOW."""
    df_edges = [(u, v) for u, v, d in G.edges(data=True)
                if d.get("relation_type") == "DATA_FLOW"]
    nodes_in_df = set()
    for u, v in df_edges:
        nodes_in_df.add(u)
        nodes_in_df.add(v)
    H = G.subgraph(nodes_in_df).copy()
    # Usun krawedzie PARENT_CHILD jesli jakies sa
    to_remove = [(u, v) for u, v, d in H.edges(data=True)
                 if d.get("relation_type") != "DATA_FLOW"]
    H.remove_edges_from(to_remove)
    return H


def draw_graph(ax, G, pos, labels, train_edges, test_edges,
               neg_sample=None, title=""):
    """Rysuje podgraf DATA_FLOW z rozroznieniem krawedzi train/test."""
    node_list = list(G.nodes())
    node_colors = [NODE_COLORS.get(G.nodes[n].get("asset_type", ""), "#888") for n in node_list]

    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=node_list,
                           node_color=node_colors, node_size=900, alpha=0.93)
    nx.draw_networkx_labels(G, pos, labels={n: labels.get(n, n[:6]) for n in node_list},
                            ax=ax, font_size=8, font_color="white", font_weight="bold")

    # Krawedzie treningowe (widoczne)
    if train_edges:
        nx.draw_networkx_edges(G, pos, edgelist=train_edges, ax=ax,
                               edge_color=EDGE_TRAIN_COLOR, arrows=True,
                               arrowsize=18, width=2.0,
                               connectionstyle="arc3,rad=0.07")

    # Krawedzie testowe (ukryte -- broken lineage)
    if test_edges:
        # Tymczasowo dodaj do grafu zeby narysowac
        G_tmp = G.copy()
        for u, v in test_edges:
            if not G_tmp.has_edge(u, v):
                G_tmp.add_edge(u, v)
        nx.draw_networkx_edges(G_tmp, pos, edgelist=test_edges, ax=ax,
                               edge_color=EDGE_TEST_COLOR, arrows=True,
                               arrowsize=18, width=2.5, style="dashed",
                               connectionstyle="arc3,rad=0.07", alpha=0.85)

    # Przykladowe pary negatywne (szare przerywane, jesli podane)
    if neg_sample:
        G_tmp2 = G.copy()
        for u, v in neg_sample:
            if not G_tmp2.has_edge(u, v):
                G_tmp2.add_edge(u, v)
        nx.draw_networkx_edges(G_tmp2, pos, edgelist=neg_sample, ax=ax,
                               edge_color=EDGE_NEG_COLOR, arrows=True,
                               arrowsize=12, width=1.0, style="dotted",
                               connectionstyle="arc3,rad=0.18", alpha=0.5)

    ax.set_title(title, fontsize=10, fontweight="bold", pad=10)
    ax.axis("off")


def visualize_broken_lineage(dlg_id="DLG4", seed=42):
    print(f"Wczytywanie {dlg_id}...")
    G = load_graph(dlg_id)

    # Podgraf DATA_FLOW
    H = extract_dataflow_subgraph(G)
    labels = build_short_labels(H)
    n_tables = sum(1 for _, d in H.nodes(data=True) if d.get("asset_type") == "Data Table")
    n_jobs   = sum(1 for _, d in H.nodes(data=True) if d.get("asset_type") == "Data Job")
    n_df     = H.number_of_edges()
    print(f"  Podgraf DATA_FLOW: {n_tables} tabel, {n_jobs} jobow, {n_df} krawedzi")

    # Split 80/20
    split = split_edges(G, edge_type="DATA_FLOW", test_ratio=0.2, seed=seed)
    pos_train = set(map(tuple, split["pos_train"]))
    pos_test  = set(map(tuple, split["pos_test"]))
    neg_test  = list(map(tuple, split["neg_test"]))[:5]  # tylko 5 dla czytelnosci

    train_edges = [e for e in H.edges() if e in pos_train]
    test_edges  = [e for e in pos_test]

    n_train = len(train_edges)
    n_test  = len(test_edges)
    print(f"  Train: {n_train} krawedzi ({n_train/n_df*100:.0f}%)")
    print(f"  Test (ukryte): {n_test} krawedzi ({n_test/n_df*100:.0f}%)")

    # Layout -- spring layout na pelnym grafie H
    pos = nx.spring_layout(H, seed=seed, k=2.5)

    # --- Rysunek ---
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(
        f"Graf {dlg_id} -- Symulacja broken lineage\n"
        f"({n_tables} tabel [T], {n_jobs} jobow [J], {n_df} krawedzi DATA_FLOW)",
        fontsize=13, fontweight="bold"
    )

    # Lewy panel: pelny graf
    draw_graph(
        axes[0], H, pos, labels,
        train_edges=list(H.edges()),
        test_edges=[],
        title=f"Graf pelny -- wszystkie {n_df} krawedzie DATA_FLOW\n(stan przed broken lineage)"
    )

    # Prawy panel: broken lineage
    draw_graph(
        axes[1], H, pos, labels,
        train_edges=train_edges,
        test_edges=test_edges,
        neg_sample=neg_test,
        title=(
            f"Symulacja broken lineage\n"
            f"Widoczne (train): {n_train}   "
            f"Ukryte / do odtworzenia (test): {n_test}\n"
            f"Szare kropkowane = przyklady par bez krawedzi (klasa negatywna)"
        )
    )

    # Legenda
    legend_handles = [
        mpatches.Patch(color=NODE_COLORS["Data Table"], label="Data Table (Tn)"),
        mpatches.Patch(color=NODE_COLORS["Data Job"],   label="Data Job (Jn)"),
        mpatches.Patch(color=EDGE_TRAIN_COLOR,  label="DATA_FLOW -- krawedz widoczna (train)"),
        mpatches.Patch(color=EDGE_TEST_COLOR,   label="DATA_FLOW -- krawedz ukryta (test, broken lineage)"),
        mpatches.Patch(color=EDGE_NEG_COLOR,    label="Para negatywna -- brak krawedzi (klasa 0)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=3, fontsize=9,
               bbox_to_anchor=(0.5, -0.02))

    fig.tight_layout(rect=[0, 0.08, 1, 0.97])

    out = os.path.join(OUT_DIR, f"{dlg_id}_broken_lineage.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Zapisano: {out}")

    # --- Drugi rysunek: tylko wezly dotknięte przez broken lineage (zoom) ---
    broken_nodes = set()
    for u, v in test_edges:
        broken_nodes.add(u)
        broken_nodes.add(v)
    # Dodaj bezposrednich sasiadow
    for node in list(broken_nodes):
        broken_nodes.update(H.predecessors(node))
        broken_nodes.update(H.successors(node))

    H_zoom = H.subgraph(broken_nodes).copy()
    pos_zoom = nx.spring_layout(H_zoom, seed=seed, k=3.0)
    train_zoom = [e for e in H_zoom.edges() if e in pos_train]
    test_zoom  = [e for e in test_edges if e[0] in broken_nodes and e[1] in broken_nodes]

    fig2, ax2 = plt.subplots(figsize=(12, 7))
    fig2.suptitle(
        f"Graf {dlg_id} -- Zoom: obszary dotkniete przez broken lineage\n"
        f"(tylko wezly polaczone z ukrytymi krawedziami i ich sasiedzi)",
        fontsize=12, fontweight="bold"
    )
    draw_graph(
        ax2, H_zoom, pos_zoom, labels,
        train_edges=train_zoom,
        test_edges=test_zoom,
        title=(
            f"Pomaranczowe = krawedzie znane (train)\n"
            f"Zielone przerywane = krawedzie ukryte (broken lineage, do odtworzenia przez algorytm)"
        )
    )
    fig2.legend(handles=legend_handles[:4], loc="lower center", ncol=2, fontsize=9,
                bbox_to_anchor=(0.5, -0.02))
    fig2.tight_layout(rect=[0, 0.08, 1, 0.95])

    out2 = os.path.join(OUT_DIR, f"{dlg_id}_broken_lineage_zoom.png")
    fig2.savefig(out2, dpi=150, bbox_inches="tight")
    plt.close(fig2)
    print(f"[OK] Zoom zapisany: {out2}")


if __name__ == "__main__":
    dlg_id = sys.argv[1] if len(sys.argv) > 1 else "DLG4"
    visualize_broken_lineage(dlg_id)
    print("\nGotowe! Pliki w:", OUT_DIR)
