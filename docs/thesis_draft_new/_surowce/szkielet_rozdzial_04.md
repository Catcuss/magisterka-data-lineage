# Szkielet rozdziału 4 — „Ocena rozwiązania" (pytania pomocnicze)

Forma robocza: pod każdym podrozdziałem masz pytania pomocnicze.
Odpowiedz PROZĄ na każde pytanie (nie punktami) — z tych odpowiedzi powstanie
tekst do `Thesis.tex`. Liczby bierz z **biegu kanonicznego**
(`results/README_BIEG_KANONICZNY.md`, `agregat_detekcja*.csv`), NIE z `_v2`.

Zasady promotora: każdą tabelę/rysunek wprowadź zdaniem „Tabela/Rysunek X
przedstawia…" PRZED jej wystąpieniem. Wariant uczciwy = główny, napompowany
= kontrast. Wszędzie te same ustawienia biegu.

Krótki wstęp rozdziału jest już napisany w `Thesis.tex` (zdanie o metodologii
z rozdz. 3) — możesz go rozwinąć jednym zdaniem o strukturze rozdziału.

---

## 4.1 Badanie wstępne: predykcja krawędzi

Cel: pokazać, że pivot był uzasadniony, a nie że coś „nie wyszło". Zwięźle,
1–1,5 strony. Źródła liczb: `results/wyniki_scenariusze.csv`, mail do promotora.

Pytania pomocnicze:
1. Jak w skrócie było sformułowane pierwotne zadanie (predykcja konkretnej
   brakującej krawędzi (job, tabela)) i jak wyglądały scenariusze A/B/C
   (staging / UDF / data mart)?
2. Jaki był protokół tej wstępnej ewaluacji (split, próbki negatywne, metryka)?
3. Jakie liczby wyszły? Który scenariusz był jedyny nielosowy (AUC-ROC ~0.70)
   i jak wypadły pozostałe (≈ losowo)?
4. Jaka cecha danych DLG-DG-23 to tłumaczy (rzadkość grafów, mało dodatnich par,
   UUID zamiast nazw niosących semantykę)?
5. Jaki wniosek stąd płynie i dlaczego prowadzi on do przeformułowania zadania
   na detekcję/ranking chorych węzłów? (Zdanie-most do reszty rozdziału.)
6. (1 zdanie obronne) Dlaczego to jest rzetelny wynik badawczy, a nie porażka —
   co mówi o samym problemie, nie o metodzie?

---

## 4.2 Wyniki detekcji chorych węzłów  [GŁÓWNY WKŁAD — pisz najpierw]

Cel: przedstawić tabelę zbiorczą wariantu uczciwego i opisać ją prozą.
Tabela LaTeX gotowa: `results/tabela_detekcja.tex`. Dane: `agregat_detekcja.csv`.

Pytania pomocnicze:
1. Jakie metody porównujesz w jednym wierszu każda? (5 heurystyk: anomalia
   stopnia, brzeg, niska łączność jobów, reguła korzenia, kompletność;
   + RF, RUSBoost, LightGBM; + LineageDetector.)
2. Jakie metryki są w kolumnach i co każda mierzy w JEDNYM zdaniu
   (AUC-ROC, AUC-PR, Precision@k, Brier)? Czemu przy tym zadaniu (silna
   nierównowaga klas) AUC-PR jest ważniejsza od AUC-ROC?
3. Ile grafów uśredniasz (8 wiarygodnych, MIN_POS=5) i co znaczy „wiarygodny"?
   Jakie ustawienia biegu cytujesz (removal_ratio=0.10, side=both, 3 seedy, LOO)?
4. Która metoda wygrywa i na ilu metrykach? (LineageDetector: AUC-ROC 0.771,
   AUC-PR 0.435, P@k 0.443, Brier 0.106 — najlepszy na wszystkich.)
5. Jak wypadają klasyczne ML względem detektora (RF 0.749, LightGBM 0.720)
   i jak — heurystyki (0.32–0.57)? Który baseline heurystyczny jest najlepszy
   i dlaczego to ciekawe (kompletność 0.559 > pozostałe)?
6. Co oznacza uwaga, że Precision@k = Recall@k = Hits@k w tym biegu
   (bo k = liczba zainfekowanych)? Jak to opisać, by nie sugerować trzech
   niezależnych metryk?
