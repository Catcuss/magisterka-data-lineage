"""
Score kompletności lineage — peer-consistency.

Pomysł (realizacja sugestii dr. Misiorka „ocena kompletności drzew"):
tabela o zerwanym lineage jest STRUKTURALNIE NIESPÓJNA ze swoimi sąsiadami w DAG.

Intuicja:
  - Tabela-korzeń (in_df=0) jest podejrzana, jeśli inne tabele wpadające do tych
    samych downstream-jobów (jej „peerzy") MAJĄ producentów, a ona nie — prawdziwe
    źródło raczej sąsiaduje z innymi źródłami.
  - Symetrycznie dla tabeli-liścia (out_df=0) i jej peerów po stronie konsumpcji.

To sygnał PROPAGACYJNY/RELACYJNY — inny niż lokalny stopień/rola — więc ma szansę
dołożyć informację, której klasyfikator z samych cech węzła jeszcze nie ma.
"""

from collections import defaultdict

import numpy as np
import networkx as nx


_FEATURE_NAMES = [
    "peer_producer_score",   # ułamek peerów-wejść (po stronie producenta), którzy mają producenta
    "peer_consumer_score",   # ułamek peerów-wyjść (po stronie konsumenta), którzy mają konsumenta
    "completeness_anomaly",  # bramkowany sygnał: niespójność brzegu (korzeń/liść)
]


def feature_names() -> list[str]:
    return list(_FEATURE_NAMES)


def _df_degrees(G: nx.DiGraph):
    in_df: dict = {n: 0 for n in G.nodes()}
    out_df: dict = {n: 0 for n in G.nodes()}
    for u, v, d in G.edges(data=True):
        if d.get("relation_type") == "DATA_FLOW":
            out_df[u] += 1
            in_df[v] += 1
    return in_df, out_df


def _job_table_maps(G: nx.DiGraph):
    """job -> tabele wejściowe oraz job -> tabele wyjściowe (po DATA_FLOW)."""
    job_inputs: dict = defaultdict(list)
    job_outputs: dict = defaultdict(list)
    for u, v, d in G.edges(data=True):
        if d.get("relation_type") != "DATA_FLOW":
            continue
        au = G.nodes[u].get("asset_type")
        av = G.nodes[v].get("asset_type")
        if au == "Data Table" and av == "Data Job":      # tabela -> job
            job_inputs[v].append(u)
        elif au == "Data Job" and av == "Data Table":    # job -> tabela
            job_outputs[u].append(v)
    return job_inputs, job_outputs


def completeness_scores(G: nx.DiGraph) -> dict:
    """
    Zwraca słownik node -> (peer_producer_score, peer_consumer_score, anomaly)
    dla węzłów typu Data Table.
    """
    in_df, out_df = _df_degrees(G)
    job_inputs, job_outputs = _job_table_maps(G)

    scores: dict = {}
    for t, data in G.nodes(data=True):
        if data.get("asset_type") != "Data Table":
            continue

        # Strona producenta: peerzy = inne wejścia do downstream-jobów tej tabeli.
        downstream_jobs = [v for _, v, d in G.out_edges(t, data=True)
                           if d.get("relation_type") == "DATA_FLOW"
                           and G.nodes[v].get("asset_type") == "Data Job"]
        prod_peers = set()
        for j in downstream_jobs:
            prod_peers.update(job_inputs.get(j, ()))
        prod_peers.discard(t)
        prod_score = (np.mean([1.0 if in_df[p] > 0 else 0.0 for p in prod_peers])
                      if prod_peers else 0.0)

        # Strona konsumenta: peerzy = inne wyjścia upstream-jobów tej tabeli.
        upstream_jobs = [u for u, _, d in G.in_edges(t, data=True)
                         if d.get("relation_type") == "DATA_FLOW"
                         and G.nodes[u].get("asset_type") == "Data Job"]
        cons_peers = set()
        for j in upstream_jobs:
            cons_peers.update(job_outputs.get(j, ()))
        cons_peers.discard(t)
        cons_score = (np.mean([1.0 if out_df[p] > 0 else 0.0 for p in cons_peers])
                      if cons_peers else 0.0)

        # Bramkowana anomalia: liczy się tylko na brzegu (korzeń/liść).
        anomaly = 0.0
        if in_df[t] == 0:
            anomaly = max(anomaly, prod_score)
        if out_df[t] == 0:
            anomaly = max(anomaly, cons_score)

        scores[t] = (float(prod_score), float(cons_score), float(anomaly))

    return scores


def completeness_features(G: nx.DiGraph, nodes: list) -> np.ndarray:
    """Macierz cech kompletności (len(nodes) × 3) w kolejności feature_names()."""
    sc = completeness_scores(G)
    rows = [list(sc.get(n, (0.0, 0.0, 0.0))) for n in nodes]
    return np.array(rows, dtype=float)


def anomaly_score(G: nx.DiGraph, nodes: list) -> np.ndarray:
    """Pojedynczy interpretowalny score (completeness_anomaly) — do użycia jako heurystyka."""
    sc = completeness_scores(G)
    return np.array([sc.get(n, (0.0, 0.0, 0.0))[2] for n in nodes], dtype=float)
