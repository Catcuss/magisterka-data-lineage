# Podsumowanie implementacji — Odkrywanie zależności między obiektami w bazie danych

**Autor:** Maria Nowicka (151851)
**Promotor:** prof. dr hab. inż. Robert Wrembel
**Data:** marzec 2026

---

## 1. Opis problemu

### 1.1 Data Lineage i Broken Lineage

**Data lineage** (śledzenie pochodzenia danych) to zdolność do odtworzenia pełnej historii
przepływu danych — od źródła, przez wszystkie transformacje, aż do tabeli wynikowej.
W środowiskach ETL/ELT lineage jest reprezentowany jako **skierowany graf zależności**,
gdzie węzły to obiekty bazodanowe (tabele, joby SQL, pola), a krawędzie to relacje przepływu
danych między nimi.

**Problem broken lineage** pojawia się, gdy w potoku ETL używane są obiekty tymczasowe
(tabele tymczasowe, widoki zmaterializowane, funkcje UDF), które są usuwane po zakończeniu
przetwarzania. Ich zniknięcie powoduje **trwałą utratę krawędzi** w grafie zależności:
system nie może już automatycznie powiązać tabeli źródłowej z tabelą docelową, bo brakuje
węzła pośredniego, który stanowił ich połączenie.

```
Graf pełny:          Graf po broken lineage:
A → TEMP → B         A      B      (brakuje krawędzi A→B)
```

Konsekwencje dla data governance:
- niemożliwa **analiza wpływu zmian** (impact analysis) — nie wiadomo, co zmiana w A
  wpłynie na B
- błędna **weryfikacja jakości danych** — systemy nie wykrywają propagacji błędów
- niekompletny **audyt zgodności** (compliance) — brak pełnego śladu danych

### 1.2 Cel pracy

Celem jest implementacja i ewaluacja algorytmów **predykcji brakujących krawędzi**
(ang. *link prediction*) w grafach lineage. Problem traktujemy jako **binarną klasyfikację**:
dla każdej pary węzłów `(u, v)` model decyduje, czy istnieje między nimi brakująca relacja
lineage (klasa 1), czy nie (klasa 0).

---

## 2. Zbiór danych — DLG-DG-23

### 2.1 Charakterystyka

Dataset **DLG-DG-23** (Chen et al., *Visual Informatics* 2024) to pierwszy publicznie
dostępny zbiór rzeczywistych grafów lineage, udostępniony przez Huawei Cloud.

| Właściwość | Wartość |
|---|---|
| Liczba grafów | 18 |
| Rozmiar | 278 – 17 085 węzłów |
| Scenariusze | infrastruktura chmurowa, obsługa klienta, analiza operacyjna |
| Anonimizacja | tak — nazwy węzłów zastąpione UUID |
| Format | JSON (Node.json + Edge.json per graf) |
| Źródło | https://github.com/csuvis/DataAssetGraphData |

### 2.2 Model grafu

Każdy graf DLG jest **heterogenicznym grafem skierowanym** z trzema typami węzłów
i dwoma typami krawędzi:

**Typy węzłów:**

| Typ | Opis |
|---|---|
| `Data Table` | Relacyjna tabela przechowująca dane |
| `Data Job` | Fragment kodu SQL przetwarzający dane między tabelami |
| `Data Field` | Kolumna tabeli (atrybut) |

**Typy krawędzi:**

| Typ | Kierunek | Opis |
|---|---|---|
| `DATA_FLOW` | `Data Table → Data Job` lub `Data Job → Data Table` | Przepływ danych: tabela dostarcza dane do joba lub job zapisuje wynik do tabeli |
| `PARENT_CHILD` | `Data Table → Data Field` | Relacja hierarchiczna: pole należy do tabeli |