7. Jak zinterpretować rozrzut (std) — czy przewaga LineageDetectora jest
   stabilna między grafami, czy zależy od pojedynczych?

---

## 4.3 Kontrola przecieku i analiza wrażliwości  [ARGUMENT ANTYKRYTYCZNY]

Cel: pokazać rzetelność — sam wykrywasz i neutralizujesz przeciek. To sekcja,
którą promotor doceni najbardziej. Źródła: wariant napompowany
(`agregat_detekcja_napompowany.csv`) vs uczciwy; `run_removal_sensitivity.py`,
`results/_faza2_runs.txt`.

Pytania pomocnicze (przeciek):
1. Na czym polega przeciek? (Po usunięciu joba ~29% chorych tabel staje się
   DATA_FLOW-izolowanych, a 0% czystych — więc trywialna reguła
   „izolowana ⟹ chora" sztucznie zawyża wynik.)
2. Jak go neutralizujesz? (Flaga `exclude_isolated` → wariant uczciwy.)
   Dlaczego pełna izolacja stopnia 0 nie zachodzi (krawędzie PARENT_CHILD
   do pól)?
3. Jak zmieniają się liczby między wariantem napompowanym a uczciwym?
   Które metody „żyły z przecieku" (heurystyki brzeg/łączność spadają
   0.60→0.455, 0.518→0.324), a które trzymają poziom (RF, LightGBM,
   LineageDetector)? Co to mówi o jakości sygnału każdej z rodzin metod?
4. HACZYK metodologiczny: dlaczego warianty mają różną liczbę grafów
   wiarygodnych (uczciwy 8 vs napompowany 10) i dlaczego NIE wolno odejmować
   liczb 1:1 między tabelami? Jak zrobiłaś/zrobisz porównanie na wspólnym
   podzbiorze grafów, żeby było uczciwe?

Pytania pomocnicze (wrażliwość):
5. Jak zmienia się wynik LineageDetectora przy różnym removal_ratio
   (np. 0.05 / 0.10 / 0.20)? Czy jest stabilny?
6. Co ten test wrażliwości dowodzi wobec potencjalnego zarzutu, że wynik
   zależy od arbitralnego wyboru odsetka usuwanych jobów?

---

## 4.4 Analiza wyników  [DLACZEGO — obrona wkładu własnego]

Cel: wyjaśnić przyczyny, nie powtarzać liczb. To odróżnia pracę magisterską
od raportu z eksperymentu.

Pytania pomocnicze:
1. DLACZEGO LineageDetector wygrywa? Jaki sygnał dokłada score kompletności
   (peer-consistency) w porównaniu z czysto lokalnymi cechami węzła?
2. Dlaczego kalibracja poprawia Brier (jakość prawdopodobieństw), nawet gdy
   ranking już jest dobry — i czemu to ważne w zastosowaniu (próg alarmu)?
3. Dlaczego heurystyki oparte na wspólnych sąsiadach (Common Neighbors itp.)
   są tu nieaplikowalne (bipartytowość grafu job–tabela)?
4. Na czym polega główna trudność zadania: dlaczego osierocona tabela-następnik
   „wygląda" jak prawdziwe źródło i myli detektory? Który typ błędu dominuje?
5. Czym różni się zachowanie metod na małych vs dużych grafach
   (per-graf w `results/_det_canon.txt`)? Co to sugeruje o przenośności?
6. (opcjonalnie, jeśli czas) Ablacja: co wnosi `use_completeness` i `calibrate`
   osobno? To najmocniejszy materiał na obronę wkładu własnego.

---

## Checklist przed zamknięciem rozdziału 4
- [ ] Każda tabela/rysunek ma zdanie wprowadzające PRZED wystąpieniem.
- [ ] Wariant uczciwy jako główny; napompowany opisany jako kontrast/aneks.
- [ ] Wszędzie te same ustawienia biegu (removal_ratio, seedy, side, MIN_POS).
- [ ] Liczby zgodne z `README_BIEG_KANONICZNY.md` (nie mieszać z `_v2`).
- [ ] Relacja P@k = R@k = Hits@k wyjaśniona słownie.
- [ ] Badanie wstępne (4.1) napisane jako motywacja, nie jako porażka.
