"""
Heurystyczne algorytmy predykcji krawędzi (link prediction).

Wszystkie metody operują na nieskierowanej wersji grafu treningowego.

Metody klasyczne (wymagają wspólnych sąsiadów):
    - Common Neighbors (CN)  — liczba wspólnych sąsiadów
    - Jaccard Coefficient    — CN / |N(u) ∪ N(v)|
    - Adamic-Adar            — Σ 1/log(deg(w)) dla wspólnych sąsiadów w

Uwaga: DATA_FLOW w DLG-DG-23 tworzy graf bipartytowy (Table↔Job).
Dla par (Table, Job) sąsiedztwa N(u) i N(v) są zawsze rozłączne
(N(Table) = {Jobs+Fields}, N(Job) = {Tables}), więc CN/Jaccard/AA = 0.
Poniższe metody działają poprawnie na grafach bipartytowych:

    - Preferential Attachment (PA) — deg(u) × deg(v), nie wymaga wspólnych sąsiadów
    - L3 (ścieżki długości 3)      — liczba ścieżek Table→Job→Table→Job
                                     odpowiednik CN na rzucie bipartytowym
"""

import math
import networkx as nx
import numpy as np


ALL_METHODS = [
    "common_neighbors",
    "jaccard",
    "adamic_adar",
    "preferential_attachment",
    "l3",
]


def score_edges(
    G_train: nx.DiGraph,
    edges: list[tuple],
    method: str = "preferential_attachment",
) -> np.ndarray:
    """
    Oblicza heurystyczny score dla listy par węzłów.

    Parameters
    ----------
    G_train : nx.DiGraph
        Graf treningowy (z usuniętymi krawędziami testowymi).
    edges : list of (u, v)
        Pary węzłów do oceny.
    method : str
        Jedna z: "common_neighbors", "jaccard", "adamic_adar",
                 "preferential_attachment", "l3"

    Returns
    -------
    np.ndarray, shape (len(edges),)
        Score dla każdej pary — wyższy = bardziej prawdopodobna krawędź.
    """
    _METHODS = {
        "common_neighbors":      _common_neighbors,
        "jaccard":               _jaccard,
        "adamic_adar":           _adamic_adar,
        "preferential_attachment": _preferential_attachment,
        "l3":                    _l3,
    }
    if method not in _METHODS:
        raise ValueError(
            f"Nieznana metoda: '{method}'. Dozwolone: {list(_METHODS.keys())}"
        )

    G_undirected = G_train.to_undirected()
    scorer = _METHODS[method]
    return np.array([scorer(G_undirected, u, v) for u, v in edges])


def score_all_methods(
    G_train: nx.DiGraph,
    edges: list[tuple],
) -> dict[str, np.ndarray]:
    """
    Oblicza scores dla wszystkich pięciu heurystyk naraz.

    Returns
    -------
    dict {method_name: np.ndarray}
    """
    G_und = G_train.to_undirected()
    return {
        "common_neighbors":        np.array([_common_neighbors(G_und, u, v)        for u, v in edges]),
        "jaccard":                 np.array([_jaccard(G_und, u, v)                 for u, v in edges]),
        "adamic_adar":             np.array([_adamic_adar(G_und, u, v)             for u, v in edges]),
        "preferential_attachment": np.array([_preferential_attachment(G_und, u, v) for u, v in edges]),
        "l3":                      np.array([_l3(G_und, u, v)                      for u, v in edges]),
    }


# ---------------------------------------------------------------------------
# Implementacje poszczególnych heurystyk
# ---------------------------------------------------------------------------

def _neighbors(G: nx.Graph, node) -> set:
    """Zbiór sąsiadów węzła (z wykluczeniem samego siebie)."""
    return set(G.neighbors(node)) - {node}


def _common_neighbors(G: nx.Graph, u, v) -> float:
    """Liczba wspólnych sąsiadów."""
    if not (G.has_node(u) and G.has_node(v)):
        return 0.0
    return float(len(_neighbors(G, u) & _neighbors(G, v)))


def _jaccard(G: nx.Graph, u, v) -> float:
    """Jaccard Coefficient: |N(u) ∩ N(v)| / |N(u) ∪ N(v)|."""
    if not (G.has_node(u) and G.has_node(v)):
        return 0.0
    nu, nv = _neighbors(G, u), _neighbors(G, v)
    union = nu | nv
    if not union:
        return 0.0
    return len(nu & nv) / len(union)


def _adamic_adar(G: nx.Graph, u, v) -> float:
    """Adamic-Adar: Σ 1/log(deg(w)) dla w ∈ N(u) ∩ N(v)."""
    if not (G.has_node(u) and G.has_node(v)):
        return 0.0
    common = _neighbors(G, u) & _neighbors(G, v)
    score = 0.0
    for w in common:
        deg = G.degree(w)
        if deg > 1:
            score += 1.0 / math.log(deg)
    return score


def _preferential_attachment(G: nx.Graph, u, v) -> float:
    """
    Preferential Attachment: deg(u) × deg(v).

    Nie wymaga wspólnych sąsiadów — działa poprawnie na grafach bipartytowych.
    Założenie: węzły o wyższym stopniu mają wyższe prawdopodobieństwo nowych połączeń.
    """
    if not (G.has_node(u) and G.has_node(v)):
        return 0.0
    return float(G.degree(u) * G.degree(v))


def _l3(G: nx.Graph, u, v) -> float:
    """
    L3 — liczba ścieżek długości 3 między u i v.

    Odpowiednik Common Neighbors na rzucie bipartytowym.
    Dla pary (Table, Job): liczy ścieżki Table→Job'→Table'→Job,
    czyli ile "alternatywnych tras" łączy u z v przez dwa węzły pośrednie.

    Złożoność: O(deg(u) × max_deg²) — może być kosztowna na dużych grafach.
    """
    if not (G.has_node(u) and G.has_node(v)):
        return 0.0
    count = 0
    for w in _neighbors(G, u):           # u → w (hop 1)
        for x in _neighbors(G, w):        # w → x (hop 2)
            if x != u and v in _neighbors(G, x):   # x → v (hop 3)
                count += 1
    return float(count)
