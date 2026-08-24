# Plan doprowadzenia pracy do postaci kompletnej rozprawy magisterskiej

> **Struktura: 5 rozdziałów** (zgodnie z wytyczną PP — decyzja zapadła, nie zmieniamy).
> Implementacja i testy wchodzą jako sekcje 3.7–3.9, metodyka SLR jako 2.8.
>
> Stan na 2026-08-12: `Thesis.pdf` = **32 strony**, treść zasadnicza **str. 1–24**,
> literatura str. 25. 15 pozycji bibliografii, 77 testów jednostkowych.
> Cel: **~70 stron treści zasadniczej**, 30–45 pozycji literatury, komplet spisów
> i dodatków. **Bez pisania nowego kodu** — brakujące liczby albo już leżą
> w `results/`, albo wymagają uruchomienia istniejących skryptów z innymi flagami.

---

## 1. Porównanie z typową pracą magisterską z informatyki

Punkt odniesienia: prace magisterskie WIiT PP o profilu badawczym (bazy danych,
eksploracja danych) oraz standardowa karta oceny recenzenta.

| Element | Typowa magisterka INF | Twoja praca | Ocena |
|---|---|---|:---:|
| Objętość treści zasadniczej | 55–80 str. | **24 str.** | ❌ ~2,5× za mało |
| Liczba pozycji literatury | 30–50 | **15** | ❌ |
| Spis rysunków / tabel / listingów | zawsze | **brak** | ❌ |
| Wykaz skrótów i oznaczeń | zwykle | **brak** | ❌ (DAG, ETL, UDF, SLR, AUC, RDF, GNN, CTE, LOGO) |
| Dodatki (załączniki) | 1–4 | **brak** | ❌ |
| Metodyka SLR (protokół, kryteria, PRISMA) | jeśli SLR — obowiązkowo | **brak** (są tylko wyniki) | ❌ masz to w `151851_SLR.pdf` |
| Opis implementacji (stos, struktura, listingi, diagram) | zawsze | **brak** — 3.6 to pół strony | ❌ |
| Listingi kodu | 3–10 | **0** (pakiet `listings` wczytany, nieużyty) | ❌ |
| Opis testów | zwykle sekcja | **brak** (77 testów nigdzie nie wspomniane) | ❌ |
| Analiza wydajności / złożoności | często | **brak** | ❌ |
| Odchylenia standardowe / istotność statystyczna | w pracach badawczych | **brak** (std są w CSV!) | ❌ krytyczne |
| Badania ablacyjne własnej metody | jeśli jest „autorska" metoda | **brak** (flagi w kodzie są) | ❌ krytyczne |
| Zagrożenia trafności (threats to validity) | w pracach empirycznych | **brak** | ❌ |
| Wyniki per obiekt testowy (nie tylko średnie) | zwykle | **brak** (są w CSV) | ❌ |
| Pytania badawcze postawione we wstępie | zawsze | **pojawiają się dopiero w rozdz. 5** | ❌ |
| Jawna lista wkładu własnego we wstępie | zwykle | **brak** | ❌ |
| Przegląd narzędzi przemysłowych | typowe dla INF | **brak** (Atlas, OpenLineage, DataHub…) | ❌ |
| Streszczenie PL + EN | zawsze | ✅ | ✅ |
| Formalne sformułowanie problemu | zwykle | ✅ | ✅ mocne |
| Protokół ewaluacji + kontrola przecieku | rzadkie | ✅ | ✅ **wyróżnik** |
| Uczciwe raportowanie wyniku negatywnego | rzadkie | ✅ (4.1) | ✅ **wyróżnik** |
| Rzeczywisty zbiór danych | rzadkie | ✅ DLG-DG-23 | ✅ **wyróżnik** |
| Test cross-dataset na zewnętrznym zbiorze | bardzo rzadkie | ✅ (4.4) | ✅ **wyróżnik** |
| Osadzenie w bieżących pracach grupy promotora | rzadkie | ✅ | ✅ **wyróżnik** |

