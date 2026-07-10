# Szkielet rozdziału 3 — UZUPEŁNIENIA (pytania pomocnicze)

Rozdział 3 ma już napisany szkielet prozy w `03_problem_i_architektura.tex`.
Tu są TYLKO brakujące fragmenty (oznaczone `% TODO` w .tex). Forma jak w
rozdz. 4/5: pytania pomocnicze → odpowiadasz prozą / wypełniasz tabelę.

Mapowanie na plik .tex (żeby wiedzieć, gdzie wkleić):
- 3.3 tabela symulacji        → TODO w linii ~170 (sekcja „Metodyka symulacji…")
- 3.4 rysunek potoku          → TODO w linii ~184 (sekcja „Architektura rozwiązania")
- 3.5 baseline'y heurystyk    → TODO w linii ~241 (podsekcja „Heurystyki strukturalne")
- 3.5 tabela cech węzła       → TODO w linii ~292 (podsekcja „Klasyczne metody ML")

---

## A) Tabela symulacji broken lineage  (sekcja 3.3)

Cel: pokazać liczbowo, co robi usuwanie jobów i skąd bierze się przeciek.
Źródło liczb: `results/_det_canon.txt` / `_det_napompowany.txt` (statystyki per
graf), ewentualnie doliczyć skryptem. Wprowadź zdaniem „Tabela X przedstawia…".

Kolumny do wypełnienia (wiersz = wariant uczciwy vs napompowany):
| removal_ratio | śr. #jobów usuwanych | śr. #infected tabel | udział izolowanych pozytywów | #grafów wiarygodnych |

Pytania pomocnicze:
1. Ile jobów średnio jest usuwanych przy removal_ratio=0.10 i jak to się
   przekłada na liczbę zainfekowanych tabel (predecessors ∪ successors)?
2. Jaki udział zainfekowanych tabel staje się DATA_FLOW-izolowany (~29%)
   i ile spośród czystych tabel jest izolowanych (0%)? To liczba, która
   uzasadnia kontrolę przecieku — podkreśl ją.
3. Dlaczego liczba grafów wiarygodnych różni się między wariantami (8 vs 10,
   MIN_POS=5) — jedno zdanie pod tabelą.

---

## B) Rysunek blokowy potoku  (sekcja 3.4)

Cel: jeden rysunek pokazujący przepływ danych przez system. Sam rysunek
zrobisz osobno (do `thesis/figures/`), tu przygotuj OPIS i zdanie wprowadzające.

Pytania pomocnicze:
1. Jakie są bloki potoku po kolei i co każdy robi w 2–4 słowach?
   (JSON grafu → loader → job_removal (symulacja) → node_features (cechy)
   → detektor/klasyfikator → node_metrics (ewaluacja).)
2. Co jest wejściem, a co wyjściem całego potoku (graf lineage → ranking
   węzłów wg p(chory) + metryki)?
3. Które bloki to wkład własny, a które reuse istniejących komponentów
   (np. `_compute_flow_metadata`)? — do zaznaczenia na rysunku.
4. Napisz jedno zdanie „Rysunek X przedstawia…" wprowadzające go w tekście.

---

## C) Baseline'y heurystyczne  (podsekcja 3.5 „Heurystyki strukturalne")

Cel: dla każdego baseline'u — intuicja + dlaczego to sensowny punkt odniesienia.
Metody z kodu (`node_classifier.py`): `degree_anomaly`, `boundary`,
`low_job_connectivity`, `rule_root` + autorski `completeness`.
(Miary CN/Jaccard/AA/L3/Katz/PPR są WYKLUCZONE — napisz dlaczego: graf
dwudzielny job–tabela, brak wspólnych sąsiadów tego samego typu.)

Dla KAŻDEGO baseline'u odpowiedz na te 3 pytania:
1. Jak liczony jest score węzła (jedno zdanie / wzór intuicyjny)?
2. Jaka jest intuicja — dlaczego chory węzeł miałby mieć wysoki score?
3. Dlaczego to sensowny baseline (co reprezentuje: stopień? pozycję brzegową?
   łączność z jobami? regułę korzenia?) — i jaka jest jego znana słabość?

Dodatkowo (całościowo):
4. Dlaczego heurystyki link-prediction (wspólni sąsiedzi) są tu nieaplikowalne?
5. Czym `completeness` (peer-consistency) różni się od pozostałych heurystyk —
   dlaczego to już wkład własny, a nie zwykły baseline? (Zapowiedź detektora.)

---

## D) Tabela cech węzła  (podsekcja 3.5 „Klasyczne metody ML")

Cel: udokumentować wektor cech. 13 cech bazowych z `node_features.py`
(+ 3 cechy kompletności dokładane przez LineageDetector). Wprowadź zdaniem
„Tabela X przedstawia wektor cech…".

Kolumny tabeli: Nr | Cecha | Opis | Po co (co odróżnia tabelę osieroconą od
prawdziwego źródła/liścia).

Cechy do opisania (dokładnie te nazwy z kodu — nie zmieniaj):
1.  `in_df`             — liczba wejściowych krawędzi DATA_FLOW
2.  `out_df`            — liczba wyjściowych krawędzi DATA_FLOW
3.  `degree`            — stopień węzła (wszystkie typy krawędzi)
4.  `role`              — rola w przepływie (źródło/pośredni/ujście)
5.  `flow_depth`        — głębokość w DAG przepływu
6.  `flow_reach`        — zasięg (ile węzłów osiąga w dół)
7.  `depth_plus_reach`  — suma głębokości i zasięgu
8.  `is_root`           — czy korzeń przepływu (brak wejść DATA_FLOW)
9.  `is_leaf`           — czy liść przepływu (brak wyjść DATA_FLOW)
10. `n_field_children`  — liczba pól (PARENT_CHILD) podpiętych do tabeli
11. `n_job_neighbors`   — liczba sąsiadujących jobów
12. `avg_job_in_df`     — śr. in_df sąsiadujących jobów
13. `avg_job_out_df`    — śr. out_df sąsiadujących jobów
    (+ dokładane przez detektor: `peer_producer_score`, `peer_consumer_score`,
     `completeness_anomaly`.)

Pytania pomocnicze (do kolumny „Po co"):
1. Dla każdej cechy: JAKI sygnał o broken lineage ona niesie — co odróżnia
   węzeł osierocony (który STRACIŁ producenta/konsumenta) od naturalnego
   źródła/liścia, które nigdy go nie miało? (To sedno trudności — te dwa
   przypadki wyglądają podobnie lokalnie.)
2. Które cechy są czysto lokalne (stopień, role), a które „patrzą dalej"
   (flow_reach, avg_job_*)? Dlaczego same lokalne nie wystarczą?
3. Co dokładają 3 cechy kompletności, czego nie ma w 13 bazowych
   (sygnał relacyjny: czy sąsiedzi-peers tabeli mają producenta/konsumenta)?

---

## Checklist przed zamknięciem uzupełnień rozdziału 3
- [ ] Tabela symulacji i tabela cech wprowadzone zdaniem „Tabela X przedstawia…".
- [ ] Rysunek potoku wprowadzony zdaniem „Rysunek X przedstawia…".
- [ ] Nazwy cech dokładnie jak w `node_features.py` (spójność z kodem).
- [ ] Wyjaśnione, dlaczego heurystyki link-prediction (CN/Jaccard/AA) wykluczone.
- [ ] `completeness` opisany jako most do wkładu własnego (LineageDetector).
