"""
Klasyfikatory ML dla predykcji krawędzi w grafach lineage.

Ponieważ ID węzłów w DLG-DG-23 są zanonimizowanymi UUID, nie można
użyć podobieństwa nazw (Jaro-Winkler). Zamiast tego używamy wyłącznie
cech topologicznych.

Cechy dla pary (u, v):
    Węzeł u:  asset_type (int), out_degree, in_degree
    Węzeł v:  asset_type (int), out_degree, in_degree
    Para:     liczba wspólnych sąsiadów, Jaccard, Adamic-Adar,
              czy istnieje ścieżka u→v, długość najkrótszej ścieżki

Dostępne modele
---------------
GraphMLClassifier       — Random Forest (sklearn), klasa bazowa modeli
RUSBoostGraphClassifier — RUSBoost (imbalanced-learn): AdaBoost +
                          Random Under-Sampling w każdej iteracji;
                          bezpośrednio porównywalny z [1] Boiński et al.
"""

import math
from collections import deque

import numpy as np
from sklearn.ensemble import RandomForestClassifier
import networkx as nx

try:
    from imblearn.ensemble import RUSBoostClassifier as _RUSBoost
    _IMBLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    _IMBLEARN_AVAILABLE = False

try:
    import lightgbm as lgb
    _LGBM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LGBM_AVAILABLE = False


_ASSET_TYPE_MAP = {"Data Table": 0, "Data Job": 1, "Data Field": 2}
_NO_PATH_VALUE = 999  # wartość długości ścieżki gdy brak połączenia


# ---------------------------------------------------------------------------
# Klasa bazowa — ekstrakcja cech wspólna dla wszystkich modeli ML
# ---------------------------------------------------------------------------

class _BaseGraphClassifier:
    """
    Klasa bazowa: ekstrakcja cech topologicznych i interfejs fit/predict_proba.

    Podklasy ustawiają self.model na dowolny estymator sklearn-compatible
    z metodami fit(X, y) i predict_proba(X).
    """

    model = None  # podklasy przypisują konkretny model

    def fit(
        self,
        G_train: nx.DiGraph,
        pos_train: list[tuple],
        neg_train: list[tuple],
    ) -> "_BaseGraphClassifier":
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
    # Ekstrakcja cech (identyczna dla wszystkich modeli)
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


# ---------------------------------------------------------------------------
# Konkretne modele
# ---------------------------------------------------------------------------

