"""
Ekstrakcja cech topologicznych per-węzeł dla detekcji zainfekowanych tabel.

Cechy opisują POZYCJĘ tabeli w grafie przepływu danych (DATA_FLOW), bo to ona
— a nie sam stopień — odróżnia prawdziwą tabelę źródłową od osieroconej
(po usunięciu joba). Reużywamy metadanych przepływu z modułu klasycznego ML
(_compute_flow_metadata: role, flow_depth, flow_reach).
"""

import numpy as np
import networkx as nx

# Dual-import: działa pod pytest (src.*) i pod runnerem (sys.path → src).
try:  # pragma: no cover
    from src.algorithms.classical_ml import _compute_flow_metadata
except ImportError:  # pragma: no cover
    from algorithms.classical_ml import _compute_flow_metadata


_FEATURE_NAMES = [
    "in_df", "out_df", "degree", "role",
    "flow_depth", "flow_reach", "depth_plus_reach",
    "is_root", "is_leaf",
    "n_field_children", "n_job_neighbors",
    "avg_job_in_df", "avg_job_out_df",
]


def feature_names() -> list[str]:
    """Nazwy cech w kolejności zwracanej przez extract_node_features."""
    return list(_FEATURE_NAMES)


def _df_degrees(G: nx.DiGraph):
    in_df: dict = {n: 0 for n in G.nodes()}
    out_df: dict = {n: 0 for n in G.nodes()}
    for u, v, d in G.edges(data=True):
        if d.get("relation_type") == "DATA_FLOW":
            out_df[u] += 1
            in_df[v] += 1
    return in_df, out_df


def extract_node_features(G: nx.DiGraph, nodes: list) -> np.ndarray:
    """
    Zwraca macierz cech (len(nodes) × len(feature_names())) dla podanych węzłów.

    Parameters
    ----------
    G : nx.DiGraph
        Graf obserwowany (po usunięciu jobów).
    nodes : list
        Węzły (tabele) do opisania — w tej samej kolejności co zwracane wiersze.
    """
    flow_depths, flow_reaches, roles = _compute_flow_metadata(G)
    in_df, out_df = _df_degrees(G)

    rows = []
    for n in nodes:
        i = in_df.get(n, 0)
        o = out_df.get(n, 0)
        deg = G.degree(n) if G.has_node(n) else 0
        role = float(roles.get(n, 3))
        fd = float(flow_depths.get(n, 999))
        fr = float(flow_reaches.get(n, 999))

        # Sąsiedzi-joby przez DATA_FLOW (in i out) oraz ich obciążenie.
        job_neighbors = []
        n_field_children = 0
        if G.has_node(n):
            for _, w, d in G.out_edges(n, data=True):
                rt = d.get("relation_type")
                at = G.nodes[w].get("asset_type")
                if rt == "DATA_FLOW" and at == "Data Job":
                    job_neighbors.append(w)
                elif rt == "PARENT_CHILD" and at == "Data Field":
                    n_field_children += 1
            for u, _, d in G.in_edges(n, data=True):
                if (d.get("relation_type") == "DATA_FLOW"
                        and G.nodes[u].get("asset_type") == "Data Job"):
                    job_neighbors.append(u)

        if job_neighbors:
            avg_job_in = float(np.mean([in_df.get(j, 0) for j in job_neighbors]))
            avg_job_out = float(np.mean([out_df.get(j, 0) for j in job_neighbors]))
        else:
            avg_job_in = 0.0
            avg_job_out = 0.0

        rows.append([
            float(i), float(o), float(deg), role,
            fd, fr, fd + fr,
            1.0 if i == 0 else 0.0,
            1.0 if o == 0 else 0.0,
            float(n_field_children),
            float(len(set(job_neighbors))),
            avg_job_in, avg_job_out,
        ])

    return np.array(rows, dtype=float)
