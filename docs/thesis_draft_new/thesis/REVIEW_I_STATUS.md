# Przegląd pracy magisterskiej — status i lista zadań

> Stan na **2026-08-04**. Praca: „Odkrywanie zależności między obiektami w bazie danych"
> (Maria Nowicka, 151851, promotor prof. R. Wrembel). Dokument roboczy — mapa tego, co
> zrobione i co zostało. Praca kompiluje się czysto: **25 stron, 0 nierozwiązanych
> odwołań/cytowań**; testy: **77 passed** (`pytest`).

---

## 1. Skrót — gdzie jesteśmy

| Element | Stan |
|---|:---:|
| Rozdz. 1 Wstęp | ✅ gotowe |
| Rozdz. 2 Podstawy + SLR | ✅ gotowe (pogrupowany SLR) |
| Rozdz. 3 Problem i architektura | ✅ gotowe (2 tabele-TODO) |
| Rozdz. 4 Ocena rozwiązania | 🟡 szkielet w .tex, **treść gotowa w `DALSZA_CZESC_PRACY.md`** |
| Rozdz. 5 Uwagi końcowe | 🟡 szkielet w .tex, **treść gotowa w `DALSZA_CZESC_PRACY.md`** |
| Streszczenie / Abstract | 🟡 placeholder w .tex, **treść gotowa w `DALSZA_CZESC_PRACY.md`** |
| Implementacja (`src/`) | ✅ gotowe, 77 testów przechodzi |
| Wyniki (bieg kanoniczny) | ✅ gotowe (`results/agregat_detekcja.csv`) |
| Rysunki (`figures/`) | ✅ wszystkie 4 pliki istnieją |
| Bibliografia | 🟡 uzupełnić pola prac warsztatowych |
| Strona tytułowa / karta pracy | 🟡 placeholder (szablon) |

Legenda: ✅ zrobione · 🟡 do dokończenia · ❌ brak.

---

## 2. CO ZOSTAŁO ZROBIONE

### Implementacja i eksperymenty
- **Kod** w `src/detection/`: loader grafów, symulacja broken lineage (`job_removal`),
  ekstrakcja 13 cech topologicznych (`node_features`), heurystyki, klasyczne klasyfikatory
  (RF, RUSBoost, LightGBM), autorski `LineageDetector` (peer-consistency + kalibracja),
  ewaluacja indukcyjna (`node_metrics`).
- **Testy jednostkowe**: 7 plików, **77 testów, wszystkie przechodzą** (`tests/`).
- **Bieg kanoniczny** (jedno źródło prawdy): 18 grafów, `removal_ratio=0.10`, 3 powtórzenia,
  protokół indukcyjny leave-one-graph-out. Wyniki: `results/agregat_detekcja.csv`
  (uczciwy, 8 grafów) i `results/agregat_detekcja_napompowany.csv` (10 grafów).
  Wynik główny: **LineageDetector AUC-ROC 0,771**, najlepszy na wszystkich metrykach.
- **Analiza wrażliwości** na `removal_ratio` (0,05–0,30): AUC-ROC 0,754–0,771 — stabilny.
- **4 rysunki** gotowe w `figures/` (pdf + png): graf przed/po, potok, AUC uczciwy vs
  napompowany, wrażliwość na removal_ratio.

### Tekst pracy
- **Rozdz. 1 (Wstęp)** — cel, zakres, motywacja (bank/RODO), struktura pracy. Spójny
  z pivotem na detekcję węzłów.
- **Rozdz. 2 (Podstawy + literatura)** — definicje lineage/provenance, struktura grafu,
  broken lineage, detekcja węzłów, metryki rankingowe, **SLR pogrupowany** (2.6.1 prace
  bazowe, 2.6.2 metody pokrewne, 2.6.3 luka, 2.6.4 prace kontekstowe), 5 prac omówionych
  w schemacie Autorzy/Problem/Rozwiązanie/Analiza.
- **Rozdz. 3 (Problem i architektura)** — formalne sformułowanie zadania, **opis zbioru
  DLG-DG-23 scalony w jednej sekcji 3.2**, metodyka symulacji przez usuwanie jobów,
  kontrola przecieku (`exclude_isolated`), architektura potoku, metody detekcji
  (3.5.1 heurystyki, 3.5.2 klasyczne ML, 3.5.3 LineageDetector ze score kompletności),
  **nowa sekcja 3.6** o repozytorium i pochodzeniu algorytmów.

### Poprawki po zwrocie promotora (ta sesja)
- Score kompletności → wtopiony w LineageDetector (nie osobna metoda).
- Spis treści: usunięto pozycje „bez numerka" (memoir `\settocdepth{subsection}`).
- Usunięto podsekcję 3.5.4 (treść wtopiona w moduł ewaluacji 3.4).
- Dodano sekcję 3.6 (repo + provenance algorytmów) + wpisy bib (scikit-learn, imblearn,
  lightgbm).
- Pogrupowano SLR; scalono opis zbioru DLG-DG-23 w sekcji 3.2.

---

## 3. CO ZOSTAŁO DO ZROBIENIA (priorytetowo)

