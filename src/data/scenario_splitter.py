"""
Strukturalny podział krawędzi symulujący realne scenariusze broken lineage.

W przeciwieństwie do losowego podziału (splitter.py), tutaj krawędzie testowe
są wybierane na podstawie roli węzła w grafie — bez znajomości nazw (UUID).

Trzy scenariusze odpowiadające docs/synthetic_schema/:

  Scenariusz A — "Staging table removed"
      Węzły intermediate Table (in_df > 0 AND out_df > 0) symulują tabele staging.
      Usuwamy ich WYJŚCIOWE krawędzie DATA_FLOW (Table→Job).
      Algorytm widzi: Job→Table (krawędź wejściowa zachowana),
      musi przewidzieć: Table→Job2 (krawędź wyjściowa ukryta).

  Scenariusz B — "UDF hidden source"
      Węzły source Table (in_df == 0, out_df > 0) symulują tabele źródłowe,
      których część zależności jest ukryta przez UDF.
      Usuwamy CZĘŚĆ wyjściowych krawędzi source Tables (losowe 20%).
      Algorytm widzi: część Table→Job, musi przewidzieć pozostałe.

  Scenariusz C — "Sink dependency hidden"
      Węzły sink Table (in_df > 0, out_df == 0) symulują data marty.
      Usuwamy ich WEJŚCIOWE krawędzie DATA_FLOW (Job→Table).
      Algorytm widzi: inne krawędzie grafu,
      musi przewidzieć: Job→Table (krawędź do ostatecznego celu).
"""

import random
from copy import deepcopy
from collections import defaultdict

import networkx as nx


_VALID_TYPE_PAIRS = {
    "DATA_FLOW": [("Data Table", "Data Job"), ("Data Job", "Data Table")],
}


# ---------------------------------------------------------------------------
# Klasyfikacja ról węzłów w podgrafie DATA_FLOW
# ---------------------------------------------------------------------------

def classify_table_roles(G: nx.DiGraph) -> dict[str, list]:
    """
    Klasyfikuje węzły Data Table według ich roli w podgrafie DATA_FLOW.

    Returns
    -------
    dict z kluczami:
        "intermediate"  — Table z in_df > 0 AND out_df > 0  (staging)
        "source"        — Table z in_df == 0 AND out_df > 0 (źródłowe)
        "sink"          — Table z in_df > 0 AND out_df == 0 (data marty)
        "isolated"      — Table bez krawędzi DATA_FLOW
    """
    df_edges = {
        (u, v) for u, v, d in G.edges(data=True)
        if d.get("relation_type") == "DATA_FLOW"
    }

    in_df  = defaultdict(int)
    out_df = defaultdict(int)
    for u, v in df_edges:
        out_df[u] += 1
        in_df[v]  += 1

    roles: dict[str, list] = {
        "intermediate": [],
        "source":       [],
        "sink":         [],
        "isolated":     [],
    }

    for node, data in G.nodes(data=True):
        if data.get("asset_type") != "Data Table":
            continue
        i = in_df[node]
        o = out_df[node]
        if i > 0 and o > 0:
            roles["intermediate"].append(node)
        elif i == 0 and o > 0:
            roles["source"].append(node)
        elif i > 0 and o == 0:
            roles["sink"].append(node)
        else:
            roles["isolated"].append(node)

    return roles


# ---------------------------------------------------------------------------
# Podział strukturalny
# ---------------------------------------------------------------------------