### Czym Twoja praca różni się od typowej — i co z tego wynika

**Na plus:** warstwa metodyczna, której większość prac nie ma — protokół indukcyjny
cross-graph, kontrola przecieku izolacji, analiza wrażliwości, test cross-dataset,
uczciwie zaraportowany wynik negatywny (predykcja krawędzi ≈ poziom losowy).
To materiał na osobny punkt „wkład metodyczny", a nie tylko techniczny.

**Na minus:** praca jest napisana jak **artykuł konferencyjny** (zwięzły, wynikowy),
a nie jak **rozprawa** (wyczerpujący opis drogi dojścia). Recenzent ocenia
„kompletność opisu rozwiązania" i „stronę formalno-edytorską" — a pominęłaś
~40 stron pracy, którą realnie wykonałaś: protokół SLR, implementację, testy,
kilka dodatkowych eksperymentów leżących w `results/`.

**Ryzyko nr 1 (merytoryczne):** przewaga LineageDetectora nad Random Forest to
**+0,022 AUC-ROC przy odchyleniu standardowym 0,056–0,064 na 8 grafach**. Bez testu
istotności i bez ablacji recenzent zakwestionuje sens „autorskiego detektora".

**Ryzyko nr 2 (percepcyjne):** brak widocznego elementu inżynierskiego — czytelnik
nie wie, jak uruchomić narzędzie ani jak jest zbudowane. Praca wygląda na mniejszą,
niż jest. Naprawia to rozbudowa 3.7–3.9 + Dodatek A.

---

## 2. Docelowa struktura — 5 rozdziałów

Legenda: ✅ jest · 🟡 jest, rozbudować · 🆕 do napisania · 📊 dane już policzone

