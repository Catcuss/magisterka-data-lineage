"""
Testy jednostkowe dla src/data/loader.py.

Weryfikowane właściwości:
- liczba węzłów i krawędzi zgodna z tabelą 2 z artykułu DLG-DG-23
- poprawne typy węzłów i krawędzi
- graf jest skierowany
- brak węzłów bez atrybutu asset_type
"""

import pytest
import networkx as nx
from src.data.loader import load_graph, load_all_graphs, graph_summary

# Tabela 2 z artykułu: (węzły, krawędzie)
EXPECTED = {
    "DLG1":  (298,    298),
    "DLG2":  (464,    467),
    "DLG3":  (603,    610),
    "DLG4":  (415,    414),
    "DLG5":  (1299,  1351),
    "DLG6":  (13840, 14325),
    "DLG7":  (574,    574),
    "DLG8":  (546,    548),
    "DLG9":  (756,    771),
    "DLG10": (5378,  5555),
    "DLG11": (2024,  2030),  # artykuł podaje 2032, JSON zawiera 2030 (drobna niespójność datasetu)
    "DLG12": (5645,  5802),
    "DLG13": (2157,  2211),
    "DLG14": (453,    452),
    "DLG15": (558,    563),  # artykuł podaje 564, JSON zawiera 563 (drobna niespójność datasetu)
    "DLG16": (5574,  5876),
    "DLG17": (651,    652),
    "DLG18": (17085, 17720),
}

VALID_NODE_TYPES = {"Data Table", "Data Job", "Data Field"}
VALID_EDGE_TYPES = {"DATA_FLOW", "PARENT_CHILD"}


class TestLoadGraph:
    def test_returns_digraph(self):
        G = load_graph("DLG1")
        assert isinstance(G, nx.DiGraph)

    def test_graph_name(self):
        G = load_graph("DLG1")
        assert G.graph["name"] == "DLG1"

    @pytest.mark.parametrize("dlg_id,expected", EXPECTED.items())
    def test_node_edge_counts(self, dlg_id, expected):
        expected_nodes, expected_edges = expected
        G = load_graph(dlg_id)
        assert G.number_of_nodes() == expected_nodes, (
            f"{dlg_id}: oczekiwano {expected_nodes} węzłów, "
            f"got {G.number_of_nodes()}"
        )
        assert G.number_of_edges() == expected_edges, (
            f"{dlg_id}: oczekiwano {expected_edges} krawędzi, "
            f"got {G.number_of_edges()}"
        )

    def test_node_types_valid(self):
        G = load_graph("DLG1")
        for node, data in G.nodes(data=True):
            assert "asset_type" in data, f"Węzeł {node} nie ma atrybutu asset_type"
            assert data["asset_type"] in VALID_NODE_TYPES, (
                f"Nieznany typ węzła: {data['asset_type']}"
            )

    def test_edge_types_valid(self):
        G = load_graph("DLG1")
        for u, v, data in G.edges(data=True):
            assert "relation_type" in data, f"Krawędź ({u},{v}) nie ma relation_type"
            assert data["relation_type"] in VALID_EDGE_TYPES, (
                f"Nieznany typ krawędzi: {data['relation_type']}"
            )

    def test_invalid_id_raises(self):
        with pytest.raises(FileNotFoundError):
            load_graph("DLG99")


class TestLoadAllGraphs:
    def test_returns_all_18(self):
        graphs = load_all_graphs()
        assert len(graphs) == 18

    def test_all_keys_present(self):
        graphs = load_all_graphs()
        for dlg_id in EXPECTED:
            assert dlg_id in graphs


class TestGraphSummary:
    def test_summary_keys(self):
        G = load_graph("DLG1")
        s = graph_summary(G)
        assert set(s.keys()) == {"name", "nodes", "edges", "node_types", "edge_types"}

    def test_summary_counts_match_graph(self):
        G = load_graph("DLG1")
        s = graph_summary(G)
        assert s["nodes"] == G.number_of_nodes()
        assert s["edges"] == G.number_of_edges()

    def test_node_type_counts_sum(self):
        G = load_graph("DLG1")
        s = graph_summary(G)
        assert sum(s["node_types"].values()) == G.number_of_nodes()

    def test_edge_type_counts_sum(self):
        G = load_graph("DLG1")
        s = graph_summary(G)
        assert sum(s["edge_types"].values()) == G.number_of_edges()
