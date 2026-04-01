# Rozdział 2 — Podstawy teoretyczne

> **Status:** Draft roboczy — do uzupełnienia i redakcji przed złożeniem pracy.

---

## 2.1 Data lineage i data provenance — definicje

W literaturze pojęcia *data lineage* i *data provenance* są często używane
zamiennie, choć niektórzy autorzy rozróżniają między nimi niuanse semantyczne.

**Data lineage** (śledzenie przepływu danych) odnosi się do rejestrowania
ścieżki, którą dane pokonują od źródła do docelowego miejsca składowania.
Skupia się na pytaniu: *skąd pochodzi dany rekord i przez jakie transformacje
przeszedł?* W kontekście hurtowni danych lineage opisuje przepływ między
tabelami i jobami ETL.

**Data provenance** (ang. *provenance* = pochodzenie, rodowód) to szersze
pojęcie obejmujące pełną historię tworzenia, modyfikacji i przemieszczania
danych, włącznie z informacjami o aktorach (osoby, procesy), czasie i miejscu
każdej operacji [Psallidas et al., 2018]. Provenance może opisywać zarówno
przepływy na poziomie tabeli (*coarse-grained lineage*), jak i na poziomie
pojedynczego rekordu lub kolumny (*fine-grained lineage*).

W niniejszej pracy stosujemy pojęcia zamiennie, skupiając się na lineage
na poziomie obiektów bazodanowych (tabele, joby, pola) — co odpowiada
modelowi danych w zbiorze DLG-DG-23.

---

## 2.2 Graf lineage jako heterogeniczny graf skierowany

### 2.2.1 Definicja formalna

Graf lineage $G$ jest **heterogenicznym grafem skierowanym**:

$$G = (V, E, \tau, \rho)$$

gdzie:
- $V$ — zbiór węzłów (obiektów bazodanowych),
- $E \subseteq V \times V$ — zbiór krawędzi (relacji między obiektami),
- $\tau: V \to \mathcal{T}_V$ — funkcja przypisująca węzłom typ z $\mathcal{T}_V$,
- $\rho: E \to \mathcal{T}_E$ — funkcja przypisująca krawędziom typ z $\mathcal{T}_E$.

W zbiorze DLG-DG-23 (Chen et al., 2024):

$$\mathcal{T}_V = \{\text{Data Table}, \text{Data Job}, \text{Data Field}\}$$
$$\mathcal{T}_E = \{\text{DATA\_FLOW}, \text{PARENT\_CHILD}\}$$

### 2.2.2 Semantyka typów

**Typy węzłów:**

| Typ | Opis |
|---|---|
| `Data Table` | Relacyjna tabela lub widok przechowujący dane |
| `Data Job` | Fragment kodu SQL lub skrypt ETL przetwarzający dane |
| `Data Field` | Kolumna (atrybut) należąca do tabeli |

**Typy krawędzi:**

| Typ | Kierunek | Semantyka |
|---|---|---|
| `DATA_FLOW` | Table→Job lub Job→Table | Tabela dostarcza dane do joba lub job zapisuje wynik do tabeli |
| `PARENT_CHILD` | Table→Field | Kolumna należy do tabeli (relacja hierarchiczna) |

### 2.2.3 Strukturalna właściwość grafu DATA_FLOW

Kluczową obserwacją strukturalną jest **bipartytowość** podgrafu krawędzi
DATA_FLOW. Formalnie: niech $V_{T} = \{v \in V : \tau(v) = \text{Data Table}\}$
i $V_{J} = \{v \in V : \tau(v) = \text{Data Job}\}$. Wówczas:

$$\forall (u, v) \in E_{\text{DATA\_FLOW}}: (u \in V_T \wedge v \in V_J)
\vee (u \in V_J \wedge v \in V_T)$$

Oznacza to, że tabele nigdy nie łączą się bezpośrednio z tabelami,
ani joby z jobami — zawsze przez węzeł pośredni drugiego typu.
Właściwość ta ma istotne konsekwencje dla doboru algorytmów
predykcji krawędzi (patrz Rozdział 5).

---

## 2.3 Problem predykcji brakujących krawędzi (link prediction)

### 2.3.1 Formalne sformułowanie problemu

Niech $G_{obs} = (V, E_{obs})$ będzie **obserwowanym** grafem lineage —
podgrafem pełnego grafu $G^* = (V, E^*)$, gdzie $E_{obs} \subsetneq E^*$.
Różnica $E^* \setminus E_{obs}$ to zbiór krawędzi utraconych w wyniku
broken lineage.

