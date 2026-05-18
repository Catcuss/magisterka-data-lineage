"""
Grid search wag ról dla RWPA na zbiorze walidacyjnym.

Szuka optymalnej kombinacji (w_intermediate, w_source, w_sink, w_isolated)
maksymalizującej średnie AUC-ROC na zbiorze walidacyjnym po wszystkich grafach.

Generuje:
  results/rwpa_grid_search.csv          — pełna tabela wyników per (wagi × graf)
  results/rwpa_best_weights.csv         — najlepsza kombinacja wag
  results/figures/rwpa_grid_heatmap.png — heatmap AUC-ROC (w_interm × w_source)

Użycie:
  python scripts/rwpa_grid_search.py
  python scripts/rwpa_grid_search.py --dlg 1 2 3 4    # szybki test
  python scripts/rwpa_grid_search.py --all            # wszystkie 18 grafów
"""

import argparse
import csv
import itertools
import sys
import time
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from data.loader import load_graph, DLG_IDS
from data.splitter import split_edges
from evaluation.metrics import tune_and_evaluate

_RESULTS_DIR = _PROJECT_ROOT / "results"
_FIGURES_DIR  = _PROJECT_ROOT / "results" / "figures"

DEFAULT_DLGS = [1, 2, 3, 4]

# ---------------------------------------------------------------------------
# Siatka wag do przeszukania
# ---------------------------------------------------------------------------

W_INTERMEDIATE = [1.5, 2.0, 3.0, 5.0, 8.0]
W_SOURCE       = [0.75, 1.0, 1.25, 1.5, 2.0]
W_SINK         = [1.0]          # punkt odniesienia — stały
W_ISOLATED     = [0.5]          # zawsze najniższy — stały

# Baseline: PA (wszystkie wagi = 1.0) i aktualne wagi z kodu
BASELINE_PA      = (1.0, 1.0, 1.0, 0.5)   # de facto PA bez isolated
BASELINE_CURRENT = (3.0, 1.5, 1.0, 0.5)   # wagi z heuristics.py


# ---------------------------------------------------------------------------
# RWPA z dowolnymi wagami (bez modyfikacji heuristics.py)
# ---------------------------------------------------------------------------

def _role_weight_custom(G, node,
                        w_interm: float, w_source: float,
                        w_sink: float, w_isolated: float) -> float:
    df_in  = sum(1 for _, _, d in G.in_edges(node,  data=True)
                 if d.get("relation_type") == "DATA_FLOW")
    df_out = sum(1 for _, _, d in G.out_edges(node, data=True)
                 if d.get("relation_type") == "DATA_FLOW")
    if df_in > 0 and df_out > 0:    return w_interm
    elif df_in == 0 and df_out > 0: return w_source
    elif df_in > 0 and df_out == 0: return w_sink
    return w_isolated


def score_rwpa_custom(G_train, edges, w_interm, w_source, w_sink, w_isolated):
    """Oblicza RWPA z podanymi wagami dla listy par krawędzi."""
    G_und = G_train.to_undirected()
    scores = []
    for u, v in edges:
        if not (G_train.has_node(u) and G_train.has_node(v)):
            scores.append(0.0)
            continue
        rw_u = _role_weight_custom(G_train, u, w_interm, w_source, w_sink, w_isolated)
        rw_v = _role_weight_custom(G_train, v, w_interm, w_source, w_sink, w_isolated)
        scores.append(rw_u * rw_v * float(G_und.degree(u) * G_und.degree(v)))
    return np.array(scores)


# ---------------------------------------------------------------------------
# Ewaluacja jednej kombinacji wag na jednym grafie
# ---------------------------------------------------------------------------

def eval_one_graph(dlg_id: str, seed: int,
                   w_interm: float, w_source: float,
                   w_sink: float, w_isolated: float) -> dict | None:
    G = load_graph(dlg_id)
    try:
        splits = split_edges(G, edge_type="DATA_FLOW",
                             test_ratio=0.2, val_ratio=0.2, seed=seed)
    except ValueError:
        return None

    G_train    = splits["G_train"]
    pos_val    = splits["pos_val"]
    neg_val    = splits["neg_val"]
    pos_test   = splits["pos_test"]
    neg_test   = splits["neg_test"]

    val_edges  = pos_val  + neg_val
    test_edges = pos_test + neg_test
    y_val  = np.array([1] * len(pos_val)  + [0] * len(neg_val))
    y_test = np.array([1] * len(pos_test) + [0] * len(neg_test))

    sc_val  = score_rwpa_custom(G_train, val_edges,  w_interm, w_source, w_sink, w_isolated)
    sc_test = score_rwpa_custom(G_train, test_edges, w_interm, w_source, w_sink, w_isolated)

    m = tune_and_evaluate(y_val, sc_val, y_test, sc_test)
    return m


# ---------------------------------------------------------------------------
# Główna pętla grid search
# ---------------------------------------------------------------------------

