# Rozdział 4 — Zbiór danych

> **Uwaga numeracji:** W finalnej pracy ten rozdział będzie numerowany jako
> Rozdział 4 (po rozdziale 3 — Przegląd literatury / SLR).
> **Status:** Draft roboczy — do uzupełnienia i redakcji przed złożeniem pracy.

---

## 4.1 Wybór zbioru danych

Ewaluacja algorytmów link prediction wymaga rzeczywistych grafów lineage
z dobrze zdefiniowaną strukturą krawędzi. Dostępność publicznych zbiorów
danych w tym obszarze jest ograniczona ze względu na wrażliwy charakter
metadanych produkcyjnych.

W niniejszej pracy zastosowano zbiór **DLG-DG-23** (Chen et al., *An open dataset
of data lineage graphs for data governance research*, Visual Informatics 2024),
który jest pierwszym publicznie dostępnym zbiorem rzeczywistych grafów lineage.
Stanowi on benchmark referencyjny w badaniach nad data governance i był
wykorzystany w kilku kluczowych artykułach z zakresu data lineage [patrz SLR].

---

## 4.2 Charakterystyka zbioru DLG-DG-23

### 4.2.1 Pochodzenie i kontekst

Zbiór DLG-DG-23 pochodzi z platformy chmurowej **Huawei Cloud** i zawiera
18 rzeczywistych grafów lineage z trzech typów środowisk produkcyjnych:
infrastruktura chmurowa, obsługa klienta i analiza operacyjna. Grafy
reprezentują rzeczywiste potoky danych stosowane w przedsiębiorstwie.

**Repozytorium:** https://github.com/csuvis/DataAssetGraphData

### 4.2.2 Anonimizacja danych

Dane zostały udostępnione z **zanonimizowanymi identyfikatorami węzłów**:
nazwy tabel, jobów i pól zostały zastąpione losowymi identyfikatorami UUID
(ang. *Universally Unique Identifier*). Jest to standardowa praktyka przy
udostępnianiu danych produkcyjnych, wynikająca z:
- ochrony poufności architektury systemu informatycznego Huawei,
- ograniczeń wynikających z wewnętrznych polityk bezpieczeństwa,
- zgodności z normami ochrony własności intelektualnej.

**Konsekwencja dla algorytmów:** Metody oparte na podobieństwie nazw
(ang. *string similarity*), takie jak Jaro-Winkler stosowany przez
Boiński et al. (2025), nie mogą być bezpośrednio zastosowane do tego zbioru.
Zamiast cech semantycznych (nazwy) używamy wyłącznie **cech topologicznych**
grafu (stopnie węzłów, ścieżki, struktury sąsiedztwa).

**Argument na korzyść podejścia topologicznego:** Cechy topologiczne są
invariantne na anonimizację i przenoszalne między różnymi systemami lineage,
co czyni opracowane algorytmy bardziej ogólnymi.

> **Uwaga dla promotora:** Schemat bazy danych z czytelnymi nazwami
> zawarty w `docs/synthetic_schema/schema_description.md` jest **schematem
> ilustracyjnym** tworzonym na potrzeby dokumentacji — odwzorowuje strukturę
> typowego środowiska ETL, ale nie jest oparty na konkretnych danych Huawei.
> Wszystkie eksperymenty są przeprowadzane na oryginalnych danych DLG-DG-23
> z UUID. Podejście to jest zgodne ze standardami publikacji danych badawczych.

### 4.2.3 Parametry zbioru

| Właściwość | Wartość |
|---|---|
| Liczba grafów | 18 |
| Min. liczba węzłów | 278 (DLG1) |
| Maks. liczba węzłów | 17 085 (DLG18) |
| Min. liczba krawędzi DATA_FLOW | ~24 |
| Maks. liczba krawędzi DATA_FLOW | ~1 220 |
| Format plików | JSON (Node.json + Edge.json per graf) |

---

## 4.3 Model grafu

### 4.3.1 Format danych

Każdy graf reprezentowany jest dwoma plikami JSON:

**Node.json:**
```json
{
  "nodes": [
    {"asset_id": "uuid-abc...", "asset_type": "Data Table"},
    {"asset_id": "uuid-def...", "asset_type": "Data Job"},
    {"asset_id": "uuid-ghi...", "asset_type": "Data Field"}
  ]
}
```

**Edge.json:**
```json
{
  "edges": [
    {"relation_id": "rel-1", "relation_type": "DATA_FLOW",
     "source": "uuid-abc...", "target": "uuid-def..."},
    {"relation_id": "rel-2", "relation_type": "PARENT_CHILD",
     "source": "uuid-abc...", "target": "uuid-ghi..."}
  ]
}
```

### 4.3.2 Rozkład grafów według rozmiaru

| ID | Węzły | DATA_FLOW | Skala |
|---|---|---|---|
| DLG1 | 298 | 24 | mały |
| DLG2 | 464 | 37 | mały |
| DLG3 | 603 | 57 | mały |
| DLG4 | 415 | 32 | mały |
| DLG5 | 1 299 | 175 | średni |
| DLG6 | 13 840 | ~970 | duży |
| DLG7 | 546 | 43 | mały |
| DLG8 | 681 | 62 | mały |
| DLG9 | 756 | 71 | mały |
| DLG10 | 2 024 | 105 | średni |
| DLG11 | 3 189 | 192 | średni |
| DLG12 | 4 501 | 245 | średni |
| DLG13 | 5 645 | 320 | średni |
| DLG14 | 453 | 24 | mały |
| DLG15 | 512 | 38 | mały |
| DLG16 | 561 | 51 | mały |
| DLG17 | 651 | 63 | mały |
| DLG18 | 17 085 | ~1 220 | duży |

