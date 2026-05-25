---
name: project-repo-structure
description: Struktura repozytorium, ocena organizacji, znalezione problemy
metadata:
  type: project
---

## Aktualna struktura repozytorium

```
MAGISTERKA/
├── src/
│   ├── data/
│   │   ├── loader.py
│   │   ├── splitter.py
│   │   └── scenario_splitter.py
│   ├── algorithms/
│   │   ├── heuristics.py
│   │   ├── classical_ml.py
│   │   └── node2vec_ml.py
│   ├── evaluation/
│   │   └── metrics.py
│   └── utils/  (pusty)
├── data/
│   ├── raw/
│   │   ├── extracted/{Node,Edge}/DLG*.json
│   │   └── DataAssetGraphData/  (submoduł git!)
├── docs/
│   ├── implementation_summary.md
│   ├── thesis_draft/thesis_my/01_wstep.md, 02_podstawy_teoretyczne.md
│   ├── graphs/*.png
│   ├── synthetic_schema/
│   └── real_graph_demo/
├── results/
│   ├── wyniki_scenariusze.txt  (UTF-16 LE, plik głównych wyników)
│   └── models/.gitkeep
├── tests/
│   ├── test_loader.py
│   └── test_splitter.py
├── run_scenario_experiments.py  (główny skrypt eksperymentów)
├── run_experiments.py
├── build_and_run.py
├── visualize_graphs.py
├── requirements.txt
└── *.pdf  (artykuły naukowe w katalogu głównym!)
```

## Problemy struktury

1. **PDFy artykułów w katalogu głównym** — 6 plików PDF bezpośrednio w root. Przenieść do `references/` lub `literature/`.

2. **Brak README.md** w głównym katalogu projektu. Jest README tylko w data/raw/DataAssetGraphData (z datasetu). Brak README opisującego strukturę projektu i uruchomienie.

3. **Skrypty w katalogu głównym** — run_scenario_experiments.py, run_experiments.py, build_and_run.py, visualize_graphs.py nie są w żadnym folderze. Powinny być w `scripts/` lub `experiments/`.

4. **src/utils/ jest pusty** — tylko __init__.py. Usunąć lub wypełnić.

5. **wyniki_scenariusze.txt jako UTF-16 LE** — plik wyników trudny do odczytu, lepiej CSV/JSON.

6. **Brak folderu experiments/** z oddzielonymi konfiguracjami eksperymentów.

7. **data/raw/DataAssetGraphData jako git submodule** — .git w podkatalogu. Może być nieoczekiwane zachowanie przy klonowaniu.

8. **.pyc pliki w src/** — __pycache__ powinien być w .gitignore.

**Why:** Struktura jest w dużej mierze poprawna (jest src/, tests/, data/, docs/, results/), ale brakuje README i skrypty są rozrzucone.
**How to apply:** Przy ocenie repozytorium wskazuj brak README jako priorytet #1.
