"""
Podział krawędzi grafu na zbiory train/val/test oraz generowanie negatywnych próbek.

Kontekst:
    Problem "broken lineage" jest traktowany jako binarna klasyfikacja krawędzi:
    - próbki pozytywne  — krawędzie istniejące w grafie (usunięte ze zbioru treningowego)
    - próbki negatywne — pary węzłów bez krawędzi (nigdy nie istniały)

Zasady generowania negatywnych próbek:
    - Respektują typy węzłów: para (u, v) jest kandydatem tylko wtedy, gdy typy
      węzłów u i v odpowiadają typom obserwowanym dla danego edge_type w grafie.
    - Żadna negatywna próbka nie istnieje jako krawędź w oryginalnym grafie G
      (ani w train, ani w test) — unikamy fałszywych negatywów.
"""

import random
import warnings
from copy import deepcopy
from collections import defaultdict

import networkx as nx


# Dozwolone pary (src_type, tgt_type) dla każdego edge_type
_VALID_TYPE_PAIRS = {
    "DATA_FLOW":    [("Data Table", "Data Job"), ("Data Job", "Data Table")],
    "PARENT_CHILD": [("Data Table", "Data Field")],
}


def split_edges(
    G: nx.DiGraph,
    edge_type: str = "DATA_FLOW",
    test_ratio: float = 0.2,
    val_ratio: float = 0.0,
    neg_ratio: float = 1.0,
    seed: int = 42,
) -> dict:
    """
    Dzieli krawędzie danego typu na train/val/test i generuje negatywne próbki.

    Parameters
    ----------
    G : nx.DiGraph
        Oryginalny graf (nie jest modyfikowany).
    edge_type : str
        Typ krawędzi do podziału: "DATA_FLOW" lub "PARENT_CHILD".
    test_ratio : float
        Udział krawędzi w zbiorze testowym (0–1).
    val_ratio : float
        Udział krawędzi w zbiorze walidacyjnym (0–1). 0 = brak walidacji.
    neg_ratio : float
        Stosunek negatywnych do pozytywnych próbek w zbiorach val/test.
    seed : int
        Ziarno losowości dla powtarzalności wyników.

    Returns
    -------
    dict z kluczami:
        G_train     — nx.DiGraph z usuniętymi krawędziami val+test
        pos_train   — lista (u, v) krawędzi treningowych
        pos_val     — lista (u, v) krawędzi walidacyjnych (pusta gdy val_ratio=0)
        pos_test    — lista (u, v) krawędzi testowych
        neg_train   — lista (u, v) negatywnych próbek treningowych (1:neg_ratio)
        neg_val     — lista (u, v) negatywnych próbek walidacyjnych
        neg_test    — lista (u, v) negatywnych próbek testowych

    Raises
    ------
    ValueError
        Gdy test_ratio + val_ratio >= 1 lub edge_type jest nieznany.
    ValueError
        Gdy po podziale zbiór testowy byłby pusty.
    """
    if edge_type not in _VALID_TYPE_PAIRS:
        raise ValueError(
            f"Nieznany edge_type: '{edge_type}'. "
            f"Dozwolone: {list(_VALID_TYPE_PAIRS.keys())}"
        )
    if test_ratio + val_ratio >= 1.0:
        raise ValueError("test_ratio + val_ratio musi być < 1.0")

    rng = random.Random(seed)

    # 1. Zbierz krawędzie docelowego typu
    target_edges = [
        (u, v)
        for u, v, d in G.edges(data=True)
        if d.get("relation_type") == edge_type
    ]

    if len(target_edges) == 0:
        raise ValueError(f"Graf nie zawiera krawędzi typu '{edge_type}'.")

    rng.shuffle(target_edges)

    # 2. Oblicz rozmiary zbiorów
    n = len(target_edges)
    n_test = max(1, round(n * test_ratio))
    n_val = max(0, round(n * val_ratio)) if val_ratio > 0 else 0

    if n_test + n_val >= n:
        raise ValueError(
            f"Za mało krawędzi ({n}) dla test_ratio={test_ratio}, "
            f"val_ratio={val_ratio}. Wymagane co najmniej {n_test + n_val + 1}."
        )

    pos_test = target_edges[:n_test]
    pos_val = target_edges[n_test: n_test + n_val]
    pos_train = target_edges[n_test + n_val:]

    # 3. Zbuduj graf treningowy (usuń krawędzie val+test)
    G_train = deepcopy(G)
    for u, v in pos_test + pos_val:
        G_train.remove_edge(u, v)

    # 4. Zbiór wszystkich istniejących krawędzi (do filtrowania negatywów)
    existing = set(G.edges())

    # 5. Wygeneruj negatywne próbki (osobna pula dla train/val/test)
    neg_test = _sample_negatives(G, existing, edge_type, round(n_test * neg_ratio), rng)
    neg_val = (
        _sample_negatives(G, existing, edge_type, round(n_val * neg_ratio), rng)
        if n_val > 0
        else []
    )
    neg_train = _sample_negatives(
        G, existing, edge_type, round(len(pos_train) * neg_ratio), rng
    )

    return {
        "G_train": G_train,
        "pos_train": pos_train,
        "pos_val": pos_val,
        "pos_test": pos_test,
        "neg_train": neg_train,
        "neg_val": neg_val,
        "neg_test": neg_test,
    }