```
Strona tytułowa                                          ✅
Karta pracy dyplomowej (placeholder)                     🟡
Streszczenie (PL) / Abstract (EN)                        ✅
Spis treści                                              ✅
Spis rysunków                                            🆕  \listoffigures
Spis tabel                                               🆕  \listoftables
Spis listingów                                           🆕  \lstlistoflistings
Wykaz skrótów i oznaczeń                                 🆕  ~1 str.

1. WSTĘP                                                     5 str. (jest 2)
   1.1 Motywacja i kontekst praktyczny                   🟡  rozwinąć bank/RODO w scenariusz end-to-end
   1.2 Nieformalne sformułowanie problemu                🟡
   1.3 Cel i zakres pracy                                ✅
   1.4 Pytania badawcze PB1–PB4                          🆕  PRZENIEŚĆ z rozdz. 5 — muszą być tutaj
   1.5 Wkład własny pracy (lista 5 punktów)              🆕
   1.6 Struktura pracy                                   ✅

2. PODSTAWY TEORETYCZNE I PRZEGLĄD LITERATURY               20 str. (jest 6)
   2.1 Data lineage i data provenance                    🟡  + why/where/how provenance, PROV-O
   2.2 Grafowa reprezentacja lineage                     🟡  + formalizm: DAG, graf dwudzielny, heterogeniczny
   2.3 Broken lineage — przyczyny i taksonomia           🟡  + TABELA taksonomii (tab. tymczasowa / UDF / CTE /
                                                              ETL zewnętrzny / partycjonowanie / widoki),
                                                              po jednym przykładzie SQL
   2.4 Narzędzia lineage w praktyce przemysłowej         🆕  Apache Atlas, OpenLineage+Marquez, DataHub,
                                                              Spline, Collibra — tabela porównawcza, ~2 str.
                                                              („przegląd technologii", którego oczekuje INF)
   2.5 Detekcja anomalii w grafach                       🟡  rodziny metod: statystyczne / oparte na cechach /
                                                              spektralne / GNN
   2.6 Wykorzystane metody uczenia maszynowego           🆕  RF, boosting, RUSBoost, LightGBM, kalibracja
                                                              izotoniczna, uczenie przy niezbalansowaniu — ~3 str.
   2.7 Metryki ewaluacji                                 ✅
   2.8 Systematyczny przegląd literatury                 
       2.8.1 Metodyka przeglądu                          🆕  ★ z 151851_SLR.pdf: pytania, bazy (Scopus/WoS/
                                                              ACM/IEEE/DBLP), łańcuchy zapytań (w listingu),
                                                              kryteria wł./wykl., DIAGRAM PRISMA, liczby
                                                              na każdym etapie selekcji
       2.8.2 Charakterystyka zbioru prac                 🆕  rozkład lat, typów publikacji, ujęć problemu
       2.8.3 Prace bazowe                                ✅
       2.8.4 Metody pokrewne                             ✅
       2.8.5 Prace kontekstowe                           ✅
       2.8.6 Synteza — tabela porównawcza prac           🆕  ★ kolumny: poziom predykcji (krawędź/węzeł),
                                                              źródło sygnału, dane, protokół, metryki, wynik,
                                                              relacja do niniejszej pracy
       2.8.7 Luka badawcza                               ✅

3. PROBLEM I SPOSÓB JEGO ROZWIĄZANIA                        22 str. (jest 8)
   3.1 Formalne sformułowanie problemu                   ✅
   3.2 Założenia i ograniczenia przyjętego modelu        🆕  jawnie: symulacja ≠ rzeczywiste zerwanie,
                                                              tylko DATA_FLOW, tylko Data Table, brak semantyki
   3.3 Zbiór danych DLG-DG-23                            🟡  + histogram rozkładu stopni, rozkład ról
                                                              (📊 `results/role_degree_stats.csv`)
   3.4 Metodyka symulacji broken lineage                 🟡  ⬜ DOKOŃCZYĆ tabelę-TODO (`03_...tex` linia ~187):
                                                              removal_ratio × liczba jobów łączących ×
                                                              śr. liczba infected × % izolowanych pozytywów
   3.5 Kontrola przecieku izolacji                       ✅
   3.6 Protokół ewaluacji indukcyjnej                    🟡  wydzielić z 3.4.3; + PSEUDOKOD
                                                              (Algorytm 1: leave-one-graph-out)
   3.7 Zaimplementowane metody detekcji                  ✅  heurystyki / klasyczne ML / LineageDetector
                                                          🟡  + PSEUDOKOD peer-consistency (Algorytm 2)
                                                              + rysunek poglądowy: tabela vs jej peerzy
   3.8 Implementacja                                     🆕  ★ ~7 str., cały blok nowy:
       3.8.1 Stos technologiczny                         🆕  tabela: Python 3.10, NetworkX, scikit-learn,
                                                              imbalanced-learn, LightGBM, pandas, pytest — z WERSJAMI
       3.8.2 Struktura repozytorium                      🆕  drzewo katalogów + odpowiedzialności modułów
       3.8.3 Architektura kodu                           🆕  diagram: loader → job_removal → node_features →
                                                              detektory → node_metrics
       3.8.4 Format danych wejściowych                   🟡  + LISTING fragmentu DLGi-node.json / DLGi-edge.json
       3.8.5 Kluczowe fragmenty implementacji            🆕  3–5 listingów: ekstrakcja cech, peer-consistency,
                                                              pętla LOGO, kalibracja
       3.8.6 Złożoność obliczeniowa i czasy wykonania    🆕  tabela: graf → liczba węzłów → czas ekstrakcji
                                                              cech / trenowania / scoringu
   3.9 Testy i odtwarzalność                             🆕  ★ ~2 str.:
                                                              77 testów — tabela plik → co pokrywa → liczba;
                                                              własności sprawdzane (poprawność etykiet, brak
                                                              przecieku, determinizm); ziarna, bieg kanoniczny,
                                                              polecenia regeneracji, URL repozytorium
   3.10 Pochodzenie algorytmów i wkład własny            ✅  (obecna 3.6, po odjęciu części o repo)

4. OCENA ROZWIĄZANIA                                        18 str. (jest 8)
   4.1 Plan eksperymentów                                🆕  tabela E1–E9: cel · konfiguracja · sekcja
   4.2 Badanie wstępne: predykcja krawędzi               ✅
   4.3 Wyniki główne (± odchylenie standardowe)          🟡  📊 std SĄ w `agregat_detekcja.csv`
   4.4 Istotność statystyczna różnic                     🆕  ★ KRYTYCZNE: Wilcoxon signed-rank dla par
                                                              (LineageDetector vs RF / LightGBM / RUSBoost)
                                                              na 8 grafach + poprawka Holma. Jeśli p > 0,05 —
                                                              napisać wprost i przeformułować wniosek główny na
                                                              „nie gorszy w rankingu, istotnie lepszy w kalibracji"
   4.5 Wyniki w rozbiciu na grafy                        🆕  📊 `wyniki_detekcja_canon.csv` — 8 grafów × 9 metod
   4.6 Kontrola przecieku izolacji                       ✅
   4.7 Wrażliwość na removal_ratio                       ✅
   4.8 Badanie ablacyjne LineageDetectora                🆕  ★ KRYTYCZNE: `calibrate=False`,
                                                              `use_completeness=False`, oba wyłączone —
                                                              jedyny bezpośredni dowód, że wkład własny działa.
                                                              Kod gotowy, wystarczy uruchomić.
   4.9 Ważność cech                                      🆕  permutation importance — 1 rysunek + interpretacja
   4.10 Test cross-dataset na grafie DUT                 ✅  NAPISANE — zostaje przy removal_ratio = 0,3
                                                          🟡  + akapit o przeglądzie konfiguracji
                                                              (📊 `results/cross_dataset_dut_sweep.md`) — patrz §3
   4.11 Warianty protokołu                               🆕  📊 wszystko policzone:
                                                              - jeden usunięty job (`wyniki_jednojob.csv`)
                                                              - generalizacja skali (`wyniki_skala.csv`)
                                                              - protokół transduktywny (`wyniki_transduktywny.csv`)
   4.12 Analiza błędów — studium przypadku               🆕  jeden graf: 5 największych FP i FN, dlaczego
   4.13 Analiza wyników (dyskusja)                       ✅  (obecna 4.5)
   4.14 Zagrożenia trafności                             🆕  ★ wewnętrzna (symulacja przez usuwanie jobów vs
                                                              rzeczywiste zerwanie), zewnętrzna (1 zbiór,
                                                              18 grafów, jedna domena), konstrukcji (czy
                                                              „incydentna do usuniętego joba" = „zainfekowana"),
                                                              wnioskowania (8 grafów, 3 powtórzenia)

5. UWAGI KOŃCOWE                                             5 str. (jest 3)
   5.1 Realizacja celu pracy                             🟡
   5.2 Odpowiedzi na pytania badawcze PB1–PB4            ✅
   5.3 Wkład własny — podsumowanie                       🆕
   5.4 Ograniczenia pracy                                🆕
   5.5 Kierunki dalszych badań                           🟡  ⬜ USUNĄĆ punkt o zewnętrznym zbiorze testowym
                                                              (już zrobiony — jest sekcją 4.10); zastąpić:
                                                              „większy graf zewnętrzny o topologii rozgałęzionej"

BIBLIOGRAFIA                                             🟡  15 → 30–45 pozycji

DODATEK A. Instrukcja uruchomienia i zawartość repozytorium   🆕  2 str.
DODATEK B. Pełne wyniki eksperymentów (18 grafów × metryki)   🆕  3–4 str. (auto z CSV)
DODATEK C. Protokół SLR: łańcuchy zapytań i lista prac        🆕  2 str.
DODATEK D. Przegląd konfiguracji testu cross-dataset          🆕  1–2 str. (z `cross_dataset_dut_sweep.md`)
```

