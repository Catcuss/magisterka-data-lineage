"""
LineageHealthDetector — własny detektor chorych węzłów (wkład pracy).

Łączy trzy podejścia w jeden skalibrowany model:
  1. lokalne cechy pozycji w DAG (node_features),
  2. relacyjny score kompletności peer-consistency (completeness),
  3. kalibrację prawdopodobieństw (isotonic) — wyjście to RZECZYWISTE p(infected),
     a nie dowolny score (odpowiedź na cel „jak najlepsze prawdopodobieństwo").

Interfejs fit(train_datasets)/score(dataset) zgodny z NodeMLClassifier, więc
detektor wpina się do istniejącego runnera obok pozostałych algorytmów.
"""

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier

try:  # pragma: no cover
    from src.detection.node_features import extract_node_features
    from src.detection.completeness import completeness_features
except ImportError:  # pragma: no cover
    from detection.node_features import extract_node_features
    from detection.completeness import completeness_features

try:
    import lightgbm as lgb
    _LGBM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LGBM_AVAILABLE = False


def _make_base(base: str, seed: int):
    """Bazowy estymator detektora: RandomForest (domyślny, najlepszy AUC) lub LightGBM."""
    if base == "rf":
        return RandomForestClassifier(
            n_estimators=300, class_weight="balanced",
            random_state=seed, n_jobs=-1,
        )
    if base == "lgbm":
        if not _LGBM_AVAILABLE:
            raise ImportError("Wymagana biblioteka lightgbm.")
        return lgb.LGBMClassifier(
            n_estimators=300, learning_rate=0.05, class_weight="balanced",
            random_state=seed, n_jobs=-1, verbose=-1,
        )
    raise ValueError(f"Nieznana baza: {base}. Dozwolone: 'rf', 'lgbm'.")


class LineageHealthDetector:
    """
    Detektor chorych tabel: [cechy węzła ⊕ kompletność] → LightGBM (+ kalibracja).

    Parameters
    ----------
    seed : int
        Ziarno losowości.
    calibrate : bool
        True → CalibratedClassifierCV (isotonic) dla rzetelnych prawdopodobieństw.
        False → surowy LightGBM (wariant do ablacji wpływu kalibracji).
    use_completeness : bool
        True → dokłada cechy kompletności; False → tylko cechy węzła
        (wariant do ablacji wpływu score'u kompletności).
    base : str
        Bazowy estymator: "rf" (RandomForest, domyślny — najlepszy AUC) lub "lgbm".
    """

    def __init__(self, seed: int = 42, calibrate: bool = True,
                 use_completeness: bool = True, base: str = "rf"):
        self.seed = seed
        self.calibrate = calibrate
        self.use_completeness = use_completeness
        self.base = base
        estimator = _make_base(base, seed)
        # cv=3 wystarcza przy puli kilku tys. węzłów; isotonic dla kalibracji.
        self.model = (CalibratedClassifierCV(estimator, method="isotonic", cv=3)
                      if calibrate else estimator)
        self._fitted = False

    def _features(self, G, nodes) -> np.ndarray:
        X = extract_node_features(G, nodes)
        if self.use_completeness:
            X = np.hstack([X, completeness_features(G, nodes)])
        return X

    def fit(self, train_datasets: list[dict]) -> "LineageHealthDetector":
        Xs, ys = [], []
        for ds in train_datasets:
            if not ds["candidates"]:
                continue
            Xs.append(self._features(ds["G_obs"], ds["candidates"]))
            ys.extend(ds["labels"])
        if not Xs:
            raise ValueError("Brak danych treningowych.")
        X = np.vstack(Xs)
        y = np.array(ys)
        if len(np.unique(y)) < 2:
            raise ValueError("Zbiór treningowy zawiera tylko jedną klasę.")
        self.model.fit(X, y)
        self._fitted = True
        return self

    def score(self, dataset: dict) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Wywołaj fit() przed score().")
        if not dataset["candidates"]:
            return np.array([])
        X = self._features(dataset["G_obs"], dataset["candidates"])
        proba = self.model.predict_proba(X)
        if proba.shape[1] == 1:
            return np.full(len(X), float(self.model.classes_[0]))
        return proba[:, 1]
