# Baza wiedzy — rozmowa z promotorem (wt. 11:15, pok. 126cw)

Wszystko, czego potrzebujesz, żeby opowiedzieć o pracy i obronić każdą liczbę.
Czytaj od góry: od pitcha, przez fakty, po trudne pytania na końcu.

---

## 1. Pitch na 30 sekund (naucz się tego płynnie)

> Badam, w jakim stopniu **sama topologia grafu lineage** — bez nazw, schematów
> i semantyki — pozwala wskazać tabele o zerwanym pochodzeniu danych (broken
> lineage). Sformułowałam to jako **ranking węzłów**: każda tabela dostaje
> prawdopodobieństwo, że jej lineage jest zerwany. Mój detektor
> (LineageDetector) osiąga **AUC-ROC 0,771** w uczciwym, indukcyjnym protokole
> na 18 rzeczywistych grafach Huawei (DLG-DG-23) — wyraźnie lepiej niż
> heurystyki i klasyczne ML. To pierwszy **topology-only baseline** dla tego
> problemu: wszystkie dotychczasowe prace, łącznie z pracami Pana zespołu,
> odtwarzają krawędzie; nikt nie pyta, **które tabele są dotknięte**.

## 2. Historia projektu — dlaczego zmiana koncepcji (opowiedz jako WYNIK)

1. **Pierwotny plan:** predykcja konkretnych brakujących krawędzi (job, tabela)
   — w duchu pracy Boińskiego i in. [1]. Trzy scenariusze usuwania:
   A (tabele stagingowe), B (UDF), C (data mart).
2. **Wynik badania wstępnego:** tylko scenariusz B nielosowy (AUC-ROC ~0,70);
   A i C ≈ 0,5 (losowo).
3. **Dlaczego:** grafy DLG-DG-23 są rzadkie (np. DLG1: 298 węzłów, tylko
   24 krawędzie DATA_FLOW), a dane zanonimizowane (UUID) — nie ma ani gęstego
   sąsiedztwa, ani semantyki nazw (Jaro-Winkler z [1] nieaplikowalny).
   Sygnał o KONKRETNEJ parze obiektów jest za słaby.
4. **Konsultacja z dr. Misiorkiem (2026-06-09)** → przeformułowanie na
   **detekcję węzłów**: nie zgadujemy krawędzi, wskazujemy podejrzane tabele.
5. **Kluczowe zdanie obronne:** "To nie porażka metody, tylko wynik o samym
   problemie — potwierdzony zresztą w pracy Pana zespołu: w artykule
   Dutkiewicz/Misiorek/Wrembel scenariusz *temporary tables* daje AUROC 0,49,
   czyli losowo, mimo użycia GNN i grafu wiedzy. Predykcja krawędzi przy
   broken lineage jest po prostu bardzo trudna."

## 3. Słownik pojęć (definicje, które musisz mieć w małym palcu)

- **Data lineage / provenance** — śledzenie pochodzenia i transformacji danych;
  w pracy traktowane jako synonimy.
- **Broken lineage** — przerwanie ciągłości grafu zależności, głównie przez
  tabele tymczasowe (znikają po ETL) i UDF (ukrywają logikę przepływu).
- **Graf DLG-DG-23** — 3 typy węzłów: **Data Job** (zapytanie/zadanie ETL),
  **Data Table**, **field** (kolumna); 2 typy krawędzi: **DATA_FLOW**
  (tabela↔job, skierowana) i **PARENT_CHILD** (tabela→pole).
  Detekcja działa na podgrafie DATA_FLOW (dwudzielny DAG job–tabela).
- **Tabela zainfekowana (infected)** — etykieta symulacyjna: tabela incydentna
  do co najmniej jednego usuniętego joba (straciła producenta lub konsumenta).
- **Job łączący** — job z ≥1 krawędzią wejściową i ≥1 wyjściową DATA_FLOW;
  tylko takie usuwamy (usunięcie zrywa lineage po obu stronach).