**Szacunek: 5 + 20 + 22 + 18 + 5 = 70 str. treści + ~14 str. literatury i dodatków
≈ 84 str. całości.** Można zejść do ~60 str. treści rezygnując z 2.4, 2.6 i Dodatku D.

---

## 3. Decyzja: NIE podmieniać sekcji 4.10 na removal_ratio = 0,4

Rekomendacja: **zostawić removal_ratio = 0,3 jako liczby główne** i wykorzystać
przegląd jako *dodatkowy dowód odporności*, nie jako zamiennik.

**Dlaczego nie podmieniać:**

1. **To byłby dobór konfiguracji pod wynik.** Cały bieg kanoniczny pracy używa
   `removal_ratio = 0,10`, a analiza wrażliwości (4.7) bada zakres 0,05–0,30.
   Wartość 0,4 leży **poza badanym zakresem** i pojawiłaby się wyłącznie w tej jednej
   sekcji. Pierwsze pytanie na obronie: „dlaczego akurat tu 0,4?". Odpowiedź
   „bo wtedy mój detektor wygrywa" jest nie do obrony.
2. **Argument z progu MIN_POS jest słabszy, niż wygląda.** 5,4 zainfekowanych to
   *średnia* z 25 powtórzeń — czyli w mniej więcej połowie powtórzeń graf i tak jest
   poniżej progu. To nie przekracza bariery wiarygodności, tylko ją uśrednia. Przy
   21 kandydatach test pozostaje jakościowy niezależnie od ratio.
