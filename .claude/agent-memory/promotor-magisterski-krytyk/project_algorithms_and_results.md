---
name: project-algorithms-and-results
description: Szczegóły implementacji algorytmów, wyniki eksperymentów i znalezione problemy metodologiczne
metadata:
  type: project
---

## Zaimplementowane algorytmy

**Heurystyki** (src/algorithms/heuristics.py):
- Common Neighbors, Jaccard, Adamic-Adar — strukturalnie bezużyteczne dla bipartytowych DATA_FLOW (zawsze 0), ale są świadomie zawarte dla porównania
- Preferential Attachment, L3, Katz Index, PPR — działają poprawnie na bipartytowych
- Kod jest dobry jakościowo: komentarze, złożoność, obsługa bipartytowości

**ML klasyczne** (src/algorithms/classical_ml.py):
- Random Forest, RUSBoost, LightGBM
- 11 cech topologicznych (brak Jaro-Winkler — UUID zanonimizowane w DLG-DG-23)
- Klasa bazowa _BaseGraphClassifier — dobra struktura OOP
- Kod dobry, zgodny z PEP8

**GNN/embeddingi** (src/algorithms/node2vec_ml.py):
- Node2Vec + MLP (hadamard embedding)
- p=1, q=0.5 (BFS-biased dla bipartytowych)
- BRAK GraphSAGE/GCN/GAT — to jest luka wymagająca uzupełnienia lub wyjaśnienia
- BRAK heterogenicznych GNN (HGT, R-GCN, HAN) — graf jest heterogeniczny, to pominięcie

## Struktura podziału danych

scenario_splitter.py — trzy scenariusze:
- A: usunięcie krawędzi wyjściowych tabeli intermediate (staging table)
- B: 20% losowych krawędzi wyjściowych source Tables
- C: krawędzie wejściowe sink Tables (data mart)
- neg_ratio=1.0 (1:1 pos:neg) — to jest problematyczne dla niezbalansowanych grafów
- seed=42 użyte globalnie — dobrze

## Kluczowe problemy w wynikach

1. **RF/RUSBoost/LightGBM F1=0.000 we wszystkich 18 grafach × Scenariusz A i C** — modele ML nie generują żadnej pozytywnej predykcji. Threshold=0.5 (stały) powoduje, że cały output modelów ML idzie do klasy 0. Trzeba zastosować best_threshold_f1 (jest w metrics.py) analogicznie jak dla heurystyk.

2. **Node2Vec F1 bardzo niskie w Scenariuszu A** — prawidłowe P ale bardzo niski R (precision wysoka np. 0.667-1.0, recall 0.03-0.18). Model jest zbyt ostrożny przy threshold=0.5.

3. **NaN w AUC-ROC** — pojawia się gdy wszystkie scores są identyczne (np. L3/Katz = 0.0 dla wszystkich par w małych grafach). To jest feature datasetu, nie bug.

4. **Brak walidacji zestawu cech** — identyczne feature names dla ML i heurystyk, ale CN/Jaccard/AA = 0 dla wszystkich par bipartytowych, przez co 3 z 11 cech są zawsze zerowe w ML.

5. **Wyniki Scenariusz B >> A, C** — avr AUC-ROC: B=0.796, A=0.632, C=0.553. Scenariusz B (UDF hidden source) jest łatwiejszy niż A i C. Wnioski w pracy muszą to tłumaczyć strukturalnie.

6. **Plik wyniki_scenariusze.txt jest plikiem UTF-16 LE** (Windows BOM) — czyta się poprawnie ale wygląda na uszkodzony w edytorach. Lepiej zapisywać UTF-8.

## Brak w implementacji (do uzupełnienia lub wytłumaczenia)

- Brak GraphSAGE/GCN/GAT — Node2Vec+MLP to nie jest pełnoprawny GNN (brak message passing)
- Brak heterogenicznych GNN (HGT, R-GCN) dla heterogenicznego grafu DLG
- Brak val set — tylko train/test, brak walidacji hiperparametrów
- Brak zapianych modeli/checkpointów — wyniki nieodtwarzalne poza uruchomieniem skryptu
- Brak zapisanych wyników w formacie CSV/JSON — tylko .txt

**Why:** To są luki które komisja może zakwestionować.
**How to apply:** Przy ocenie pracy wskazuj te luki jako priorytety poprawy.
