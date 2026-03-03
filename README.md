# Odkrywanie zależności między obiektami w bazie danych

Praca magisterska — Maria Nowicka (151851)
Politechnika Poznańska, Wydział Informatyki i Telekomunikacji
Promotor: prof. dr hab. inż. Robert Wrembel, 2026

## Temat

Implementacja i ewaluacja algorytmów predykcji brakujących krawędzi (link prediction)
w grafach pochodzenia danych (data lineage). Problem: rekonstrukcja zerwanego lineage
spowodowanego usunięciem tabel tymczasowych lub UDF w potokach ETL.

## Dataset

**DLG-DG-23** — 18 rzeczywistych grafów lineage z Huawei Cloud
(Chen et al., *An open dataset of data lineage graphs for data governance research*, Visual Informatics 2024).

- Repozytorium z danymi: https://github.com/csuvis/DataAssetGraphData
- 18 grafów skierowanych, 278–17 085 węzłów
- Typy węzłów: `Data Table`, `Data Job`, `Data Field`
- Typy krawędzi: `DATA_FLOW` (Table↔Job), `PARENT_CHILD` (Table→Field)

Dane pobierz ręcznie do `data/raw/` (pliki .rar wykluczone z repozytorium).

## Stan implementacji

### Zrealizowane

| Moduł | Plik | Opis |
|---|---|---|
| Wczytywanie danych | `src/data/loader.py` | Parsuje Node.json + Edge.json → `nx.DiGraph`; wczytuje wszystkie 18 grafów |
| Podział danych | `src/data/splitter.py` | Train/val/test split; generowanie negatywnych próbek z uwzględnieniem typów węzłów |
| Heurystyki grafowe | `src/algorithms/heuristics.py` | Common Neighbors, Jaccard, Adamic-Adar, Preferential Attachment, L3 |
| Klasyfikator ML | `src/algorithms/classical_ml.py` | Random Forest z cechami strukturalnymi grafu (stopnie, ścieżki, CN) |
| Metryki ewaluacji | `src/evaluation/metrics.py` | Precision, Recall, F1, AUC-ROC, AUC-PR |
| Testy jednostkowe | `tests/` | 46 testów: loader (29), splitter (17) |


### Wstępne wyniki (małe grafy, DATA_FLOW, test 20%, seed=42)

> **Odkrycie:** Graf DATA_FLOW jest bipartytowy (Table↔Job), więc heurystyki
> oparte na wspólnych sąsiadach (CN, Jaccard, Adamic-Adar) zawsze zwracają 0
> — brak trójkątów w grafach bipartytowych. Przydatne są heurystyki
> Preferential Attachment i L3 (ścieżki długości 3).

| Graf | Węzły | DF edges | RF F1 | RF AUC-ROC | PA AUC-ROC | L3 AUC-ROC |
|------|-------|----------|-------|------------|------------|------------|
| DLG4 | 415 | 32 | **0.833** | 0.778 | 0.583 | 0.333 |
| DLG2 | 464 | 37 | 0.714 | 0.673 | 0.204 | **0.673** |
| DLG3 | 603 | 57 | — | 0.702 | 0.467 | 0.640 |
| DLG1 | 298 | 24 | — | 0.080 | 0.700 | 0.300 |

*DLG1: za mało próbek treningowych (19) dla RF.*

## Struktura projektu

```
MAGISTERKA/
├── data/
│   ├── raw/DataAssetGraphData/   # sklonowane repo (Node.rar, Edge.rar)
│   │   └── extracted/            # wypakowane JSON (18×Node + 18×Edge)
│   └── processed/                # grafy .pkl, splity .npz (generowane)
├── src/
│   ├── data/
│   │   ├── loader.py             # wczytywanie grafów JSON → NetworkX
│   │   └── splitter.py           # train/val/test split + próbki negatywne
│   ├── algorithms/
│   │   ├── heuristics.py         # CN, Jaccard, AA, PA, L3
│   │   └── classical_ml.py       # Random Forest (cechy strukturalne)
│   └── evaluation/
│       └── metrics.py            # Precision, Recall, F1, AUC-ROC, AUC-PR
├── notebooks/                    # Jupyter (do uzupełnienia)
├── tests/                        # 46 testów jednostkowych
└── results/                      # metryki, wykresy, modele
```

## Uruchomienie

```bash
pip install -r requirements.txt
pytest tests/
```
