# Szkielet rozdziału 5 — „Uwagi końcowe" (pytania pomocnicze)

Forma robocza: pod każdym podrozdziałem pytania pomocnicze — odpowiedz prozą.
Rozdział krótki (2–4 strony). Pisz go „na rozpędzie" zaraz po rozdz. 4, gdy
masz świeżo w głowie wyniki. Bez nowych liczb — tylko te z biegu kanonicznego.

Krótki wstęp rozdziału jest już w `Thesis.tex`.

---

## 5.1 Podsumowanie

Cel: domknąć pracę — wrócić do pytań badawczych i postawić jeden mocny wniosek
główny. Odwołaj się do celu z rozdz. 1.

Pytania pomocnicze:
1. Jaki był cel pracy (detekcja/ranking chorych węzłów w grafach lineage na
   podstawie samej topologii) i czy został osiągnięty? W jednym zdaniu.
2. PB1 (ekstrakcja grafów lineage z logów/metadanych) — jak Twoja praca się do
   tego odnosi? (Korzystasz z gotowego zbioru DLG-DG-23; ekstrakcja poza
   zakresem, ale opisana w przeglądzie — OneProvenance itd.)
3. PB2 (adaptacja ML/GNN do predykcji brakujących zależności) — co pokazałaś?
   (Klasyczne ML na cechach topologicznych + autorski LineageDetector; GNN
   jako uzasadniony następny krok.)
4. PB3 (rekurencja/CTE i UDF) — jak to adresujesz? (Broken lineage z powodu
   UDF/tabel tymczasowych jest źródłem chorych węzłów; sama obsługa rekurencji
   po stronie ekstrakcji — poza zakresem, wskazana w dalszych badaniach.)
5. PB4 (metryki i datasety do ewaluacji) — co ustaliłaś? (Zestaw metryk
   rankingowych AUC-ROC/AUC-PR/P@k/Brier + protokół indukcyjny LOO +
   kontrola przecieku jako wkład metodologiczny.)
6. Jaki jest GŁÓWNY wniosek liczbowy? (Sama topologia niesie umiarkowany, ale
   użyteczny sygnał o broken lineage na poziomie węzłów: LineageDetector
   AUC-ROC 0.771, wariant uczciwy, indukcyjny.)
7. Jak pozycjonujesz pracę wobec programu badawczego grupy promotora?
   (Topology-only baseline dla porównania z metodami KG/GNN — TGD/Misiorek,
   DARLIAP, Brzeski; jedyna rodzina metod nieobecna w tym programie.)
8. Jaki jest Twój deklarowany wkład własny? (Score kompletności peer-consistency,
   LineageDetector z kalibracją, protokół z kontrolą przecieku exclude_isolated.)

---

## 5.2 Kierunki dalszych badań

Cel: pokazać dojrzałość — gdzie to prowadzi. Każdy kierunek: 2–3 zdania
(co + dlaczego to naturalny następny krok).

Pytania pomocnicze:
1. Indukcyjne GNN (GraphSAGE / R-GCN / HGT) — dlaczego to logiczny następny
   krok po cechach topologicznych? Jak sformułować, że Node2Vec wykluczono
   jako transduktywny (embeddingi nieporównywalne między grafami) — a więc to
   WYNIK motywujący GNN, nie luka w pracy?
2. Benchmark KG grupy promotora (github.com/dudenzz/lineage) — dlaczego warto
   przenieść metodę na te dane i co by to dało (porównywalność z SOTA)?
3. Semantyka nazw/schematów — kiedy miałoby to sens (gdy dane przestaną być
   zanonimizowane UUID) i co mogłoby dołożyć do topologii?
4. Potok dwuetapowy: detekcja chorych węzłów → predykcja konkretnych krawędzi.
   Jak wynik 4.1 (predykcja krawędzi trudna „na ślepo") uzasadnia, że warto
   najpierw zawęzić obszar detekcją?
5. (opcjonalnie) Inne źródła broken lineage / większe zbiory / walidacja na
   danych produkcyjnych — co byłoby potrzebne do wdrożenia?

---

## Checklist przed zamknięciem rozdziału 5
- [ ] Każde PB1–PB4 ma jawną odpowiedź (choćby „poza zakresem, bo…").
- [ ] Wniosek główny podany liczbowo i spójny z rozdz. 4.
- [ ] Node2Vec opisany jako świadoma decyzja, nie brak.
- [ ] Dalsze badania spójne z niszą „topology-only baseline".
- [ ] Brak nowych liczb/twierdzeń niewynikających z rozdz. 4.
