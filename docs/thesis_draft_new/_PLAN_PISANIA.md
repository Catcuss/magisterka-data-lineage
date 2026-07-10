# Plan pisania kolejnych rozdziałów (nowa koncepcja: detekcja chorych węzłów)

Kolejność wynika z zależności: najpierw dopnij trzon merytoryczny (rozdz. 3),
potem wygeneruj tabele/rysunki, potem wyniki (rozdz. 4), na końcu obudowa
(rozdz. 2/1/5) i streszczenia. Streszczenia PISZ NA KOŃCU — wymagają
finalnych liczb.

Legenda pilności: 🔴 blokujące / 🟡 ważne / 🟢 kosmetyka.
Nakład: S = <1h, M = 1–3h, L = >3h.

---

## FAZA 0 — Przygotowanie materiału (zanim zaczniesz pisać prozę)  ✅ ZROBIONE (rysunki poza)

- [x] 🔴 **Agregacja wyników** — skrypt `scripts/aggregate_detection.py`
  (mean±std per algorytm, tylko grafy wiarygodne). Wyjście:
  `results/agregat_detekcja.csv` + gotowa tabela LaTeX `results/tabela_detekcja.tex`.
- [x] 🔴 **Ustal wariant kanoniczny** — udokumentowany w
  `results/README_BIEG_KANONICZNY.md`. Bieg odtworzony od nowa (stary
  `wyniki_detekcja_v2.csv` był niespójny). Ustawienia: removal_ratio=0.10,
  side=both, exclude_isolated=True, seedy 42–44, indukcyjny LOO, MIN_POS=5.
  Liczby zgadzają się z mailem (LineageDetector 0.771). Wariant napompowany
  dla kontrastu też wygenerowany (`wyniki_detekcja_napompowany.csv`).
  ⚠️ Haczyk: uczciwy = 8 grafów wiarygodnych, napompowany = 10 (patrz README).
- [ ] 🟡 **Rysunki** (L) — POZOSTAJE DO ZROBIENIA. Wygeneruj do `thesis/figures/`:
  1. schemat potoku (JSON→loader→job_removal→cechy→detektor→metryki),
  2. mały graf przed/po usunięciu joba z zaznaczonymi „infected",
  3. wykres słupkowy AUC-ROC per algorytm (uczciwy vs napompowany),
  4. (opcjonalnie) krzywa wrażliwości na removal_ratio.

---

## ROZDZIAŁ 3 — Problem i sposób rozwiązania (DOKOŃCZYĆ)

Szkielet gotowy w `03_problem_i_architektura.tex`. Do uzupełnienia:

- [ ] 🔴 **Tabela cech węzła** (S) — sekcja „Wektor cech węzła".
  13 cech z `src/detection/node_features.py`:
  `in_df, out_df, degree, role, flow_depth, flow_reach, depth_plus_reach,
  is_root, is_leaf, n_field_children, n_job_neighbors, avg_job_in_df,
  avg_job_out_df`. Kolumny tabeli: Nr | Cecha | Opis | Po co (co odróżnia
  tabelę osieroconą od prawdziwego źródła). Detektor dokłada 3 cechy
  kompletności (`peer_producer_score, peer_consumer_score, completeness_anomaly`).
- [ ] 🔴 **Rysunek potoku** (S, sam wstaw + zdanie wprowadzające) — sekcja 3.4.
- [ ] 🟡 **Tabela symulacji** (S) — sekcja 3.3: removal_ratio | #jobów łączących
  | śr. #infected | udział izolowanych pozytywów (uczciwy vs napompowany).
- [ ] 🟡 **Baseline'y heurystyk** (M) — sekcja „Heurystyki strukturalne”:
  opisz baseline'y użyte w kodzie: `degree_anomaly`, `boundary`,
  `low_job_connectivity`, `rule_root` + autorski `completeness`. Dla każdego:
  intuicja + dlaczego to sensowny baseline. (Miary CN/Jaccard/AA już wykluczone.)
- [ ] 🟢 Rysunki poglądowe grafu przed/po usunięciu joba (opcjonalne).

---

## ROZDZIAŁ 4 — Ocena rozwiązania (GŁÓWNY WKŁAD PISARSKI)

- [ ] 🔴 **4.1 Badanie wstępne: predykcja krawędzi** (M). Zwięźle (1–1,5 str.):
  dawne scenariusze A/B/C, wynik: tylko 1 nielosowy (AUC~0.70), reszta ~losowo
  → uzasadnienie pivotu. Źródła: `results/wyniki_scenariusze.csv`, mail.
  To NIE jest porażka — to motywacja. Napisz tak, żeby broniło zmiany kierunku.
- [ ] 🔴 **4.2 Wyniki detekcji** (L). Tabela zbiorcza: wiersz = algorytm
  (5 heurystyk + RF + RUSBoost + LightGBM + LineageDetector), kolumny =
  AUC-ROC | AUC-PR | Precision@k | Recall@k | Hits@k | Brier (średnia±std).
  Wariant uczciwy jako główny. Proza: LineageDetector najlepszy na wszystkich
  metrykach; score kompletności > pozostałe heurystyki.
