# Odkrywanie zależności między obiektami w bazie danych

Praca magisterska — Maria Nowicka (151851)
Politechnika Poznańska, Wydział Informatyki i Telekomunikacji
Promotor: prof. dr hab. inż. Robert Wrembel, 2026

## Temat

Wykrywanie zjawiska *broken lineage* — zerwania ciągłości grafu pochodzenia
danych (*data lineage*) przez tabele tymczasowe i UDF — w heterogenicznym
grafie skierowanym, wyłącznie na podstawie jego topologii.

Praca przeszła **zmianę koncepcji** (po konsultacji z dr. P. Misiorkiem):

- **Podejście aktualne — detekcja chorych węzłów** (`src/detection/`): zamiast
  zgadywać konkretne brakujące krawędzie, wykrywamy **zainfekowane tabele** —
  te, które po usunięciu zadania (joba) straciły producenta lub konsumenta
  danych. Zadanie = ranking węzłów wg prawdopodobieństwa zerwanego lineage.
- **Podejście wstępne — predykcja krawędzi** (`src/algorithms/`, `src/data/`):
  klasyfikacja binarna brakujących krawędzi. Okazało się zbyt trudne na rzadkich
  grafach DLG-DG-23 (AUC-ROC ≈ 0.5–0.7), co umotywowało zmianę kierunku.
  Zachowane jako badanie wstępne; pełny snapshot pod tagiem `magisterka_old`
  i gałęzią `edge-prediction-archive`.

## Środowisko

- Python 3.10
- Główne zależności: `networkx`, `numpy`, `scikit-learn`, `imbalanced-learn`,
  `lightgbm`, `node2vec`, `pytest`.

```bash
pip install -r requirements.txt
pytest tests/                 # 71 testów jednostkowych
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

---

# Podejście aktualne — detekcja chorych węzłów

## Sformułowanie zadania

Usunięcie zadania `J` (joba łączącego: `in_df>0 ∧ out_df>0`) zrywa lineage
tabel z nim incydentnych — *poprzedników* (`u → J`) i *następników* (`J → w`).
Te tabele stają się **zainfekowane**. Z grafu budujemy instancję klasyfikacji
węzłów: usuwamy podzbiór jobów, a zadaniem algorytmu jest wskazać ranking tabel
wg prawdopodobieństwa, że są zainfekowane (`src/detection/job_removal.py`).

**Protokół główny — indukcyjny cross-graph** (leave-one-graph-out): trening na
puli pozostałych grafów, test na grafie *niewidzianym* w treningu — zgodnie z
kierunkiem prac zespołu (Dutkiewicz, Misiorek, Wrembel 2026).

## Pułapka metodologiczna — przeciek izolacji

Po usunięciu joba ~29% chorych tabel staje się DATA_FLOW-izolowanych
(`in_df=0 ∧ out_df=0`), a 0% czystych — więc trywialna reguła „izolowana ⟹ chora"
zawyża wynik. Flaga `--exclude-isolated` daje **wariant uczciwy**: detekcja
chorych tabel, które *wciąż mają połączenia* (częściowy broken lineage).

## Algorytmy i cechy (`src/detection/`)

| Komponent | Plik | Opis |
|---|---|---|
| Symulacja usuwania jobów | `job_removal.py` | infected ground-truth, podział indukcyjny |
| Cechy węzła (~13) | `node_features.py` | pozycja w DAG: in/out_df, rola, `flow_depth`/`flow_reach`, is_root/leaf, sąsiedzi-joby |
| Heurystyki anomalii | `node_classifier.py` | `degree_anomaly`, `boundary`, `low_job_connectivity` |
| Klasyczne ML | `node_classifier.py` | Random Forest, RUSBoost, LightGBM na cechach węzła |
| Metryki rankingowe | `node_metrics.py` | AUC-ROC, AUC-PR, Precision@k, Recall@k, Hits@k |

> Node2Vec jest **transduktywny** (embeddingi nieporównywalne między grafami),
> więc nie wchodzi do protokołu indukcyjnego — co samo w sobie jest wynikiem
> motywującym indukcyjne GNN.

## Uruchomienie

```bash
# Protokół główny (indukcyjny), wariant uczciwy, 18 grafów
python src/detection/run_detection_experiments.py --all --exclude-isolated

