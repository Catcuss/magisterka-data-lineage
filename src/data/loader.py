"""
Wczytywanie grafów DLG-DG-23 z plików JSON do obiektów NetworkX DiGraph.

Format plików:
  Node.json: {"nodes": [{"asset_id": str, "asset_type": str}, ...]}
  Edge.json: {"edges": [{"relation_id": str, "relation_type": str,
                          "source": str, "target": str}, ...]}

Typy węzłów:  "Data Table", "Data Job", "Data Field"
Typy krawędzi: "DATA_FLOW", "PARENT_CHILD"
"""

import json
from pathlib import Path
import networkx as nx

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "extracted"
NODE_DIR = DATA_DIR / "Node"
EDGE_DIR = DATA_DIR / "Edge"

DLG_IDS = [f"DLG{i}" for i in range(1, 19)]


def load_graph(dlg_id: str) -> nx.DiGraph:
    """
    Wczytuje jeden graf DLG z pary plików JSON.

    Parameters
    ----------
    dlg_id : str
        Identyfikator grafu, np. "DLG1", "DLG15".

    Returns
    -------
    nx.DiGraph
        Graf skierowany z atrybutami:
        - węzeł: asset_type ("Data Table" | "Data Job" | "Data Field")
        - krawędź: relation_type ("DATA_FLOW" | "PARENT_CHILD")
        - atrybut grafu: name (np. "DLG1")
    """
    node_path = NODE_DIR / f"{dlg_id}-node.json"
    edge_path = EDGE_DIR / f"{dlg_id}-edge.json"

    with open(node_path, encoding="utf-8") as f:
        nodes = json.load(f)["nodes"]

    with open(edge_path, encoding="utf-8") as f:
        edges = json.load(f)["edges"]

    G = nx.DiGraph(name=dlg_id)

    for node in nodes:
        G.add_node(node["asset_id"], asset_type=node["asset_type"])

    for edge in edges:
        G.add_edge(
            edge["source"],
            edge["target"],
            relation_id=edge["relation_id"],
            relation_type=edge["relation_type"],
        )

    return G


def load_all_graphs() -> dict[str, nx.DiGraph]:
    """
    Wczytuje wszystkie 18 grafów DLG-DG-23.

    Returns
    -------
    dict[str, nx.DiGraph]
        Słownik {dlg_id: graf}, np. {"DLG1": G1, ..., "DLG18": G18}.
    """
    return {dlg_id: load_graph(dlg_id) for dlg_id in DLG_IDS}


def graph_summary(G: nx.DiGraph) -> dict:
    """
    Zwraca podstawowe statystyki grafu.

    Returns
    -------
    dict z polami: name, nodes, edges, node_types, edge_types
    """
    node_types = {}
    for _, data in G.nodes(data=True):
        t = data.get("asset_type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1

    edge_types = {}
    for _, _, data in G.edges(data=True):
        t = data.get("relation_type", "unknown")
        edge_types[t] = edge_types.get(t, 0) + 1

    return {
        "name": G.graph.get("name"),
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "node_types": node_types,
        "edge_types": edge_types,
    }