### 🔴 P0 — konieczne do złożenia
1. **Wkleić rozdz. 4 i 5 z `DALSZA_CZESC_PRACY.md` do `.tex`** i zamienić 8 znaczników
   `% TODO` w rozdz. 4–5 na gotową treść. Tabele wyników wstawić jako LaTeX.
2. **Streszczenie (PL) i Abstract (EN)** — zamienić placeholdery w `Thesis.tex`
   (linie 82, 89) treścią z `DALSZA_CZESC_PRACY.md`.
3. **Wstawić 2 rysunki rozdz. 4** — `rys_auc_uczciwy_napompowany.pdf` oraz
   `rys_wrazliwosc_removal_ratio.pdf` (istnieją w `figures/`, ale nie są jeszcze
   referowane w tekście).
4. **URL repozytorium w sekcji 3.6** — zamienić placeholder `github.com/<uzupełnić>`
   na właściwy adres.
5. **Tabela wyników detekcji** — użyć wersji BEZ osobnego wiersza „Kompletność"
   (z `DALSZA_CZESC_PRACY.md`, zgodnie z uwagą promotora). Uwaga: autogenerowana
   `results/tabela_detekcja.tex` wciąż ten wiersz zawiera.

### 🟠 P1 — jakość i kompletność
6. **2 tabele-TODO w rozdz. 3/4**:
   - tabela symulacji (removal_ratio × liczba jobów łączących × % izolowanych pozytywów)
     — `03_...tex`, linia ~187;
   - opis haczyka „8 vs 10 grafów wiarygodnych" w 4.3 (jest w `DALSZA_CZESC_PRACY.md`).
7. **Ujednolicić metryki `k`** — raz jasno napisać, że w tym biegu P@k = R@k = Hits@k
   (bo k = liczba zainfekowanych), by nie sugerować trzech niezależnych metryk.
8. **Bibliografia** — uzupełnić pola prac warsztatowych: `Dutkiewicz2026`,
   `Andrzejewski2025`, `Brzeski2025` (strony, DOI/URL, dokładna nazwa warsztatu).
9. **Strona tytułowa / karta pracy** — placeholder w szablonie (linie 66–69 `Thesis.tex`).

### 🟡 P2 — opcjonalne wzmocnienia
10. **Zewnętrzny zbiór testowy Dutkiewicza** — opisany jako kierunek dalszych badań
    (rozdz. 5). Opcjonalnie: minimalny adapter RDF/CSV → tabela–zadanie–DATA_FLOW,
    by uruchomić DLG-DG-23→Northwind jako test cross-dataset (patrz sekcja 5).
11. **Badania ablacyjne** — wyłączenie kalibracji / cech kompletności w LineageDetector
    (`calibrate=False`, `use_completeness=False`) jako osobny akapit w analizie wyników.
12. **Korekta językowa całości** — jednolitość terminologii (np. „zainfekowana" vs
    „chora"; „zadanie" vs „job"), spójność zapisu liczb (przecinek dziesiętny).

---

## 4. Przegląd rozdział po rozdziale (uwagi merytoryczne)

**Rozdz. 1.** Mocny, klarowny cel i pozycjonowanie (detekcja węzłów jako komplementarna
do predykcji krawędzi). Bez zastrzeżeń.

**Rozdz. 2.** SLR pogrupowany i dobrze umocowany. Luka badawcza („nikt nie robi detekcji
na poziomie węzłów") postawiona wyraźnie. *Do rozważenia:* sekcja 2.2 jest teraz
konceptualna — sprawdź, czy odsyłacz do 3.2 czyta się płynnie.

**Rozdz. 3.** Formalizm poprawny; zbiór opisany w jednym miejscu (3.2). Sekcja 3.6 dobrze
rozgranicza wkład własny od narzędzi zapożyczonych — to odpowiedź na uwagę promotora.
*Braki:* 1 tabela symulacji (TODO).

**Rozdz. 4.** Treść merytoryczna gotowa (w `.md`), oparta wyłącznie na biegu kanonicznym.
Kluczowa uczciwość: raportowanie wariantu uczciwego jako głównego + kontrola przecieku.
*Braki:* przeniesienie do `.tex`, wstawienie tabel i 2 rysunków.

**Rozdz. 5.** Odpowiedzi na PB1–PB4 + kierunki dalszych badań (GNN indukcyjne, zewnętrzny
zbiór testowy, semantyka nazw, potok dwuetapowy). *Braki:* przeniesienie do `.tex`.

---

## 5. Ryzyka / rzeczy do pilnowania
- **Nie mieszać** wyników z `results/*_v2.*` (archiwum, inna wersja detektora) — cytować
  wyłącznie bieg kanoniczny (`README_BIEG_KANONICZNY.md`).
- **Decyzja do potwierdzenia z promotorem:** sposób prezentacji score kompletności
  (jako składnik LineageDetectora, bez osobnego wiersza w tabeli).
- **Warianty uczciwy vs napompowany** mają różną liczbę grafów wiarygodnych (8 vs 10) —
  nie odejmować liczb 1:1.
