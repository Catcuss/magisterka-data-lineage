"""
Klasyfikator ML dla predykcji krawędzi w grafach lineage.

Model: Random Forest trenowany na cechach strukturalnych grafu.
Ponieważ ID węzłów w DLG-DG-23 są zanonimizowanymi UUID, nie można
użyć podobieństwa nazw (Jaro-Winkler). Zamiast tego używamy wyłącznie
cech topologicznych.

Cechy dla pary (u, v):
    Węzeł u:  asset_type (int), out_degree, in_degree
    Węzeł v:  asset_type (int), out_degree, in_degree
    Para:     liczba wspólnych sąsiadów, Jaccard, Adamic-Adar,
              czy istnieje ścieżka u→v, długość najkrótszej ścieżki
"""

import math
from collections import defaultdict

import numpy as np
from sklearn.ensemble import RandomForestClassifier

import networkx as nx


_ASSET_TYPE_MAP = {"Data Table": 0, "Data Job": 1, "Data Field": 2}
_NO_PATH_VALUE = 999  # wartość długości ścieżki gdy brak połączenia


class GraphMLClassifier:
    """
    Klasyfikator Random Forest dla link prediction w grafach.

    Usage
    -----
    clf = GraphMLClassifier()
    clf.fit(G_train, pos_train, neg_train)
    scores = clf.predict_proba(G_train, test_edges)   # zwraca P(edge=1)
    """

    def __init__(self, n_estimators: int = 100, seed: int = 42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
        )
        self._G_undirected = None

    def fit(
        self,
        G_train: nx.DiGraph,
        pos_train: list[tuple],
        neg_train: list[tuple],
    ) -> "GraphMLClassifier":
        """
        Trenuje klasyfikator na krawędziach treningowych.

        Parameters
        ----------
        G_train : nx.DiGraph
            Graf treningowy (bez krawędzi testowych).
        pos_train : list of (u, v)
            Pozytywne próbki treningowe (istniejące krawędzie).
        neg_train : list of (u, v)
            Negatywne próbki treningowe (nieistniejące krawędzie).
        """
        self._G_undirected = G_train.to_undirected()

        edges = pos_train + neg_train
        y = np.array([1] * len(pos_train) + [0] * len(neg_train))

        X = self._extract_features(G_train, edges)
        self.model.fit(X, y)
        return self

    def predict_proba(
        self,
        G_train: nx.DiGraph,
        edges: list[tuple],
    ) -> np.ndarray:
        """
        Zwraca prawdopodobieństwo istnienia krawędzi P(edge=1) dla każdej pary.

        Parameters
        ----------
        G_train : nx.DiGraph
            Ten sam graf treningowy co podczas fit().
        edges : list of (u, v)
            Pary węzłów do oceny.

        Returns
        -------
        np.ndarray, shape (len(edges),)
        """
        if self._G_undirected is None:
            raise RuntimeError("Wywołaj fit() przed predict_proba().")
        X = self._extract_features(G_train, edges)
        return self.model.predict_proba(X)[:, 1]

    def feature_names(self) -> list[str]:
        return [
            "src_type", "src_out_deg", "src_in_deg",
            "tgt_type", "tgt_out_deg", "tgt_in_deg",
            "common_neighbors", "jaccard", "adamic_adar",
            "has_path", "shortest_path",
        ]

    # ------------------------------------------------------------------
    # Ekstrakcja cech
    # ------------------------------------------------------------------

    def _extract_features(
        self,
        G: nx.DiGraph,
        edges: list[tuple],
    ) -> np.ndarray:
        G_und = G.to_undirected()
        rows = [self._edge_features(G, G_und, u, v) for u, v in edges]
        return np.array(rows, dtype=float)

    def _edge_features(
        self,
        G: nx.DiGraph,
        G_und: nx.Graph,
        u,
        v,
    ) -> list[float]:
        # Cechy węzła źródłowego
        u_data = G.nodes.get(u, {})
        src_type = _ASSET_TYPE_MAP.get(u_data.get("asset_type", ""), -1)
        src_out = G.out_degree(u) if G.has_node(u) else 0
        src_in = G.in_degree(u) if G.has_node(u) else 0

        # Cechy węzła docelowego
        v_data = G.nodes.get(v, {})
        tgt_type = _ASSET_TYPE_MAP.get(v_data.get("asset_type", ""), -1)
        tgt_out = G.out_degree(v) if G.has_node(v) else 0
        tgt_in = G.in_degree(v) if G.has_node(v) else 0

        # Cechy pary (na podstawie grafu nieskierowanego)
        nu = set(G_und.neighbors(u)) - {u} if G_und.has_node(u) else set()
        nv = set(G_und.neighbors(v)) - {v} if G_und.has_node(v) else set()
        common = nu & nv
        union = nu | nv

        cn = float(len(common))
        jaccard = len(common) / len(union) if union else 0.0
        aa = sum(
            1.0 / math.log(G_und.degree(w))
            for w in common
            if G_und.degree(w) > 1
        )

        # Ścieżka w grafie nieskierowanym
        try:
            path_len = nx.shortest_path_length(G_und, u, v)
            has_path = 1.0
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path_len = _NO_PATH_VALUE
            has_path = 0.0

        return [
            src_type, src_out, src_in,
            tgt_type, tgt_out, tgt_in,
            cn, jaccard, aa,
            has_path, float(path_len),
        ]