class GraphMLClassifier(_BaseGraphClassifier):
    """
    Random Forest dla link prediction w grafach lineage.

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

    def feature_importances(self) -> dict[str, float]:
        """Zwraca ważność cech po trenowaniu."""
        return dict(zip(self.feature_names(), self.model.feature_importances_))


class RUSBoostGraphClassifier(_BaseGraphClassifier):
    """
    RUSBoost dla link prediction w grafach lineage.

    RUSBoost = AdaBoost + Random Under-Sampling w każdej iteracji boosting.
    Zaprojektowany dla niezbalansowanych zbiorów danych.

    Bezpośrednio porównywalny z modelem z artykułu [1] Boiński et al. (ISD2025),
    który osiągnął F1=0.79 na syntetycznych grafach lineage.

    Wymaga: pip install imbalanced-learn

    Usage
    -----
    clf = RUSBoostGraphClassifier()
    clf.fit(G_train, pos_train, neg_train)
    scores = clf.predict_proba(G_train, test_edges)
    """

    def __init__(self, n_estimators: int = 100, learning_rate: float = 1.0, seed: int = 42):
        if not _IMBLEARN_AVAILABLE:
            raise ImportError(
                "Wymagana biblioteka imbalanced-learn. "
                "Zainstaluj: pip install imbalanced-learn"
            )
        self.model = _RUSBoost(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            random_state=seed,
        )


class LightGBMGraphClassifier(_BaseGraphClassifier):
    """
    LightGBM dla link prediction w grafach lineage.

    Gradient boosting na tych samych 11 cechach topologicznych co RF i RUSBoost.
    Zwykle szybszy i dokładniejszy niż RF na małych zbiorach danych.
    Wbudowana obsługa niezbalansowania przez class_weight="balanced".

    Wymaga: pip install lightgbm

    Usage
    -----
    clf = LightGBMGraphClassifier()
    clf.fit(G_train, pos_train, neg_train)
    scores = clf.predict_proba(G_train, test_edges)
    """

    def __init__(self, n_estimators: int = 200, learning_rate: float = 0.05, seed: int = 42):
        if not _LGBM_AVAILABLE:
            raise ImportError(
                "Wymagana biblioteka lightgbm. "
                "Zainstaluj: pip install lightgbm"
            )
        self.model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
            verbose=-1,
        )


# ---------------------------------------------------------------------------
# ETL-aware: cechy flow-position (7 dodatkowych cech)
# ---------------------------------------------------------------------------

def _multi_source_bfs(G: nx.DiGraph, sources: list) -> dict:
    """BFS z wielu źródeł. Zwraca minimalną odległość od zbioru sources."""
    depths: dict = {}
    queue: deque = deque()
    for s in sources:
        if s not in depths:
            depths[s] = 0
            queue.append(s)
    while queue:
        node = queue.popleft()
        for nb in G.successors(node):
            if nb not in depths:
                depths[nb] = depths[node] + 1
                queue.append(nb)
    return depths


def _compute_flow_metadata(G: nx.DiGraph) -> tuple[dict, dict, dict]:
    """
    Oblicza metadane pozycji ETL dla każdego węzła.

    Returns
    -------
    flow_depths : dict[node, int]
        Minimalna odległość od source table (in_df=0, out_df>0, Data Table).
        Węzły nieosiągalne → 999.
    flow_reaches : dict[node, int]
        Minimalna odległość do sink table (in_df>0, out_df=0, Data Table).
        Węzły nieosiągalne → 999.
    roles : dict[node, int]
        0=source, 1=intermediate, 2=sink, 3=isolated
        na podstawie stopni DATA_FLOW.
    """
    df_edges = [(u, v) for u, v, d in G.edges(data=True)
                if d.get("relation_type") == "DATA_FLOW"]

    in_df: dict  = {n: 0 for n in G.nodes()}
    out_df: dict = {n: 0 for n in G.nodes()}
    for u, v in df_edges:
        out_df[u] = out_df.get(u, 0) + 1
        in_df[v]  = in_df.get(v,  0) + 1

    roles: dict = {}
    for n in G.nodes():
        i, o = in_df.get(n, 0), out_df.get(n, 0)
        if   i > 0 and o > 0: roles[n] = 1   # intermediate
        elif i == 0 and o > 0: roles[n] = 0  # source
        elif i > 0 and o == 0: roles[n] = 2  # sink
        else:                  roles[n] = 3  # isolated

    G_flow = nx.DiGraph()
    G_flow.add_nodes_from(G.nodes())
    G_flow.add_edges_from(df_edges)

    sources = [n for n in G.nodes()
               if roles[n] == 0
               and G.nodes[n].get("asset_type") == "Data Table"]
    sinks   = [n for n in G.nodes()
               if roles[n] == 2
               and G.nodes[n].get("asset_type") == "Data Table"]

    flow_depths  = _multi_source_bfs(G_flow, sources)
    flow_reaches = _multi_source_bfs(G_flow.reverse(), sinks)

    return flow_depths, flow_reaches, roles


class _ETLAwareMixin:
    """
    Mixin rozszerzający wektor cech o 7 cech ETL-aware (flow-position).

    Nadpisuje _extract_features: oblicza flow_depths/flow_reaches/roles
    raz per graf, potem dokłada do każdej pary 7 nowych cech:
        flow_depth_u, flow_depth_v  — odległość od source table
        flow_reach_u, flow_reach_v  — odległość do sink table
        role_u, role_v              — rola ETL (0-3)
        depth_gap                   — |flow_depth_u - flow_depth_v|
    """

    def _extract_features(
        self,
        G: nx.DiGraph,
        edges: list[tuple],
    ) -> np.ndarray:
        flow_depths, flow_reaches, roles = _compute_flow_metadata(G)
        G_und = G.to_undirected()
        rows = []
        for u, v in edges:
            base = self._edge_features(G, G_und, u, v)
            fd_u = float(flow_depths.get(u, 999))
            fd_v = float(flow_depths.get(v, 999))
            fr_u = float(flow_reaches.get(u, 999))
            fr_v = float(flow_reaches.get(v, 999))
            r_u  = float(roles.get(u, 3))
            r_v  = float(roles.get(v, 3))
            depth_gap = float(abs(fd_u - fd_v))
            rows.append(base + [fd_u, fd_v, fr_u, fr_v, r_u, r_v, depth_gap])
        return np.array(rows, dtype=float)

    def feature_names(self) -> list[str]:
        return super().feature_names() + [
            "flow_depth_u", "flow_depth_v",
            "flow_reach_u", "flow_reach_v",
            "role_u", "role_v",
            "depth_gap",
        ]


class ETLAwareGraphMLClassifier(_ETLAwareMixin, GraphMLClassifier):
    """
    Random Forest z 18 cechami (11 topologicznych + 7 ETL-aware).

    Wariant eksperymentalny do porównania z RF-11 (GraphMLClassifier).
    Hipoteza: pozycja węzła w potoku ETL (flow_depth, role) poprawia AUC-ROC.
    """


class ETLAwareRUSBoostClassifier(_ETLAwareMixin, RUSBoostGraphClassifier):
    """
    RUSBoost z 18 cechami (11 topologicznych + 7 ETL-aware).

    Wariant eksperymentalny do porównania z RUSBoost-11 (RUSBoostGraphClassifier).
    """