- **Protokół indukcyjny (cross-graph)** — trening na jednych grafach, test na
  grafie NIEWIDZIANYM (leave-one-graph-out). Sprawdza generalizację, nie
  zapamiętanie grafu.
- **Wariant uczciwy (exclude_isolated)** — z ewaluacji usuwamy tabele, które po
  symulacji straciły WSZYSTKIE krawędzie DATA_FLOW (patrz sekcja 6 — przeciek).

## 4. Dataset — fakty

- **DLG-DG-23** (Chen i in., Visual Informatics 2024) — 18 grafów z produkcji
  Huawei Cloud, 278–17 085 węzłów, jedyny publiczny zbiór realnych grafów
  lineage. Zanonimizowany (UUID zamiast nazw).
- Klasy wielkości: małe <1000 węzłów (większość), średnie 1000–5000,
  duże >5000 (DLG6: 13 840; DLG18: 17 085).
- Częstość pozytywów w symulacji: **~10–14% kandydatów** — silna nierównowaga
  klas (dlatego AUC-PR ważniejsze od AUC-ROC).

## 5. Metodyka symulacji (jak powstają etykiety)

1. Weź graf → znajdź joby łączące → usuń losowe **10%** z nich
   (removal_ratio=0.10, side=both).
2. Tabele incydentne do usuniętych jobów = **zainfekowane** (etykieta 1),
   reszta = czyste (0).
3. Kandydaci = wszystkie Data Table w grafie obserwowanym.
4. **3 powtórzenia** (seedy 42, 43, 44), agregacja ze średnią po powtórzeniach.
5. Graf "wiarygodny" = ma **≥5 zainfekowanych** w teście (MIN_POS=5);
   tylko takie wchodzą do średnich. **Uczciwy: 8 grafów wiarygodnych,
   napompowany: 10** (wykluczenie izolowanych zmniejsza liczbę pozytywów,
   2 grafy spadają poniżej progu).

## 6. Przeciek i wariant uczciwy (TWÓJ NAJMOCNIEJSZY ARGUMENT)

- Po usunięciu joba **~29% zainfekowanych tabel** traci wszystkie krawędzie
  DATA_FLOW (staje się izolowanych w warstwie przepływu), a **0% czystych**.
- Trywialna reguła "izolowana ⟹ zainfekowana" zawyża więc każdy wynik —
  to przeciek etykiety do cech.
- (Pełna izolacja stopnia 0 nie zachodzi — tabele trzymają krawędzie
  PARENT_CHILD do pól.)
- **Rozwiązanie:** flaga `exclude_isolated` usuwa izolowane z puli kandydatów
  → zadanie trudniejsze i realistyczne: wykryć tabele o CZĘŚCIOWO zerwanym
  lineage. Raportuję oba warianty, uczciwy jako główny.
- **Dowód, że przeciek był realny:** heurystyki brzeg/łączność w wariancie
  napompowanym 0,600/0,518 → w uczciwym **spadają poniżej losowego**
  (0,455/0,324). "Żyły z przecieku". ML i detektor trzymają poziom
  (spadek ~0,07, wciąż mocno >0,5) — ich sygnał jest prawdziwy.
- ⚠️ Nie porównuj wariantów 1:1 liczbowo — różne zbiory grafów wiarygodnych
  (8 vs 10). Uczciwe porównanie tylko na wspólnym podzbiorze.

## 7. Metody (co porównuję)

**Heurystyki (bez uczenia, baseline):**
| nazwa | wzór/idea |
|---|---|
| anomalia stopnia | 1/(1+deg) — mało połączeń = podejrzana |
| brzeg | is_root + is_leaf |
| niska łączność jobów | 1/(1+liczba sąsiednich jobów) |
| reguła korzenia | is_root (in_df=0) — celowo trywialny baseline |
| **kompletność (peer-consistency)** ← wkład własny | patrz niżej |