- [ ] 🔴 **4.3 Kontrola przecieku + wrażliwość** (M). Porównanie napompowany
  vs uczciwy (heurystyki spadają do ~0.46 — „żyły z przecieku”; ML/detektor
  trzymają poziom). Analiza wrażliwości na removal_ratio z
  `results/_faza2_runs.txt` / `run_removal_sensitivity.py`. To argument
  antykrytyczny — mocno podkreśl.
- [ ] 🟡 **4.4 Analiza wyników** (M). DLACZEGO: (a) kompletność dokłada sygnał
  relacyjny nieobecny w cechach lokalnych; (b) kalibracja poprawia Brier;
  (c) trudność „osierocona tabela-następnik wygląda jak źródło”; (d) rozrzut
  mały vs duży graf (patrz per-graf w `_det_v2.txt`).
- [ ] 🟢 **Ablacje** (M, jeśli czas) — wpływ `use_completeness` i `calibrate`
  (detektor je wspiera). Świetny materiał na obronę wkładu własnego.

---

## ROZDZIAŁ 2 — Podstawy i literatura (DOSZLIFOWAĆ)

Proza w większości gotowa. Do zrobienia:

- [ ] 🟡 **Uzupełnić bibliografię** (M): pola DOI/stron dla Dutkiewicz2026,
  Andrzejewski2025 (DARLIAP), Brzeski2025 z PDF-ów w `references/new/`.
  Zweryfikować tytuł/autorów Brzeskiego (w bib jest placeholder).
- [ ] 🟡 **Rysunek/tabela struktury grafu** (S) — sekcja 2.2: mały przykład
  z 3 typami węzłów i 2 typami krawędzi.
- [ ] 🟢 Sprawdzić, czy luka badawcza („nikt nie robi detekcji węzłów”) jest
  wybrzmiana spójnie w 2.5 i w mailu.

---

## ROZDZIAŁ 1 — Wstęp (DROBIAZGI)

- [ ] 🟡 Sprawdzić spójność „cel = detekcja węzłów” w całym wstępie
  (już przepisane, przeczytać na świeżo).
- [ ] 🟢 Ewentualnie rozszerzyć akapit o RODO/audycie (jest hook z `01_wstep.md`).

---

## ROZDZIAŁ 5 — Uwagi końcowe

- [ ] 🟡 **5.1 Podsumowanie** (M): odpowiedzi na PB1–PB4; wniosek główny —
  sama topologia niesie umiarkowany, użyteczny sygnał (LineageDetector 0.771).
  Pozycjonowanie: topology-only baseline dla porównań KG/GNN grupy promotora.
- [ ] 🟡 **5.2 Dalsze badania** (S): indukcyjne GNN (GraphSAGE/R-GCN/HGT),
  benchmark `github.com/dudenzz/lineage`, semantyka nazw, potok dwuetapowy
  (detekcja → predykcja krawędzi). Node2Vec = wynik motywujący GNN, nie luka.

---

## FINISZ — Streszczenia i redakcja (NA KOŃCU)

- [ ] 🔴 **Streszczenie PL** (S) — cel, problem, luka, metodyka, wynik główny
  liczbowo. 250–300 słów, bez cytowań. Bazuj na `_surowce/mail_do_promotora.txt`.
- [ ] 🔴 **Abstract EN** (S) — tłumaczenie.
- [ ] 🟡 **Słowa kluczowe** (S): data lineage, broken lineage, node/anomaly
  detection, inductive learning, graph topology, LineageDetector.
- [ ] 🟢 **Przejście redakcyjne** (M): spójność terminów (Data Table/Data Job,
  „zainfekowana”/„chora” — wybierz jeden), sprawdzić że każda tabela/rysunek
  ma zdanie wprowadzające PRZED wystąpieniem, przelać przez agenta
  `thesis-editor-pl`.

---

## Sugerowana kolejność sesji roboczych

1. FAZA 0 (agregacja + kanoniczny bieg) — bez tego reszta stoi.
2. Rozdz. 3: tabela cech + rysunek potoku + baseline'y heurystyk.
3. Rozdz. 4: 4.2 wyniki → 4.3 przeciek → 4.1 badanie wstępne → 4.4 analiza.
4. Rozdz. 5 (krótki, „na rozpędzie” po wynikach).
5. Rozdz. 2/1 doszlifowanie + bibliografia.
6. Streszczenia PL/EN + redakcja końcowa.

## Zasady, o których pamiętać (promotor je sprawdza)
- Każda tabela/rysunek wprowadzona zdaniem „Tabela/Rysunek X przedstawia…”.
- Wariant UCZCIWY (exclude_isolated) = główny; napompowany tylko dla kontrastu.
- Wszędzie te same ustawienia biegu (removal_ratio, seedy, side).
- Node2Vec: nieobecność w wynikach to świadoma decyzja (indukcyjność), nie brak.
- Nie chować słabości — badanie wstępne i przeciek to atuty (pokazują rzetelność).
