"""
Testy jednostkowe dla src/detection/node_features.py.

Weryfikowane właściwości:
- macierz cech ma poprawny kształt,
- flagi is_root / is_leaf liczone poprawnie,
- in_df / out_df zgodne ze strukturą DATA_FLOW,
- brak wartości NaN/inf,
- integracja z metrykami detekcji.
"""

import numpy as np
import networkx as nx

from src.data.loader import load_graph
from src.detection.node_features import extract_node_features, feature_names
from src.detection.node_metrics import node_detection_metrics


def _toy_graph() -> nx.DiGraph:
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


def test_feature_matrix_shape():
    G = _toy_graph()
    nodes = ["T1", "T2", "T3"]
    X = extract_node_features(G, nodes)
    assert X.shape == (3, len(feature_names()))


def test_is_root_is_leaf():
    G = _toy_graph()
    X = extract_node_features(G, ["T1", "T2", "T3"])
    names = feature_names()
    i_root, i_leaf = names.index("is_root"), names.index("is_leaf")
    i_in, i_out = names.index("in_df"), names.index("out_df")
    # T1: source (in=0, out=1)
    assert X[0, i_root] == 1.0 and X[0, i_leaf] == 0.0
    assert X[0, i_in] == 0.0 and X[0, i_out] == 1.0
    # T2: pośrednia (in=1, out=1)
    assert X[1, i_root] == 0.0 and X[1, i_leaf] == 0.0
    # T3: sink (in=1, out=0)
    assert X[2, i_root] == 0.0 and X[2, i_leaf] == 1.0


def test_no_nan_or_inf():
    G = load_graph("DLG5")
    nodes = [n for n, d in G.nodes(data=True)
             if d.get("asset_type") == "Data Table"][:50]
    X = extract_node_features(G, nodes)
    assert np.isfinite(X).all()


def test_metrics_integration():
    y = np.array([1, 0, 1, 0, 0])
    scores = np.array([0.9, 0.1, 0.8, 0.2, 0.05])
    m = node_detection_metrics(y, scores)
    assert m["n_pos"] == 2
    assert 0.0 <= m["auc_roc"] <= 1.0
    assert 0.0 <= m["precision_at_k"] <= 1.0
    assert m["hits_at_k"] == 1.0  # oba pozytywy w top-2