**Peer-consistency (mój pomysł, realizacja sugestii Misiorka):** tabela-korzeń
jest podejrzana, jeśli jej "peerzy" (inne tabele wpadające do tych samych
downstream-jobów) MAJĄ producentów, a ona nie — prawdziwe źródło zwykle
sąsiaduje z innymi źródłami. Symetrycznie dla liści. To sygnał RELACYJNY
(o otoczeniu), nie lokalny (o samym węźle). 3 cechy: peer_producer_score,
peer_consumer_score, completeness_anomaly (bramkowana: aktywna tylko na brzegu).

**Klasyczne ML:** Random Forest, RUSBoost (nawiązanie do [1]), LightGBM —
binarna klasyfikacja węzła na **13 cechach topologicznych**
(in_df, out_df, degree, role, flow_depth, flow_reach, depth+reach, is_root,
is_leaf, n_field_children, n_job_neighbors, avg_job_in_df, avg_job_out_df).
class_weight=balanced na nierównowagę.

**LineageDetector (wkład główny):**
[13 cech węzła ⊕ 3 cechy kompletności] → RandomForest (300 drzew, balanced)
→ **kalibracja izotoniczna** (CalibratedClassifierCV, cv=3).
Wyjście = rzeczywiste p(zainfekowana), nie dowolny score → można ustawić próg
alarmu. Wspiera ablacje: calibrate=False, use_completeness=False.

**Wykluczenia (świadome decyzje, nie braki):**
- **Node2Vec** — transduktywny: embeddingi uczone per graf są geometrycznie
  nieporównywalne między grafami → nie działa w protokole indukcyjnym.
  To WYNIK motywujący indukcyjne GNN (GraphSAGE/R-GCN/HGT) jako future work.
- **Common Neighbors / Jaccard / Adamic-Adar** — graf dwudzielny job–tabela:
  dwa węzły tego samego typu nie mają wspólnych sąsiadów bezpośrednich.
- **Jaro-Winkler / semantyka nazw** — UUID, nie ma czego porównywać.

## 8. WYNIKI — bieg kanoniczny (te liczby MUSISZ znać)

Ustawienia: 18 grafów, removal_ratio=0.10, side=both, seedy 42–44, LOO,
MIN_POS=5, exclude_isolated. Źródło: results/README_BIEG_KANONICZNY.md.

**Wariant UCZCIWY (główny), 8 grafów wiarygodnych:**

| Metoda | AUC-ROC | AUC-PR | P@k | Brier↓ |
|---|---|---|---|---|
| Niska łączność jobów | 0,324 | 0,112 | 0,094 | 0,226 |
| Anomalia stopnia | 0,427 | 0,165 | 0,142 | 0,134 |
| Brzeg | 0,455 | 0,137 | 0,146 | 0,745 |
| Kompletność* | 0,559 | 0,206 | 0,240 | 0,144 |
| Reguła korzenia | 0,574 | 0,168 | 0,180 | 0,469 |
| RUSBoost | 0,631 | 0,249 | 0,340 | 0,152 |
| LightGBM | 0,720 | 0,381 | 0,398 | 0,147 |
| Random Forest | 0,749 | 0,425 | 0,380 | 0,117 |
| **LineageDetector*** | **0,771** | **0,435** | **0,443** | **0,106** |

\* wkład własny. **LineageDetector najlepszy na WSZYSTKICH metrykach.**
Std AUC-ROC detektora: 0,056 — przewaga stabilna między grafami.

**Wariant NAPOMPOWANY (kontrast), 10 grafów:** LD 0,842, RF 0,816,
LGBM 0,805; brzeg 0,600, łączność 0,518.

**Wrażliwość na removal_ratio** (0,05/0,10/0,20/0,30):
LD = 0,761/0,771/0,755/0,754 — **płasko**; wynik nie jest artefaktem wyboru 10%.
(LightGBM rośnie z ratio 0,706→0,761 — więcej usunięć = więcej przykładów
treningowych.)

