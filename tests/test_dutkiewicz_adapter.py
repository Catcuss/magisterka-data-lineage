"""
Testy adaptera zewnętrznego grafu Dutkiewicza (src/data/dutkiewicz_adapter.py).

Sprawdzają, że graf zbudowany z DataLineage.csv jest zgodny z konwencją
loadera DLG-DG-23 (asset_type/relation_type) i nadaje się do symulacji
broken lineage tym samym kodem (job_removal), co grafy DLG.
"""

import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data.dutkiewicz_adapter import build_dutkiewicz_graph, summary
from detection.job_removal import build_node_dataset, list_connecting_jobs
from detection.node_features import extract_node_features, feature_names


def _tmp_lineage(tmp_path: Path) -> Path:
    """Minimalny DataLineage.csv: A,B -> vw -> Final (łańcuch z rozgałęzieniem)."""
    p = tmp_path / "DataLineage.csv"
    p.write_text(
        "SourceName;SourcePKName;SourceID;TargetName;TargetPKName;TargetID\n"
        "<class 'str'>;<class 'str'>;<class 'str'>;<class 'str'>;<class 'str'>;<class 'str'>\n"
        "A;AID;1;vw;VID;1\n"
        "B;BID;2;vw;VID;1\n"
        "vw;VID;1;Final;FID;1\n",
        encoding="utf-8",
    )
    return p


def test_graph_conventions(tmp_path):
    """Węzły i krawędzie mają dozwolone typy asset_type/relation_type."""
    G = build_dutkiewicz_graph([_tmp_lineage(tmp_path)], name="T")
    assert isinstance(G, nx.DiGraph)
    assert {d["asset_type"] for _, d in G.nodes(data=True)} <= {
        "Data Table", "Data Job", "Data Field"}
    assert {d["relation_type"] for _, _, d in G.edges(data=True)} <= {
        "DATA_FLOW", "PARENT_CHILD"}


def test_table_job_table_structure(tmp_path):
    """Dla targetu 'vw' powstaje zadanie karmione przez A i B, produkujące vw."""
    G = build_dutkiewicz_graph([_tmp_lineage(tmp_path)], name="T")
    tables = {n for n, d in G.nodes(data=True) if d["asset_type"] == "Data Table"}
    jobs = {n for n, d in G.nodes(data=True) if d["asset_type"] == "Data Job"}
    assert {"A", "B", "vw", "Final"} <= tables
    # 2 targety (vw, Final) => 2 zadania.
    assert len(jobs) == 2
    job_vw = "job::vw"
    assert G.has_edge("A", job_vw) and G.has_edge("B", job_vw)
    assert G.has_edge(job_vw, "vw")


def test_all_jobs_are_connecting(tmp_path):
    """Każde zadanie ma wejście i wyjście => jest jobem łączącym (usuwalnym)."""
    G = build_dutkiewicz_graph([_tmp_lineage(tmp_path)], name="T")
    jobs = {n for n, d in G.nodes(data=True) if d["asset_type"] == "Data Job"}
    assert set(list_connecting_jobs(G)) == jobs


def test_job_removal_marks_infected(tmp_path):
    """Symulacja broken lineage oznacza tabele incydentne do usuniętego zadania."""
    G = build_dutkiewicz_graph([_tmp_lineage(tmp_path)], name="T")
    ds = build_node_dataset(G, removal_ratio=1.0, seed=0, side="both")
    assert ds["n_infected"] >= 1
    assert len(ds["candidates"]) == len(ds["labels"])


def test_features_extractable(tmp_path):
    """Cechy topologiczne liczą się na grafie adaptera (zgodność z pipeline)."""
    G = build_dutkiewicz_graph([_tmp_lineage(tmp_path)], name="T")
    tables = [n for n, d in G.nodes(data=True) if d["asset_type"] == "Data Table"]
    X = extract_node_features(G, tables)
    assert X.shape == (len(tables), len(feature_names()))


def test_real_data_if_present():
    """Jeśli dane źródłowe są w repo — graf ma sensowną skalę i jest DAG-iem przepływu."""
    default_dir = Path(__file__).resolve().parents[1] / "data" / "external" / "dutkiewicz"
    if not (default_dir / "train_DataLineage.csv").exists():
        pytest.skip("Brak danych zewnętrznych Dutkiewicza (opcjonalne).")
    G = build_dutkiewicz_graph()
    s = summary(G)
    assert s["node_types"].get("Data Table", 0) >= 10
    assert s["node_types"].get("Data Job", 0) >= 5
    assert len(list_connecting_jobs(G)) >= 5
