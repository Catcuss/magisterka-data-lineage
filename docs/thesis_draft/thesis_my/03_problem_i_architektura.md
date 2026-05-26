# 3. Problem i architektura rozwiązania

---

## 3.1 Sformułowanie problemu

<!-- Odpowiedz na te pytania: -->

<!-- Jak formalnie opisać graf lineage który masz — co to jest G_obs i G*? -->
Graf lineage mozna formalnie opisac jako G = (V,E), gdzie V to zbiór obiektów bazodanowych, a E* to krawędzie reprezentujące zbiór wszystkich relacji DATA_FLOW. Po usunięciu krawędzi dostajemy graf G_obs = (V,E_obs), gdzie E_obs to krawędzie które widzimi ale nie jest to zbiór wszystkich krawędzi. Celem jest wyznaczenie funkcji, która dla każdej pary węzłów oszacuje prawdopodobieństwo z jakim dana krawędz istniała w pełnym grafie.

<!-- Czym są brakujące krawędzie E* \ E_obs — co reprezentują w kontekście broken lineage? -->
Krawędzie E*\ E_obs reprezentują zerwane zależności np. poprzez usunięcia tabeli tymczasowej albo ukrycia transformacji przez UDF. To własnie ich istnienie algorytmy będa próbować odtworzyć.
<!-- Jak zamieniasz to na problem klasyfikacji binarnej — co jest klasą 0 a co klasą 1? -->
Problem odkrywania przekształacamy na problem klasyfikacji binarnej, gdzie klasa 1 oznacza że krawędz istnieje, natomiast klasa 0 oznacza, że nie istnieje. Pozwala to określić prawdopodobieństwo istnienia i ułatwia to praca algorytmów jak prawdopobocienstwo przekracza 50% to algorytm przewiduje ze krawedz istanieje.
<!-- Dlaczego tylko pary (Data Table, Data Job) są kandydatami — a nie np. (Table, Table)? --> Kandydatami sa tylko pary job i table poniewaz to wlasnie miedzy tymi wierzcholkami jest relacja DATA_FLOW ktora chcemy przewidywac, nie mozemy brac pod uwage zaleznosci tabla tabla poniewaz one nie istnieja, natomiast relacja miedzy tabla a field to poprostu ektykieta ktora kolumna nalezy do danej tableli 
<!-- Co algorytm "widzi" a czego nie widzi podczas predykcji? -->

---

## 3.2 Architektura systemu

<!-- TU MUSI BYĆ RYSUNEK — wstaw diagram z draw.io lub narysuj w PowerPoint -->
<!-- Diagram: JSON → loader → NetworkX → splitter → algorytmy → metryki -->

<!-- Opisz każdy komponent jednym akapitem: -->

<!-- Co robi loader.py — jakie pliki wczytuje, co zwraca, jak wygląda struktura NetworkX DiGraph? -->

<!-- Co robi splitter.py — jak działa podział 80/20, jak generowane są próbki negatywne, 
     dlaczego stosunek 1:1, dlaczego próbki muszą być zgodne typologicznie? -->

<!-- Co robi scenario_splitter.py — czym różni się od zwykłego splittera? -->
W kontekscie pracy wykorzystany zostal skrypty do uruchamiania wszystkich implementacji. Spliter korzystal z usuwania losowych mozliwych w sensie te ktore sa miedzy job a table itd natomiast scenario_splitter rozdziela na 3 wspomniane we wczesniejszym rozdziale scenariusze 
<!-- Jak algorytmy używają G_train — co dostają na wejściu, co zwracają? -->

<!-- Co robi metrics.py — jakie metryki, jak dobierany próg binaryzacji? -->

---

## 3.3 Zbiór danych DLG-DG-23

<!-- Skąd pochodzi dataset — kto go stworzył, kiedy, z jakiego systemu? -->

<!-- Dlaczego wybrałaś akurat ten dataset — co go wyróżnia spośród innych? 
     (podpowiedź: jedyny publiczny dataset rzeczywistych grafów lineage) -->

<!-- Co oznacza że dane są zanonimizowane i jaką ma to konsekwencję dla algorytmów? -->

<!-- Wstaw tabelę 18 grafów: ID | Węzły | Krawędzie DATA_FLOW | Skala (mały/średni/duży) -->

<!-- Jak wygląda rozkład stopni węzłów — czy jest scale-free, co to znaczy dla PA? -->

---

## 3.4 Metodyka symulacji broken lineage