**Problem link prediction:** dla danego grafu $G_{obs}$ i zbioru
kandydackich par węzłów $\mathcal{C} \subseteq V \times V \setminus E_{obs}$
znaleźć funkcję oceny (ang. *scoring function*):

$$f: V \times V \to \mathbb{R}$$

taką, aby pary o wyższym $f(u, v)$ z większym prawdopodobieństwem
należały do $E^* \setminus E_{obs}$.

W ujęciu klasyfikacyjnym (podejście zastosowane w niniejszej pracy):

$$\hat{y}(u, v) = \begin{cases} 1 & \text{jeśli } (u,v) \in E^* \setminus E_{obs} \\ 0 & \text{w.p.p.} \end{cases}$$

### 2.3.2 Próbkowanie negatywne

Zbiór krawędzi pozytywnych $E^+ = E^* \setminus E_{obs}$ jest z definicji
mały w stosunku do całkowitej liczby kandydackich par
$|V \times V| - |E_{obs}|$. Aby zbudować zbalansowany zbiór treningowy,
stosuje się **losowe próbkowanie negatywne** — wybiera się pary
$(u, v) \notin E^*$ jako przykłady klasy negatywnej.

W przypadku heterogenicznych grafów lineage próbkowanie musi respektować
ograniczenia typologiczne: negatywne próbki dla krawędzi DATA_FLOW muszą
być parami $(u \in V_T, v \in V_J)$ lub $(u \in V_J, v \in V_T)$.
Losowe pary $(V_T, V_T)$ lub $(V_J, V_J)$ nie są kandydatami dla DATA_FLOW
i nie powinny wchodzić do zbioru negatywnego.

---

## 2.4 Typy broken lineage

Na podstawie przeglądu literatury wyróżniamy cztery główne przyczyny
broken lineage w środowiskach produkcyjnych:

### Typ 1 — Tabele tymczasowe (temporary tables)

**Mechanizm:** Potok ETL tworzy tabelę tymczasową $T_{temp}$ jako
wynik pośredni i usuwa ją po załadowaniu danych do tabeli docelowej.
System lineage rejestruje krawędzie $(T_{src} \to T_{temp})$ i
$(T_{temp} \to T_{dst})$, ale po usunięciu $T_{temp}$ obie krawędzie
znikają z katalogu metadanych.

**Utracona zależność:** $T_{src} \to T_{dst}$ (przez usuniętą tabelę)

**Częstość:** Bardzo wysoka — tabele staging/tymczasowe są powszechne
w procesach ETL batch.

### Typ 2 — Funkcje UDF (User-Defined Functions)

**Mechanizm:** Job ETL wywołuje UDF, która wewnętrznie odpytuje tabelę
referencyjną $T_{ref}$. Systemy lineage zazwyczaj nie śledzą zależności
wewnątrz kodu UDF (black-box), więc krawędź $(T_{ref} \to J_{etl})$
nie jest rejestrowana.

**Utracona zależność:** $T_{ref} \to J_{etl}$ (ukryta przez kod UDF)

**Częstość:** Wysoka w środowiskach z wieloma UDF lub procedurami składowanymi.

### Typ 3 — Rekurencja i CTE (Common Table Expressions)

**Mechanizm:** Zapytanie SQL z rekurencyjnym CTE tworzy wewnętrzne
pośrednie wyniki (każda iteracja to kolejna "tabela" logiczna).
Systemy lineage mogą nie rozwijać rekurencji, co powoduje niepełne
śledzenie przepływu danych przez rekurencyjne transformacje.

**Utracona zależność:** Zależności pośrednie w rekurencji CTE
(Dietrich et al., 2023).

**Częstość:** Umiarkowana — dotyczy zapytań hierarchicznych
(drzewa organizacyjne, bill-of-materials, sieci społecznościowe).

### Typ 4 — Ewolucja schematu (schema evolution)

**Mechanizm:** Migracja systemu (zmiana nazwy tabeli, podział tabeli,
zastąpienie widoku zmaterializowanego) powoduje, że historyczny lineage
nie łączy się z nowym schematem. System widzi dwa rozłączne grafy:
historyczny i bieżący.

**Utracona zależność:** Historyczne ścieżki lineage przez przemianowane
lub usunięte obiekty.

**Częstość:** Umiarkowana — dotyczy środowisk z aktywnym rozwojem platformy
danych.

---

## 2.5 Algorytmy link prediction — przegląd klas

### 2.5.1 Heurystyki grafowe