3. **Obecny tekst jest naukowo mocniejszy niż podmieniony byłby.** Sekcja 4.10 już
   teraz uczciwie tłumaczy, *dlaczego* LineageDetector nie wygrywa na DUT: łańcuchowa
   topologia nie daje peerów, więc peer-consistency milczy. To jest **wynik o warunkach
   stosowalności metody** — cenniejszy i bezpieczniejszy niż marginalna wygrana
   0,684 vs 0,656. Pokazanie, kiedy metoda nie działa, buduje wiarygodność.

**Co zrobić zamiast podmiany** — dopisać do 4.10 jeden akapit i tabelę w Dodatku D:

- Przegląd 2 warianty × 3 wartości ratio × 25 powtórzeń potwierdza, że wnioski
  z sekcji **nie są artefaktem jednej konfiguracji** (klasyczna kontrola odporności).
- **Monotoniczność:** im więcej usuniętych zadań, tym silniejszy sygnał i tym lepsze
  metody uczone (napompowany: 0,767 → 0,812 → 0,843 AUC-ROC dla ratio 0,2/0,3/0,4).
  To sensowna własność — potwierdza, że modele reagują na natężenie zjawiska,
  a nie na szum.
- **Najmocniejszy pojedynczy fakt z przeglądu:** score kompletności daje AUC-ROC
  **dokładnie 0,500 we wszystkich sześciu konfiguracjach**. To dowód, że sygnał
  peer-consistency jest na DUT **tożsamościowo zerowy z przyczyn strukturalnych**
  (brak rozgałęzień), a nie że „wypadł słabo". Obecny tekst mówi tylko „załamuje się";
  z przeglądem możesz to postawić jako twarde stwierdzenie o topologii.
- **Obserwacja o progu**, sformułowana jako spostrzeżenie, nie jako główny wynik:
  *„przy silniejszym zaburzeniu (ratio 0,4), gdy liczba zainfekowanych tabel zbliża
  się do progu wiarygodności, LineageDetector wraca na prowadzenie (AUC-ROC 0,684
  wobec 0,656 dla LightGBM, przy najlepszym P@k 0,555) — przewaga detektora ujawnia
  się dopiero przy dostatecznej liczbie pozytywów, co jest spójne z obserwacją
  z sekcji 4.6 o wpływie liczby pozytywów na stabilność oszacowań."*

