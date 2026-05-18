"""
Parsuje wyniki_scenariusze.txt i generuje wykres do prezentacji.

Wynik:
  results/figures/prezentacja_scenariusze.png

Użycie:
  python scripts/generate_scenario_charts.py
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TXT  = _PROJECT_ROOT / "results" / "wyniki_scenariusze.txt"
_OUT  = _PROJECT_ROOT / "results" / "figures"
_OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

ALGO_LABELS = {
    "preferential_attachment": "PA",
    "l3":           "L3",
    "katz":         "Katz",
    "ppr":          "PPR",
    "RandomForest": "RF-11",
    "RUSBoost":     "RUSBoost",
    "LightGBM":     "LightGBM",
    "Node2Vec+MLP": "Node2Vec+MLP",
}

ALGO_COLORS = {
    "PA":           "#1976D2",
    "L3":           "#1976D2",
    "Katz":         "#1976D2",
    "PPR":          "#1976D2",
    "RF-11":        "#388E3C",
    "RUSBoost":     "#388E3C",
    "LightGBM":     "#388E3C",
    "Node2Vec+MLP": "#E64A19",
}

ALGO_ORDER = ["PA", "L3", "Katz", "PPR",
              "RF-11", "RUSBoost", "LightGBM", "Node2Vec+MLP"]


def decode_spaced(text: str) -> str:
    """Usuwa spacje wstawione między każdy znak (artefakt UTF-16 czytanego jako ASCII)."""
    return re.sub(r'(?<=[A-Za-z0-9_.+\-])\s(?=[A-Za-z0-9_.+\-])', '', text)


def parse_file(path: Path) -> list[dict]:
    """
    Czyta plik UTF-16 z wynikami scenariuszowymi.
    Zwraca listę słowników: {scenario, graph, algorithm, auc_roc, f1}
    """
    raw = path.read_text(encoding="utf-16", errors="replace")

    records        = []
    current_sc     = None
    scenario_pat   = re.compile(r'SCENARIUSZ\s+([ABC])\s*:', re.IGNORECASE)

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        m = scenario_pat.search(line)
        if m:
            current_sc = m.group(1).upper()
            continue

        if current_sc is None:
            continue

        # Pola oddzielone co najmniej 2 spacjami
        # Format: DLG1  298  21  3  algorytm  P  R  F1  AUC-ROC  AUC-PR
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) < 9:
            continue
        if not parts[0].startswith("DLG"):
            continue

        graph = parts[0].strip()
        algo  = parts[4].strip()  # index 4: po graph, nodes, tr+, te+
        label = ALGO_LABELS.get(algo)
        if label is None:
            continue

        try:
            vals    = parts[5:]  # P R F1 AUC-ROC AUC-PR
            f1_str  = vals[2] if len(vals) > 2 else "nan"
            auc_str = vals[3] if len(vals) > 3 else "nan"
            auc = float(auc_str) if auc_str.strip() != "nan" else float("nan")
            f1  = float(f1_str)  if f1_str.strip()  != "nan" else float("nan")
        except (ValueError, IndexError):
            continue

        records.append({
            "scenario":  current_sc,
            "graph":     graph,
            "algorithm": label,
            "auc_roc":   auc,
            "f1":        f1,
        })

    return records


# ---------------------------------------------------------------------------
# Wykres: grouped bar chart — mean AUC-ROC per algorytm × scenariusz
# ---------------------------------------------------------------------------

def plot_scenarios(records: list[dict]) -> None:
    if not records:
        print("Brak danych do wykresu!")
        return

    # Agregacja: mean AUC-ROC per (algo, scenario)
    sums   = defaultdict(list)
    for r in records:
        if not np.isnan(r["auc_roc"]):
            sums[(r["algorithm"], r["scenario"])].append(r["auc_roc"])

    algos = [a for a in ALGO_ORDER
             if any((a, sc) in sums for sc in "ABC")]
    scenarios = ["A", "B", "C"]
    sc_labels = {
        "A": "A — staging\n(umiarkowany)",
        "B": "B — UDF\n(najłatwiejszy)",
        "C": "C — sink\n(najtrudniejszy)",
    }
    sc_colors  = {"A": "#C62828", "B": "#E65100", "C": "#2E7D32"}
    sc_hatches = {"A": "//",      "B": "..",       "C": ""}

    n_algos = len(algos)
    n_sc    = len(scenarios)
    x       = np.arange(n_algos)
    width   = 0.22

    fig, ax = plt.subplots(figsize=(13, 5.5))

    for i, sc in enumerate(scenarios):
        means = []
        for algo in algos:
            vals = sums.get((algo, sc), [])
            means.append(np.mean(vals) if vals else float("nan"))

        offset = (i - 1) * width
        bars = ax.bar(x + offset, means, width,
                      color=sc_colors[sc], alpha=0.82,
                      hatch=sc_hatches[sc], edgecolor="white",
                      linewidth=1.2, label=sc_labels[sc], zorder=3)

        for bar, val in zip(bars, means):
            if not np.isnan(val):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.008,
                        f"{val:.2f}", ha="center", va="bottom",
                        fontsize=6.5, color="#333", zorder=4)

    # Linia AUC=0.5
    ax.axhline(0.5, color="black", linestyle="--",
               linewidth=1.0, alpha=0.5, zorder=2)
    ax.text(n_algos - 0.4, 0.502, "0.5 (losowe)", fontsize=7,
            color="gray", va="bottom")

    ax.set_xticks(x)
    ax.set_xticklabels([a for a in algos], fontsize=9)
    ax.set_ylabel("Mean AUC-ROC", fontsize=10)
    ax.set_ylim(0, 0.82)
    ax.set_title("Wyniki scenariuszowe — mean AUC-ROC per algorytm\n"
                 "(18 grafów DLG-DG-23, scenariusze A / B / C)",
                 fontsize=11)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.92)
    ax.grid(axis="y", alpha=0.3, zorder=1)

    # Separator heurystyki / ML / Node2Vec
    ax.axvline(3.5,  color="#CFD8DC", linewidth=1.5, zorder=2)
    ax.axvline(6.5,  color="#CFD8DC", linewidth=1.5, zorder=2)
    ax.text(1.5,  0.78, "Heurystyki",  ha="center", fontsize=8,
            color="#546E7A")
    ax.text(5.0,  0.78, "Klasyczne ML", ha="center", fontsize=8,
            color="#546E7A")
    ax.text(7.0,  0.78, "Node2Vec",    ha="center", fontsize=8,
            color="#546E7A")

    plt.tight_layout()
    out = _OUT / "prezentacja_scenariusze.png"
    plt.savefig(out, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Zapisano: {out}")


# ---------------------------------------------------------------------------
# Druk podsumowania w konsoli
# ---------------------------------------------------------------------------

def print_summary(records: list[dict]) -> None:
    from collections import defaultdict
    sums = defaultdict(list)
    for r in records:
        if not np.isnan(r["auc_roc"]):
            sums[(r["scenario"], r["algorithm"])].append(r["auc_roc"])

    print(f"\n{'Scenariusz':<5} {'Algorytm':<16} {'mean AUC-ROC':>12} {'n':>4}")
    print("-" * 42)
    for sc in "ABC":
        for algo in ALGO_ORDER:
            vals = sums.get((sc, algo), [])
            if vals:
                print(f"{sc:<5} {algo:<16} {np.mean(vals):>12.3f} {len(vals):>4}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Wczytuję: {_TXT}")
    records = parse_file(_TXT)
    print(f"Sparsowano {len(records)} wierszy")

    if not records:
        print("Brak danych — sprawdz plik")
        sys.exit(1)

    print_summary(records)
    plot_scenarios(records)
    print("Gotowe.")


if __name__ == "__main__":
    main()
