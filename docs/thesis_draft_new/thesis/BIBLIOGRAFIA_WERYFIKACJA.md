# Weryfikacja bibliografii — `bibliography.bib`

Data: **2026-09-06**
Zakres: **wszystkie 43 pozycje sprawdzone indywidualnie w sieci**
Stan: **poprawki naniesione** na `bibliography.bib`, `Thesis.tex` i `03_problem_i_architektura.tex`

Po zmianach: 42 pozycje (jedna usunięta jako duplikat), 42 klucze cytowane,
zero rozbieżności w obie strony, zero ostrzeżeń BibTeXa, zero nierozwiązanych cytowań.

---

## 1. Naniesione poprawki merytoryczne

### 1.1 `KohanMarzagao2023` → `KohanMarzagao2025` — zły dziennik i zły rok

Najpoważniejszy błąd. Pozycja pełni w pracy rolę źródła metryk podobieństwa grafów.

| Pole | Było | Jest |
|---|---|---|
| journal | IEEE Trans. **Pattern Analysis and Machine Intelligence** | IEEE Trans. **Knowledge and Data Engineering** |
| year | 2023 | **2025** |
| volume (number) | — | 37 (6) |
| pages | — | 3653–3668 |
| doi | — | 10.1109/TKDE.2025.3543097 |

Źródło pomyłki: preprint arXiv pochodzi z 2020 r., a wersja recenzowana ukazała się dopiero
w 2025 r. Klucz zmieniono na `KohanMarzagao2025`, żeby ta sama pułapka się nie powtórzyła
(3 miejsca cytowania zaktualizowane).

- <https://dl.acm.org/doi/10.1109/TKDE.2025.3543097> · [preprint](https://arxiv.org/abs/2010.10343) · [open access](https://e-space.mmu.ac.uk/638948/)

### 1.2 `Shan2023` → `Shan2024` — zły rok, brak woluminu

Było: *Information Sciences*, 2023, bez woluminu.
Jest: *Information Sciences* **659:120059, 2024**. (3 miejsca cytowania zaktualizowane.)

DOI **nie został dodany** — postać `10.1016/j.ins.2024.120059` wynika ze schematu numeracji
Elseviera, ale nie potwierdziłam jej bezpośrednio u wydawcy. Jeśli chcesz go mieć w pliku,
zweryfikuj najpierw na stronie ScienceDirect.

### 1.3 `lightgbm` + `Ke2017` — duplikat usunięty