**Wariant jednojob** (usuwamy dokładnie 1 job — najtrudniejszy, minimalny
sygnał): RF 0,796, **LD 0,794** (AUC-ROC praktycznie remis), ale LD ma
**najlepszy Brier 0,042** — kalibracja robi różnicę. Uczciwie: w tym wariancie
RF jest minimalnie lepszy w rankingu; przewaga LD to jakość prawdopodobieństw.

## 9. Jak INTERPRETOWAĆ liczby (na wypadek "co to znaczy 0,771?")

- **AUC-ROC 0,771** = biorąc losowo jedną zainfekowaną i jedną czystą tabelę,
  detektor w 77% przypadków da zainfekowanej wyższy wynik. Losowo = 0,5.
- **AUC-PR 0,435** przy częstości bazowej ~0,10–0,13 = **3–4× powyżej
  losowego** (losowy klasyfikator ma AUC-PR = częstość pozytywów).
  Przy nierównowadze klas to metryka ważniejsza niż AUC-ROC.
- **P@k 0,443** (k = liczba zainfekowanych) = wśród top-k wskazań ~44% trafień;
  losowo byłoby ~10–13%.
- **Brier 0,106** (niżej=lepiej) = średni kwadrat błędu prawdopodobieństwa;
  najniższy = najlepiej skalibrowane p(zainfekowana).
- **Uwaga:** w tym biegu P@k = R@k = Hits@k (bo k = liczba pozytywów) — mówić
  o jednej metryce, nie trzech.
- **Ton:** "umiarkowany, ale użyteczny sygnał" — nie przesadzać. 0,771 to nie
  jest 0,95 i nie udajemy, że jest.

## 10. Wkład własny (wymień pewnie, gdy zapyta "co jest Pani?")

1. **Score kompletności peer-consistency** — nowa heurystyka relacyjna;
   najlepsza z heurystyk (0,559), dokłada sygnał nieobecny w cechach lokalnych.
2. **LineageDetector** — połączenie cech DAG + kompletności + kalibracji
   izotonicznej; wygrywa na wszystkich metrykach; zwraca realne
   prawdopodobieństwa (próg alarmu w praktyce).
3. **Protokół z kontrolą przecieku** (exclude_isolated) — sama wykryłam
   i zneutralizowałam przeciek etykiety; raportuję oba warianty.
4. (Metodycznie) sformułowanie broken lineage jako detekcji WĘZŁÓW — luka
   w literaturze.

## 11. Pozycjonowanie wobec prac zespołu promotora (ZNAJ TE PRACE!)

| Praca | Co robi | Relacja do Twojej |
|---|---|---|
| **Boiński i in., ISD 2025** [1] | ML na parach obiektów, cechy z metadanych + Jaro-Winkler, RUSBoost F1=0,79, syntetyczne schematy z LLM | punkt wyjścia; oni: krawędzie+semantyka, ja: węzły+topologia; przejęłam rodzinę klasyfikatorów |
| **Dutkiewicz, Misiorek, Wrembel, EDBT/ICDT WS 2026** | baza→graf wiedzy (RDF, PROV-O, valueDerivedFrom), indukcyjny path-based GNN, benchmark LLM (github.com/dudenzz/lineage), negatywy 50:1, AUROC+Hits@10 | przejęłam protokół indukcyjny i metryki rankingowe; ich **temporary tables = 0,49 (losowo!)** — koronny argument, że krawędzie są trudne |
| **Andrzejewski, Boiński, Wrembel, EDBT/ICDT WS 2026 (DARLI-AP)** | analitycznie odzyskuje funkcję liniową (slope/intercept) i warunek selekcji dla obiektów select-project | wymaga WARTOŚCI danych — u mnie niedostępne; komplementarna |
| **Brzeski, Roman, VLDB AIDB 2025** | bi-encoder + cross-encoder na metadanych schematu, kierunkowe linki kolumn, nierównowaga 1:90 000, dane komercyjne | wymaga semantyki nazw — u mnie UUID; pokazuje wartość sygnału semantycznego, komplementarnego do mojego topologicznego |

