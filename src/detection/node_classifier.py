"""
Klasyfikatory/scorery węzłów dla detekcji zainfekowanych tabel.

Dwie grupy metod działające w protokole INDUKCYJNYM (cross-graph):
    1. Heurystyki anomalii (bez uczenia) — interpretowalny baseline,
    2. Klasyczne ML (RF, RUSBoost, LightGBM) na cechach pozycji węzła.

Uwaga o Node2Vec: zanurzenia Node2Vec są TRANSDUKTYWNE — uczone osobno na
każdym grafie, nie są porównywalne między grafami, więc nie da się ich użyć
w protokole cross-graph (trening na jednych grafach, test na innych). To jest
samo w sobie wynik: metody zanurzeń nie generalizują do niewidzianych grafów,
co motywuje stosowanie indukcyjnych GNN (por. Dutkiewicz, Misiorek, Wrembel 2026).
Dlatego Node2Vec nie wchodzi do głównego porównania indukcyjnego.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier

try:
    from src.detection.node_features import extract_node_features
except ImportError:  # pragma: no cover
    from detection.node_features import extract_node_features

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


# Heurystyki anomalii (bez uczenia)
# Indeksy cech (zgodne z node_features.feature_names()):
#   2=degree, 7=is_root, 8=is_leaf, 10=n_job_neighbors

HEURISTICS = ["degree_anomaly", "boundary", "low_job_connectivity"]


class HeuristicNodeScorer:
    """
    Interpretowalny scorer węzłów oparty na strukturze (bez treningu).

    Intuicja: tabela, która straciła joba (zainfekowana), zwykle ma mniej
    połączeń i częściej staje się brzegiem grafu (korzeń/liść).
    """

    def __init__(self, name: str):
        if name not in HEURISTICS:
            raise ValueError(f"Nieznana heurystyka: {name}. Dozwolone: {HEURISTICS}")
        self.name = name

    def fit(self, train_datasets) -> "HeuristicNodeScorer":
        return self  # heurystyki nie wymagają uczenia

    def score(self, dataset: dict) -> np.ndarray:
        X = extract_node_features(dataset["G_obs"], dataset["candidates"])
        if self.name == "degree_anomaly":
            return 1.0 / (1.0 + X[:, 2])             # mniejszy stopień → wyższy score
        if self.name == "boundary":
            return X[:, 7] + X[:, 8]                  # is_root + is_leaf
        if self.name == "low_job_connectivity":
            return 1.0 / (1.0 + X[:, 10])             # mniej sąsiadów-jobów → wyższy score
        raise AssertionError("unreachable")


# Klasyczne ML na cechach węzła (protokół indukcyjny)

ML_MODELS = ["RandomForest", "RUSBoost", "LightGBM"]


class NodeMLClassifier:
    """
    Klasyfikator węzłów uczony na PULI grafów treningowych (cross-graph),
    oceniany na grafach testowych (niewidzianych) — protokół indukcyjny.
    """

    def __init__(self, name: str, seed: int = 42):
        self.name = name
        if name == "RandomForest":
            self.model = RandomForestClassifier(
                n_estimators=200, class_weight="balanced",
                random_state=seed, n_jobs=-1,
            )
        elif name == "RUSBoost":
            if not _IMBLEARN_AVAILABLE:
                raise ImportError("Wymagana biblioteka imbalanced-learn.")
            self.model = _RUSBoost(n_estimators=200, random_state=seed)
        elif name == "LightGBM":
            if not _LGBM_AVAILABLE:
                raise ImportError("Wymagana biblioteka lightgbm.")
            self.model = lgb.LGBMClassifier(
                n_estimators=300, learning_rate=0.05,
                class_weight="balanced", random_state=seed,
                n_jobs=-1, verbose=-1,
            )
        else:
            raise ValueError(f"Nieznany model: {name}. Dozwolone: {ML_MODELS}")
        self._fitted = False

    def fit(self, train_datasets: list[dict]) -> "NodeMLClassifier":
        Xs, ys = [], []
        for ds in train_datasets:
            if not ds["candidates"]:
                continue
            Xs.append(extract_node_features(ds["G_obs"], ds["candidates"]))
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
        X = extract_node_features(dataset["G_obs"], dataset["candidates"])
        proba = self.model.predict_proba(X)
        # Zabezpieczenie, gdyby model widział tylko jedną klasę.
        if proba.shape[1] == 1:
            return np.full(len(X), float(self.model.classes_[0]))
        return proba[:, 1]
