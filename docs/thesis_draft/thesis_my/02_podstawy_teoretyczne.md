data lineage i data povenance to w sumie pojecia ktore stosuje sie zamiennie ale niektorzy tez rozrozniaja te definicje
2.1 — Co to jest data lineage i po co komuś to wiedzieć?
data lineage to bardziej sledzi przebieg informacji i jak ona przechodzi przez rozne systemy oraz jak dane sie zmieniaja natomiast data provenance raczej sprawdza pochodzenie i autenczytcznosc danych. jednak te zjawiska sa na tyle zblizone do siebie ze raczej wiekszosc ludzi traktuje je jako jedna pojecie. w mojej pracy raczej tez ebdziemy to tak ktraktowac. Dla firm i dzialalnosci wazna jest informacja o histori danych np. w raportach koncowych zwykle gdy wyjda jakies nieprawidlowosci to chca sie dowiedziec z kad pochodza dane albo gdzie jest blad a nie moga dojsc czy to wina jakiegos zlego zagregowania albo zlego query idk mozna by wymyslec lepszy przyklad. Tez mozna usunac jakas tabele ktora teoretycznie nie jest z niczym powiazana a jakies dane z niej byly uzywane idk zweryfikuj to claudzie prosze. 

2.2 — Jak wygląda graf lineage w DLG-DG-23?
no sa 3 typy wezlow czyli job tabele i fieldy a co one reprezentuja no to joby to sa query sql i costam z etl itd, w tablach to chyba wszystkie table i widoki zdanymi natomiast fieldy to atrybuty nalezace do tabeli. Przechodzac do krawedzi to sa dwa typy data_flow czyli z tabeli do joba lub na odwrot a drugie to partentchild czy jakos tak i to jest z tabeli do fielda i w sumie to poprostu kest etykieta w senie ktora kolumna nalezy do tabeli. Nie mam pojecia czemu tak tworza szczerze graf dwodzielny tworzy sie gdy mozna podzielic na dwa rozwlaczene zbiory i to ma sens bo jakby etykieta jest zbiorem niz dane wiec dlatego dwudzielny idk 

2.3 — Dlaczego graf lineage bywa niekompletny?
Graf lineage moze byc niekapletny bo jakas widoki materializowane znikna albo powstaje tabla tymczasowa z ktorej czerpiemy dane do jakiegos raportu i potem ta tabla znika i nie wiem skad mamy te dane w sumie. tutaj nie iwem jakie inne przyklady ze np. jakeis query jest nie jawne idk juz wymyslam zdupy

2.4 — Czym jest link prediction i jak pasuje do Twojego problemu?
Link prediction to jest poroba przewidzenia czy jakiestam polaczenia miedzy danymi istanieja mimo ze nie sa one jawnie przedstawione w grafie, my mamy pelne grafy wiec bedziemy musieli sobie usuwac krawedzie sami, robimy to na 3 sposoby aka mamy 3 scenariusze . jeden to 20% losowych krawedzi usuwamy nastepny to ukryta zaleznosc przez udf a trzeci to usuniecie widoku zmatrializowanego.
Bedizemy mieli 3 klasy algorytmow: heurystyki , uczenie maszynowe i embeddingi.

2.5 — Co znalazłaś w SLR?