Heurystyki grafowe to algorytmy **niewymagające trenowania**. Na podstawie
lokalnej lub globalnej struktury grafu przypisują każdej parze $(u, v)$
numeryczny score. Są szybkie, interpretowalny i nie wymagają etykietowanych
danych treningowych.

Najważniejsze heurystyki i ich zachowanie na grafach bipartytowych:

| Heurystyka | Definicja | Bipartytowy? |
|---|---|---|
| Common Neighbors (CN) | $\|N(u) \cap N(v)\|$ | Zawsze 0 ✗ |
| Jaccard | $\|N(u) \cap N(v)\| / \|N(u) \cup N(v)\|$ | Zawsze 0 ✗ |
| Adamic-Adar (AA) | $\sum_{w \in N(u) \cap N(v)} 1/\log \deg(w)$ | Zawsze 0 ✗ |
| Preferential Attachment (PA) | $\deg(u) \times \deg(v)$ | Działa ✓ |
| L3 (ścieżki dł. 3) | $\|\{(w,x): w \in N(u), x \in N(w), v \in N(x)\}\|$ | Działa ✓ |

**Kluczowa obserwacja:** CN, Jaccard i Adamic-Adar opierają się na
wspólnych sąsiadach $N(u) \cap N(v)$. W grafach bipartytowych
dla każdej pary predykcyjnej (Table, Job) zachodzi
$N(\text{Table}) \cap N(\text{Job}) = \emptyset$
(węzły jednego typu nie mają wspólnych sąsiadów), co czyni te heurystyki
strukturalnie nieskutecznymi.

### 2.5.2 Klasyczne uczenie maszynowe

Podejście nadzorowane: każda para $(u, v)$ jest reprezentowana jako
wektor cech, a model klasyfikacyjny uczy się odróżniać krawędzie
od nie-krawędzi na podstawie etykietowanych przykładów.

Najważniejsza cecha wektora w kontekście grafów lineage:
**długość najkrótszej ścieżki** między $u$ a $v$ w obserwowanym grafie
$G_{obs}$ — węzły blisko siebie topologicznie mają wyższe prawdopodobieństwo
brakującej krawędzi (wynik wstępnych eksperymentów: feature importance = 52.6%).

### 2.5.3 Metody oparte na embeddingach węzłów

**Node2Vec** (Grover & Leskovec, 2016) to algorytm uczący niskowymiarową
reprezentację każdego węzła w przestrzeni $\mathbb{R}^d$ na podstawie
losowych spacerów po grafie. Węzły o podobnym otoczeniu strukturalnym
mają zbliżone embeddingi.

Dla predykcji krawędzi: reprezentacja pary $(u, v)$ to operacja
na embeddingach (np. element-wise product $\mathbf{z}_u \odot \mathbf{z}_v$
lub konkatenacja $[\mathbf{z}_u || \mathbf{z}_v]$), a klasyfikator binarny
(np. logistyczna regresja) decyduje o istnieniu krawędzi.

Node2Vec jest szczególnie skuteczny na grafach z wyraźną strukturą
społecznościową (community structure), które mogą odpowiadać grupom
powiązanych obiektów w hurtowni danych (np. wszystkie joby jednego
potoku ETL).

---

## 2.6 Metryki ewaluacji

Do oceny algorytmów stosuje się standardowe metryki binarnej klasyfikacji:

**Precision (precyzja):**
$$P = \frac{TP}{TP + FP}$$
Odsetek poprawnie przewidzianych krawędzi spośród wszystkich przewidzianych.

**Recall (czułość):**
$$R = \frac{TP}{TP + FN}$$
Odsetek rzeczywiście brakujących krawędzi, które algorytm odnalazł.

**F1-score:**
$$F_1 = \frac{2 \cdot P \cdot R}{P + R}$$
Harmoniczna średnia Precision i Recall — główna metryka przy niezbalansowanych
zbiorach danych.

**AUC-ROC** (Area Under ROC Curve):
Pole pod krzywą ROC mierzy zdolność rankingowania par $(u,v)$ niezależnie
od progu binaryzacji. Wartość 0.5 odpowiada losowemu klasyfikatorowi,
1.0 — idealnemu.

**AUC-PR** (Area Under Precision-Recall Curve):
Bardziej informatywna niż AUC-ROC przy silnie niezbalansowanych zbiorach
(klasa negatywna znacznie dominuje nad pozytywną), co jest typową sytuacją
w link prediction.

---

*[TODO: Rozważyć dodanie podrozdziału o grafowych sieciach neuronowych (GNN)
jako uzupełnienie przed opisem Node2Vec w rozdziale 5.]*