Ta sama praca (Ke et al., LightGBM, NeurIPS 2017) figurowała pod dwoma kluczami z różną
paginacją, a w [03_problem_i_architektura.tex:768](03_problem_i_architektura.tex#L768)
stało `\cite{lightgbm,Ke2017}` — jedna praca cytowana dwukrotnie w jednym nawiasie.

Wpis `lightgbm` usunięty, cytowanie skrócone do `\cite{Ke2017}`, paginacja poprawiona
na oficjalną z materiałów NeurIPS: **3149–3157** (było 3146–3154).

- <https://proceedings.neurips.cc/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf>

### 1.4 `Psallidas2022` → `Psallidas2023` — preprint zastąpiony wersją recenzowaną

Wpis mieszał dwie wersje: tytuł z artykułu PVLDB, dane wydawnicze z preprintu arXiv.
Tytuły faktycznie się różnią — arXiv: „…from Database **Logs** [Technical Report]",
PVLDB: „…From Database Query **Event** Logs".

Jest: *Proceedings of the VLDB Endowment* **16(12):3662–3675, 2023**,
DOI `10.14778/3611540.3611555`. (5 miejsc cytowania zaktualizowanych.)

---

## 2. Poprawki porządkowe

| Co | Zmiana |
|---|---|
| `Andrzejewski2025` z polem `year = {2026}` | klucz → `Andrzejewski2026` (4 cytowania) |
| `Yamada2023` bez zeszytu | dodane `number = {5}` |
| `Martinez2016` | dodane `articleno = {69}`; **`pages` zachowane** — `plain.bst` nie zna `articleno` i wydruk straciłby strony |
| `OpenLineage` — „An Open Standard for Data Lineage Collection" | → „An Open Framework for Data Lineage Collection and Analysis" (oficjalny opis ze strony projektu) |
| Komentarze robocze i `TODO` po pivocie | usunięte (6 wierszy, m.in. „NOWA KONCEPCJA: detekcja chorych węzłów", „TODO: dodać właściwe źródło") |

---

## 3. Czego **nie** zmieniałam

- **DOI nie zostały dodane hurtowo.** Mam potwierdzone identyfikatory dla większości pozycji
  (są w tabeli niżej), ale `plain.bst` i tak ich nie drukuje, więc byłby to duży diff bez
  wpływu na złożoną bibliografię. Powiedz, jeśli chcesz je mieć w pliku źródłowym.
- **`Hamilton2017`** — w `.bib` figuruje „Rex Ying", w materiałach NeurIPS i DBLP „Zhitao Ying".
  To ta sama osoba i obie formy są w obiegu; zostawiłam bez zmian.
- **Zakres lat SLR.** Protokół deklaruje lata 2022–2025, a trzy prace są z 2025–2026.
  Sprawdziłam: to **nie jest** niespójność — sekcja „Uzupełnienie przeglądu o prace spoza bazy"
  ([Thesis.tex](Thesis.tex), sekcja 2.8) wprost tłumaczy, że dotarto do nich później,
  poza wyszukiwaniem systematycznym.

---

## 4. Pełny wykaz z odnośnikami

Wszystkie pozycje sprawdzone indywidualnie. ⚠ oznacza wpis, który wymagał poprawki.

### Prace kluczowe dla tematu

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 1 | `Boinski2025` | Boiński, Andrzejewski, Grocholewski, Gruszczyński, Wrembel — *Leveraging ML techniques for discovering broken lineage links between database objects*, ISD 2025 | <https://aisel.aisnet.org/isd2014/proceedings2025/transformation/25/> |
| 2 | `Chen2024` | Chen, Zhao, Li, Zhang, Long, Zhou — *An open dataset of data lineage graphs for data governance research*, Visual Informatics 8:1–5 | <https://doi.org/10.1016/j.visinf.2024.01.001> |
| 3 | `Dietrich2022` | Dietrich, Müller, Grust — *Data Provenance for Recursive SQL Queries*, TaPP '22 | <https://doi.org/10.1145/3530800.3534536> |
| 4 | `KohanMarzagao2025` ⚠ | Kohan Marzagão, Huynh, Helal, Baccas, Moreau — *Provenance Graph Kernel*, TKDE 37(6):3653–3668, 2025 | <https://dl.acm.org/doi/10.1109/TKDE.2025.3543097> |
| 5 | `Psallidas2023` ⚠ | Psallidas i in. — *OneProvenance*, PVLDB 16(12):3662–3675, 2023 | <https://doi.org/10.14778/3611540.3611555> |
| 6 | `Shan2024` ⚠ | Shan, Du, Wang, Wang, Liu — *KPI-HGNN*, Information Sciences 659:120059, 2024 | <https://www.semanticscholar.org/paper/ab257d46dfd35ef165b2059e179897f7f042061d> |
| 7 | `Yamada2023` ⚠ | Yamada, Kitagawa, Amagasa, Matono — *Augmented lineage*, VLDB J 32(5):963–983 | <https://doi.org/10.1007/s00778-022-00769-7> |

### Prace grupy promotora

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 8 | `Dutkiewicz2026` | Dutkiewicz, Misiorek, Wrembel — *Data Lineage Discovery in Databases based on Knowledge Graph Link Prediction*, warsztat **TGD** | <https://ceur-ws.org/Vol-4192/TGD-paper2.pdf> |
| 9 | `Andrzejewski2026` ⚠ | Andrzejewski, Boiński, Wrembel — *On Discovering Provenance of Data Warehouse Objects Created by Select-Project Queries*, warsztat **DARLI-AP** | <https://ceur-ws.org/Vol-4192/> |
| 10 | `Brzeski2025` | Brzeski, Roman — *Inferring Missing Data Lineage Links from Schema Metadata Using Transformer-Based Models*, AIDB@VLDB 2025 | <https://sites.google.com/view/aidbvldb2025/home/accepted-papers> |

Wolumin CEUR-WS 4192: *Proceedings of the Workshops of the EDBT/ICDT 2026 Joint Conference*,
red. Alexander Krause i João Felipe Pimentel, Tampere (Finlandia), 24 marca 2026.

### Klasyka proweniencji

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 11 | `CuiWidom2003` | Cui, Widom — *Lineage Tracing for General Data Warehouse Transformations*, VLDB J 12(1):41–58 | [VLDB J](https://vldb.org/vldb_journal/index.php/component/remository/Published-Articles/Volume-12/Number-1/Lineage-tracing-for-general-data-warehouse-transformations/) · [wersja konf. 2001](https://www.vldb.org/conf/2001/P471.pdf) |
| 12 | `Herschel2017` | Herschel, Diestelkämper, Ben Lahmar — *A survey on provenance*, VLDB J 26(6):881–906 | <https://doi.org/10.1007/s00778-017-0486-1> |
| 13 | `Buneman2001` | Buneman, Khanna, Tan — *Why and Where*, ICDT 2001 (LNCS 1973), 316–330 | <https://doi.org/10.1007/3-540-44503-X_20> |
| 14 | `Green2007` | Green, Karvounarakis, Tannen — *Provenance Semirings*, PODS 2007, 31–40 | <https://doi.org/10.1145/1265530.1265535> |

### Standardy i narzędzia

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 15 | `ProvO2013` | Lebo, Sahoo, McGuinness — *PROV-O: The PROV Ontology*, W3C Recommendation, 30 kwietnia 2013 | <https://www.w3.org/TR/prov-o/> |
| 16 | `OpenLineage` ⚠ | *OpenLineage — An open framework for data lineage collection and analysis* | <https://openlineage.io/> |
| 17 | `ApacheAtlas` | *Apache Atlas — Data Governance and Metadata framework for Hadoop* | <https://atlas.apache.org/> |

### Detekcja anomalii w grafach

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 18 | `Akoglu2015` | Akoglu, Tong, Koutra — *Graph based anomaly detection and description: a survey*, DMKD 29(3):626–688 | <https://doi.org/10.1007/s10618-014-0365-y> |
| 19 | `Ma2023` | Ma i in. — *A Comprehensive Survey on Graph Anomaly Detection with Deep Learning*, TKDE 35(12):12012–12038 | <https://doi.org/10.1109/TKDE.2021.3118815> |

### GNN i zanurzenia grafowe

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 20 | `Hamilton2017` | Hamilton, Ying, Leskovec — *Inductive Representation Learning on Large Graphs* (GraphSAGE), NIPS 2017, 1024–1034 | [NeurIPS](https://proceedings.neurips.cc/paper/2017/file/5dd9db5e033da9c6fb5ba83c7a7ebea9-Paper.pdf) · [dblp](https://dblp.org/rec/conf/nips/HamiltonYL17.html) |
| 21 | `Schlichtkrull2018` | Schlichtkrull i in. — *Modeling Relational Data with Graph Convolutional Networks* (R-GCN), ESWC 2018 (LNCS 10843), 593–607 | <https://doi.org/10.1007/978-3-319-93417-4_38> |
| 22 | `Hu2020` | Hu, Dong, Wang, Sun — *Heterogeneous Graph Transformer*, WWW 2020, 2704–2710 | <https://doi.org/10.1145/3366423.3380027> |
| 23 | `Grover2016` | Grover, Leskovec — *node2vec*, KDD 2016, 855–864 | [dblp](https://dblp.org/rec/conf/kdd/GroverL16.html) · [PDF](https://cs.stanford.edu/people/jure/pubs/node2vec-kdd16.pdf) |

### Metody uczenia maszynowego

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 24 | `Breiman2001` | Breiman — *Random Forests*, Machine Learning 45(1):5–32 | <https://doi.org/10.1023/A:1010933404324> |
| 25 | `Seiffert2010` | Seiffert, Khoshgoftaar, Van Hulse, Napolitano — *RUSBoost*, IEEE T-SMC A 40(1):185–197 | <https://doi.org/10.1109/TSMCA.2009.2029559> |
| 26 | `Ke2017` ⚠ | Ke i in. — *LightGBM*, NeurIPS 2017, 3149–3157 | <https://proceedings.neurips.cc/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf> |
| 27 | `Zadrozny2002` | Zadrozny, Elkan — *Transforming Classifier Scores into Accurate Multiclass Probability Estimates*, KDD 2002, 694–699 | <https://doi.org/10.1145/775047.775151> |
| 28 | `Niculescu2005` | Niculescu-Mizil, Caruana — *Predicting Good Probabilities with Supervised Learning*, ICML 2005, 625–632 | <https://doi.org/10.1145/1102351.1102430> |

### Metryki, statystyka, metodyka

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 29 | `Brier1950` | Brier — *Verification of Forecasts Expressed in Terms of Probability*, Monthly Weather Review 78(1):1–3 | [AMS](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml) |
| 30 | `Davis2006` | Davis, Goadrich — *The Relationship Between Precision-Recall and ROC Curves*, ICML 2006, 233–240 | <https://doi.org/10.1145/1143844.1143874> |
| 31 | `Saito2015` | Saito, Rehmsmeier — *The Precision-Recall Plot Is More Informative…*, PLOS ONE 10(3):e0118432 | <https://doi.org/10.1371/journal.pone.0118432> |
| 32 | `Demsar2006` | Demšar — *Statistical Comparisons of Classifiers over Multiple Data Sets*, JMLR 7:1–30 | <https://jmlr.org/papers/v7/demsar06a.html> |
| 33 | `Wilcoxon1945` | Wilcoxon — *Individual Comparisons by Ranking Methods*, Biometrics Bulletin 1(6):80–83 | <https://doi.org/10.2307/3001968> |
| 34 | `Holm1979` | Holm — *A Simple Sequentially Rejective Multiple Test Procedure*, Scand. J. Statistics 6(2):65–70 | [PDF](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf) |
| 35 | `Kitchenham2007` | Kitchenham, Charters — *Guidelines for Performing SLRs in Software Engineering*, EBSE-2007-01 | <https://ebse.webspace.durham.ac.uk/ebse-bibliography/guidelines-for-performing-systematic-literature-reviews-in-software-engineering/> |
| 36 | `Wohlin2012` | Wohlin i in. — *Experimentation in Software Engineering*, Springer 2012 | <https://doi.org/10.1007/978-3-642-29044-2> |

### Predykcja krawędzi i sieci złożone

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 37 | `Barabasi1999` | Barabási, Albert — *Emergence of Scaling in Random Networks*, Science 286(5439):509–512 | <https://doi.org/10.1126/science.286.5439.509> |
| 38 | `LibenNowell2007` | Liben-Nowell, Kleinberg — *The Link-Prediction Problem for Social Networks*, JASIST 58(7):1019–1031 | <https://doi.org/10.1002/asi.20591> |
| 39 | `Martinez2016` ⚠ | Martínez, Berzal, Cubero — *A Survey of Link Prediction in Complex Networks*, ACM CSUR 49(4), art. 69 | <https://doi.org/10.1145/3012704> |
| 40 | `Kovacs2019` | Kovács i in. — *Network-based prediction of protein interactions* (L3), Nature Comm. 10:1240 | <https://doi.org/10.1038/s41467-019-09177-y> |

### Biblioteki

| # | Klucz | Pozycja | Link |
|---|---|---|---|
| 41 | `scikit-learn` | Pedregosa i in. — *Scikit-learn: Machine Learning in Python*, JMLR 12:2825–2830 | <https://www.jmlr.org/papers/v12/pedregosa11a.html> |
| 42 | `imblearn` | Lemaître, Nogueira, Aridas — *Imbalanced-learn*, JMLR 18(17):1–5 | <https://jmlr.org/papers/v18/16-365.html> |

---

## 5. Podsumowanie

- Sprawdzonych indywidualnie: **43 z 43** (100%).
- Poprawionych wpisów: **9** — 4 błędy merytoryczne i 5 porządkowych.
- **Żadna pozycja nie okazała się zmyślona ani nieistniejąca.** Wszystkie prace realnie
  istnieją, mają zgodnych autorów i tytuły.
- Wśród 23 pozycji sprawdzonych w drugiej turze (klasyka ML, statystyki i proweniencji)
  **nie znalazłam ani jednego błędu** — wszystkie woluminy, zeszyty, strony i lata się zgadzają.
  Błędy skupiły się wyłącznie w pracach nowych, gdzie zmieniał się status publikacji
  (preprint → wersja recenzowana).
