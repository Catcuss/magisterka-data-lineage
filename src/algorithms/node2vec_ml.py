"""
Node2Vec + MLP dla predykcji krawędzi w grafach lineage.

Kategoria: zanurzenia sieciowe (network embeddings). Node2Vec NIE jest
grafową siecią neuronową (GNN) — uczy reprezentacji węzłów poprzez biased
random walks (rozszerzenie skip-gramu Word2Vec na grafy), bez mechanizmu
propagacji wiadomości (message passing) charakterystycznego dla GCN /
GraphSAGE / GAT. Klasyfikatorem nad embeddingami jest MLP, a nie warstwa
grafowa.

Podejście:
    1. Node2Vec uczy reprezentacje węzłów przez biased random walks na G_train.
    2. Dla każdej pary (u, v) embedding krawędzi = hadamard(emb_u, emb_v).
    3. MLP (sklearn) klasyfikuje pary jako krawędź / brak krawędzi.

Parametry Node2Vec dla grafów bipartytowych:
    p=1, q=0.5  — BFS-biased (szeroka eksploracja sąsiedztwa);
                   na grafach bipartytowych bez trójkątów DFS (q>1) jest mniej
                   skuteczny, ponieważ random walk szybko "utyka" w swoim typie węzła.

Wymaga: pip install node2vec

Literatura: Grover & Leskovec, "node2vec: Scalable Feature Learning for Networks",
            KDD 2016.
"""

import warnings

import numpy as np
from sklearn.neural_network import MLPClassifier
import networkx as nx

try:
    from node2vec import Node2Vec as _Node2Vec
    _NODE2VEC_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NODE2VEC_AVAILABLE = False


class Node2VecMLPClassifier:
    """
    Node2Vec + MLP dla link prediction w grafach lineage.

    Faza trenowania:
        - Node2Vec uczy embeddingi węzłów na G_train (random walks)
        - MLP trenowany na parach (pos_train + neg_train) z embedding krawędzi

    Embedding krawędzi (u, v):
        hadamard = emb_u ⊙ emb_v   (element-wise product, standard dla LP)

    Usage
    -----
    clf = Node2VecMLPClassifier()
    clf.fit(G_train, pos_train, neg_train)
    scores = clf.predict_proba(G_train, test_edges)
    """

    def __init__(
        self,
        dimensions: int = 64,
        walk_length: int = 20,
        num_walks: int = 100,
        p: float = 1.0,
        q: float = 0.5,
        workers: int = 1,
        seed: int = 42,
    ):
        """
        Parameters
        ----------
        dimensions : int
            Wymiar przestrzeni embeddingu.
        walk_length : int
            Długość jednego random walk.
        num_walks : int
            Liczba random walks startujących z każdego węzła.
        p : float
            Return parameter — prawdopodobieństwo powrotu do poprzedniego węzła.
            p=1 (neutral), p<1 (DFS-like), p>1 (BFS-like).
        q : float
            In-out parameter — eksploracja dalej vs bliżej.
            q=0.5 (BFS-biased, zalecane dla grafów bipartytowych).
        workers : int
            Wątki do trenowania gensim Word2Vec (1 = deterministyczny).
        seed : int
            Ziarno losowości.
        """
        if not _NODE2VEC_AVAILABLE:
            raise ImportError(
                "Wymagana biblioteka node2vec. "
                "Zainstaluj: pip install node2vec"
            )
        self.dimensions  = dimensions
        self.walk_length = walk_length
        self.num_walks   = num_walks
        self.p           = p
        self.q           = q
        self.workers     = workers
        self.seed        = seed

        self._embeddings = None  # dict: node → np.ndarray
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            max_iter=300,
            random_state=seed,
        )

    def fit(
        self,
        G_train: nx.DiGraph,
        pos_train: list[tuple],
        neg_train: list[tuple],
    ) -> "Node2VecMLPClassifier":
        """
        Trenuje Node2Vec na G_train, potem MLP na parach treningowych.
        """
        G_und = G_train.to_undirected()

        # --- Krok 1: Node2Vec embeddingi ---
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            n2v = _Node2Vec(
                G_und,
                dimensions=self.dimensions,
                walk_length=self.walk_length,
                num_walks=self.num_walks,
                p=self.p,
                q=self.q,
                workers=self.workers,
                seed=self.seed,
                quiet=True,
            )
            model = n2v.fit(window=5, min_count=1, sg=1)

        # Zapisz embeddingi jako słownik node → wektor
        self._embeddings = {
            node: model.wv[str(node)]
            for node in G_und.nodes()
            if str(node) in model.wv
        }

        # --- Krok 2: MLP na embedding krawędzi ---
        edges = pos_train + neg_train
        y = np.array([1] * len(pos_train) + [0] * len(neg_train))
        X = self._edge_features(edges)

        # Pomiń pary, dla których brakuje embeddingu
        mask = np.array([
            u in self._embeddings and v in self._embeddings
            for u, v in edges
        ])
        if mask.sum() < 2:
            raise ValueError(
                "Za mało węzłów z embeddingiem do trenowania MLP. "
                "Sprawdź czy G_train ma wystarczająco krawędzi dla Node2Vec."
            )

        self.mlp.fit(X[mask], y[mask])
        return self

    def predict_proba(
        self,
        G_train: nx.DiGraph,
        edges: list[tuple],
    ) -> np.ndarray:
        """
        Zwraca P(edge=1) dla każdej pary. Pary bez embeddingu dostają score 0.
        """
        if self._embeddings is None:
            raise RuntimeError("Wywołaj fit() przed predict_proba().")

        scores = np.zeros(len(edges))
        X = self._edge_features(edges)
        mask = np.array([
            u in self._embeddings and v in self._embeddings
            for u, v in edges
        ])
        if mask.sum() > 0:
            scores[mask] = self.mlp.predict_proba(X[mask])[:, 1]
        return scores

    # ------------------------------------------------------------------

    def _edge_features(self, edges: list[tuple]) -> np.ndarray:
        """Embedding krawędzi: hadamard(emb_u, emb_v)."""
        zero = np.zeros(self.dimensions)
        rows = [
            self._embeddings.get(u, zero) * self._embeddings.get(v, zero)
            for u, v in edges
        ]
        return np.array(rows, dtype=float)
