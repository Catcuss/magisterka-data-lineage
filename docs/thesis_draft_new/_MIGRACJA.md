# Migracja pracy: predykcja krawędzi → detekcja chorych węzłów

Pivot z 2026-06-09 (konsultacja z dr. Misiorkiem). Stara koncepcja: predykcja
konkretnych brakujących **krawędzi** (link prediction). Nowa koncepcja: **detekcja
zainfekowanych tabel** (ranking węzłów wg p(broken lineage), protokół indukcyjny
cross-graph).

Ten folder (`thesis_draft_new/`) zawiera zaadaptowaną wersję pracy. Oryginał
(`docs/thesis_draft/`) pozostaje nietknięty jako archiwum.

---

## 1. Co WYRZUCIĆ / PRZEROBIĆ z pracy (edge prediction → node detection)

### Do usunięcia w całości (specyficzne dla predykcji krawędzi)
- **Sekcja „Wykrywanie brakujących krawędzi" (link prediction)** — całe ujęcie
  „dla pary węzłów oszacuj P((u,v)∈E)". Zastąpione detekcją węzłów.
- **Formułowanie problemu jako binarnej klasyfikacji PAR** (G* vs G_obs, para
  (job,table), próg 0.5) — zastąpione rankingiem tabel.
- **Scenariusze A/B/C usuwania KRAWĘDZI** (staging/UDF/data mart jako usuwanie
  krawędzi) — zastąpione symulacją przez **usuwanie jobów** (`job_removal.py`).
- **Splitter krawędziowy 60/20/20 + próbki negatywne 1:1** (`splitter.py`,
  `scenario_splitter.py`) — nie dotyczy detekcji węzłów.
- **Node2Vec** (cała podsekcja: biased random walk, Hadamard, MLP) — wykluczony
  z protokołu indukcyjnego (transduktywny). Zostaje TYLKO jako future work.
- **Heurystyki jako predyktory krawędzi PA/L3/Katz/PPR** w dawnej formie (score
  dla pary) — L3/Katz/PPR odpadają; PA ewentualnie jako baseline stopnia węzła.
- **Metryka F1 jako główna** — zadanie rankingowe, nie klasyfikacja przy progu.

### Do przeróbki (zachować szkielet, zmienić treść)
- **Metryki**: zachować AUC-ROC, AUC-PR; dodać Precision@k, Recall@k, Hits@k,
  Brier. Usunąć F1/precision/recall liczone dla krawędzi przy progu 0.5.
- **Cel i zakres pracy** (rozdz. 1) — przeformułowany na detekcję węzłów +
  framing „topology-only baseline".
- **Broken lineage** (rozdz. 2) — konsekwencja opisana na poziomie WĘZŁÓW
  (tabela traci producenta/konsumenta), nie brakujących krawędzi.
- **Boiński et al.** (rozdz. 2) — zmiana roli: z „głównej inspiracji metodycznej"
  na „pracę KONTRASTOWĄ" (oni: krawędzie + semantyka nazw; my: węzły + topologia).
- **Rozdział 3 cały** — przepisany pod job_removal / infected tables /
  LineageDetector / protokół indukcyjny. Patrz `thesis/03_problem_i_architektura.tex`.
- **Rozdział 4** — dawna predykcja krawędzi staje się „badaniem wstępnym"
  (uzasadnienie pivotu); główne wyniki to detekcja węzłów.

### Do ZACHOWANIA bez zmian (nadal aktualne)
- Cała infrastruktura LaTeX: `ppfcmthesis.cls`, `wit/` (logotypy), preambuła.
- Akapity wstępu o data lineage / tabelach tymczasowych / provenance.
- Definicje data lineage vs data provenance (rozdz. 2).
- Opis struktury grafu DLG-DG-23 (typy węzłów/krawędzi) i tabela 18 grafów.
- Przyczyny broken lineage (temp tables, UDF, widoki zmaterializowane).
- Opis zbioru Chen et al. (DLG-DG-23) jako ground truth.
- Motywacja biznesowa (bank, RODO).
- Klasyfikatory RF / RUSBoost / LightGBM (ale jako klasyfikatory WĘZŁÓW).

