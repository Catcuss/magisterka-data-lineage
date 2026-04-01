# Rozdział 1 — Wstęp

> **Status:** Draft roboczy — do uzupełnienia i redakcji przed złożeniem pracy.
> Sekcje oznaczone [TODO] wymagają doprecyzowania lub dopisania.

---

## 1.1 Kontekst i motywacja

W dobie powszechnej cyfryzacji przedsiębiorstw dane stały się kluczowym zasobem
strategicznym. Organizacje gromadzą coraz większe wolumeny danych w hurtowniach
danych (ang. *data warehouse*) i jeziorach danych (ang. *data lake*), a ich
przetwarzanie odbywa się poprzez złożone potoki ETL
(ang. *Extract, Transform, Load*). W takich środowiskach dane nie są statycznym
artefaktem — przepływają przez dziesiątki lub setki przekształceń, zanim trafią
do końcowych raportów analitycznych.

Zarządzanie jakością danych w tak złożonych środowiskach wymaga zdolności do
odtworzenia pełnej historii przepływu danych — od pierwotnych źródeł, przez
wszystkie transformacje, aż do końcowych tabel wynikowych. Zdolność ta nosi
nazwę **śledzenia pochodzenia danych** (ang. *data lineage* lub *data provenance*)
i stanowi jeden z filarów nowoczesnego zarządzania danymi (ang. *data governance*).

Systemy lineage są dziś integralną częścią platform takich jak Apache Atlas,
Microsoft Purview czy OpenLineage. Ich wartość przejawia się w trzech obszarach:

1. **Analiza wpływu zmian** (ang. *impact analysis*) — umożliwia przewidywanie,
   które obiekty analityczne ulegną zmianie po modyfikacji tabeli źródłowej.
2. **Weryfikacja jakości danych** — pozwala wykryć propagację błędów danych
   przez kolejne warstwy przetwarzania.
3. **Audyt zgodności** (ang. *compliance audit*) — dostarcza regulatorom
   kompletny ślad danych wymagany przez przepisy (RODO, SOX, HIPAA).

## 1.2 Problem badawczy — broken lineage

Pomimo dojrzałości systemów śledzenia lineage, w praktyce inżynierskiej
często dochodzi do **zerwania ciągłości grafu zależności** — zjawiska
określanego w literaturze jako *broken lineage*. Problem pojawia się,
gdy w potoku ETL używane są obiekty tymczasowe (tabele tymczasowe,
widoki zmaterializowane, funkcje UDF), które są usuwane po zakończeniu
przetwarzania lub w wyniku ewolucji schematu.

Formalna definicja problemu: niech $G = (V, E)$ będzie grafem lineage,
gdzie $V$ to zbiór obiektów bazodanowych (tabele, joby ETL, pola), a $E$
to zbiór relacji przepływu danych między nimi. *Broken lineage* oznacza
sytuację, w której usunięcie węzła $v_{temp} \in V$ (lub braku jego
rejestracji) prowadzi do utraty krawędzi $\{(u, v_{temp}), (v_{temp}, w)\} \subset E$,
pomimo że logiczna zależność $u \to w$ nadal istnieje w przetwarzaniu danych.

Poniższy przykład ilustruje problem:

```
Graf kompletny:     raw_calls → stg_daily_agg → dm_revenue

Graf po usunięciu   raw_calls                   dm_revenue
tabeli staging:               ↑
                              stg_daily_agg usunięta
                              Zależność raw_calls → dm_revenue niewidoczna
```

Konsekwencje dla organizacji:
- Niemożliwa ocena wpływu zmian w tabelach źródłowych na raporty analityczne
- Niekompletna weryfikacja jakości danych w łańcuchu transformacji
- Ryzyko naruszeń compliance z powodu luk w audycie danych

## 1.3 Cel i zakres pracy