**Nisza:** jedyna rodzina metod NIEobecna w tym programie badawczym =
czysta topologia + poziom węzłów. Twoja praca może być baseline'em do
porównania metod planowanego w sekcji 7 pracy TGD.

## 12. Kod i odtwarzalność (gdy zapyta o implementację)

- Pakiet `src/detection/`: job_removal.py (symulacja), node_features.py
  (13 cech), completeness.py (peer-consistency), node_classifier.py
  (heurystyki+ML), lineage_detector.py (detektor), node_metrics.py (metryki),
  run_detection_experiments.py, run_removal_sensitivity.py.
- **70 testów pytest** (m.in. test_job_removal, test_node_features,
  test_lineage_detector, test_completeness).
- Odtworzenie wyników jedną komendą:
  `python -m src.detection.run_detection_experiments --all --exclude-isolated
  --removal-ratio 0.10 --repeats 3 --seed 42`
- Stare podejście (predykcja krawędzi) zarchiwizowane: git tag
  `magisterka_old`, branch `edge-prediction-archive`.

## 13. Stan pracy pisemnej (gdy zapyta "ile napisane?")

- Rozdz. 1 (wstęp), 2 (podstawy + SLR z pracami zespołu), 3 (problem,
  metodyka, architektura, metody) — **napisane**, z rysunkami i tabelami.
- Rozdz. 4 (wyniki) i 5 (wnioski) — struktura gotowa, proza do napisania;
  WSZYSTKIE liczby i rysunki już wygenerowane (bieg kanoniczny).
- Streszczenia PL/EN na końcu. Szacunkowo ~65% całości.
- Plan do września: rozdz. 4 → rozdz. 5 → bibliografia/szlif → streszczenia.

## 14. TRUDNE PYTANIA I GOTOWE ODPOWIEDZI (przećwicz na głos!)

**P: Dlaczego zmieniła Pani koncepcję bez konsultacji ze mną?**
O: Zmiana wynikła z konsultacji z dr. Misiorkiem po tym, jak badanie wstępne
pokazało, że predykcja krawędzi na DLG-DG-23 jest ≈losowa. Chciałam najpierw
mieć wyniki nowego podejścia, żeby przyjść z konkretem, nie z problemem.
Badanie wstępne zostaje w pracy jako motywacja.

**P: Skąd pewność, że symulacja (usuwanie jobów) odpowiada realnemu broken lineage?**
O: Usunięcie joba odwzorowuje dokładnie mechanizm zjawiska: zniknięcie tabeli
tymczasowej lub UDF to utrata całego węzła pośredniczącego wraz z krawędziami
— tak definiują to [1] i praca TGD. DLG-DG-23 to grafy w pełni zaobserwowane,
więc kontrolowana symulacja to jedyny sposób uzyskania ground truth; tak samo
robią wszystkie prace w tym nurcie (Boiński: rekurencyjne zastępowanie
tabel tymczasowych; TGD: generowane scenariusze).

**P: 0,771 to dużo czy mało?**
O: Umiarkowanie dobrze — i tak to opisuję. Kontekst: (1) losowo = 0,5;
(2) AUC-PR 0,435 przy bazie ~0,13 to 3–4× powyżej losowego; (3) w analogicznie
trudnym scenariuszu temporary tables GNN na grafie wiedzy dał 0,49. Sama
topologia, bez żadnej semantyki, niesie realny sygnał — to jest teza pracy,
nie "rozwiązaliśmy problem".

**P: Czemu nie GNN?**
O: Świadoma decyzja zakresu: najpierw ustalić, ile daje czysta topologia
z interpretowalnymi cechami — to brakujący baseline w literaturze. GNN
(GraphSAGE/R-GCN/HGT) to naturalny następny krok i tak go wskazuję; wynik
z Node2Vec (transduktywność uniemożliwia protokół indukcyjny) dodatkowo
uzasadnia, że potrzebne są GNN indukcyjne, nie embeddingi per graf.

