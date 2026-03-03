"""
Ewaluacja algorytmów predykcji krawędzi.

Metryki: Precision, Recall, F1-score, AUC-ROC.
Wspólny interfejs dla wszystkich algorytmów — przyjmuje y_true i scores.
"""

import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)


def best_threshold_f1(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Zwraca próg maksymalizujący F1 na podanych danych."""
    best_t, best_f1 = 0.5, 0.0
    for t in np.unique(scores):
        y_pred = (scores >= t).astype(int)
        f = f1_score(y_true, y_pred, zero_division=0)
        if f > best_f1:
            best_f1, best_t = f, t
    return float(best_t)


def compute_metrics(
    y_true: list | np.ndarray,
    scores: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """
    Oblicza metryki klasyfikacji krawędzi.

    Parameters
    ----------
    y_true : array-like, shape (n,)
        Etykiety: 1 = krawędź istnieje, 0 = nie istnieje.
    scores : np.ndarray, shape (n,)
        Scores/prawdopodobieństwa zwrócone przez algorytm.
    threshold : float
        Próg binaryzacji scores → predykcja 0/1. Domyślnie 0.5.

    Returns
    -------
    dict z kluczami: precision, recall, f1, auc_roc, auc_pr
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores, dtype=float)
    y_pred = (scores >= threshold).astype(int)

    # Gdy wszystkie scores są 0 (np. brak wspólnych sąsiadów), AUC jest niezdefiniowane
    unique_scores = np.unique(scores)
    if len(unique_scores) < 2:
        auc_roc = float("nan")
        auc_pr = float("nan")
    else:
        auc_roc = roc_auc_score(y_true, scores)
        auc_pr = average_precision_score(y_true, scores)

    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall":    recall_score(y_true, y_pred, zero_division=0),
        "f1":        f1_score(y_true, y_pred, zero_division=0),
        "auc_roc":   auc_roc,
        "auc_pr":    auc_pr,
    }


def evaluate_split(
    splits: dict,
    scores_test: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """
    Oblicza metryki dla zbioru testowego z gotowego słownika splits.

    Parameters
    ----------
    splits : dict
        Wynik split_edges() — musi zawierać pos_test i neg_test.
    scores_test : np.ndarray
        Scores dla pos_test + neg_test (w tej kolejności).
    threshold : float
        Próg binaryzacji.
    """
    n_pos = len(splits["pos_test"])
    n_neg = len(splits["neg_test"])
    y_true = np.array([1] * n_pos + [0] * n_neg)
    return compute_metrics(y_true, scores_test, threshold)


def print_metrics(name: str, metrics: dict) -> None:
    """Wypisuje metryki w czytelnym formacie."""
    print(
        f"{name:30s}  "
        f"P={metrics['precision']:.3f}  "
        f"R={metrics['recall']:.3f}  "
        f"F1={metrics['f1']:.3f}  "
        f"AUC-ROC={metrics['auc_roc']:.3f}  "
        f"AUC-PR={metrics['auc_pr']:.3f}"
    )
