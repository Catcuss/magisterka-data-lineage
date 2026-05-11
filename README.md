# Odkrywanie zależności między obiektami w bazie danych

Praca magisterska — Maria Nowicka (151851)
Politechnika Poznańska, Wydział Informatyki i Telekomunikacji
Promotor: prof. dr hab. inż. Robert Wrembel, 2026

## Temat

Implementacja i ewaluacja algorytmów predykcji brakujących krawędzi
(*link prediction*) w grafach pochodzenia danych (*data lineage*). Problem
"broken lineage" — zerwanie ciągłości grafu zależności przez tabele
tymczasowe i UDF — sprowadzony do binarnej klasyfikacji krawędzi w
heterogenicznym grafie skierowanym.

## Środowisko

- Python 3.10
- Główne zależności: `networkx`, `numpy`, `scikit-learn`, `imbalanced-learn`,
  `lightgbm`, `node2vec`, `tensorflow` (Node2Vec+MLP), `pytest`.

```bash
pip install -r requirements.txt
pytest tests/                 # 55 testów jednostkowych
```

## Dataset

**DLG-DG-23** — 18 rzeczywistych grafów lineage z Huawei Cloud
(Chen et al., *An open dataset of data lineage graphs for data governance
research*, Visual Informatics 2024).

- Repozytorium: <https://github.com/csuvis/DataAssetGraphData>
- 18 grafów skierowanych, 278–17 085 węzłów
- Typy węzłów: `Data Table`, `Data Job`, `Data Field`
- Typy krawędzi: `DATA_FLOW` (Table↔Job), `PARENT_CHILD` (Table→Field)

Dataset nie jest częścią tego repozytorium (katalog `data/` w `.gitignore`).
Pobierz go w katalogu projektu:

```bash
git clone https://github.com/csuvis/DataAssetGraphData.git \
          data/raw/DataAssetGraphData
# następnie wypakuj Node.rar i Edge.rar do data/raw/DataAssetGraphData/extracted/
```

Skutek: `data/raw/DataAssetGraphData/.git/` jest świadomie pozostawiony —
pozwala zaciągnąć aktualizacje upstream przez `git -C data/raw/DataAssetGraphData pull`.

## Implementowane algorytmy

### Heurystyki grafowe (bezparametryczne)

| Algorytm | Plik | Uwagi |
|---|---|---|
| Common Neighbors, Jaccard, Adamic-Adar | `src/algorithms/heuristics.py` | Zawsze 0 w grafie bipartytowym Table↔Job — celowo pozostawione jako baseline |
| Preferential Attachment | `src/algorithms/heuristics.py` | Iloczyn stopni węzłów |
| L3 — paths length 3 | `src/algorithms/heuristics.py` | Wersja CN dla grafów bipartytowych |
| Katz | `src/algorithms/heuristics.py` | Skrócony szereg Neumanna |
| PPR — Personalized PageRank | `src/algorithms/heuristics.py` | Random walks z restartem |

### Klasyczne uczenie maszynowe

| Algorytm | Plik | Cechy |
|---|---|---|
| Random Forest | `src/algorithms/classical_ml.py` | 11 cech topologicznych (stopnie, CN, Jaccard, AA, długość ścieżki) |
| RUSBoost | `src/algorithms/classical_ml.py` | Boosting + Random Under-Sampling — bezpośrednio porównywalny z Boiński et al. (ISD2025) |
| LightGBM | `src/algorithms/classical_ml.py` | Gradient boosting na tych samych cechach |

### Embeddingi sieciowe

| Algorytm | Plik | Uwagi |
|---|---|---|
| Node2Vec + MLP | `src/algorithms/node2vec_ml.py` | Random-walk embeddings + binarny klasyfikator MLP nad konkatenacją wektorów (u,v) |

## Pipeline ewaluacji

1. **Podział danych:** 60/20/20 train/val/test (`src/data/splitter.py`,
   `src/data/scenario_splitter.py`).
2. **Strojenie progu:** próg binaryzacji dobierany na zbiorze walidacyjnym
   przez maksymalizację F1 (`tune_and_evaluate` w `src/evaluation/metrics.py`).
   Wszystkie algorytmy traktowane identycznie — brak przecieku informacji
   ze zbioru testowego.
3. **Metryki raportowane na teście:** Precision, Recall, F1, AUC-ROC, AUC-PR.
   AUC-ROC i AUC-PR są niezależne od progu i stanowią metryki główne.

### Scenariusze broken lineage

`src/data/scenario_splitter.py` implementuje trzy strukturalne podziały
krawędzi testowych (zamiast losowego splita):

- **A — Staging table removed:** ukryte krawędzie wyjściowe *intermediate*
  Table → Job (symuluje usunięcie tabeli tymczasowej).
- **B — UDF hidden source:** losowe 20% krawędzi wyjściowych *source*
  Table → Job (symuluje zależność ukrytą za UDF).
- **C — Sink dependency hidden:** krawędzie wejściowe Job → *sink* Table
  (symuluje ukrytą zależność do data martu).

## Uruchomienie eksperymentów

Skrypty wejściowe znajdują się w `scripts/` i uruchamiane są z katalogu głównego:

```bash
# Losowy split 60/20/20 — szybki podgląd na DLG1-DLG4
python scripts/run_experiments.py

# Wszystkie 18 grafów, scenariusze A/B/C
python scripts/run_scenario_experiments.py --all

# Wybrane grafy, tylko scenariusz A, bez ML
python scripts/run_scenario_experiments.py --dlg 1 4 --scenario A --no-ml
```

Wyniki zapisywane są w `results/`. Przekierowanie do pliku:

```bash
python scripts/run_scenario_experiments.py --all > results/wyniki.txt 2>&1
```

## Struktura projektu

```
MAGISTERKA/
├── data/
│   └── raw/DataAssetGraphData/        # Node.json, Edge.json (18 grafów)
├── docs/
│   ├── thesis_draft/                  # tekst pracy magisterskiej
│   ├── plan_dla_promotora.md
│   └── plan_kontynuacji.md
├── references/                        # PDF-y artykułów źródłowych
├── results/                           # wyniki eksperymentów (CSV/TXT)
├── src/
│   ├── data/                          # loader, splitter, scenario_splitter
│   ├── algorithms/                    # heuristics, classical_ml, node2vec_ml
│   └── evaluation/                    # metrics
├── scripts/
│   ├── run_experiments.py             # losowy split 60/20/20
│   ├── run_scenario_experiments.py    # scenariusze A/B/C
│   ├── build_and_run.py               # pełny pipeline (testy + wiz + eksp)
│   └── visualize_graphs.py            # wizualizacje grafów
├── tests/                             # testy jednostkowe (pytest)
├── requirements.txt
└── 151851_SLR.pdf                     # raport Systematic Literature Review
```

## Status pracy

- [x] Zadanie 1 — Systematic Literature Review (`151851_SLR.pdf`)
- [x] Zadanie 2 — Implementacja 3 grup algorytmów (heurystyki, ML, embedding)
- [x] Zadanie 3 — Zastosowanie do datasetu DLG-DG-23 (18 grafów)
- [x] Zadanie 4 — Testy jednostkowe (55 testów)
- [~] Zadanie 5 — Ewaluacja eksperymentalna (w toku)

## Reproducibility

Wszystkie eksperymenty są deterministyczne przy `--seed 42` (domyślny).
Negatywne próbki, splity train/val/test i inicjalizacja modeli używają
tego samego ziarna.
