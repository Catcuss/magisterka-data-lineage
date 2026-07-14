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


def hits_at_k(y_true: np.ndarray, scores: np.ndarray, k: int = 10) -> float:
    """
    Hits@k — udział pozytywów wśród k par o najwyższym score.

    Metryka rankingowa, niezależna od progu klasyfikacji (jak AUC-ROC/AUC-PR).
    Stosowana m.in. w pracach o indukcyjnej predykcji krawędzi w grafach wiedzy
    (np. Dutkiewicz, Misiorek, Wrembel 2026), co pozwala na porównywalność wyników.

    Definicja: spośród k par o najwyższych scores liczymy, ile jest pozytywami,
    i normalizujemy przez min(k, liczba pozytywów) — wartość w [0, 1].

    Returns
    -------
    float — nan, gdy brak pozytywów lub pusty wektor scores.
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores, dtype=float)
    n_pos = int(y_true.sum())
    if len(scores) == 0 or n_pos == 0:
        return float("nan")
    k_eff = min(k, len(scores))
    top_idx = np.argsort(-scores, kind="stable")[:k_eff]
    hits = int(y_true[top_idx].sum())
    return hits / min(k, n_pos)


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
    k: int = 10,
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
        "hits_at_k": hits_at_k(y_true, scores, k=k),
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


def tune_and_evaluate(
    y_val: np.ndarray,
    scores_val: np.ndarray,
    y_test: np.ndarray,
    scores_test: np.ndarray,
) -> dict:
    """
    Wybiera próg klasyfikacji na zbiorze walidacyjnym, raportuje metryki na teście.

    Eliminuje przeciek informacji (próg dobrany na teście) i ujednolica
    traktowanie wszystkich algorytmów: heurystyki i ML są strojone identycznie.

    Gdy zbiór walidacyjny jest pusty lub scores są stałe, próg = 0.5
    (raportowane P/R/F1 wówczas mają ograniczoną wiarygodność, ale AUC-ROC
    i AUC-PR pozostają poprawne).

    Returns
    -------
    dict z kluczami: precision, recall, f1, auc_roc, auc_pr, threshold
    """
    scores_val = np.asarray(scores_val, dtype=float)
    if len(scores_val) > 0 and len(np.unique(scores_val)) > 1:
        threshold = best_threshold_f1(y_val, scores_val)
    else:
        threshold = 0.5
    metrics = compute_metrics(y_test, scores_test, threshold=threshold)
    metrics["threshold"] = threshold
    return metrics


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