Tak sformułowane dostajesz cały kredyt za mocniejszy wynik, bez ryzyka zarzutu
o dobieranie konfiguracji.

---

## 4. Kolejność prac

### 🔴 P0 — bez tego praca jest niekompletna merytorycznie *(~3 dni)*

1. ✅ **ZROBIONE — Test istotności statystycznej** — nowa sekcja 4.3
   `\label{sec:istotnosc}` + tabela `tab:istotnosc`. Skrypt:
   `scripts/test_istotnosci.py`, wyniki: `results/istotnosc_wilcoxon.csv`.
   Wynik: przewaga nad heurystykami istotna (wszystkie 20 porównań,
   $p_{Holm}$ = 0,039); nad RUSBoost i LightGBM istotna na AUC-PR i Brier
   ($p_{Holm}$ = 0,023); **wobec Random Forest brak istotności**
   ($p_{Holm}$ = 0,109–0,461). Wnioski przeformułowane w streszczeniu PL/EN,
   w PB2 i w sekcji „Analiza wyników".
2. ✅ **ZROBIONE — Badanie ablacyjne** — nowa sekcja 4.4 `\label{sec:ablacja}`
   + tabela `tab:ablacja`. Skrypt: `src/detection/run_ablation.py`, wyniki:
   `results/wyniki_ablacja.csv`, `results/istotnosc_ablacja.csv`.
   Wynik: score kompletności odpowiada za przewagę (ubytek P@k −0,042,
   istotny, 8/8 grafów); **kalibracja izotoniczna pogarsza ranking**
   (AUC-ROC 0,786 bez niej vs 0,771 z nią), poprawiając Brier.
3. ✅ **ZROBIONE — Odchylenia standardowe w tabeli głównej** (4.2).
4. ✅ **ZROBIONE — Wyniki per graf** — nowa sekcja 4.3 `sec:per-graf`,
   tabela `tab:per-graf`. Ujawnia, że rozrzut między grafami (0,18) jest
   ośmiokrotnie większy niż przewaga detektora nad RF (0,022) — to bezpośrednio
   tłumaczy brak istotności statystycznej.
5. ✅ **ZROBIONE — Zagrożenia trafności** — nowa sekcja 4.9 `sec:trafnosc`,
   cztery kategorie (konstrukcji, wewnętrzna, zewnętrzna, wnioskowania).
6. ✅ **ZROBIONE — Tabela symulacji** (3.4, `tab:symulacja`). Skrypt:
   `scripts/tabela_symulacji.py`. Kluczowa liczba: przy biegu kanonicznym
   22,9% pozytywów to tabele izolowane — to mierzy skalę przecieku.
7. ✅ **ZROBIONE — Akapit o przeglądzie konfiguracji** w sekcji cross-dataset.
8. ✅ **ZROBIONE — 5.5** — punkt przeformułowany na „większy graf zewnętrzny
   o topologii rozgałęzionej" + uwaga o liczbie grafów a mocy testu.
9. ⬜ **Skomitować** `src/data/dutkiewicz_adapter.py` i `src/detection/run_cross_dataset.py`
   — sekcja cross-dataset opisuje adapter, którego nie ma w repozytorium.
   (Wymaga Twojej zgody — nie commituję bez pytania.)

### 🟠 P1 — objętość i standard formalny *(~5 dni)*

10. ✅ **ZROBIONE — Sekcje 3.8–3.9 (implementacja + testy)** — stos
    technologiczny z wersjami, struktura repozytorium, format JSON, rdzeń
    peer-consistency, pętla LOGO, złożoność obliczeniowa, tabela 83 testów,
    odtwarzalność. 4 listingi, 2 tabele.