<!-- Dlaczego symulujesz broken lineage przez "chowanie" krawędzi zamiast prawdziwych danych? -->

<!-- Jak działa podział losowy 80/20 — co jest E_train, co E_test, jak to mapuje na broken lineage? -->

<!-- Scenariusz A: które krawędzie chowasz i co to symuluje w rzeczywistości? -->
<!-- Narysuj mały graf przed i po usunięciu krawędzi scenariusza A -->

<!-- Scenariusz B: które krawędzie chowasz i co to symuluje? -->
<!-- Narysuj mały graf przed i po -->

<!-- Scenariusz C: które krawędzie chowasz i co to symuluje? -->
<!-- Narysuj mały graf przed i po -->

<!-- Wstaw tabelę: Scenariusz | Co usuwamy | Co symuluje | Typ węzłów dotkniętych -->

---

## 3.5 Zaimplementowane algorytmy

<!-- === HEURYSTYKI === -->

<!-- Dlaczego w ogóle testujesz heurystyki — jaka jest ich rola jako baseline? -->
heurystyki sa proste w implementacji i dzialaja szybko bez koniecznosci uczenia sie danych wiec mozna latwo je wykorzystac i porownac z bardziej skomplikowanymi rozwiazaniami czy oplaca sie inwestowac czas na uczenie skoro bedzie mozna miec odrazu odpowiedz
<!-- Dlaczego CN/Jaccard/AA nie działają na Twoim grafie — 
     napisz to jednym zdaniem z odwołaniem do bipartytowości -->
Przy wyborze algorytmow rozwarzane zostaly algorytmy CN Jaccard oraz AA jednagrze bo wstepnej analizie okazalo sie ze nie dziala on na grafie dwudzielnym poniewaz wiec zostaly one wyelimowane z naszej implemenacji
Heurystyka 

**Preferential Attachment** (PA) przypisuje parze węzłów $u$ i $v$ wynik proporcjonalny do iloczynu ich stopni:

$$\text{PA}(u, v) = |N(u)| \cdot |N(v)|$$

Intuicja: węzły o dużej liczbie połączeń mają statystycznie większe szanse na nawiązanie nowej relacji — zgodnie z zasadą „bogaty staje się bogatszy" \cite{LibenNowell2007}.

W przeciwieństwie do miar opartych na wspólnych sąsiadach (Common Neighbors, Jaccard, Adamic-Adar), PA nie wymaga istnienia wspólnego sąsiedztwa między $u$ i $v$. Jest to kluczowa własność w grafach dwudzielnych: ponieważ węzły tego samego typu (np. dwie tabele) nigdy nie są bezpośrednio połączone, nie mogą mieć wspólnych sąsiadów w ramach jednej warstwy, co zeruje wyniki CN/Jaccard/AA dla każdej rozpatrywanej pary. PA oblicza się wyłącznie na podstawie stopni węzłów, omijając ten problem.

<!-- L3: wzór, intuicja (co to jest ścieżka długości 3 w kontekście Table→Job→Table→Job),
     złożoność obliczeniowa -->

<!-- Katz: wzór z parametrem beta, jak się ma do L3 (jest jego uogólnieniem) -->

<!-- PPR: idea random walk z restartem, parametr alpha, dlaczego batch obliczenie -->

<!-- === KLASYCZNE ML === -->

<!-- Jakie 11 cech tworzy wektor dla pary (u,v) — wstaw tabelę -->

<!-- Dlaczego nie możesz użyć nazw węzłów jako cech (UUID)? -->

<!-- Dlaczego shortest_path jest najważniejszą cechą — 
     co to mówi o strukturze grafów lineage? (52.6% feature importance) -->

<!-- Random Forest: jak działa bagging, dlaczego class_weight="balanced" -->

<!-- RUSBoost: czym różni się od RF, dlaczego porównujesz z Boiński et al.? -->

<!-- LightGBM: dlaczego gradient boosting, co wnosi względem RF? -->

<!-- === NODE2VEC === -->

<!-- Co to znaczy że węzeł ma "embedding" — jak go sobie wyobrazić? -->

<!-- Dlaczego p=1, q=0.5 — co to zmienia w random walk na grafie bipartytowym? -->

<!-- Jak z dwóch embeddingów węzłów robisz embedding krawędzi (Hadamard)? -->

<!-- Dlaczego Node2Vec NIE jest GNN — czym się różni od GraphSAGE? -->