Celem niniejszej pracy jest **implementacja i ewaluacja algorytmów predykcji
brakujących krawędzi** (ang. *link prediction*) w grafach lineage jako metody
rekonstrukcji zerwanego lineage.

Problem jest formalnie traktowany jako **binarna klasyfikacja**: dla każdej
kandydackiej pary węzłów $(u, v)$ algorytm decyduje, czy między nimi istnieje
brakująca relacja lineage (klasa pozytywna), czy nie (klasa negatywna).

W ramach pracy zostaną zrealizowane następujące zadania:

1. Przegląd literatury dotyczącej data lineage/provenance oraz algorytmów
   odkrywania brakujących krawędzi w grafach (Systematyczny Przegląd Literatury).
2. Implementacja trzech wybranych algorytmów:
   - heurystyki grafowe (Preferential Attachment, L3),
   - klasyczne uczenie maszynowe (Random Forest z cechami topologicznymi),
   - metody oparte na embeddingach węzłów (Node2Vec + klasyfikacja krawędzi).
3. Zastosowanie algorytmów do odkrywania zależności między obiektami
   w rzeczywistych grafach lineage ze zbioru DLG-DG-23.
4. Opracowanie metodyki ewaluacji (metryki, protokół testowy).
5. Przeprowadzenie testów i ocena jakości odkrytych powiązań.

## 1.4 Pytania badawcze

Praca odpowiada na następujące pytania badawcze:

- **PB1:** Jakie techniki ekstrakcji grafów lineage z logów i metadanych
  baz danych są stosowane w literaturze?
- **PB2:** Jak można zaadaptować metody uczenia maszynowego i grafowych
  sieci neuronowych (GNN) do predykcji brakujących krawędzi w grafach lineage?
- **PB3:** Jak obsługiwać specyficzne przypadki broken lineage wynikające
  z rekurencji (CTE) i funkcji UDF?
- **PB4:** Jakie metryki i zbiory danych są odpowiednie do ewaluacji
  algorytmów rekonstrukcji lineage?

## 1.5 Wkład naukowy

Niniejsza praca wnosi następujące oryginalne wkłady:

1. Pierwsza kompleksowa implementacja i porównanie trzech klas algorytmów
   link prediction (heurystyki, ML klasyczne, embeddingi) na rzeczywistym
   zbiorze grafów lineage DLG-DG-23.
2. Analiza wpływu bipartytowości grafu DATA_FLOW na skuteczność
   standardowych heurystyk link prediction (CN, Jaccard, Adamic-Adar)
   i uzasadnienie doboru algorytmów alternatywnych.
3. Identyfikacja kluczowych cech topologicznych predyktywnych dla
   broken lineage w środowiskach ETL (najkrótsza ścieżka, stopnie węzłów).

## 1.6 Struktura pracy

Praca podzielona jest na następujące rozdziały:

- **Rozdział 2 — Podstawy teoretyczne:** formalna definicja data lineage
  i data provenance, model grafu lineage, problem link prediction,
  przegląd typów broken lineage.
- **Rozdział 3 — Przegląd literatury:** wyniki Systematycznego Przeglądu
  Literatury (SLR) — 7 kluczowych artykułów z lat 2022–2025.
- **Rozdział 4 — Zbiór danych:** opis DLG-DG-23, charakterystyka grafów,
  metodyka podziału train/val/test, próbkowanie negatywne.
- **Rozdział 5 — Implementacja algorytmów:** szczegółowy opis trzech
  zaimplementowanych algorytmów z analizą złożoności.
- **Rozdział 6 — Ewaluacja:** metodyka testów, wyniki eksperymentów
  na 18 grafach, tabela porównawcza, analiza błędów.
- **Rozdział 7 — Podsumowanie i wnioski.**

---

*Słowa kluczowe: data lineage, data provenance, broken lineage, link prediction,
graf zależności, ETL, uczenie maszynowe, Random Forest, Node2Vec, DLG-DG-23.*