11. ✅ **ZROBIONE — Metodyka SLR** — sekcja 2.8.1: strategia wyszukiwania
    (DBLP, zapytanie), kryteria włączenia/wyłączenia, tabela przebiegu
    selekcji (1256 → 288 → 24 → 17 → 7) oraz **jawna deklaracja**, że trzy
    prace (Dutkiewicz, Andrzejewski, Brzeski) dołączono spoza procedury SLR
    — inaczej liczby by się nie zgadzały. Dodatkowo sekcja 2.8.6 „Synteza
    porównawcza" z tabelą pozycjonującą pracę na dwóch wymiarach.
12. ✅ **ZROBIONE — Spisy** (rysunków, tabel, listingów) + **wykaz skrótów
    i oznaczeń** (21 skrótów + 10 oznaczeń).
13. ✅ **ZROBIONE — Dodatki A, B, C.** A: instrukcja uruchomienia (polecenia
    odtwarzające każdą tabelę rozdz. 4). B: pełne wyniki dla wszystkich
    18 grafów × 4 metryki, generowane skryptem `scripts/dodatek_wyniki.py`.
    C: przegląd konfiguracji testu cross-dataset.
14. ✅ **ZROBIONE — Bibliografia 16 → 43 pozycje**, wszystkie cytowane
    w tekście. Uzupełniono przy okazji `requirements.txt` o `scipy`
    (brakowało, a jest wymagany przez skrypt testów istotności).
    ⬜ **Zostało:** uzupełnić pola prac warsztatowych (strony, DOI/URL,
    dokładna nazwa warsztatu) dla `Dutkiewicz2026`, `Andrzejewski2025`,
    `Brzeski2025` — tego nie da się ustalić bez dostępu do materiałów.
15. ✅ **ZROBIONE — Rozbudowa rozdz. 2**: rodzaje proweniencji (why/where/how,
    PROV-O), taksonomia przyczyn broken lineage (tabela), narzędzia
    przemysłowe (tabela: Atlas, OpenLineage, Spline, DataHub/Collibra +
    argument, że wszystkie zbierają lineage prospektywnie i nie sygnalizują
    braków), rodziny metod detekcji anomalii w grafach, teoria metod ML
    (RF, boosting, RUSBoost, kalibracja izotoniczna), uzupełnione metryki.

**Dawna lista P1 — pozostałe pozycje:**
    klasyka provenance (Cui&Widom, Buneman, Green semirings),
    PROV-O/W3C, OpenLineage, przeglądy lineage, detekcja anomalii w grafach
    (survey Akoglu), GNN (GraphSAGE, R-GCN, HGT), metody (Breiman RF, Seiffert
    RUSBoost, Ke LightGBM, Zadrozny kalibracja), metryki (Davis&Goadrich), testy
    statystyczne (Demšar 2006). Uzupełnić pola prac warsztatowych: `Dutkiewicz2026`,
    `Andrzejewski2025`, `Brzeski2025`.

### 🟡 P2 — dopracowanie

16. ✅ **ZROBIONE — Pytania badawcze + wkład własny we wstępie** (1.4–1.5).
    Przy okazji rozwiązana niezgodność: SLR stawiał PB2 jako pytanie
    o predykcję krawędzi — dopisany akapit o przeformułowaniu po badaniu
    wstępnym, zamiast cichej podmiany treści pytania.
17. ⬜ **Pseudokody — świadomie pominięte.** Sekcja 3.8 zawiera cztery
    listingi z rzeczywistym kodem (peer-consistency, pętla LOGO, format
    danych, struktura repo). Dokładanie pseudokodu tych samych algorytmów
    byłoby duplikacją. Do rozważenia, jeśli promotor woli notację formalną.
