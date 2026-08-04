# Dalsza część pracy — streszczenia, rozdział 4 i rozdział 5

> **Plik roboczy (Markdown).** Zawiera wygenerowaną treść brakujących części pracy:
> streszczenie (PL/EN), pełny rozdział 4 („Ocena rozwiązania") oraz rozdział 5
> („Uwagi końcowe"). Treść należy przenieść do `Thesis.tex` / `03_...` w miejsca
> oznaczone `% TODO`. **Wszystkie liczby pochodzą z biegu kanonicznego**
> (`results/agregat_detekcja.csv`, `results/agregat_detekcja_napompowany.csv`,
> `results/_faza2_runs.txt`, sekcja SWEEP) — nie zmyślono żadnej wartości.
>
> Ustawienia biegu (za `results/README_BIEG_KANONICZNY.md`): wszystkie 18 grafów,
> `removal_ratio = 0.10`, `side = both`, 3 powtórzenia (seedy 42/43/44), protokół
> indukcyjny leave-one-graph-out, próg wiarygodności grafu `MIN_POS = 5`, agregacja
> po grafach wiarygodnych.

---

## Streszczenie (PL)

Ciągłość grafów pochodzenia danych (*data lineage*) ulega przerwaniu, gdy w potokach
przetwarzania wykorzystywane są obiekty pośrednie — tabele tymczasowe oraz funkcje
definiowane przez użytkownika. Zjawisko to, określane jako *broken lineage*, pozbawia
tabele informacji o ich producencie lub konsumencie danych i utrudnia audyt oraz kontrolę
jakości danych. Dotychczasowe prace modelują ten problem wyłącznie jako predykcję
brakujących krawędzi; nie stawiają natomiast pytania, **które tabele** mają zerwane
pochodzenie danych. Niniejsza praca wypełnia tę lukę, formułując zadanie na poziomie
**węzłów** — jako ranking tabel według prawdopodobieństwa zainfekowania zjawiskiem broken
lineage.

Celem pracy jest zbadanie, w jakim stopniu **sama topologia** grafu lineage pozwala
wskazać takie tabele, bez dostępu do semantyki nazw obiektów i schematów bazy. Zjawisko
broken lineage symulowano przez kontrolowane usuwanie zadań (jobów) ze zbioru
DLG-DG-23 — 18 zanonimizowanych, rzeczywistych grafów lineage ze środowiska Huawei Cloud.
Porównano trzy klasy metod: heurystyki strukturalne, klasyczne klasyfikatory uczenia
maszynowego oparte na cechach pozycji węzła w grafie DAG oraz autorski detektor
**LineageDetector**, łączący cechy topologiczne z relacyjnym score kompletności
(*peer-consistency*) i kalibracją izotoniczną prawdopodobieństw. Ewaluację przeprowadzono
w protokole indukcyjnym cross-graph, z kontrolą przecieku wynikającego z trywialnie
izolowanych węzłów.

W wariancie uczciwym (z wykluczeniem węzłów izolowanych) LineageDetector osiągnął
najlepszy wynik na wszystkich metrykach rankingowych: AUC-ROC 0,771, AUC-PR 0,435,
Precision@k 0,443 oraz Brier 0,106, przewyższając zarówno heurystyki, jak i klasyczne
klasyfikatory. Wynik okazał się stabilny względem odsetka usuwanych zadań. Główny wniosek:
sama topologia grafu niesie umiarkowany, lecz użyteczny sygnał o broken lineage na poziomie
węzłów, stanowiący punkt odniesienia (*topology-only baseline*) dla metod
grafowo-semantycznych.

*Słowa kluczowe:* data lineage, broken lineage, detekcja anomalii w grafach, uczenie
indukcyjne, uczenie maszynowe.

---

## Abstract (EN)

The continuity of data lineage graphs is disrupted whenever processing pipelines rely on
intermediate objects — temporary tables and user-defined functions. This phenomenon, known
as *broken lineage*, deprives tables of information about their data producer or consumer
and hampers auditing and data-quality control. Existing work models the problem exclusively
as missing-edge prediction; it does not ask **which tables** have broken lineage. This
thesis fills that gap by formulating the task at the **node** level — as a ranking of tables
by their probability of being affected by broken lineage.

The goal is to investigate to what extent the **topology alone** of a lineage graph allows
such tables to be identified, without access to the semantics of object names or database
schemas. Broken lineage was simulated by the controlled removal of jobs from the DLG-DG-23
dataset — 18 anonymised, real-world lineage graphs from the Huawei Cloud environment. Three
classes of methods were compared: structural heuristics, classical machine-learning
classifiers based on DAG-position features, and the proposed **LineageDetector**, which
combines topological features with a relational peer-consistency completeness score and
isotonic probability calibration. Evaluation followed an inductive cross-graph protocol,
with control for the leakage caused by trivially isolated nodes.

In the fair variant (excluding isolated nodes), LineageDetector achieved the best result on
every ranking metric: AUC-ROC 0.771, AUC-PR 0.435, Precision@k 0.443, and Brier 0.106,
outperforming both the heuristics and the classical classifiers. The result proved stable
with respect to the fraction of removed jobs. The main conclusion: graph topology alone
carries a moderate yet useful signal about broken lineage at the node level, providing a
topology-only baseline for graph-semantic methods.

*Keywords:* data lineage, broken lineage, graph anomaly detection, inductive learning,
machine learning.

---

# Rozdział 4 — Ocena rozwiązania

W rozdziale przedstawiono wyniki eksperymentów przeprowadzonych zgodnie z metodyką opisaną
w rozdziale 3. Dla każdej z metod detekcji podano wartości metryk rankingowych uśrednione
po grafach zbioru DLG-DG-23 w protokole indukcyjnym.

## 4.1 Badanie wstępne: predykcja krawędzi

Punktem wyjścia pracy było ujęcie broken lineage jako **predykcji brakujących krawędzi** —
zgodne z dotychczasową literaturą. W badaniu wstępnym każdy z 18 grafów poddano trzem
scenariuszom usuwania krawędzi (oznaczonym A, B, C, różniącym się sposobem doboru krawędzi
usuwanych i próbkowaniem negatywów), a następnie oceniono zdolność metod do odtworzenia
usuniętych powiązań. Testowano heurystyki predykcji krawędzi (Preferential Attachment, L3,
Katz, Personalized PageRank), klasyczne klasyfikatory (Random Forest, RUSBoost, LightGBM)
oraz zanurzenia sieciowe (Node2Vec + MLP), w tym samym protokole indukcyjnym cross-graph.

Wyniki okazały się **niesatysfakcjonujące i niestabilne**. Na grafach wiarygodnych
(dostatecznie liczna klasa pozytywna w zbiorze testowym) średnie AUC-ROC utrzymywało się
w pobliżu poziomu losowego (0,5), przy bardzo wysokiej wariancji między grafami
i scenariuszami. Jedynie pojedyncze pary (graf, scenariusz) osiągały AUC-ROC rzędu 0,70,
lecz bez powtarzalności — żadna metoda nie generalizowała się w sposób spójny na grafy
niewidziane. Obserwacja ta jest zbieżna z wynikami Dutkiewicza et al. [Dutkiewicz2026],
u których scenariusz tabel tymczasowych — najczęstsza praktyczna przyczyna broken lineage —
osiągał AUROC 0,49, czyli poziom losowy, nawet dla zaawansowanych metod
grafowo-semantycznych.

Przyczyną jest **rzadkość** grafów DLG-DG-23: liczba krawędzi przepływu danych jest o rząd
wielkości mniejsza od liczby węzłów (tab. 3.1), przez co sygnał o konkretnej brakującej
parze obiektów jest zbyt słaby, aby umożliwić wiarygodną predykcję krawędzi bez dostępu do
semantyki nazw. Wynik ten stanowi bezpośrednią motywację **zmiany ujęcia problemu** na
poziom węzłów (sekcja 2.4): zamiast pytać, *która krawędź* została utracona, pyta się,
*które tabele* są dotknięte brakiem — zadanie słabiej uzależnione od pojedynczej krawędzi,
a przez to wykonalne mimo rzadkości grafu.

## 4.2 Wyniki detekcji węzłów o zerwanym lineage

Tabela 4.1 przedstawia średnie metryki rankingowe wszystkich metod detekcji w protokole
indukcyjnym, w wariancie uczciwym (z wykluczeniem węzłów izolowanych, sekcja 3.3.1),
uśrednione po ośmiu grafach wiarygodnych. Wariant ten przyjęto jako główny, ponieważ nie
korzysta z trywialnego przecieku „tabela izolowana ⟹ zainfekowana" (por. sekcja 4.3).

**Tabela 4.1.** Średnie metryki detekcji zainfekowanych tabel per metoda (protokół
indukcyjny, wariant uczciwy; gwiazdka — wkład własny; pogrubienie — najlepsza wartość
w kolumnie).

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|:---:|:---:|:---:|:---:|
| *Heurystyki strukturalne* | | | | |
| Anomalia stopnia | 0,427 | 0,165 | 0,142 | 0,134 |
| Brzeg (root/leaf) | 0,455 | 0,137 | 0,146 | 0,745 |
| Niska łączność jobów | 0,324 | 0,112 | 0,094 | 0,226 |
| Reguła korzenia | 0,574 | 0,168 | 0,180 | 0,469 |
| *Klasyczne metody ML* | | | | |
| Random Forest | 0,749 | 0,425 | 0,380 | 0,117 |
| RUSBoost | 0,631 | 0,249 | 0,340 | 0,152 |
| LightGBM | 0,720 | 0,381 | 0,398 | 0,147 |
| *Autorski detektor* | | | | |
| **LineageDetector\*** | **0,771** | **0,435** | **0,443** | **0,106** |

> **Uwaga metodyczna (do zamieszczenia pod tabelą).** W tym biegu przyjęto *k* równe
> liczbie tabel faktycznie zainfekowanych w grafie testowym, przez co Precision@k,
> Recall@k i Hits@k przyjmują tę samą wartość; w tabeli podano zatem jedną kolumnę
> (P@k) i opisano tę relację słownie, aby nie sugerować trzech niezależnych metryk.

LineageDetector uzyskał **najlepszy wynik na wszystkich czterech metrykach** jednocześnie.
Przewaga nad najlepszym klasycznym klasyfikatorem (Random Forest) wynosi +0,022 AUC-ROC
i +0,010 AUC-PR, a nad LightGBM — odpowiednio +0,051 i +0,054. Wyraźnie niższy Brier score
(0,106 wobec 0,117–0,152) potwierdza, że kalibracja izotoniczna daje rzetelne oszacowania
prawdopodobieństwa, a nie jedynie poprawny ranking.

Heurystyki strukturalne oparte na lokalnym symptomie wypadają słabo: żadna nie przekracza
AUC-ROC 0,58, a trzy z czterech plasują się **poniżej poziomu losowego**. Wynika to
z natury zadania w wariancie uczciwym — po wykluczeniu tabel w pełni izolowanych symptom
lokalny (niski stopień, pozycja na brzegu) przestaje wystarczać, ponieważ osierocona
tabela-następnik jest strukturalnie nieodróżnialna od prawdziwej tabeli źródłowej
(sekcja 3.1). Rozróżnienie tych przypadków wymaga sygnału relacyjnego oraz uczenia
indukcyjnego — obecnych dopiero w klasycznych klasyfikatorach i w LineageDetectorze.

> **Analiza składnika autorskiego (ablacja peer-consistency).** Relacyjny score
> kompletności — sedno wkładu LineageDetectora — użyty samodzielnie jako heurystyka
> osiąga AUC-ROC 0,559, AUC-PR 0,206 i P@k 0,240, a więc **wyraźnie powyżej** wszystkich
> pozostałych heurystyk lokalnych po stronie AUC-PR i P@k. Potwierdza to, że informacja
> relacyjna (spójność tabeli z jej peerami) jest jakościowo bogatsza od samego stopnia
> węzła; jej pełną wartość realizuje jednak dopiero LineageDetector, łącząc ją z cechami
> pozycji w DAG i kalibracją (0,771). *(Prezentacja score kompletności jako składnika
> detektora, a nie samodzielnej metody konkurencyjnej — zgodnie z uwagą promotora.)*

## 4.3 Kontrola przecieku i analiza wrażliwości

### Przeciek izolacji

Usunięcie zadania może pozbawić tabelę **wszystkich** krawędzi przepływu danych, czyniąc ją
w pełni izolowaną w podgrafie DATA_FLOW. Ponieważ w oryginalnych grafach tabele izolowane
nie występują, trywialna reguła „tabela izolowana ⟹ zainfekowana" pozwala rozpoznać znaczną
część pozytywów bez żadnego uczenia i sztucznie zawyża wynik. Aby zmierzyć skalę tego
zjawiska, każdą metodę oceniono w dwóch wariantach: **napompowanym** (izolowane pozostają
w puli kandydatów) oraz **uczciwym** (flaga `exclude_isolated` usuwa je z puli). Tabela 4.2
zestawia oba warianty.

**Tabela 4.2.** Wpływ przecieku izolacji na AUC-ROC (protokół indukcyjny).

| Metoda | Napompowany | Uczciwy |
|---|:---:|:---:|
| Brzeg (root/leaf) | 0,600 | 0,455 |
| Niska łączność jobów | 0,518 | 0,324 |
| Random Forest | 0,816 | 0,749 |
| LightGBM | 0,805 | 0,720 |
| **LineageDetector\*** | **0,842** | **0,771** |

Heurystyki lokalne tracą najwięcej: `boundary` spada z 0,600 do 0,455, a
`low_job_connectivity` z 0,518 do 0,324 — „żyły" one głównie z przecieku izolacji. Metody
uczone spadają znacznie łagodniej (RF: 0,816→0,749; LineageDetector: 0,842→0,771),
co pokazuje, że opierają się na rzeczywistym sygnale strukturalnym, a nie na trywialnej
regule. W obu wariantach LineageDetector pozostaje najlepszy.

> **Haczyk metodyczny (do wyraźnego zaznaczenia).** Oba warianty uśredniono po **różnej
> liczbie grafów wiarygodnych**: uczciwy — 8, napompowany — 10. Wykluczenie izolowanych
> zmniejsza liczbę pozytywów, przez co dwa grafy spadają poniżej progu `MIN_POS = 5`.
> Z tego powodu **nie należy odejmować wartości 1:1** między kolumnami tabeli 4.2 jako
> „wielkości przecieku"; liczby ilustrują tendencję (metody uczone są odporniejsze),
> a nie dokładny ubytek. Ścisłe porównanie wymagałoby wspólnego podzbioru grafów.

### Wrażliwość na odsetek usuwanych zadań

Zbadano wpływ parametru `removal_ratio` (udział usuwanych jobów łączących) na wynik
LineageDetectora, przy wartościach 0,05 / 0,10 / 0,20 / 0,30 (tabela 4.3).

**Tabela 4.3.** Wrażliwość LineageDetectora na `removal_ratio` (AUC-ROC, protokół indukcyjny).

| removal_ratio | 0,05 | 0,10 | 0,20 | 0,30 |
|---|:---:|:---:|:---:|:---:|
| AUC-ROC | 0,761 | 0,771 | 0,755 | 0,754 |

Wynik jest **stabilny**: w całym badanym zakresie AUC-ROC mieści się w przedziale
0,754–0,771, a różnice są rzędu wariancji między powtórzeniami. Oznacza to, że skuteczność
detektora nie zależy istotnie od intensywności symulowanego broken lineage — zarówno przy
rzadkich (5%), jak i częstych (30%) usunięciach zadań detektor zachowuje porównywalną
jakość rankingu.

## 4.4 Analiza wyników

**Dlaczego LineageDetector wygrywa.** Przewaga detektora wynika z połączenia trzech
niezależnych źródeł sygnału. Cechy pozycji w DAG opisują węzeł lokalnie, lecz nie
odróżniają osieroconej tabeli-następnika od prawdziwego źródła. Score kompletności
*peer-consistency* dokłada sygnał **relacyjny** — porównuje tabelę z jej peerami wpadającymi
do tych samych zadań — którego żadna cecha lokalna nie zawiera; to on odpowiada za wzrost
AUC-PR. Kalibracja izotoniczna nie zmienia rankingu, lecz urealnia oszacowania
prawdopodobieństwa, obniżając Brier score do najlepszej w zestawieniu wartości 0,106.

**Dlaczego heurystyki oparte na wspólnych sąsiadach zawodzą.** Podgraf przepływu danych jest
**dwudzielny** (tabele łączą się wyłącznie z zadaniami, nie bezpośrednio z innymi tabelami),
więc miary typu Common Neighbors, Jaccard czy Adamic-Adar są tożsamościowo zerowe między
węzłami tego samego typu i nie niosą informacji — dlatego wykluczono je z implementacji.
Heurystyki oparte na stopniu i roli w grafie mierzą jedynie lokalny symptom, który po
usunięciu przecieku izolacji przestaje wystarczać.

**Główna trudność zadania.** Najtrudniejszym przypadkiem pozostaje osierocona
tabela-następnik: po usunięciu zadania traci ona producenta (in_df = 0) i staje się
strukturalnie identyczna z prawdziwą tabelą źródłową. Rozróżnienie ich jest możliwe tylko
dzięki kontekstowi relacyjnemu (czy peerzy również są źródłami) oraz uczeniu na innych
grafach — co wyjaśnia, dlaczego metody indukcyjne przewyższają heurystyki, a sygnał
topologiczny, choć użyteczny, ma naturalny sufit skuteczności (AUC-ROC ≈ 0,77) bez dostępu
do semantyki nazw i schematów.

---

# Rozdział 5 — Uwagi końcowe

Rozdział podsumowuje uzyskane wyniki, odnosząc je do postawionych pytań badawczych,
oraz wskazuje kierunki dalszych badań.

## 5.1 Podsumowanie

Celem pracy było zbadanie, w jakim stopniu sama topologia grafu lineage pozwala wskazać
tabele o zerwanym pochodzeniu danych. Poniżej odniesiono się do pytań badawczych.

**PB1 — Techniki ekstrakcji grafów lineage.** Praca korzysta z gotowych, rzeczywistych
grafów zbioru DLG-DG-23, wczytywanych z reprezentacji JSON (węzły + krawędzie z typami
`asset_type`, `relation_type`) do postaci skierowanego grafu DAG przepływu danych. Pokazano,
że dla zadania detekcji węzłów wystarcza podgraf przepływu (krawędzie DATA_FLOW między
tabelami a zadaniami), bez potrzeby odtwarzania semantyki nazw czy schematów.

**PB2 — Adaptacja ML do wykrywania niekompletności lineage.** Zaadaptowano trzy klasyczne
klasyfikatory (Random Forest, RUSBoost, LightGBM) z zadania klasyfikacji par obiektów do
**klasyfikacji węzła** na podstawie 13-elementowego wektora cech topologicznych, oraz
zaproponowano autorski detektor LineageDetector. Wykazano, że metody uczone przewyższają
heurystyki, a najlepszy wynik — AUC-ROC 0,771 przy najlepszym Brier score 0,106 — osiąga
LineageDetector łączący cechy pozycji w DAG, relacyjny score kompletności i kalibrację.

**PB3 — Obsługa rekurencji (CTE) i UDF.** W przyjętym ujęciu przyczyny broken lineage (UDF,
tabele tymczasowe, zapytania rekurencyjne) są modelowane **jednolicie** — jako usunięcie
węzła-zadania wraz z jego krawędziami — niezależnie od konkretnego mechanizmu. Dzięki temu
detektor nie wymaga osobnej obsługi każdego typu transformacji; ograniczeniem jest brak
rozróżnienia przyczyny zerwania, co pozostaje otwartym kierunkiem.

**PB4 — Metryki i datasety.** Zastosowano zbiór DLG-DG-23 jako *ground truth* oraz metryki
rankingowe czułe na niezrównoważenie klas (AUC-ROC, AUC-PR, Precision@k/Recall@k/Hits@k,
Brier). Zaproponowano protokół ewaluacji **indukcyjnej** cross-graph oraz kontrolę przecieku
izolacji (`exclude_isolated`) — element metodyczny niezbędny dla uczciwej oceny, dotąd
nieobecny w literaturze broken lineage.

**Wniosek główny.** Sama topologia grafu lineage niesie **umiarkowany, lecz użyteczny**
sygnał o broken lineage na poziomie węzłów (LineageDetector, AUC-ROC 0,771 w wariancie
uczciwym i indukcyjnym). Praca pozycjonuje się jako *topology-only baseline* — punkt
odniesienia dla bogatszych metod grafowo-semantycznych (grafy wiedzy, GNN), pokazujący,
ile można osiągnąć bez dostępu do nazw i schematów, oraz uzupełniający dotychczasowe
podejścia o brakujące ujęcie węzłowe: wskazanie podejrzanych tabel może poprzedzać
kosztowniejsze odtwarzanie konkretnych zależności.

## 5.2 Kierunki dalszych badań

- **Indukcyjne grafowe sieci neuronowe (GNN).** Naturalnym następnym krokiem po cechach
  topologicznych są modele uczące reprezentacji węzła z propagacją komunikatów: GraphSAGE,
  R-GCN, HGT. Metoda Node2Vec została świadomie wykluczona z protokołu indukcyjnego, gdyż
  uczy zanurzeń **transduktywnie** (embeddingi nieporównywalne między grafami) — jest to
  wynik motywujący GNN, a nie luka implementacyjna.

- **Zewnętrzny zbiór testowy (weryfikacja przenośności cross-dataset).** Naturalnym
  rozszerzeniem protokołu indukcyjnego jest wytrenowanie detektora na grafach DLG-DG-23
  i przetestowanie go na **niezależnym** benchmarku grupy promotora
  (`github.com/dudenzz/lineage`; Dutkiewicz, Misiorek, Wrembel), zbudowanym z bazy
  Northwind i syntetycznych scenariuszy SQL. Rola czysto testowa jest wręcz korzystniejsza
  niż współtrenowanie: stanowi mocny sprawdzian generalizacji między różnymi domenami
  (produkcyjny Huawei Cloud vs. syntetyczny Northwind). Warunkiem jest adapter mapujący
  reprezentację benchmarku (RDF/CSV, lineage wierszowy w `DataLineage.csv`) na model
  tabela–zadanie–DATA\_FLOW oraz automatyczne wyznaczenie etykiet zainfekowanych tabel —
  ten sam nakład mapowania schematu jest potrzebny niezależnie od tego, czy zbiór posłuży
  do treningu, czy tylko do testu.

- **Włączenie semantyki nazw i schematów.** Sygnał topologiczny badany w pracy i sygnał
  semantyczny (podobieństwo nazw, metadane schematu) są komplementarne [Boinski2025,
  Brzeski2025]. Jeśli dane przestaną być zanonimizowane, połączenie obu powinno przekroczyć
  sufit ≈ 0,77 właściwy podejściu czysto topologicznemu.

- **Potok dwuetapowy detekcja → predykcja.** Wskazanie podejrzanych tabel (niniejsza praca)
  może służyć jako tani etap wstępny ograniczający przestrzeń kandydatów przed kosztowną
  predykcją konkretnych brakujących krawędzi — łącząc oba ujęcia problemu broken lineage.

- **Rozróżnienie przyczyny zerwania.** Rozszerzenie etykiet o typ zdarzenia (UDF vs. tabela
  tymczasowa vs. CTE) umożliwiłoby nie tylko detekcję, lecz i diagnozę przyczyny broken
  lineage.
