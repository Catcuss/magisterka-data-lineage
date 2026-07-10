"""
Testy jednostkowe dla src/detection/completeness.py.

Kluczowa własność: chora tabela (korzeń, którego peerzy MAJĄ producentów) dostaje
wysoki score anomalii, a prawdziwe źródło (wśród innych źródeł) — niski.
"""

import numpy as np
import networkx as nx

from src.detection.completeness import (
    completeness_features, feature_names, anomaly_score, completeness_scores,
)


def _toy_graph() -> nx.DiGraph:
    """
    Klaster źródłowy:  S1, S2 -> J -> T          (S1, S2 to prawdziwe źródła)
    Klaster chory:     B -> J1,  Q -> J1          (B: korzeń bez producenta)
                       Pq -> Jq -> Q              (Q MA producenta)
    """
    G = nx.DiGraph()
    for t in ["S1", "S2", "T", "B", "Q", "Pq"]:
        G.add_node(t, asset_type="Data Table")
    for j in ["J", "J1", "Jq"]:
        G.add_node(j, asset_type="Data Job")
    df = "DATA_FLOW"
    for u, v in [("S1", "J"), ("S2", "J"), ("J", "T"),
                 ("B", "J1"), ("Q", "J1"),
                 ("Pq", "Jq"), ("Jq", "Q")]:
        G.add_edge(u, v, relation_type=df)
    return G


def test_broken_root_high_genuine_source_low():
    G = _toy_graph()
    sc = completeness_scores(G)
    # B to korzeń, którego peer (Q) ma producenta → anomalia wysoka.
    assert sc["B"][2] == 1.0
    # S1 to korzeń wśród innych korzeni (S2 bez producenta) → anomalia zerowa.
    assert sc["S1"][2] == 0.0


def test_anomaly_score_ranks_broken_above_source():
    G = _toy_graph()
    nodes = ["B", "S1", "S2"]
    s = anomaly_score(G, nodes)
    assert s[0] > s[1] and s[0] > s[2]


def test_feature_matrix_shape_and_finite():
    G = _toy_graph()
    nodes = ["S1", "S2", "T", "B", "Q", "Pq"]
    X = completeness_features(G, nodes)
    assert X.shape == (6, len(feature_names()))
    assert np.isfinite(X).all()
    assert (X >= 0).all() and (X <= 1).all()