Eksperymenty wstępne przeprowadzono na grafach małych (DLG1–DLG4, DLG7–DLG9,
DLG14–DLG17). Ewaluacja finalna obejmuje wszystkie 18 grafów.

---

## 4.4 Metodyka symulacji broken lineage

### 4.4.1 Strategia podziału danych

W celu ewaluacji algorytmów link prediction stosujemy metodę
**symulacji broken lineage przez ukrywanie krawędzi** (ang. *edge masking*).
Podejście jest standardem w literaturze link prediction
(Liben-Nowell & Kleinberg, 2007; Zhou et al., 2009).

Dla każdego grafu $G = (V, E)$:

1. Wyodrębniamy krawędzie DATA_FLOW: $E_{DF} \subset E$
2. Losowo dzielimy $E_{DF}$ na zbiory treningowy i testowy (seed=42):
   - $E_{train}$ — 80% krawędzi (widoczne dla algorytmu)
   - $E_{test}$ — 20% krawędzi (ukryte, symulujące broken lineage)
3. Graf treningowy $G_{train} = (V, E \setminus E_{test})$ — usuniętymi
   krawędziami testowymi
4. Algorytm widzi tylko $G_{train}$ i przewiduje, które krawędzie z $E_{test}$
   istniały

**Uzasadnienie 80/20:** Proporcja zapewnia wystarczającą liczbę próbek
treningowych (minimum 20 krawędzi dla małych grafów) przy jednoczesnym
zachowaniu sensownego zbioru testowego.

### 4.4.2 Próbkowanie negatywne

Dla każdej krawędzi pozytywnej w $E_{test}$ generujemy jedną próbkę negatywną
(stosunek 1:1), tzn. parę węzłów $(u, v)$ bez krawędzi DATA_FLOW w $G^*$.

Próbkowanie spełnia dwa warunki:
1. **Brak fałszywych negatywów:** $(u, v) \notin E^*$ (para nie jest krawędzią
   ani w zbiorze treningowym, ani testowym)
2. **Zgodność typów:** para należy do
   $(V_T \times V_J) \cup (V_J \times V_T)$ — to jedyne poprawne pary dla DATA_FLOW

### 4.4.3 Interpretacja eksperymentalna

| Zbiór | Rola | Analogia w broken lineage |
|---|---|---|
| $E_{train}$ | Dostępny lineage (znane zależności) | Krawędzie zachowane w katalogu metadanych |
| $E_{test}$ pozytywne | Brakujące krawędzie do odkrycia | Zależności utracone przez usunięcie temp tables/UDF |
| $E_{test}$ negatywne | Pary bez zależności | Obiekty, które nigdy nie miały relacji lineage |

---

## 4.5 Wstępna analiza strukturalna

### 4.5.1 Bipartytowość grafu DATA_FLOW

Analiza 18 grafów DLG-DG-23 potwierdza, że podgraf krawędzi DATA_FLOW
jest **niemal idealnie bipartytowy** — krawędzie istnieją wyłącznie między
węzłami typów `Data Table` i `Data Job`. Obserwacja ta ma kluczowe
konsekwencje dla doboru algorytmów (patrz Rozdział 5).

### 4.5.2 Rozkład stopni

Wstępna analiza rozkładów stopni wskazuje na charakterystykę zbliżoną
do sieci bezskalowych (ang. *scale-free networks*) — większość węzłów
ma niski stopień, ale niewielka liczba "hub" węzłów (np. centralne joby ETL
agregujące wiele tabel) ma stopień znacząco wyższy niż średnia.

Właściwość ta sprzyja skuteczności heurystyki Preferential Attachment,
która preferencyjnie łączy węzły o wysokim stopniu.

### 4.5.3 Wstępne wyniki algorytmów (małe grafy)

Poniższe wyniki dotyczą 4 najmniejszych grafów, podziału 80/20, seed=42:

| Graf | Węzły | DF edges | RF F1 | RF AUC-ROC | PA AUC-ROC | L3 AUC-ROC |
|---|---|---|---|---|---|---|
| DLG4 | 415 | 32 | **0.833** | 0.778 | 0.583 | 0.333 |
| DLG2 | 464 | 37 | 0.714 | 0.673 | 0.204 | **0.673** |
| DLG3 | 603 | 57 | — | 0.702 | 0.467 | 0.640 |
| DLG1 | 298 | 24 | — | 0.080 | 0.700 | 0.300 |

*RF = Random Forest; PA = Preferential Attachment; L3 = ścieżki długości 3*

Szczegółowa analiza wyników zawarta jest w Rozdziale 6 (Ewaluacja).

---

## 4.6 Implementacja wczytywania danych

Moduł `src/data/loader.py` wczytuje pliki JSON do obiektów `networkx.DiGraph`:

```python
from src.data.loader import load_graph, graph_summary

G = load_graph("DLG5")
# G.nodes["uuid-abc"]["asset_type"] == "Data Table"
# G.edges["uuid-abc", "uuid-xyz"]["relation_type"] == "DATA_FLOW"

summary = graph_summary(G)
# {'nodes': 1299, 'edges': 4821, 'data_flow': 175, 'parent_child': 4646,
#  'data_table': 176, 'data_job': 176, 'data_field': 947}
```

Podział danych realizuje moduł `src/data/splitter.py`:

```python
from src.data.splitter import split_edges

split = split_edges(G, test_size=0.2, neg_ratio=1.0, seed=42)
# split.pos_train — krawędzie treningowe (pozytywne)
# split.pos_test  — krawędzie testowe (pozytywne, "ukryte")
# split.neg_train — próbki negatywne treningowe
# split.neg_test  — próbki negatywne testowe
# split.G_train   — graf treningowy (bez krawędzi testowych)
```
