"""
Testy jednostkowe dla src/detection/job_removal.py.

Weryfikowane właściwości:
- usunięte joby nie występują w G_obs,
- zbiór infected = tabele incydentne do usuniętych jobów,
- etykiety zgodne z listą kandydatów (1 = infected),
- kandydaci to wyłącznie tabele,
- powtarzalność przy tym samym seed,
- wariant side="pred"/"succ",
- błąd przy braku jobów łączących.
"""

import pytest
import networkx as nx

from src.data.loader import load_graph
from src.detection.job_removal import (
    build_node_dataset, list_connecting_jobs, incident_tables, inductive_split,
)


def _toy_graph() -> nx.DiGraph:
    """T1 -> J1 -> T2 -> J2 -> T3 (dwa joby łączące)."""
    G = nx.DiGraph(name="TOY")
    for t in ["T1", "T2", "T3"]:
        G.add_node(t, asset_type="Data Table")
    for j in ["J1", "J2"]:
        G.add_node(j, asset_type="Data Job")
    df = "DATA_FLOW"
    G.add_edge("T1", "J1", relation_type=df)
    G.add_edge("J1", "T2", relation_type=df)
    G.add_edge("T2", "J2", relation_type=df)
    G.add_edge("J2", "T3", relation_type=df)
    return G


@pytest.fixture(scope="module")
def G5():
    return load_graph("DLG5")


class TestToyGraph:
    def test_connecting_jobs(self):
        assert set(list_connecting_jobs(_toy_graph())) == {"J1", "J2"}

    def test_incident_tables_both(self):
        G = _toy_graph()
        assert incident_tables(G, "J1", side="both") == {"T1", "T2"}
        assert incident_tables(G, "J2", side="both") == {"T2", "T3"}

    def test_incident_tables_sides(self):
        G = _toy_graph()
        assert incident_tables(G, "J1", side="pred") == {"T1"}
        assert incident_tables(G, "J1", side="succ") == {"T2"}

    def test_dataset_removes_one_job(self):
        ds = build_node_dataset(_toy_graph(), removal_ratio=0.2, seed=1)
        assert len(ds["removed_jobs"]) == 1
        rj = ds["removed_jobs"][0]
        assert not ds["G_obs"].has_node(rj)

    def test_labels_match_infected(self):
        ds = build_node_dataset(_toy_graph(), removal_ratio=0.2, seed=1)
        assert sum(ds["labels"]) == len(ds["infected"])
        for node, lab in zip(ds["candidates"], ds["labels"]):
            assert (lab == 1) == (node in ds["infected"])

    def test_candidates_are_tables(self):
        ds = build_node_dataset(_toy_graph(), removal_ratio=0.2, seed=1)
        for n in ds["candidates"]:
            assert ds["G_obs"].nodes[n]["asset_type"] == "Data Table"

    def test_no_connecting_jobs_raises(self):
        G = nx.DiGraph()
        G.add_node("T1", asset_type="Data Table")
        G.add_node("J1", asset_type="Data Job")
        G.add_edge("T1", "J1", relation_type="DATA_FLOW")  # job tylko z wejściem
        with pytest.raises(ValueError, match="job"):
            build_node_dataset(G, removal_ratio=0.5)


class TestRealGraph:
    def test_dataset_structure(self, G5):
        ds = build_node_dataset(G5, removal_ratio=0.2, seed=42)
        assert len(ds["candidates"]) == len(ds["labels"])
        assert ds["n_infected"] == sum(ds["labels"])
        for rj in ds["removed_jobs"]:
            assert not ds["G_obs"].has_node(rj)

    def test_reproducibility(self, G5):
        a = build_node_dataset(G5, removal_ratio=0.2, seed=42)
        b = build_node_dataset(G5, removal_ratio=0.2, seed=42)
        assert a["removed_jobs"] == b["removed_jobs"]
        assert a["labels"] == b["labels"]

    def test_different_seed_differs(self, G5):
        a = build_node_dataset(G5, removal_ratio=0.2, seed=1)
        b = build_node_dataset(G5, removal_ratio=0.2, seed=2)
        assert a["removed_jobs"] != b["removed_jobs"]


class TestInductiveSplit:
    def test_disjoint(self):
        train, test = inductive_split(["DLG1", "DLG2", "DLG3"], ["DLG2"])
        assert set(train).isdisjoint(test)
        assert test == ["DLG2"]
        assert set(train) == {"DLG1", "DLG3"}