---

## 2. Co NOWEGO trzeba dopisać (nie istniało w starej pracy)

- Sformułowanie problemu jako detekcji/rankingu węzłów (gotowe w rozdz. 3).
- Symulacja przez usuwanie jobów + definicja „infected" (gotowe w rozdz. 3).
- **Kontrola przecieku** `exclude_isolated` (wariant uczciwy vs napompowany) —
  KLUCZOWE, promotor to doceni (gotowe w rozdz. 3, wyniki: TODO w rozdz. 4).
- **Score kompletności peer-consistency** (wkład własny, gotowe w rozdz. 3).
- **LineageDetector** (wkład własny: cechy DAG + kompletność + kalibracja).
- **Protokół indukcyjny cross-graph** (gotowe w rozdz. 3).
- Nowe pozycje bibliografii: Dutkiewicz/Misiorek, Andrzejewski (DARLIAP), Brzeski.
- Wyniki liczbowe (rozdz. 4) — z `results/wyniki_detekcja_v2.csv` i mailu.

---

## 3. Zawartość tego folderu

```
thesis_draft_new/
├── _MIGRACJA.md                      # ten plik
├── thesis/
│   ├── Thesis.tex                    # NOWY główny plik (detekcja węzłów)
│   ├── 03_problem_i_architektura.tex # NOWY rozdział 3 (job removal, LineageDetector)
│   ├── bibliography.bib              # rozszerzona (stare + Dutkiewicz/DARLIAP/Brzeski)
│   ├── ppfcmthesis.cls               # skopiowany (bez zmian)
│   └── wit/                          # logotypy PP (bez zmian)
└── _surowce/                         # materiał roboczy do wykorzystania
    ├── mail_do_promotora.txt         # REALNE liczby wyników nowej koncepcji
    ├── spotkanie_misiorek_2026-06-09.md
    ├── 01_wstep.md                   # dawny draft wstępu (część reużywalna)
    └── 02_podstawy_teoretyczne.md    # dawny draft podstaw (definicje reużywalne)
```

## 4. Źródła liczb do rozdziału 4 (wyniki)

- `results/wyniki_detekcja_v2.csv`, `results/_det_v2.txt` — wyniki detekcji.
- `results/wyniki_detekcja_honest.csv` vs `wyniki_detekcja.csv` — uczciwy vs napompowany.
- `results/wyniki_jednojob.csv`, `results/_faza2_runs.txt` — wariant 1-job + wrażliwość.
- `mail_do_promotora.txt` — podsumowanie (wariant uczciwy, indukcyjny):
  - score kompletności: AUC-ROC 0.559 (> heurystyki 0.32–0.46),
  - Random Forest: AUC-ROC 0.749; LightGBM: 0.720,
  - **LineageDetector: AUC-ROC 0.771, AUC-PR 0.435, Precision@k 0.443, Brier 0.106** (najlepszy).

## 5. Kod nowej koncepcji (referencja przy pisaniu rozdz. 3)

`src/detection/`: `job_removal.py`, `completeness.py`, `lineage_detector.py`,
`node_features.py`, `node_classifier.py`, `node_metrics.py`,
`run_detection_experiments.py`, `run_removal_sensitivity.py`.
Testy: `tests/test_lineage_detector.py`, `tests/test_completeness.py`.

## 6. Do zrobienia (TODO w plikach .tex)
Wszystkie miejsca wymagające uzupełnienia oznaczono `% TODO` w `Thesis.tex`
i `03_problem_i_architektura.tex` (streszczenie, rysunki, tabele cech/wyników,
badanie wstępne, analiza). Uzupełnić bibliografię (pola DOI/stron nowych prac).