**Kluczowa obserwacja strukturalna:** Graf krawędzi `DATA_FLOW` jest **niemal bipartytowy** —
krawędzie istnieją wyłącznie między węzłami typów `Data Table` i `Data Job`.
Tabele nigdy nie łączą się bezpośrednio z tabelami, ani joby z jobami.
Ma to fundamentalne konsekwencje dla doboru algorytmów (patrz sekcja 4.1).

### 2.3 Rozkład grafów

| ID | Węzły | Krawędzie DATA_FLOW | Skala |
|---|---|---|---|
| DLG1 | 298 | 24 | mały |
| DLG2 | 464 | 37 | mały |
| DLG3 | 603 | 57 | mały |
| DLG4 | 415 | 32 | mały |
| DLG5 | 1 299 | 175 | średni |
| DLG6 | 13 840 | ~970 | duży |
| DLG7–DLG9 | 546–756 | 43–71 | mały |
| DLG10–DLG13 | 2 024–5 645 | 105–320 | średni |
| DLG14–DLG17 | 453–651 | 24–63 | mały |
| DLG18 | 17 085 | ~1 220 | duży |

---

## 3. Architektura implementacji

### 3.1 Struktura projektu

```
src/
├── data/
│   ├── loader.py       # wczytywanie grafów JSON → NetworkX DiGraph
│   └── splitter.py     # podział train/val/test + próbki negatywne
├── algorithms/
│   ├── heuristics.py   # CN, Jaccard, AA, PA, L3
│   └── classical_ml.py # Random Forest z cechami strukturalnymi
└── evaluation/
    └── metrics.py      # Precision, Recall, F1, AUC-ROC, AUC-PR
```

### 3.2 Reprezentacja danych — NetworkX DiGraph

Każdy graf DLG wczytywany jest do obiektu `networkx.DiGraph`. Węzły przechowują
atrybut `asset_type`, krawędzie przechowują atrybut `relation_type`.

```python
G = load_graph("DLG5")
# G.nodes["uuid-abc"]["asset_type"] == "Data Table"
# G.edges["uuid-abc", "uuid-xyz"]["relation_type"] == "DATA_FLOW"
```

### 3.3 Podział danych i próbkowanie negatywne

Problem link prediction wymaga zarówno **próbek pozytywnych** (istniejące krawędzie),
jak i **próbek negatywnych** (pary węzłów bez krawędzi). Generowanie negatywów jest
kluczowe i musi spełniać dwa warunki:

1. **Brak fałszywych negatywów** — para (u, v) klasyfikowana jako negatyw nie może
   istnieć jako krawędź w oryginalnym grafie (ani w zbiorze treningowym, ani testowym)
2. **Zgodność typów** — negatywne próbki dla `DATA_FLOW` muszą być parami
   (Table, Job) lub (Job, Table), a nie np. (Table, Table)

Podział danych:
```
Krawędzie DATA_FLOW:
  80% → pos_train  (krawędzie widoczne podczas treningu)
  20% → pos_test   (krawędzie "usunięte" — symulacja broken lineage)

Próbki negatywne (stosunek 1:1):
  neg_train — losowe pary bez krawędzi (tyle samo co pos_train)
  neg_test  — losowe pary bez krawędzi (tyle samo co pos_test)
```

Graf treningowy `G_train` to oryginalny graf **z usuniętymi krawędziami testowymi**.
Algorytmy widzą tylko `G_train` i próbują przewidzieć, które z usuniętych krawędzi
istniały.

---

## 4. Zaimplementowane algorytmy

### 4.1 Heurystyki grafowe

Heurystyki to algorytmy **niewymagające trenowania**. Na podstawie lokalnej struktury
grafu przypisują każdej parze `(u, v)` numeryczny score — im wyższy, tym bardziej
prawdopodobna krawędź.

Wszystkie heurystyki operują na **nieskierowanej** wersji grafu treningowego
(kierunek krawędzi jest ignorowany przy obliczaniu sąsiedztw). Jest to standardowe
podejście w literaturze link prediction.

#### 4.1.1 Common Neighbors (CN)