# Porównanie 1: generalizacja do skali (małe+średnie → duże)
python src/detection/run_scale_generalization.py --exclude-isolated

# Porównanie 2: transduktywny (podział węzłów w obrębie grafu) vs indukcyjny
python src/detection/run_transductive.py --exclude-isolated
```

## Wyniki wstępne (Random Forest, AUC-ROC, wariant uczciwy)

| Protokół | Opis | RF | Heurystyki |
|---|---|---|---|
| Transduktywny | podział węzłów *tego samego* grafu | 0.82 | ~0.45 |
| **Indukcyjny (główny)** | trening na innych grafach → test na nieznanym | **0.76** | ~0.46 |
| Generalizacja skali | tylko małe+średnie → duże | 0.63 | ~0.43 |

Heurystyki tkwią na poziomie losowym (~0.45) → sygnał niesie ML, nie trywialna
struktura. Wyniki w `results/wyniki_detekcja*.csv`, `wyniki_skala.csv`,
`wyniki_transduktywny.csv`.

---

# Podejście wstępne — predykcja krawędzi (zarchiwizowane)

Klasyfikacja binarna brakujących krawędzi na trzech scenariuszach broken lineage
(`src/data/scenario_splitter.py`): **A** staging, **B** UDF/source, **C** sink.
Trzy grupy algorytmów: heurystyki grafowe (`src/algorithms/heuristics.py`),
klasyczne ML (`classical_ml.py`), Node2Vec+MLP (`node2vec_ml.py`).
Najlepszy wynik: scenariusz B, RUSBoost AUC-ROC ≈ 0.70; A/C ≈ losowo.

```bash
python scripts/run_scenario_experiments.py --all     # uruchom stare eksperymenty (scenariusze A/B/C)
git checkout edge-prediction-archive                 # pełny snapshot sprzed pivotu
```

## Struktura projektu

```
MAGISTERKA/
├── data/raw/DataAssetGraphData/        # Node.json, Edge.json (18 grafów, gitignore)
├── docs/thesis_draft/                  # tekst pracy magisterskiej
├── references/                         # PDF-y artykułów źródłowych
├── results/                            # wyniki eksperymentów (CSV/TXT)
├── src/
│   ├── data/                           # loader, splitter, scenario_splitter (wstępne)
│   ├── algorithms/                     # heuristics, classical_ml, node2vec_ml (wstępne)
│   ├── evaluation/                     # metrics (predykcja krawędzi)
│   └── detection/                      # AKTUALNE: job_removal, node_features,
│                                       #   node_classifier, node_metrics, runnery
├── scripts/                            # runnery predykcji krawędzi (wstępne)
├── tests/                              # testy jednostkowe (pytest, 71)
├── requirements.txt
└── 151851_SLR.pdf                      # raport Systematic Literature Review
```

## Status pracy

- [x] Zadanie 1 — Systematic Literature Review (`151851_SLR.pdf`)
- [x] Zadanie 2 — Implementacja algorytmów (predykcja krawędzi + detekcja węzłów)
- [x] Zadanie 3 — Zastosowanie do datasetu DLG-DG-23 (18 grafów)
- [x] Zadanie 4 — Testy jednostkowe (71 testów)
- [~] Zadanie 5 — Ewaluacja eksperymentalna (pivot na detekcję węzłów; wyniki wstępne)

## Reproducibility

Wszystkie eksperymenty są deterministyczne przy `--seed 42` (domyślny).
Usuwanie jobów, podziały i inicjalizacja modeli używają tego samego ziarna;
powtórzenia (`--repeats`) agregowane z odrzuceniem skrajnych wartości.
