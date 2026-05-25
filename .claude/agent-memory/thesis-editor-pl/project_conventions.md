---
name: project-conventions
description: Konwencje stylistyczne i terminologiczne przyjęte w pracy magisterskiej
metadata:
  type: project
---

## Terminologia (ujednolicona)

- "data lineage" — termin angielski, stosowany bez tłumaczenia (lub "zależności między obiektami")
- "data provenance" — termin angielski, stosowany bez tłumaczenia
- "broken lineage" — termin angielski, stosowany bez tłumaczenia (lub "przerwany graf zależności")
- "graf lineage" — przyjęta hybryda polska; alternatywnie "graf zależności"
- "predykcja krawędzi" — polskie tłumaczenie "link prediction"
- "link prediction" — angielski termin używany przy pierwszym wprowadzeniu z rozwinięciem
- Graf DLG-DG-23 — dataset z Huawei Cloud, 18 grafów dwudzielnych, węzły: job, table, field
- Typy krawędzi: data_flow (tabela↔job), parent_child (tabela→field)

## Skróty (rozwijać przy pierwszym użyciu)

- ML — Machine Learning (uczenie maszynowe)
- GNN — Graph Neural Network (grafowa sieć neuronowa)
- GCN — Graph Convolutional Network
- SLR — Systematic Literature Review (systematyczny przegląd literatury)
- UDF — User-Defined Function (funkcja definiowana przez użytkownika)
- CTE — Common Table Expression
- ETL — Extract, Transform, Load
- PGK — Provenance Graph Kernel
- KPI-HGNN — skrót z artykułu Shan et al.
- Node2Vec — nazwa własna (bez rozwijania)
- GraphSAGE — nazwa własna
- RUSBoost — nazwa własna (Random Under-Sampling Boosting)

## Cytowania

- Format: [numer], np. \cite{Boinski2025}
- Przed kropką zdania
- Numerowane rosnąco w kolejności pojawienia się w tekście

## Interpunkcja list

- Krótkie elementy: kończą się przecinkami, ostatni — kropką
- Dłuższe elementy (zdania): kończą się średnikami, ostatni — kropką

## Klucze bibliograficzne (BibLaTeX)

1. Boinski2025 — Boiński et al. (ISD2025), ML dla broken lineage, RUSBoost, F1=0.79
2. Chen2023 — Chen et al., dataset DLG-DG-23 (18 grafów, Huawei Cloud)
3. Dietrich2023 — Dietrich et al., data provenance dla rekurencyjnych SQL
4. KohanMarzagao2023 — Kohan Marzagão et al., Provenance Graph Kernel (PGK)
5. Psallidas2020 — Psallidas et al., OneProvenance (log analysis, QQTree)
6. Shan2022 — Shan et al., KPI-HGNN (heterogeniczne GNN)
7. Yamada2023 — Yamada et al., Augmented lineage (UDF, VLDB 2023)

## Struktura pracy (wymagana przez promotora)

1. Wstęp
2. Przegląd technologii i algorytmów (podstawy teoretyczne)
3. Problem i sposób jego rozwiązania
4. Ocena rozwiązania
5. Uwagi końcowe

## Scenariusze podziału danych (cztery, uszczegółowione w 01-wstep.tex)

- Podział losowy (80/20 split)
- Scenariusz A: usunięcie tabeli pośredniej (staging)
- Scenariusz B: ukrycie zależności przez UDF
- Scenariusz C: ukrycie krawędzi prowadzących do warstwy data mart

## Konwencje LaTeX (ustalone w rozdziale 1)

- Terminy angielskie kursywą: \textit{data lineage}, \textit{broken lineage}, \textit{data provenance}
- Skróty przy pierwszym użyciu: pełna nazwa + ang.\ + \textit{skrót}, np. "funkcji definiowanych przez użytkownika (ang.\ \textit{User-Defined Function}, UDF)"
- Niełamliwe spacje przed: ~\cite, ~2, ~A, ~B, ~C (przy odwołaniach do rozdziałów i scenariuszy)
- \section{} dla podrozdziałów wstępu (nie \subsection{})
- Rozdział wstępu NIE zawiera cytowań (brak \cite w 01-wstep.tex — motywacja RODO/banki bez źródeł)

**Why:** Ustalono w trakcie tworzenia Thesis.tex na podstawie draftów autorki.
**How to apply:** Używaj tych terminów konsekwentnie. Sprawdzaj spójność przy każdej korekcie.
