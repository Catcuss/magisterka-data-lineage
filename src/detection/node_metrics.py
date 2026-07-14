"""
Metryki rankingowe dla detekcji zainfekowanych węzłów.

Detekcja zwraca dla każdego węzła score = P(infected). Oceniamy jakość
RANKINGU (a nie pojedynczego progu), bo zainfekowane tabele są rzadkie:
    - AUC-ROC, AUC-PR  — niezależne od progu, jak w predykcji krawędzi,
    - Precision@k, Recall@k — jakość k najwyżej ocenionych węzłów,
    - Hits@k           — czy infected trafiają do top-k,
    - MAP (Average Precision) — jakość całego rankingu.

k domyślnie = liczba rzeczywiście zainfekowanych węzłów (k = #positives),
co daje uczciwe Precision@k = Recall@k przy idealnym rankingu.
"""

import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score


def _rank_topk_indices(scores: np.ndarray, k: int) -> np.ndarray:
    """Indeksy k najwyższych score (stabilnie, malejąco)."""
    k = min(k, len(scores))
    return np.argsort(-scores, kind="stable")[:k]


def precision_recall_at_k(y_true: np.ndarray, scores: np.ndarray, k: int) -> tuple:
    """Precision@k i Recall@k dla rankingu."""
    y_true = np.asarray(y_true)
    n_pos = int(y_true.sum())
    if len(scores) == 0 or k <= 0:
        return float("nan"), float("nan")
    top = _rank_topk_indices(np.asarray(scores, dtype=float), k)
    hits = int(y_true[top].sum())
    precision = hits / min(k, len(scores))
    recall = hits / n_pos if n_pos > 0 else float("nan")
    return precision, recall


def hits_at_k(y_true: np.ndarray, scores: np.ndarray, k: int) -> float:
    """Udział pozytywów w top-k, znormalizowany przez min(k, #positives)."""
    y_true = np.asarray(y_true)
    n_pos = int(y_true.sum())
    if len(scores) == 0 or n_pos == 0:
        return float("nan")
    top = _rank_topk_indices(np.asarray(scores, dtype=float), k)
    return int(y_true[top].sum()) / min(k, n_pos)


def node_detection_metrics(
    y_true: list | np.ndarray,
    scores: np.ndarray,
    k: int | None = None,
) -> dict:
    """
    Komplet metryk detekcji węzłów.

    Parameters
    ----------
    y_true : array-like
        Etykiety węzłów (1 = infected, 0 = clean).
    scores : np.ndarray
        Score P(infected) dla każdego węzła (ta sama kolejność co y_true).
    k : int | None
        Próg rankingu dla Precision@k/Recall@k/Hits@k. None → k = liczba
        zainfekowanych węzłów (#positives).

    Returns
    -------
    dict: auc_roc, auc_pr, precision_at_k, recall_at_k, hits_at_k, map, k, n_pos.
        AUC = nan, gdy w zbiorze jest tylko jedna klasa.
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores, dtype=float)
    n_pos = int(y_true.sum())
    n = len(y_true)
    if k is None:
        k = max(1, n_pos)

    if n == 0 or n_pos == 0 or n_pos == n:
        # Brak obu klas — AUC niezdefiniowane.
        auc_roc = float("nan")
        auc_pr = float("nan")
    else:
        auc_roc = roc_auc_score(y_true, scores)
        auc_pr = average_precision_score(y_true, scores)

    p_at_k, r_at_k = precision_recall_at_k(y_true, scores, k)
    return {
        "auc_roc":        auc_roc,
        "auc_pr":         auc_pr,
        "precision_at_k": p_at_k,
        "recall_at_k":    r_at_k,
        "hits_at_k":      hits_at_k(y_true, scores, k),
        "map":            auc_pr,  # average_precision_score = MAP dla jednego rankingu
        "k":              int(k),
        "n_pos":          n_pos,
    }