**Definicja:**
```
score_CN(u, v) = |N(u) ∩ N(v)|
```
gdzie `N(u)` to zbiór sąsiadów węzła `u` w grafie nieskierowanym.

**Intuicja:** Jeśli dwa węzły mają wielu wspólnych sąsiadów, istnieje duże
prawdopodobieństwo, że są bezpośrednio połączone (zasada "wspólni znajomi").

**Złożoność:** O(deg(u) + deg(v)) po wstępnym posortowaniu zbiorów sąsiedztwa.

**Ograniczenie w DLG-DG-23:** Graf DATA_FLOW jest bipartytowy — sąsiedztwa
`N(Data Table)` zawierają wyłącznie węzły typu `Data Job` i `Data Field`,
natomiast `N(Data Job)` zawiera wyłącznie węzły typu `Data Table`.
Dla każdej pary predykcyjnej (Table, Job): `N(Table) ∩ N(Job) = ∅`, stąd
`score_CN = 0` dla wszystkich par. **CN jest strukturalnie nieskuteczny dla tego datasetu.**

#### 4.1.2 Jaccard Coefficient

**Definicja:**
```
score_Jaccard(u, v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
```

**Intuicja:** Normalizacja CN przez rozmiar sumy sąsiedztw. Eliminuje bias
wobec węzłów o bardzo wysokim stopniu (hub nodes).

**Zakres wartości:** [0, 1]. Gdy `N(u) ∩ N(v) = ∅`, score = 0.

**Ograniczenie:** Identyczne jak CN — zawsze 0 dla grafów bipartytowych DATA_FLOW.

#### 4.1.3 Adamic-Adar (AA)

**Definicja:**
```
score_AA(u, v) = Σ  1 / log(deg(w))   dla w ∈ N(u) ∩ N(v)
```

**Intuicja:** Ulepszona wersja CN — wspólni sąsiedzi o małym stopniu
(połączeni z niewioma węzłami) są traktowani jako silniejszy sygnał niż
sąsiedzi "hubs" (połączeni z wieloma węzłami). Wywodzi się z analizy
sieci społecznościowych.

**Ograniczenie:** Identyczne jak CN — zawsze 0 dla grafów bipartytowych DATA_FLOW.

#### 4.1.4 Preferential Attachment (PA)

**Definicja:**
```
score_PA(u, v) = deg(u) × deg(v)
```

**Intuicja:** W sieciach bezskalowych (scale-free) nowe krawędzie preferencyjnie
łączą się z węzłami już dobrze połączonymi — efekt "bogaci stają się bogatsi"
(Matthew effect). PA **nie wymaga wspólnych sąsiadów**, więc działa na grafach
bipartytowych.

**Właściwości:**
- Nie wymaga wspólnych sąsiadów
- Działa na grafach bipartytowych ✓
- Bardzo szybki: O(1) per para po wstępnym obliczeniu stopni
- Słaba dyskryminacja lokalnej struktury (tylko globalne stopnie)

**Wyniki:** DLG1: AUC-ROC = 0.700, DLG4: AUC-ROC = 0.583

#### 4.1.5 L3 (ścieżki długości 3)

**Definicja:**
```
score_L3(u, v) = |{(w, x) : w ∈ N(u), x ∈ N(w), v ∈ N(x), x ≠ u}|
```
Liczba ścieżek długości 3 między `u` i `v` przez dwa węzły pośrednie.

**Intuicja:** Dla grafów bipartytowych (Table↔Job) ścieżka długości 3 ma postać:
```
Table_u → Job_w → Table_x → Job_v
```
Oznacza to: "Table_u i Job_v są połączone przez tabelę Table_x, która
korzysta z tych samych jobów co Table_u i sama korzysta z Job_v."
Jest to **odpowiednik Common Neighbors na grafie rzutowanym** (bipartite projection),
gdzie węzły tego samego typu są łączone pośrednio przez węzły drugiego typu.