def _sample_negatives(
    G: nx.DiGraph,
    existing: set,
    edge_type: str,
    n_needed: int,
    rng: random.Random,
) -> list[tuple]:
    """
    Losuje n_needed par węzłów, które:
    - mają typy zgodne z edge_type,
    - nie istnieją jako krawędź w G.

    Używa rejection sampling: losuje pary i odrzuca te istniejące/zduplikowane.
    Pełna enumeracja par (kosztowna na dużych grafach, O(|src|×|tgt|)) jest
    wykonywana wyłącznie awaryjnie, gdy rejection sampling nie wypełni puli.
    """
    return _rejection_sample_negatives(
        G, existing, _VALID_TYPE_PAIRS[edge_type], n_needed, rng,
        context=f"edge_type='{edge_type}'",
    )


def _rejection_sample_negatives(
    G: nx.DiGraph,
    existing: set,
    valid_pairs: list[tuple],
    n_needed: int,
    rng: random.Random,
    context: str = "",
) -> list[tuple]:
    """
    Wspólny generator negatywów (rejection sampling z awaryjną enumeracją).

    Zwraca n_needed par (lub mniej, z ostrzeżeniem, gdy pula jest za mała).
    """
    if n_needed <= 0:
        return []

    nodes_by_type = defaultdict(list)
    for node, data in G.nodes(data=True):
        nodes_by_type[data.get("asset_type", "")].append(node)

    type_pairs = [
        (nodes_by_type[s], nodes_by_type[t])
        for s, t in valid_pairs
        if nodes_by_type[s] and nodes_by_type[t]
    ]
    if not type_pairs:
        warnings.warn(f"Brak węzłów dla negatywów ({context}).")
        return []

    seen: set = set()
    result: list[tuple] = []
    # Budżet prób proporcjonalny do potrzeb; chroni przed pętlą gdy pula gęsta.
    max_attempts = max(n_needed * 20, 2000)
    attempts = 0
    while len(result) < n_needed and attempts < max_attempts:
        attempts += 1
        src_nodes, tgt_nodes = rng.choice(type_pairs)
        u = rng.choice(src_nodes)
        v = rng.choice(tgt_nodes)
        if u == v or (u, v) in existing or (u, v) in seen:
            continue
        seen.add((u, v))
        result.append((u, v))

    if len(result) >= n_needed:
        return result[:n_needed]

    # Awaryjnie: pełna enumeracja brakujących kandydatów (pula okazała się mała).
    for src_nodes, tgt_nodes in type_pairs:
        for u in src_nodes:
            for v in tgt_nodes:
                if u != v and (u, v) not in existing and (u, v) not in seen:
                    seen.add((u, v))
                    result.append((u, v))
    if len(result) < n_needed:
        warnings.warn(
            f"Za mała pula kandydatów ({len(result)}) dla {n_needed} "
            f"negatywnych próbek ({context}). Zwrócono {len(result)}."
        )
        return result
    rng.shuffle(result)
    return result[:n_needed]


def split_summary(splits: dict) -> dict:
    """
    Zwraca statystyki podziału (liczności zbiorów).
    """
    return {
        "G_train_edges": splits["G_train"].number_of_edges(),
        "pos_train":     len(splits["pos_train"]),
        "neg_train":     len(splits["neg_train"]),
        "pos_val":       len(splits["pos_val"]),
        "neg_val":       len(splits["neg_val"]),
        "pos_test":      len(splits["pos_test"]),
        "neg_test":      len(splits["neg_test"]),
    }