def scenario_split(
    G: nx.DiGraph,
    scenario: str,
    val_ratio: float = 0.0,
    neg_ratio: float = 1.0,
    seed: int = 42,
) -> dict:
    """
    Tworzy podział train/val/test na podstawie scenariusza broken lineage.

    Parameters
    ----------
    G : nx.DiGraph
        Oryginalny graf.
    scenario : str
        "A" — usunięcie tabeli staging (krawędzie wyjściowe intermediate Tables)
        "B" — ukryta zależność przez UDF (krawędzie wyjściowe source Tables)
        "C" — ukryta zależność do data martu (krawędzie wejściowe sink Tables)
    val_ratio : float
        Udział pozostałych krawędzi (po wydzieleniu testu) trafiających do
        zbioru walidacyjnego. Walidacja jest losowana ze zbioru treningowego —
        nie z krawędzi scenariuszowych — by zbiór testowy zachował intencję
        scenariusza. 0.0 = brak walidacji (kompatybilność wsteczna).
    neg_ratio : float
        Stosunek negatywnych do pozytywnych próbek (osobno dla train/val/test).
    seed : int
        Ziarno losowości.

    Returns
    -------
    dict z kluczami: G_train, pos_train, pos_val, pos_test,
                     neg_train, neg_val, neg_test, scenario, roles_summary
    """
    if scenario not in ("A", "B", "C"):
        raise ValueError(f"Nieznany scenariusz: '{scenario}'. Dozwolone: A, B, C")
    if not 0.0 <= val_ratio < 1.0:
        raise ValueError("val_ratio musi być w przedziale [0, 1).")

    rng = random.Random(seed)
    roles = classify_table_roles(G)

    df_edges = [
        (u, v) for u, v, d in G.edges(data=True)
        if d.get("relation_type") == "DATA_FLOW"
    ]

    # Wybierz krawędzie testowe na podstawie scenariusza
    if scenario == "A":
        # Krawędzie wyjściowe tabeli intermediate: Table→Job
        intermediate = set(roles["intermediate"])
        pos_test = [(u, v) for u, v in df_edges
                    if u in intermediate
                    and G.nodes[v].get("asset_type") == "Data Job"]

    elif scenario == "B":
        # Losowe 20% krawędzi wyjściowych source Tables: Table→Job
        source = set(roles["source"])
        candidates = [(u, v) for u, v in df_edges
                      if u in source
                      and G.nodes[v].get("asset_type") == "Data Job"]
        rng.shuffle(candidates)
        n_test = max(1, round(len(candidates) * 0.2))
        pos_test = candidates[:n_test]

    else:  # C
        # Krawędzie wejściowe tabeli sink: Job→Table
        sink = set(roles["sink"])
        pos_test = [(u, v) for u, v in df_edges
                    if v in sink
                    and G.nodes[u].get("asset_type") == "Data Job"]

    if len(pos_test) == 0:
        raise ValueError(
            f"Scenariusz {scenario}: brak krawędzi testowych w tym grafie. "
            f"Role: intermediate={len(roles['intermediate'])}, "
            f"source={len(roles['source'])}, sink={len(roles['sink'])}"
        )

    pos_test_set = set(pos_test)
    remaining = [(u, v) for u, v in df_edges if (u, v) not in pos_test_set]

    # Walidacja: losowa próbka z krawędzi nietestowych (nie ze scenariusza,
    # bo wszystkie krawędzie scenariuszowe muszą zostać w teście).
    pos_val: list[tuple] = []
    pos_train = remaining
    if val_ratio > 0 and len(remaining) > 1:
        rng.shuffle(remaining)
        n_val = max(1, round(len(remaining) * val_ratio))
        if n_val >= len(remaining):
            n_val = len(remaining) - 1  # zostaw przynajmniej 1 do treningu
        pos_val   = remaining[:n_val]
        pos_train = remaining[n_val:]

    # Graf treningowy — bez krawędzi testowych ANI walidacyjnych
    G_train = deepcopy(G)
    for u, v in pos_test + pos_val:
        G_train.remove_edge(u, v)

    # Negatywne próbki — osobne pule dla train / val / test
    existing = set(G.edges())
    neg_test  = _sample_negatives(G, existing, round(len(pos_test)  * neg_ratio), rng)
    neg_val   = _sample_negatives(G, existing, round(len(pos_val)   * neg_ratio), rng)
    neg_train = _sample_negatives(G, existing, round(len(pos_train) * neg_ratio), rng)

    return {
        "G_train":   G_train,
        "pos_train": pos_train,
        "pos_val":   pos_val,
        "pos_test":  pos_test,
        "neg_train": neg_train,
        "neg_val":   neg_val,
        "neg_test":  neg_test,
        "scenario":  scenario,
        "roles_summary": {
            role: len(nodes) for role, nodes in roles.items()
        },
    }


def _sample_negatives(
    G: nx.DiGraph,
    existing: set,
    n_needed: int,
    rng: random.Random,
) -> list[tuple]:
    """Losuje n_needed par (Table,Job) lub (Job,Table) których nie ma w G."""
    if n_needed == 0:
        return []

    nodes_by_type = defaultdict(list)
    for node, data in G.nodes(data=True):
        nodes_by_type[data.get("asset_type", "")].append(node)

    candidates = []
    for src_type, tgt_type in [("Data Table", "Data Job"), ("Data Job", "Data Table")]:
        for u in nodes_by_type[src_type]:
            for v in nodes_by_type[tgt_type]:
                if u != v and (u, v) not in existing:
                    candidates.append((u, v))

    if len(candidates) < n_needed:
        n_needed = len(candidates)  # weź ile możemy, nie rzucaj błędu

    rng.shuffle(candidates)
    return candidates[:n_needed]


def scenario_summary(splits: dict) -> str:
    """Zwraca czytelne podsumowanie podziału scenariuszowego."""
    s = splits["scenario"]
    roles = splits["roles_summary"]
    n_pos_test  = len(splits["pos_test"])
    n_pos_train = len(splits["pos_train"])
    return (
        f"Scenariusz {s} | "
        f"intermediate={roles['intermediate']} "
        f"source={roles['source']} "
        f"sink={roles['sink']} | "
        f"train_pos={n_pos_train} test_pos={n_pos_test}"
    )
