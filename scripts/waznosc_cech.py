"""
Ważność cech detektora LineageDetector (sekcja 4.10 pracy).

Liczona metodą permutacyjną: dla każdej cechy jej wartości są losowo
przestawiane w zbiorze testowym, a spadek AUC-ROC mierzy, ile model tracił
bez tej informacji. W odróżnieniu od ważności wbudowanej w drzewa
(oparte na liczbie podziałów) metoda permutacyjna nie faworyzuje cech
o wielu unikatowych wartościach i mierzy wpływ na faktycznie używaną metrykę.

Protokół jak w biegu kanonicznym: leave-one-graph-out po grafach
wiarygodnych, uśrednienie po grafach i seedach.

Użycie:
    python scripts/waznosc_cech.py
"""

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph                                   # noqa: E402
from detection.completeness import feature_names as compl_names      # noqa: E402
from detection.lineage_detector import LineageHealthDetector         # noqa: E402
from detection.node_features import feature_names                    # noqa: E402
from detection.run_detection_experiments import (                    # noqa: E402
    ALL_DLGS, MIN_POS, build_datasets,
)

SEEDS = [42, 43, 44]
N_REPEATS = 10          # liczba permutacji na cechę
RATIO = 0.10

PL_NAMES = {
    "in_df": "in\\_df — wejściowe krawędzie DATA\\_FLOW",
    "out_df": "out\\_df — wyjściowe krawędzie DATA\\_FLOW",
    "degree": "degree — stopień całkowity",
    "role": "role — rola w~przepływie",
    "flow_depth": "flow\\_depth — głębokość w~DAG",
    "flow_reach": "flow\\_reach — zasięg w~dół DAG",
    "depth_plus_reach": "depth\\_plus\\_reach — długość ścieżki",
    "is_root": "is\\_root — brak producenta",
    "is_leaf": "is\\_leaf — brak konsumenta",
    "n_field_children": "n\\_field\\_children — liczba pól tabeli",
    "n_job_neighbors": "n\\_job\\_neighbors — liczba sąsiednich zadań",
    "avg_job_in_df": "avg\\_job\\_in\\_df — śr.\\ stopień wej.\\ zadań",
    "avg_job_out_df": "avg\\_job\\_out\\_df — śr.\\ stopień wyj.\\ zadań",
    "peer_producer_score": "peer\\_producer\\_score\\textsuperscript{*}",
    "peer_consumer_score": "peer\\_consumer\\_score\\textsuperscript{*}",
    "completeness_anomaly": "completeness\\_anomaly\\textsuperscript{*}",
}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    names = feature_names() + compl_names()
    print(f"Cech: {len(names)} (13 topologicznych + "
          f"{len(compl_names())} kompletności)\n")

    graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in ALL_DLGS}
    drops = {n: [] for n in names}
    rng = np.random.default_rng(0)

    for seed in SEEDS:
        print(f"Seed {seed}...", flush=True)
        datasets = build_datasets(graphs, RATIO, seed, "both",
                                  exclude_isolated=True)
        gids = list(datasets)
        for test_g in gids:
            ds = datasets[test_g]
            y = np.asarray(ds["labels"])
            if y.sum() < MIN_POS or y.sum() == len(y):
                continue

            det = LineageHealthDetector(seed=seed).fit(
                [datasets[g] for g in gids if g != test_g])
            X = det._features(ds["G_obs"], ds["candidates"])
            base = roc_auc_score(y, det.model.predict_proba(X)[:, 1])

            for j, name in enumerate(names):
                losses = []
                for _ in range(N_REPEATS):
                    Xp = X.copy()
                    rng.shuffle(Xp[:, j])
                    losses.append(
                        base - roc_auc_score(y, det.model.predict_proba(Xp)[:, 1]))
                drops[name].append(float(np.mean(losses)))

    rows = sorted(((n, float(np.mean(v)), float(np.std(v)))
                   for n, v in drops.items() if v),
                  key=lambda r: -r[1])

    print(f"\n{'Cecha':<26}{'spadek AUC-ROC':>16}{'odch. std':>12}")
    print("-" * 54)
    for name, mean, std in rows:
        print(f"{name:<26}{mean:>+16.4f}{std:>12.4f}")

    tex = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Ważność cech detektora LineageDetector mierzona metodą "
        r"permutacyjną: średni spadek AUC-ROC po~losowym przestawieniu "
        r"wartości cechy (10~permutacji, protokół indukcyjny, grafy "
        r"wiarygodne). Gwiazdka — cecha wnoszona przez~autorski score "
        r"kompletności.}",
        r"\label{tab:waznosc}",
        r"\small",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"\textbf{Cecha} & \textbf{Spadek AUC-ROC} & "
        r"\textbf{Odch.\ std} \\",
        r"\midrule",
    ]
    def pl(value: float, sign: bool = False) -> str:
        """Liczba z przecinkiem dziesiętnym; podmiana tylko w liczbie."""
        fmt = f"{value:+.4f}" if sign else f"{value:.4f}"
        return fmt.replace(".", "{,}")

    for name, mean, std in rows:
        label = PL_NAMES.get(name, name.replace("_", r"\_"))
        tex.append(f"{label} & ${pl(mean, sign=True)}$ & {pl(std)} " + r"\\")
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    out = _PROJECT_ROOT / "results" / "tabela_waznosc_cech.tex"
    out.write_text("\n".join(tex), encoding="utf-8")
    print(f"\nZapisano: {out}")


if __name__ == "__main__":
    main()
