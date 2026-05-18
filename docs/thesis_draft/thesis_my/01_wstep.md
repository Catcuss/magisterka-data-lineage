# 1. Wstęp

Współczesne systemy bazodanowe przetwarzają dane przez złożone potoki transformacji SQL. W firmach często dane są przez jakąś agregację i zapytania SQL i powstają tabele tymczasowe, w sumie często nie są zapisane te zapytania i chcemy się dowiedzieć skąd te dane pochodzą — tak zwana historia danych, zależność między obiektami baz danych. Dokładniej chodzi o usunięcie krawędzi w grafie, które następnie za pomocą różnych algorytmów będziemy chcieli odtworzyć. Jest to ważny problem baz danych, bo często są tabele tymczasowe, które znikają, i potem już nie ma widocznych połączeń w bazie i my chcemy je wyszukać. Chcemy wykorzystać zjawisko data lineage, aby z jakimś prawdopodobieństwem znaleźć te zależności i odtworzyć połączenia przy pomocy algorytmów, np. ML.


## 1.1 Cel i zakres pracy

Celem pracy jest znalezienie i zbadanie jak już istniejące algorytmy radzą sobie z problemem próby odtwarzania i znajdowania tych relacji na podstawie data lineage. Dane będą przeprowadzane na algorytmach ML oraz heurystykach oraz embeddingach węzłów, a dane to z Huawei — 18 grafów dwudzielnych, gdzie są joby i tabele takie, które przedstawiają zanonimizowane prawdziwe i realne dane, jednak nie posiadają one schematów tej bazy, bo nie ma schematów ze względu na ochronę danych, ale to że dane są realne jest korzystne i od razu mamy i dużą i małą skalę. Mamy też na pewno 3 scenariusze podziału danych: pierwszy losowy 80/20, drugi symulujący usunięcie tabeli staging (scenariusz A) lub ukrycie zależności przez UDF (scenariusz B), trzeci to ukrycie krawędzi do data martu (scenariusz C). W pracy nie znajdziemy prawdziwego schematu bazy danych, własnego algorytmu autorskiego itd.

Jest to realny problem, ktory dotyka takie instytucje jak banki czy wymagania firm związane z RODO. W raportach kwartalnych banki muszą wykazać, które transakcje źródłowe złożyły sie na dane pozycje. W ETL wyniki często są pośrednie w tabelach tymczasowych, graf lineage zostaje przerwany i audyt jest niemożliwy.
Jeśli chodzi o RODO to każdy użytkownik ma prawo poprosić o usunięcie swoich danych, jeżeli gdzieś jest przerwanie to dojscie do wszystkich danych jest czasochonne albo nawet niemozliwe co moze nakladac kary na dana firme.

## 1.2 Struktura pracy

- W rozdziale drugim zajmiemy się przedstawieniem najważniejszych pojęć takich jak data lineage, data provenance, graf lineage, problem broken lineage itd., oraz przeglądem literatury i metrykami ewaluacji.
- W rozdziale trzecim opisano problem i architekturę rozwiązania wraz z rysunkami, pochodzenie danych, metodykę symulacji i zaimplementowane algorytmy.
- W rozdziale czwartym przedstawiono ocenę rozwiązania — wyniki eksperymentów przeprowadzonych na wszystkich 18 grafach ze zbioru DLG-DG-23.
- Rozdział piąty zawiera uwagi końcowe — podsumowanie tego co wyszło, co nie wyszło i możliwe rozszerzenia.