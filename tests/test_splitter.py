"""
Testy jednostkowe dla src/data/splitter.py.

Weryfikowane właściwości:
- brak wycieku danych (krawędzie testowe nie ma w G_train)
- brak fałszywych negatywów (negatywne próbki nie istnieją w oryginalnym G)
- poprawne proporcje zbiorów
- respektowanie typów węzłów w negatywnych próbkach
- powtarzalność przy tym samym seed
- obsługa błędów
"""

import pytest
import networkx as nx
from src.data.loader import load_graph
from src.data.splitter import split_edges, split_summary


@pytest.fixture(scope="module")
def G1():
    return load_graph("DLG1")


@pytest.fixture(scope="module")
def G5():
    return load_graph("DLG5")


class TestNoDataLeakage:
    def test_test_edges_absent_from_G_train(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.1)
        for u, v in splits["pos_test"]:
            assert not splits["G_train"].has_edge(u, v), \
                f"Krawędź testowa ({u},{v}) znaleziona w G_train"

    def test_val_edges_absent_from_G_train(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.1)
        for u, v in splits["pos_val"]:
            assert not splits["G_train"].has_edge(u, v), \
                f"Krawędź walidacyjna ({u},{v}) znaleziona w G_train"

    def test_no_false_negatives(self, G5):
        splits = split_edges(G5, test_ratio=0.2, neg_ratio=1.0)
        for u, v in splits["neg_test"]:
            assert not G5.has_edge(u, v), \
                f"Negatywna próbka ({u},{v}) istnieje w oryginalnym grafie"


class TestSetSizes:
    def test_test_size(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.0)
        n_df = sum(1 for _, _, d in G5.edges(data=True)
                   if d["relation_type"] == "DATA_FLOW")
        expected = max(1, round(n_df * 0.2))
        assert len(splits["pos_test"]) == expected

    def test_val_empty_when_zero(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.0)
        assert splits["pos_val"] == []
        assert splits["neg_val"] == []

    def test_val_size(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.1)
        n_df = sum(1 for _, _, d in G5.edges(data=True)
                   if d["relation_type"] == "DATA_FLOW")
        expected_val = max(0, round(n_df * 0.1))
        assert len(splits["pos_val"]) == expected_val

    def test_neg_ratio(self, G5):
        splits = split_edges(G5, test_ratio=0.2, neg_ratio=2.0)
        assert len(splits["neg_test"]) == round(len(splits["pos_test"]) * 2.0)

    def test_partition_is_complete(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.1)
        total = len(splits["pos_train"]) + len(splits["pos_val"]) + len(splits["pos_test"])
        n_df = sum(1 for _, _, d in G5.edges(data=True)
                   if d["relation_type"] == "DATA_FLOW")
        assert total == n_df


class TestNodeTypeConstraints:
    def test_neg_samples_respect_type_pairs(self, G5):
        valid_pairs = {("Data Table", "Data Job"), ("Data Job", "Data Table")}
        splits = split_edges(G5, edge_type="DATA_FLOW", test_ratio=0.2, neg_ratio=1.0)
        for u, v in splits["neg_test"]:
            pair = (G5.nodes[u]["asset_type"], G5.nodes[v]["asset_type"])
            assert pair in valid_pairs, \
                f"Negatywna próbka ({u},{v}) ma nieprawidłowe typy: {pair}"

    def test_parent_child_type_pairs(self):
        G = load_graph("DLG5")
        splits = split_edges(G, edge_type="PARENT_CHILD", test_ratio=0.1, neg_ratio=1.0)
        for u, v in splits["neg_test"]:
            assert G.nodes[u]["asset_type"] == "Data Table"
            assert G.nodes[v]["asset_type"] == "Data Field"


class TestReproducibility:
    def test_same_seed_same_result(self, G5):
        s1 = split_edges(G5, test_ratio=0.2, seed=42)
        s2 = split_edges(G5, test_ratio=0.2, seed=42)
        assert s1["pos_test"] == s2["pos_test"]
        assert s1["neg_test"] == s2["neg_test"]

    def test_different_seed_different_result(self, G5):
        s1 = split_edges(G5, test_ratio=0.2, seed=42)
        s2 = split_edges(G5, test_ratio=0.2, seed=99)
        assert s1["pos_test"] != s2["pos_test"]


class TestEdgeCases:
    def test_G_train_is_copy(self, G5):
        splits = split_edges(G5, test_ratio=0.2)
        splits["G_train"].add_node("__test__")
        assert "__test__" not in G5.nodes

    def test_unknown_edge_type_raises(self, G5):
        with pytest.raises(ValueError, match="Nieznany edge_type"):
            split_edges(G5, edge_type="NIEZNANY")

    def test_ratio_overflow_raises(self, G5):
        with pytest.raises(ValueError):
            split_edges(G5, test_ratio=0.6, val_ratio=0.5)


class TestSplitSummary:
    def test_summary_keys(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.1)
        s = split_summary(splits)
        assert set(s.keys()) == {
            "G_train_edges", "pos_train", "neg_train",
            "pos_val", "neg_val", "pos_test", "neg_test"
        }

    def test_summary_counts_match(self, G5):
        splits = split_edges(G5, test_ratio=0.2, val_ratio=0.1)
        s = split_summary(splits)
        assert s["pos_test"] == len(splits["pos_test"])
        assert s["G_train_edges"] == splits["G_train"].number_of_edges()
