"""
Adapter zewnętrznego grafu lineage z repozytorium Dutkiewicz–Misiorek–Wrembel
(github.com/dudenzz/lineage) do formatu grafu używanego w tej pracy.

Cel: umożliwić TEST cross-dataset — model wytrenowany na DLG-DG-23 ocenia się
na grafie zbudowanym z zupełnie innego źródła (baza Northwind + syntetyczne
scenariusze SQL), aby sprawdzić przenośność metody poza zbiór treningowy.

Źródło danych
-------------
Plik ``DataLineage.csv`` zawiera lineage NA POZIOMIE WIERSZY:
    SourceName;SourcePKName;SourceID;TargetName;TargetPKName;TargetID
gdzie (SourceName, SourcePKName=SourceID) — wartość źródłowa, a
(TargetName, TargetPKName=TargetID) — wartość docelowa, która z niej powstała.

Mapowanie na model tabela–zadanie–DATA_FLOW
-------------------------------------------
Agregujemy wiersze do poziomu TABEL: dla każdej tabeli docelowej T tworzymy
węzeł-zadanie ``job::T`` karmiony przez wszystkie tabele źródłowe, które
przyczyniły się do T, i produkujący T:
    S_i --DATA_FLOW--> job::T --DATA_FLOW--> T
Dzięki temu powstaje dwudzielny, skierowany graf DAG (Data Table / Data Job),
zgodny z konwencją loadera DLG-DG-23 (asset_type, relation_type). Kolumny
kluczy (SourcePKName / TargetPKName) dodajemy jako węzły ``Data Field``
połączone krawędzią PARENT_CHILD (zasila cechę ``n_field_children``).

Konwencje (identyczne jak w src/data/loader.py):
    asset_type   ∈ {"Data Table", "Data Job", "Data Field"}
    relation_type ∈ {"DATA_FLOW", "PARENT_CHILD"}
    DATA_FLOW: Table -> Job (tabela karmi zadanie), Job -> Table (zadanie produkuje).

Ograniczenie: brak dostępu do pełnych schematów tabel — pola ograniczono do
kolumn kluczy występujących w lineage. To realistyczny element domain-shiftu
(w DLG-DG-23 pól jest więcej), nie wpływający na główny sygnał topologiczny.
"""

from pathlib import Path

import networkx as nx

# Domyślna lokalizacja skopiowanych danych źródłowych.
_DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "external" / "dutkiewicz"
_DEFAULT_CSVS = [_DEFAULT_DIR / "train_DataLineage.csv",
                 _DEFAULT_DIR / "test_DataLineage.csv"]


def _parse_lineage_rows(path: Path):
    """Zwraca listę krotek (src_table, src_pk, tgt_table, tgt_pk) z DataLineage.csv."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    rows = []
    # Wiersz 0 — nagłówek, wiersz 1 — adnotacje typów (<class '...'>); pomijamy oba.
    for line in lines[2:]:
        parts = line.split(";")
        if len(parts) < 6:
            continue
        src, src_pk = parts[0].strip(), parts[1].strip()
        tgt, tgt_pk = parts[3].strip(), parts[4].strip()
        if src and tgt:
            rows.append((src, src_pk, tgt, tgt_pk))
    return rows


def build_dutkiewicz_graph(csv_paths=None, name: str = "DUT",
                           add_fields: bool = True) -> nx.DiGraph:
    """
    Buduje jeden graf lineage z jednego lub wielu plików DataLineage.csv.

    Parameters
    ----------
    csv_paths : list[Path] | None
        Ścieżki do plików DataLineage.csv. None → train + test z data/external/dutkiewicz.
    name : str
        Nazwa grafu (atrybut G.graph["name"]).
    add_fields : bool
        Czy dodać węzły Data Field (kolumny kluczy) i krawędzie PARENT_CHILD.

    Returns
    -------
    nx.DiGraph
        Graf zgodny z konwencją loadera DLG-DG-23.
    """
    if csv_paths is None:
        csv_paths = _DEFAULT_CSVS
    csv_paths = [Path(p) for p in csv_paths]

    # Agregacja do poziomu tabel: target -> zbiór źródeł; oraz kolumny kluczy per tabela.
    tgt_to_srcs: dict[str, set] = {}
    table_pks: dict[str, set] = {}
    for p in csv_paths:
        for src, src_pk, tgt, tgt_pk in _parse_lineage_rows(p):
            tgt_to_srcs.setdefault(tgt, set()).add(src)
            if src_pk:
                table_pks.setdefault(src, set()).add(src_pk)
            if tgt_pk:
                table_pks.setdefault(tgt, set()).add(tgt_pk)

    all_tables = set(tgt_to_srcs) | {s for srcs in tgt_to_srcs.values() for s in srcs}

    G = nx.DiGraph(name=name)

    for t in all_tables:
        G.add_node(t, asset_type="Data Table")

    # Jedno zadanie na tabelę docelową: źródła -> job -> target.
    for tgt, srcs in tgt_to_srcs.items():
        job = f"job::{tgt}"
        G.add_node(job, asset_type="Data Job")
        for s in srcs:
            G.add_edge(s, job, relation_type="DATA_FLOW", relation_id=f"{s}->{job}")
        G.add_edge(job, tgt, relation_type="DATA_FLOW", relation_id=f"{job}->{tgt}")

    if add_fields:
        for table, pks in table_pks.items():
            for col in pks:
                field = f"{table}::field::{col}"
                G.add_node(field, asset_type="Data Field")
                G.add_edge(table, field, relation_type="PARENT_CHILD",
                           relation_id=f"{table}->{field}")

    return G


def summary(G: nx.DiGraph) -> dict:
    """Zwraca liczności typów węzłów/krawędzi (do raportu)."""
    nt: dict = {}
    for _, d in G.nodes(data=True):
        nt[d.get("asset_type", "?")] = nt.get(d.get("asset_type", "?"), 0) + 1
    et: dict = {}
    for _, _, d in G.edges(data=True):
        et[d.get("relation_type", "?")] = et.get(d.get("relation_type", "?"), 0) + 1
    return {"name": G.graph.get("name"), "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(), "node_types": nt, "edge_types": et}


if __name__ == "__main__":
    G = build_dutkiewicz_graph()
    print(summary(G))
