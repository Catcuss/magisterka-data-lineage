"""
Testy jednostkowe dla src/detection/lineage_detector.py.

Sprawdzają, że detektor uczy się na puli grafów i zwraca poprawne
prawdopodobieństwa p∈[0,1] dla niewidzianego grafu (protokół indukcyjny).
"""

import numpy as np
import pytest

from src.data.loader import load_graph
from src.detection.job_removal import build_node_dataset
from src.detection.lineage_detector import LineageHealthDetector


@pytest.fixture(scope="module")
def train_test():
    train = [build_node_dataset(load_graph(g), 0.2, 42) for g in ("DLG5", "DLG6")]
    test = build_node_dataset(load_graph("DLG7"), 0.2, 42)
    return train, test


def test_fit_score_probabilities(train_test):
    train, test = train_test
    det = LineageHealthDetector(seed=42).fit(train)
    s = det.score(test)
    assert len(s) == len(test["candidates"])
    assert ((s >= 0.0) & (s <= 1.0)).all()


def test_ablation_variants_run(train_test):
    train, test = train_test
    # bez kalibracji i bez kompletności — wariant do ablacji, ma działać
    det = LineageHealthDetector(seed=42, calibrate=False,
                                use_completeness=False).fit(train)
    s = det.score(test)
    assert len(s) == len(test["candidates"])
    assert ((s >= 0.0) & (s <= 1.0)).all()


def test_score_before_fit_raises():
    det = LineageHealthDetector(seed=42)
    with pytest.raises(RuntimeError):
        det.score({"candidates": ["x"], "G_obs": None})