def run_grid_search(dlg_ids: list[str], seed: int) -> list[dict]:
    weight_combos = list(itertools.product(
        W_INTERMEDIATE, W_SOURCE, W_SINK, W_ISOLATED
    ))
    # Dodaj baseline PA i aktualne wagi jeśli nie ma ich w siatce
    for baseline in [BASELINE_PA, BASELINE_CURRENT]:
        if baseline not in weight_combos:
            weight_combos.append(baseline)

    total = len(weight_combos) * len(dlg_ids)
    print(f"Kombinacji wag: {len(weight_combos)}")
    print(f"Grafów:         {len(dlg_ids)}")
    print(f"Łącznych ewaluacji: {total}")
    print()

    all_rows = []
    done = 0
    t0 = time.time()

    for w_interm, w_source, w_sink, w_isolated in weight_combos:
        label = f"interm={w_interm} src={w_source} sink={w_sink} iso={w_isolated}"
        auc_rocs = []

        for dlg_id in dlg_ids:
            m = eval_one_graph(dlg_id, seed, w_interm, w_source, w_sink, w_isolated)
            done += 1
            if m is None:
                continue
            auc_val = m.get("auc_roc", float("nan"))
            auc_rocs.append(auc_val if not np.isnan(auc_val) else 0.0)
            all_rows.append({
                "w_intermediate": w_interm,
                "w_source":       w_source,
                "w_sink":         w_sink,
                "w_isolated":     w_isolated,
                "graph":          dlg_id,
                "auc_roc":        round(auc_val, 4),
                "f1":             round(m.get("f1", float("nan")), 4),
                "auc_pr":         round(m.get("auc_pr", float("nan")), 4),
            })

        mean_auc = np.mean(auc_rocs) if auc_rocs else 0.0
        elapsed  = time.time() - t0
        eta      = elapsed / done * (total - done) if done else 0
        print(f"  [{done:>4}/{total}]  {label:<42}  "
              f"mean_AUC={mean_auc:.4f}  "
              f"ETA {eta:.0f}s", flush=True)

    return all_rows


# ---------------------------------------------------------------------------
# Analiza wyników
# ---------------------------------------------------------------------------

def analyze_results(all_rows: list[dict]) -> dict:
    """Agreguje AUC-ROC per kombinacja wag i zwraca najlepsze."""
    from collections import defaultdict
    combo_aucs: dict = defaultdict(list)

    for r in all_rows:
        key = (r["w_intermediate"], r["w_source"], r["w_sink"], r["w_isolated"])
        v = r["auc_roc"]
        if not np.isnan(v):
            combo_aucs[key].append(v)

    summary = []
    for key, aucs in combo_aucs.items():
        summary.append({
            "w_intermediate": key[0],
            "w_source":       key[1],
            "w_sink":         key[2],
            "w_isolated":     key[3],
            "mean_auc_roc":   round(np.mean(aucs), 4),
            "median_auc_roc": round(np.median(aucs), 4),
            "n_graphs":       len(aucs),
        })

    summary.sort(key=lambda x: x["mean_auc_roc"], reverse=True)
    return summary


def print_top(summary: list[dict], n: int = 10) -> None:
    print("\n" + "=" * 75)
    print("TOP wyniki grid search (sortowane po mean AUC-ROC na val)")
    print(f"{'w_interm':>9} {'w_src':>6} {'w_sink':>7} {'w_iso':>6}  "
          f"{'mean_AUC':>9} {'median':>7} {'n':>3}")
    print("-" * 75)

    baseline_pa_key      = BASELINE_PA
    baseline_current_key = BASELINE_CURRENT

    for i, r in enumerate(summary[:n]):
        key = (r["w_intermediate"], r["w_source"], r["w_sink"], r["w_isolated"])
        tag = ""
        if key == baseline_pa_key:      tag = "  ← PA baseline"
        if key == baseline_current_key: tag = "  ← current RWPA"
        if i == 0:                      tag += " ** BEST"
        print(f"{r['w_intermediate']:>9} {r['w_source']:>6} "
              f"{r['w_sink']:>7} {r['w_isolated']:>6}  "
              f"{r['mean_auc_roc']:>9.4f} {r['median_auc_roc']:>7.4f} "
              f"{r['n_graphs']:>3}{tag}")

    print("=" * 75)

    # Porównanie best vs baseline
    best = summary[0]
    pa_row  = next((r for r in summary
                    if (r["w_intermediate"], r["w_source"],
                        r["w_sink"], r["w_isolated"]) == BASELINE_PA), None)
    cur_row = next((r for r in summary
                    if (r["w_intermediate"], r["w_source"],
                        r["w_sink"], r["w_isolated"]) == BASELINE_CURRENT), None)

    print("\nPorównanie wag:")
    if pa_row:
        delta_pa = best["mean_auc_roc"] - pa_row["mean_auc_roc"]
        print(f"  best vs PA baseline:      delta = {delta_pa:+.4f}")
    if cur_row:
        delta_cur = best["mean_auc_roc"] - cur_row["mean_auc_roc"]
        print(f"  best vs current (3.0/1.5): delta = {delta_cur:+.4f}")

    best_key = (best["w_intermediate"], best["w_source"],
                best["w_sink"], best["w_isolated"])
    if pa_row and best["mean_auc_roc"] <= pa_row["mean_auc_roc"] + 0.005:
        print("\n  WNIOSEK: żadna kombinacja wag nie poprawia PA o więcej niż 0.005 AUC.")
        print("  RWPA nie wnosi istotnego sygnału ponad PA na tym datasecie.")
        print("  Rekomendacja: zachowaj PA jako główną heurystykę,")
        print("  RWPA opisz jako negatywny wynik eksperymentalny.")
    else:
        print(f"\n  WNIOSEK: optymalne wagi ({best_key}) poprawiają AUC.")
        print(f"  Zaktualizuj _role_weight() w heuristics.py.")