**Właściwości:**
- Działa poprawnie na grafach bipartytowych ✓
- Wykrywa lokalne wzorce przepływu danych
- Złożoność: O(deg(u) × max_deg²) — może być kosztowna dla węzłów hub

**Wyniki:** DLG2: AUC-ROC = 0.673, DLG3: AUC-ROC = 0.640

---

### 4.2 Klasyczne uczenie maszynowe — Random Forest

#### 4.2.1 Podejście

Random Forest to **nadzorowany algorytm klasyfikacji**. W odróżnieniu od heurystyk,
model jest trenowany na przykładach pozytywnych i negatywnych, a następnie stosowany
do nowych par węzłów.

Każda para `(u, v)` jest reprezentowana jako **wektor cech** (feature vector).
Model uczy się, które kombinacje cech odpowiadają istniejącym krawędziom lineage.

#### 4.2.2 Wektor cech (11 cech)

Ponieważ identyfikatory węzłów w DLG-DG-23 są zanonimizowanymi UUID,
nie można zastosować miary podobieństwa nazw (Jaro-Winkler, stosowanej
w artykule Boiński et al. 2025). Zamiast tego używamy wyłącznie cech
topologicznych grafu:

| # | Cecha | Opis |
|---|---|---|
| 1 | `src_type` | Typ węzła `u`: Table=0, Job=1, Field=2 |
| 2 | `src_out_deg` | Stopień wychodzący węzła `u` w G_train |
| 3 | `src_in_deg` | Stopień wchodzący węzła `u` w G_train |
| 4 | `tgt_type` | Typ węzła `v` |
| 5 | `tgt_out_deg` | Stopień wychodzący węzła `v` w G_train |
| 6 | `tgt_in_deg` | Stopień wchodzący węzła `v` w G_train |
| 7 | `common_neighbors` | Liczba wspólnych sąsiadów (w grafie nieskierowanym) |
| 8 | `jaccard` | Jaccard score (w grafie nieskierowanym) |
| 9 | `adamic_adar` | Adamic-Adar score (w grafie nieskierowanym) |
| 10 | `has_path` | Czy istnieje ścieżka u↔v w G_train (0/1) |
| 11 | `shortest_path` | Długość najkrótszej ścieżki u↔v (999 jeśli brak) |

#### 4.2.3 Random Forest — działanie

Las losowy (Random Forest) składa się z `n` drzew decyzyjnych trenowanych
niezależnie na losowych podzbiorach danych (bootstrap sampling) i losowych
podzbiorach cech (feature sampling). Predykcja jest uśrednionym głosowaniem
wszystkich drzew.

Kluczowe właściwości:
- **Odporność na overfitting** dzięki agregacji wielu drzew (bagging)
- **Obsługa niezbalansowanych klas** poprzez parametr `class_weight="balanced"`,
  który automatycznie nadaje wyższe wagi rzadszej klasie pozytywnej
- **Interpretowalność** przez analizę ważności cech (feature importance)
- **Brak wymogu normalizacji** cech — drzewa są nieczułe na skale wartości

#### 4.2.4 Wyniki feature importance

Z analizy wytrenowanego modelu na DLG4:

| Cecha | Ważność |
|---|---|
| `shortest_path` | 52.6% |
| `has_path` | 26.0% |
| `tgt_in_deg` | 8.1% |
| `tgt_out_deg` | 7.0% |
| `src_out_deg` | 4.6% |
| `src_in_deg` | 1.0% |
| `src_type` / `tgt_type` | ~0.7% |
| `common_neighbors` / `jaccard` / `adamic_adar` | ~0.0% |

**Interpretacja:** Model kieruje się głównie odległością topologiczną
między węzłami w grafie treningowym. Jeśli `u` i `v` są blisko siebie
(mała długość ścieżki lub choćby jakaś ścieżka istnieje), model przypisuje
wyższe prawdopodobieństwo krawędzi. Cechy CN/Jaccard/AA mają zerową ważność
potwierdzając, że są strukturalnie nieinformatywne dla tego datasetu.

