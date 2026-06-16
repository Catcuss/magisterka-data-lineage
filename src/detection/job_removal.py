"""
Symulacja broken lineage przez usuwanie zadań (jobów) i wyznaczanie
zbioru zainfekowanych tabel (ground truth dla detekcji węzłów).

Mechanizm (zgodny z sugestią dr. Misiorka):
    Usunięcie całego joba J zrywa lineage tabel z nim incydentnych:
    - poprzedniki (tabele karmiące J: u --data_flow--> J),
    - następniki (tabele karmione przez J: J --data_flow--> w).
    Te tabele stają się "osierocone" — ich zależność przez J znika z grafu.

Z grafu G budujemy instancję klasyfikacji węzłów:
    - usuwamy podzbiór jobów łączących (in_df>0 ∧ out_df>0),
    - infected = suma tabel incydentnych do usuniętych jobów,
    - graf obserwowany G_obs = G bez usuniętych jobów (i ich krawędzi),
    - kandydaci = wszystkie tabele w G_obs; etykieta 1 = infected, 0 = clean.

Trudność: osierocona tabela-następnik po usunięciu joba wygląda jak prawdziwa
tabela źródłowa (in_df=0). Dlatego detekcja wymaga cech pozycji w DAG oraz
uczenia indukcyjnego (cross-graph), a nie tylko stopnia węzła.
"""

import random
from copy import deepcopy

import networkx as nx


def _df_neighbors(G: nx.DiGraph):
    """Zwraca (in_df, out_df) — liczniki krawędzi DATA_FLOW per węzeł."""
    in_df: dict = {n: 0 for n in G.nodes()}
    out_df: dict = {n: 0 for n in G.nodes()}
    for u, v, d in G.edges(data=True):
        if d.get("relation_type") == "DATA_FLOW":
            out_df[u] += 1
            in_df[v] += 1
    return in_df, out_df


def list_connecting_jobs(G: nx.DiGraph) -> list:
    """
    Joby łączące: Data Job z co najmniej jedną wejściową i jedną wyjściową
    krawędzią DATA_FLOW od/do tabel. Usunięcie takiego joba zrywa lineage
    po obu stronach.
    """
    in_df, out_df = _df_neighbors(G)
    jobs = []
    for n, data in G.nodes(data=True):
        if data.get("asset_type") != "Data Job":
            continue
        if in_df[n] > 0 and out_df[n] > 0:
            jobs.append(n)
    return jobs


def incident_tables(G: nx.DiGraph, job, side: str = "both") -> set:
    """
    Tabele incydentne do joba przez krawędzie DATA_FLOW.

    side : "both" | "pred" | "succ"
        "pred" — tabele karmiące job (u->job), "succ" — karmione (job->w).
    """
    tables: set = set()
    if side in ("both", "pred"):
        for u, _, d in G.in_edges(job, data=True):
            if (d.get("relation_type") == "DATA_FLOW"
                    and G.nodes[u].get("asset_type") == "Data Table"):
                tables.add(u)
    if side in ("both", "succ"):
        for _, w, d in G.out_edges(job, data=True):
            if (d.get("relation_type") == "DATA_FLOW"
                    and G.nodes[w].get("asset_type") == "Data Table"):
                tables.add(w)
    return tables


def build_node_dataset(
    G: nx.DiGraph,
    removal_ratio: float = 0.2,
    seed: int = 42,
    side: str = "both",
) -> dict:
    """
    Buduje instancję klasyfikacji węzłów przez usunięcie podzbioru jobów łączących.

    Parameters
    ----------
    G : nx.DiGraph
        Oryginalny (pełny) graf lineage. Nie jest modyfikowany.
    removal_ratio : float
        Udział jobów łączących do usunięcia (symulacja broken lineage).
    seed : int
        Ziarno losowości (powtarzalność wyboru jobów).
    side : str
        Która strona joba liczy się jako infected: "both" | "pred" | "succ".

    Returns
    -------
    dict z kluczami:
        G_obs        — graf po usunięciu wybranych jobów,
        candidates   — lista węzłów Data Table (kandydaci do oceny),
        labels       — list[int] zgodny z candidates (1 = infected, 0 = clean),
        removed_jobs — lista usuniętych jobów,
        infected     — set zainfekowanych tabel,
        n_infected   — liczba zainfekowanych tabel.

    Raises
    ------
    ValueError
        Gdy graf nie zawiera jobów łączących lub brak tabel-kandydatów.
    """
    if not 0.0 < removal_ratio <= 1.0:
        raise ValueError("removal_ratio musi być w (0, 1].")

    rng = random.Random(seed)
    connecting = list_connecting_jobs(G)
    if not connecting:
        raise ValueError("Graf nie zawiera jobów łączących (in_df>0 ∧ out_df>0).")

    rng.shuffle(connecting)
    n_remove = max(1, round(len(connecting) * removal_ratio))
    removed_jobs = connecting[:n_remove]

    infected: set = set()
    for job in removed_jobs:
        infected |= incident_tables(G, job, side=side)

    G_obs = deepcopy(G)
    G_obs.remove_nodes_from(removed_jobs)

    candidates = [
        n for n, data in G_obs.nodes(data=True)
        if data.get("asset_type") == "Data Table"
    ]
    if not candidates:
        raise ValueError("Brak tabel-kandydatów po usunięciu jobów.")

    infected_in_obs = infected & set(candidates)
    labels = [1 if n in infected_in_obs else 0 for n in candidates]

    return {
        "G_obs":        G_obs,
        "candidates":   candidates,
        "labels":       labels,
        "removed_jobs": removed_jobs,
        "infected":     infected_in_obs,
        "n_infected":   len(infected_in_obs),
    }


def inductive_split(graph_ids: list, test_ids: list) -> tuple[list, list]:
    """
    Dzieli identyfikatory grafów na zbiór treningowy i testowy (cross-graph).
    Zbiory są rozłączne — żaden graf testowy nie jest widziany w treningu.
    """
    test = [g for g in graph_ids if g in set(test_ids)]
    train = [g for g in graph_ids if g not in set(test_ids)]
    return train, test
