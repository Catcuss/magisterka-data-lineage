# Notatka na spotkanie z dr. Pawłem Misiorkiem — 9 czerwca 2026

Temat: konsultacja pracy mgr „Odkrywanie zależności między obiektami w bazie danych"
w kontekście artykułu **Dutkiewicz, Misiorek, Wrembel — *Data Lineage Discovery in
Databases Based on Knowledge Graph Link Prediction*** (EDBT/ICDT 2026 Workshops).

---

## 1. Jak rozumiem Pana artykuł (żeby pokazać, że przeczytałam uważnie)

- Problem: broken object lineage (temp tables, UDF, materialized views) — **ten sam co u mnie**.
- Metoda: DB → ontologia/KG (RDF, `valueDerivedFrom`/`columnDerivedFrom`, PROV-O)
  → **indukcyjna** predykcja krawędzi path-based GNN-em [8] (ℰ_train ∩ ℰ_test = ∅).
- Dane: własny benchmark LLM (Northwind + Gemini 3, 50 scenariuszy), `github.com/dudenzz/lineage`.
- Negatywy 50:1; metryki AUROC + Hits@10; 10 powtórzeń, trim min/max.
- Wyniki kluczowe: Basic copy 0.92/0.86; złożone ~0.60; **Temporary tables 0.49 (= losowy)**.

## 2. Gdzie widzę moją pracę względem Pana programu badawczego

Pana *future work* (sek. 7) zapowiada porównanie: (1) KG-GNN, (2) SOTA, (3) statystyczna
[37 = DARLIAP], (4) ML [38 = Boiński ISD2025, moja ref. [1]]. **Brakuje systematycznego
baseline'u klasycznych metod strukturalnych** (heurystyki grafowe → feature-based ML →
płytkie embeddingi) na wspólnych danych.

**Propozycja pozycjonowania mojej pracy:** „ile sygnału o lineage niesie SAMA topologia
grafu — bez ontologii, bez semantyki, bez GNN", jako baseline do Państwa porównania.

## 3. Co pokazuję na ekranie

1. Strukturę repo + 3 grupy algorytmów (heurystyki / klasyczne ML / Node2Vec).
2. Tabelę wyników scenariuszowych — **uczciwie**, z zaznaczeniem problemu F1=0.000
   (próg strojony na innym rozkładzie niż test → degeneracja; mam diagnozę i poprawkę).
3. Wizualizacje grafów DLG-DG-23 (docs/graphs/).

## 4. Pytania, które MUSZĘ zadać

1. **Dataset:** czy zostać przy DLG-DG-23 (realne, duże, ale UUID = brak semantyki,
   brak prawdziwych etykiet broken), czy przejść / dołożyć Państwa benchmark
   `github.com/dudenzz/lineage`? Czy mogę go użyć?
2. **Nisza:** czy framing „topology-only baseline" jest tym, czego brakuje w Państwa
   porównaniu — czy raczej oczekują Państwo, żebym zrobiła GNN?
3. **Protokół:** czy mam się dostroić do Państwa — indukcyjność (cross-graph: trenuj na
   części z 18 grafów, testuj na reszcie), negatywy 50:1, metryki Hits@n, trim 10×?
4. **Temp tables 0.49:** skoro bogaty GNN zawodzi na temp-table, czy sensownie jest, bym
   na tym scenariuszu w ogóle testowała topologię, czy zawęzić do basic-copy/join?
5. Jak widzą Państwo wpięcie mojej pracy do planowanego „comprehensive comparison"?

## 5. Co przyznaję sama, zanim on to wytknie (przewaga, nie słabość)

- „Odkrywanie broken lineage" w moim setupie to faktycznie **rekonstrukcja sztucznie
  usuniętych krawędzi** (link prediction), bo etykiety fabrykuję regułą o stopniach.
  Poprawiam tytuł rozdziału na „predykcja brakujących krawędzi z cech topologicznych".
- Mój scenariusz A usuwa krawędź, ale **zostawia węzeł** → łatwiejszy niż Państwa temp-table.
- Negatywy 1:1 → podnoszę; F1 → zastępuję AUC-PR/Hits@n; dokładam cross-graph (indukcja).

## 6. Po spotkaniu — decyzje do zapisania
- [ ] Dataset: DLG-DG-23 / ich benchmark / oba?
- [ ] GNN: tak / zostaje jako future work?
- [ ] Protokół ewaluacji: które elementy ich metodyki adoptuję?