**P: Czemu Node2Vec zniknął z porównania?**
O: Node2Vec uczy embeddingów osobno dla każdego grafu — przestrzenie nie są
porównywalne między grafami, więc modelu nie da się nauczyć na 17 grafach
i przetestować na 18. W protokole indukcyjnym jest bezużyteczny; to wynik,
który raportuję, nie pominięcie.

**P: Czy Pani etykiety nie są trywialne (tabela traci krawędź → widać to od razu)?**
O: Dokładnie ten problem wykryłam i kontroluję: ~29% pozytywów staje się
DATA_FLOW-izolowanych i TE wykluczam (wariant uczciwy). Zostają tabele
o częściowo zerwanym lineage, które nadal mają połączenia — trudność w tym,
że osierocona tabela wygląda jak prawdziwe źródło (in_df=0 w obu przypadkach).
To jest właśnie główne wyzwanie zadania.

**P: Dlaczego różna liczba grafów w wariantach (8 vs 10)?**
O: Wykluczenie izolowanych zmniejsza liczbę pozytywów; 2 grafy spadają poniżej
progu wiarygodności MIN_POS=5. Dlatego wariantów nie porównuję 1:1, tylko
opisuję kierunek zmian, a ścisłe porównanie robię na wspólnym podzbiorze.

**P: P@k, R@k, Hits@k — czemu identyczne wartości?**
O: Bo przyjęłam k = liczba zainfekowanych w grafie; wtedy Precision@k
= Recall@k, a Hits@k się z nimi pokrywa. W tabeli raportuję jedną i wyjaśniam
relację, żeby nie sugerować trzech niezależnych metryk.

**P: Skąd wiadomo, że RF w detektorze nie wystarczy? Co daje kompletność i kalibracja?**
O: Kompletność to sygnał relacyjny (o peerach), którego nie ma w cechach
lokalnych — jako samodzielna heurystyka jest najlepsza (0,559 vs 0,32–0,57),
a w detektorze podnosi wynik ponad czysty RF (0,771 vs 0,749). Kalibracja
poprawia Brier (0,106 vs 0,117), czyli jakość samych prawdopodobieństw —
w praktyce pozwala ustawić próg alarmu. Detektor wspiera ablacje
(use_completeness, calibrate) i planuję je pokazać w rozdz. 4.

**P: Jak to się ma do naszego benchmarku KG?**
O: Chętnie przeniosę metodę na Państwa benchmark (github.com/dudenzz/lineage)
— to jeden z moich kierunków dalszych badań; dałoby to bezpośrednią
porównywalność z metodą KG-GNN i wpisało pracę w planowane porównanie rodzin
metod.

**P: Zastosowanie praktyczne?**
O: Narzędzie data governance: ranking tabel do ręcznej inspekcji (audyt,
RODO, bezpieczne usuwanie obiektów). Dzięki kalibracji można ustawić próg
p>t i kontrolować liczbę alarmów. Dwuetapowo: najpierw moja detekcja zawęża
obszar, potem droższe metody (KG-GNN, DARLIAP) odtwarzają konkretne zależności
tylko dla podejrzanych tabel.

## 15. Checklist przed wtorkiem

- [ ] Wydrukuj **wniosek** (wypełniony: 151851, Nowicka Maria, stacjonarne,
      Informatyka, specjalność z USOS; termin: 15 września; uzasadnienie
      gotowe) — najlepiej 2 egzemplarze.
- [ ] Weź **wydruk/laptop z Thesis.pdf** (24 strony) — pokaż rozdz. 2.6 (SLR
      z ich pracami), rys. przed/po, tabelę cech.
- [ ] Miej pod ręką **tabelę wyników** (sekcja 8 tego pliku) — wydrukuj ją.
- [ ] Przećwicz na głos: pitch (sekcja 1), historia pivotu (sekcja 2),
      3 najtrudniejsze pytania (sekcja 14).
- [ ] Pamiętaj: on już wie o pivocie z maila i mimo to podpisuje wniosek —
      rozmowa to zainteresowanie wynikami, nie egzamin.
