"""
Testy jednostkowe dla src/data/scenario_splitter.py.

Weryfikowane właściwości:
- pos_test odpowiada definicji scenariusza (intermediate/source/sink)
- pos_val jest losowane z pozostałych krawędzi, nie ze scenariuszowych
- G_train nie zawiera krawędzi test ANI val (brak wycieku)
- powtarzalność przy tym samym seed
- kompatybilność wsteczna: val_ratio=0.0 zwraca puste pos_val/neg_val
"""

import pytest

from src.data.loader import load_graph
from src.data.scenario_splitter import scenario_split, classify_table_roles


@pytest.fixture(scope="module")
def G5():
    return load_graph("DLG5")


class TestBackwardCompatibility:
    def test_val_empty_when_zero(self, G5):
        splits = scenario_split(G5, scenario="A", val_ratio=0.0, seed=42)
        assert splits["pos_val"] == []
        assert splits["neg_val"] == []


class TestNoDataLeakage:
    def test_test_edges_absent_from_G_train(self, G5):
        splits = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        for u, v in splits["pos_test"]:
            assert not splits["G_train"].has_edge(u, v), \
                f"Krawędź testowa ({u},{v}) znaleziona w G_train"

    def test_val_edges_absent_from_G_train(self, G5):
        splits = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        for u, v in splits["pos_val"]:
            assert not splits["G_train"].has_edge(u, v), \
                f"Krawędź walidacyjna ({u},{v}) znaleziona w G_train"

    def test_no_overlap_train_val_test(self, G5):
        splits = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        train = set(splits["pos_train"])
        val   = set(splits["pos_val"])
        test  = set(splits["pos_test"])
        assert train.isdisjoint(val)
        assert train.isdisjoint(test)
        assert val.isdisjoint(test)


class TestScenarioSemantics:
    def test_scenario_A_test_edges_are_intermediate_out(self, G5):
        """Scenariusz A: krawędzie testowe to wyjścia z intermediate Tables."""
        splits = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        intermediate = set(classify_table_roles(G5)["intermediate"])
        for u, v in splits["pos_test"]:
            assert u in intermediate, f"Krawędź testowa ({u},{v}) nie z intermediate"
            assert G5.nodes[v]["asset_type"] == "Data Job"

    def test_val_not_taken_from_scenario_edges(self, G5):
        """pos_val musi być losowane spoza pos_test — krawędzie scenariusza
        powinny zostać w teście, by zbiór testowy zachowywał intencję."""
        splits = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        test_set = set(splits["pos_test"])
        for edge in splits["pos_val"]:
            assert edge not in test_set


class TestReproducibility:
    def test_same_seed_same_split(self, G5):
        s1 = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        s2 = scenario_split(G5, scenario="A", val_ratio=0.2, seed=42)
        assert s1["pos_test"] == s2["pos_test"]
        assert s1["pos_val"]  == s2["pos_val"]


class TestValidation:
    def test_negative_val_ratio_raises(self, G5):
        with pytest.raises(ValueError, match="val_ratio"):
            scenario_split(G5, scenario="A", val_ratio=-0.1)

    def test_val_ratio_one_raises(self, G5):
        with pytest.raises(ValueError, match="val_ratio"):
            scenario_split(G5, scenario="A", val_ratio=1.0)