---

## 5. Metryki ewaluacji

Do oceny jakości predykcji używamy czterech standardowych metryk klasyfikacji
binarnej:

**Precision (Precyzja):**
```
P = TP / (TP + FP)
```
Jaki odsetek przewidzianych krawędzi rzeczywiście istnieje.

**Recall (Czułość):**
```
R = TP / (TP + FN)
```
Jaki odsetek rzeczywiście istniejących krawędzi został odnaleziony.

**F1-score:**
```
F1 = 2 × P × R / (P + R)
```
Harmoniczna średnia Precision i Recall — główna metryka przy niezbalansowanych zbiorach.

**AUC-ROC** (Area Under the ROC Curve):
Pole pod krzywą ROC (Receiver Operating Characteristic). Mierzy zdolność modelu
do rozróżniania klas **niezależnie od progu binaryzacji**. Wartość 0.5 = losowe
zgadywanie, 1.0 = idealna klasyfikacja. Jest preferowaną metryką w tym zadaniu,
ponieważ nie wymaga ustalenia progu.

**AUC-PR** (Area Under the Precision-Recall Curve):
Pole pod krzywą Precision-Recall. Bardziej informatywna niż AUC-ROC przy
mocno niezbalansowanych zbiorach (gdy klasa negatywna dominuje).

---

## 6. Wyniki wstępne

Eksperymenty przeprowadzono na 4 najmniejszych grafach, krawędzie DATA_FLOW,
podział 80/20 train/test, próbkowanie negatywne 1:1, seed=42.

| Graf | Węzły | DF | CN AUC | PA AUC | L3 AUC | RF F1 | RF AUC |
|------|-------|----|--------|--------|--------|-------|--------|
| DLG1 | 298 | 24 | nan* | 0.700 | 0.300 | 0.667† | 0.080 |
| DLG4 | 415 | 32 | nan* | 0.583 | 0.333 | **0.833** | **0.778** |
| DLG2 | 464 | 37 | nan* | 0.204 | **0.673** | 0.714 | 0.673 |
| DLG3 | 603 | 57 | nan* | 0.467 | 0.640 | — | 0.702 |

*nan = wszystkie scores identyczne (=0), AUC niezdefiniowane
†trivial classifier (threshold=0, przewiduje wszystko jako pozytyw)

**Wnioski:**
1. CN/Jaccard/AA są nieskuteczne dla bipartytowego grafu DATA_FLOW
2. PA i L3 wykazują umiarkowaną dyskryminację (AUC 0.3–0.7)
3. Random Forest osiąga najlepsze wyniki na grafach ze ≥26 próbkami treningowymi
4. DLG1 (19 próbek treningowych) jest zbyt mały dla skutecznego treningu RF

---

## 7. Dalsze kroki

| Zadanie | Opis |
|---|---|
| Node2Vec | Trzeci algorytm: uczenie embeddingów węzłów na strukturze grafu, klasyfikacja krawędzi przez iloczyn embeddingów |
| Ewaluacja pełna | Uruchomienie wszystkich algorytmów na wszystkich 18 grafach |
| Notebook eksploracyjny | Wizualizacja grafów, rozkładów stopni, wyników |
| Tabela porównawcza | Zestawienie wszystkich algorytmów × wszystkich grafów |

---

## 8. Bibliografia (wybrane pozycje z SLR)

1. Boiński et al. — *Leveraging machine learning techniques for discovering broken lineage links between database objects*, ISD2025
2. Chen et al. — *An open dataset of data lineage graphs for data governance research*, Visual Informatics 2024
3. Kohan Marzagão et al. — *Provenance graph kernel*, IEEE TKDE 2025
4. Liben-Nowell & Kleinberg — *The link-prediction problem for social networks*, JASIST 2007 *(klasyczna praca o heurystykach)*
5. Zhou et al. — *Predicting missing links via local information*, EPJB 2009 *(PA, CN, AA)*
