"""
Tabela zbiorcza symulacji broken lineage (sekcja 3.4 pracy).

Dla każdej wartości removal_ratio raportuje, ile zadań łączących jest usuwanych,
ile tabel staje się zainfekowanych i jaki odsetek tych pozytywów to tabele
w pełni izolowane — czyli takie, które trywialna reguła „izolowana => chora"
rozpoznaje bez żadnego uczenia (por. kontrola przecieku, sekcja 3.5).

Liczby uśredniane po 18 grafach i po seedach biegu kanonicznego (42, 43, 44).

Użycie:
    python scripts/tabela_symulacji.py
"""

import sys
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph                                   # noqa: E402
from detection.job_removal import (                                  # noqa: E402
    build_node_dataset, list_connecting_jobs,
)

RATIOS = [0.05, 0.10, 0.20, 0.30]
SEEDS = [42, 43, 44]
DLGS = list(range(1, 19))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in DLGS}
    n_jobs = {g: len(list_connecting_jobs(G)) for g, G in graphs.items()}
    print(f"Zadań łączących ogółem w 18 grafach: {sum(n_jobs.values())} "
          f"(od {min(n_jobs.values())} do {max(n_jobs.values())} na graf)\n")

    rows = []
    for ratio in RATIOS:
        removed, infected, isolated, candidates = [], [], [], []
        for gid, G in graphs.items():
            for seed in SEEDS:
                try:
                    # Wariant napompowany: izolowane pozostają w puli kandydatów,
                    # inaczej nie dałoby się policzyć ich udziału wśród pozytywów.
                    ds = build_node_dataset(G, ratio, seed, "both",
                                            exclude_isolated=False)
                except ValueError:
                    continue
                labels = np.asarray(ds["labels"])
                cands = ds["candidates"]
                G_obs = ds["G_obs"]

                n_iso_pos = 0
                for node, lab in zip(cands, labels):
                    if not lab:
                        continue
                    deg = sum(1 for *_, d in G_obs.in_edges(node, data=True)
                              if d.get("relation_type") == "DATA_FLOW")
                    deg += sum(1 for *_, d in G_obs.out_edges(node, data=True)
                               if d.get("relation_type") == "DATA_FLOW")
                    if deg == 0:
                        n_iso_pos += 1

                removed.append(len(ds["removed_jobs"]))
                infected.append(int(labels.sum()))
                isolated.append(n_iso_pos)
                candidates.append(len(cands))

        tot_inf, tot_iso = sum(infected), sum(isolated)
        rows.append({
            "ratio": ratio,
            "usuniete": np.mean(removed),
            "infected": np.mean(infected),
            "kandydaci": np.mean(candidates),
            "udzial_poz": 100 * sum(infected) / sum(candidates),
            "udzial_izol": 100 * tot_iso / tot_inf if tot_inf else 0.0,
        })

    print(f"{'ratio':>7}{'usun. zadań':>13}{'zainfekowanych':>16}"
          f"{'kandydatów':>12}{'% pozytywów':>13}{'% izolow. poz.':>16}")
    print("-" * 77)
    for r in rows:
        print(f"{r['ratio']:>7.2f}{r['usuniete']:>13.1f}{r['infected']:>16.1f}"
              f"{r['kandydaci']:>12.1f}{r['udzial_poz']:>13.1f}"
              f"{r['udzial_izol']:>16.1f}")

    tex = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Charakterystyka symulacji broken lineage w~zależności "
        r"od~parametru \texttt{removal\_ratio}. Wartości uśrednione po~18~grafach "
        r"i~trzech ziarnach losowości. Ostatnia kolumna — odsetek tabel "
        r"zainfekowanych, które utraciły \emph{wszystkie} krawędzie przepływu "
        r"danych i~są~rozpoznawalne trywialną regułą izolacji "
        r"(por.~sekcja~\ref{sec:exclude-isolated}).}",
        r"\label{tab:symulacja}",
        r"\begin{tabular}{ccccc}",
        r"\toprule",
        r"\texttt{removal\_ratio} & \textbf{Usuniętych} & "
        r"\textbf{Tabel} & \textbf{Udział} & \textbf{Pozytywów} \\",
        r" & \textbf{zadań} & \textbf{zainfekowanych} & "
        r"\textbf{pozytywów} & \textbf{izolowanych} \\",
        r"\midrule",
    ]
    def pl(value: float, digits: int = 1) -> str:
        """Liczba z przecinkiem dziesiętnym (konwencja polska)."""
        return f"{value:.{digits}f}".replace(".", "{,}")

    for r in rows:
        tex.append(
            f"0{{,}}{int(r['ratio'] * 100):02d} & {pl(r['usuniete'])} & "
            f"{pl(r['infected'])} & {pl(r['udzial_poz'])}\\% & "
            f"{pl(r['udzial_izol'])}\\% \\\\"
        )
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    out = _PROJECT_ROOT / "results" / "tabela_symulacji.tex"
    out.write_text("\n".join(tex), encoding="utf-8")
    print(f"\nZapisano: {out}")


if __name__ == "__main__":
    main()