def plot_heatmap(summary: list[dict], out_path: Path) -> None:
    """Heatmap mean AUC-ROC dla kombinacji w_intermediate × w_source."""
    # Tylko wiersze z w_sink=1.0, w_isolated=0.5
    rows = [r for r in summary
            if r["w_sink"] == 1.0 and r["w_isolated"] == 0.5]
    if not rows:
        return

    w_i_vals = sorted(set(r["w_intermediate"] for r in rows))
    w_s_vals = sorted(set(r["w_source"]       for r in rows))

    matrix = np.zeros((len(w_i_vals), len(w_s_vals)))
    lookup = {(r["w_intermediate"], r["w_source"]): r["mean_auc_roc"]
              for r in rows}

    for i, wi in enumerate(w_i_vals):
        for j, ws in enumerate(w_s_vals):
            matrix[i, j] = lookup.get((wi, ws), 0.0)

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto",
                   vmin=matrix.min() * 0.95, vmax=matrix.max() * 1.02)

    ax.set_xticks(range(len(w_s_vals)))
    ax.set_yticks(range(len(w_i_vals)))
    ax.set_xticklabels([str(w) for w in w_s_vals])
    ax.set_yticklabels([str(w) for w in w_i_vals])
    ax.set_xlabel("w_source")
    ax.set_ylabel("w_intermediate")
    ax.set_title("Grid search RWPA: mean AUC-ROC na zbiorze walidacyjnym\n"
                 "(w_sink=1.0 stały, w_isolated=0.5 stały)")

    # Wartości w komórkach
    for i in range(len(w_i_vals)):
        for j in range(len(w_s_vals)):
            val = matrix[i, j]
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=9, color="black" if val > matrix.mean() else "white")

    # Zaznacz current i best
    best_val = matrix.max()
    for i, wi in enumerate(w_i_vals):
        for j, ws in enumerate(w_s_vals):
            if matrix[i, j] == best_val:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                           fill=False, edgecolor="blue",
                                           linewidth=2.5, label="best"))
            if wi == BASELINE_CURRENT[0] and ws == BASELINE_CURRENT[1]:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                           fill=False, edgecolor="red",
                                           linewidth=2, linestyle="--",
                                           label="current (3.0/1.5)"))

    plt.colorbar(im, ax=ax, label="mean AUC-ROC")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Heatmap zapisany:  {out_path}")


def save_csvs(all_rows: list[dict], summary: list[dict]) -> None:
    # Szczegóły per (wagi × graf)
    detail_path = _RESULTS_DIR / "rwpa_grid_search.csv"
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["w_intermediate", "w_source", "w_sink", "w_isolated",
              "graph", "auc_roc", "f1", "auc_pr"]
    with detail_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Szczegóły CSV:     {detail_path}")

    # Podsumowanie + najlepsza kombinacja
    best_path = _RESULTS_DIR / "rwpa_best_weights.csv"
    sum_fields = ["w_intermediate", "w_source", "w_sink", "w_isolated",
                  "mean_auc_roc", "median_auc_roc", "n_graphs"]
    with best_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=sum_fields)
        writer.writeheader()
        writer.writerows(summary)
    print(f"Najlepsze wagi CSV: {best_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Grid search wag ról RWPA na zbiorze walidacyjnym"
    )
    parser.add_argument("--all",  action="store_true", help="wszystkie 18 grafów")
    parser.add_argument("--dlg",  nargs="+", type=int,  help="wybrane numery grafów")
    parser.add_argument("--seed", type=int, default=42,  help="ziarno losowości")
    args = parser.parse_args()

    if args.dlg:
        dlg_ids = [f"DLG{i}" for i in args.dlg]
    elif args.all:
        dlg_ids = DLG_IDS
    else:
        dlg_ids = [f"DLG{i}" for i in DEFAULT_DLGS]

    print(f"Grafy: {dlg_ids}")
    print(f"Seed:  {args.seed}")
    print()

    all_rows = run_grid_search(dlg_ids, args.seed)
    summary  = analyze_results(all_rows)

    print_top(summary, n=10)
    plot_heatmap(summary, _FIGURES_DIR / "rwpa_grid_heatmap.png")
    save_csvs(all_rows, summary)

    print(f"\nGotowe.")


if __name__ == "__main__":
    main()
