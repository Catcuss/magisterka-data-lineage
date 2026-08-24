"""
Analiza poboczna: zachowanie detektora na zewnętrznym grafie DUT w wielu
konfiguracjach (przegląd removal_ratio × wariant izolacji × dużo powtórzeń).

Trening WYŁĄCZNIE na małych+średnich grafach DLG-DG-23 (jak w schemacie scale),
ewaluacja TYLKO na grafie DUT (Dutkiewicz, train+test scalone) — dzięki temu
bieg jest szybki (pomijamy kosztowną ekstrakcję cech na dużych grafach DLG).

Wynik zapisywany jest do pliku pobocznego results/cross_dataset_dut_sweep.md.

Użycie:
    python src/detection/run_cross_dataset_dut_sweep.py
"""

import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph
from data.dutkiewicz_adapter import build_dutkiewicz_graph, summary
from detection.job_removal import build_node_dataset
from detection.node_metrics import node_detection_metrics
from detection.run_scale_generalization import size_class
from detection.run_detection_experiments import (
    _heuristic_score, _make_model, HEUR_NAMES, FIT_MODELS,
)

ALL_DLGS = list(range(1, 19))
RATIOS = [0.2, 0.3, 0.4]
REPEATS = 25
ALGOS = HEUR_NAMES + FIT_MODELS


def eval_config(dlg_graphs: dict, G_dut, ratio: float, exclude_isolated: bool):
    """Zwraca dict: algorytm -> uśrednione metryki na DUT + śr. #infected."""
    acc = {a: {"auc_roc": [], "auc_pr": [], "precision_at_k": [], "brier": []}
           for a in ALGOS}
    infected_counts = []
    for i in range(REPEATS):
        seed = 42 + i
        # Trening: małe+średnie DLG przy tym samym ratio/wariancie.
        train_pool = []
        for gid, G in dlg_graphs.items():
            if size_class(G.number_of_nodes()) == "duży":
                continue
            try:
                train_pool.append(build_node_dataset(
                    G, ratio, seed, "both", exclude_isolated=exclude_isolated))
            except ValueError:
                pass
        try:
            ds = build_node_dataset(G_dut, ratio, seed, "both",
                                    exclude_isolated=exclude_isolated)
        except ValueError:
            continue
        infected_counts.append(ds["n_infected"])
        if ds["n_infected"] == 0 or ds["n_infected"] == len(ds["candidates"]):
            continue

        fitted = {}
        for name in FIT_MODELS:
            try:
                fitted[name] = _make_model(name, seed).fit(train_pool)
            except (ValueError, ImportError):
                pass
        for name in HEUR_NAMES:
            m = node_detection_metrics(ds["labels"], _heuristic_score(name, ds))
            for k in acc[name]:
                if not np.isnan(m[k]):
                    acc[name][k].append(m[k])
        for name, clf in fitted.items():
            m = node_detection_metrics(ds["labels"], clf.score(ds))
            for k in acc[name]:
                if not np.isnan(m[k]):
                    acc[name][k].append(m[k])

    out = {}
    for a in ALGOS:
        out[a] = {k: (float(np.mean(v)) if v else float("nan"))
                  for k, v in acc[a].items()}
    return out, (float(np.mean(infected_counts)) if infected_counts else float("nan"))


def main():
    t0 = time.time()
    dlg_graphs = {f"DLG{i}": load_graph(f"DLG{i}") for i in ALL_DLGS}
    G_dut = build_dutkiewicz_graph()
    s = summary(G_dut)

    lines = []
    lines.append("# Test cross-dataset — przegląd konfiguracji na grafie DUT\n")
    lines.append("Analiza poboczna (nie wchodzi do głównej tabeli pracy). Trening: "
                 "małe+średnie DLG-DG-23; ewaluacja: graf zewnętrzny DUT (Dutkiewicz, "
                 "train+test scalone).\n")
    lines.append(f"- Graf DUT: {s['node_types']}, krawędzie {s['edge_types']}")
    lines.append(f"- Powtórzenia na konfigurację: {REPEATS}; removal_ratio ∈ {RATIOS}\n")

    for exclude_isolated in (False, True):
        variant = "uczciwy (exclude_isolated)" if exclude_isolated else "napompowany"
        lines.append(f"\n## Wariant: {variant}\n")
        for ratio in RATIOS:
            print(f"[{variant}] ratio={ratio} ...", flush=True)
            res, inf = eval_config(dlg_graphs, G_dut, ratio, exclude_isolated)
            lines.append(f"### removal_ratio = {ratio}  (śr. #infected ≈ {inf:.1f})\n")
            lines.append("| Metoda | AUC-ROC | AUC-PR | P@k | Brier |")
            lines.append("|---|---|---|---|---|")
            for a in ALGOS:
                r = res[a]
                def f(x):
                    return f"{x:.3f}" if not np.isnan(x) else "—"
                lines.append(f"| {a} | {f(r['auc_roc'])} | {f(r['auc_pr'])} "
                             f"| {f(r['precision_at_k'])} | {f(r['brier'])} |")
            lines.append("")

    lines.append(f"\n_Wygenerowano skryptem run_cross_dataset_dut_sweep.py, "
                 f"czas {time.time()-t0:.0f}s._\n")

    out_path = _PROJECT_ROOT / "results" / "cross_dataset_dut_sweep.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nZapisano: {out_path}")
    print(f"Czas: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