18. ✅ **ZROBIONE — Warianty protokołu** (sekcja 4.13 + podsekcja 4.13.3).
    **Uwaga:** CSV-ki leżące w `results/` pochodziły z innej konfiguracji
    (ratio 0,2, wariant napompowany) — wszystkie trzy warianty przeliczono
    ponownie w konfiguracji kanonicznej, inaczej porównanie z tabelą główną
    byłoby nieuczciwe.
    Wyniki: transduktywny łatwiejszy od indukcyjnego (RF +0,045, detektor
    tylko +0,019 — sygnał relacyjny lepiej się przenosi); trening na małych
    grafach → test na dużych obniża wszystko o ~0,15 (najpoważniejsze
    ograniczenie praktyczne); wariant jednego zadania podnosi AUC-ROC,
    ale obniża AUC-PR ponaddwukrotnie.
    Wymagało to dodania `LineageDetector` do dwóch skryptów porównawczych
    (2 linie na skrypt) — wcześniej liczyły tylko baseline'y.
19. ✅ **ZROBIONE — Ważność cech** (sekcja 4.12, `scripts/waznosc_cech.py`).
    ★ **Odkrycie:** `peer_consumer_score` ma spadek dokładnie 0,0000 przy
    zerowym odchyleniu. Przyczyna strukturalna: w DLG-DG-23 **każde zadanie
    zapisuje dokładnie jedną tabelę** (100% zadań), więc zbiór peerów
    konsumenta jest zawsze pusty i połowa score'u peer-consistency jest
    martwa. Opisane w 4.12 + zastrzeżenie przy wzorze w 3.5.3.
    Drugi wniosek: najsilniejsze cechy opisują otoczenie węzła
    (`avg_job_in_df`, `n_job_neighbors`), nie sam symptom zerwania.
    ✅ Czasy wykonania — w sekcji 3.8.6.
    ⬜ Analiza błędów (studium przypadku FP/FN) — nie zrobiona.
20. ✅ **ZROBIONE — ujednolicenie „job" → „zadanie"** w tekście ciągłym
    (17 zamian); anglicyzm został tylko w identyfikatorach kodu.
    ⬜ Pełna korekta językowa całości — do zrobienia na końcu, na gotowym
    tekście.

### Drobiazgi redakcyjne

- `\authortitle{}` pusty (`Thesis.tex:55`) — wpisać „inż.", jeśli masz tytuł.
- `\ppsupervisor` — sprawdzić zgodność zapisu stopnia z kartą pracy.
- Przypis w 3.10: „Dostęp zweryfikowano w dniu obrony pracy" → konkretna data.
- Pakiet `listings` wczytany bez ani jednego listingu — znika po dodaniu 3.8.5.
- Komentarze robocze `% [ZACHOWANE]`, `% [ZMIENIONE]` — wyczyścić przed oddaniem źródeł.

---

## 5. Skąd wziąć każdą brakującą liczbę (bez pisania nowego kodu)

| Sekcja | Źródło | Status |
|---|---|---|
| 4.3 std | `results/agregat_detekcja.csv` (kolumny `*_std`) | gotowe |
| 4.5 per graf | `results/wyniki_detekcja_canon.csv` | gotowe |
| 4.10 przegląd konfiguracji + Dodatek D | `results/cross_dataset_dut_sweep.md` | gotowe |
| 4.11 jeden job | `results/wyniki_jednojob.csv` | gotowe |
| 4.11 skala | `results/wyniki_skala.csv` | gotowe |
| 4.11 transduktywny | `results/wyniki_transduktywny.csv` | gotowe |
| 3.3 rozkład stopni/ról | `results/role_degree_stats.csv` | gotowe |
| 4.4 istotność | `scipy.stats.wilcoxon` na `wyniki_detekcja_canon.csv` | skrypt ~20 linii |
| 4.8 ablacja | `run_detection_experiments` + istniejące flagi | tylko uruchomić |
| 4.9 ważność cech | `permutation_importance` na wytrenowanym RF | ~15 linii |
| 3.8.6 czasy | `time.perf_counter()` wokół istniejącego potoku | ~10 linii |
| 3.9 testy | `pytest --collect-only -q` → tabela | 1 polecenie |
