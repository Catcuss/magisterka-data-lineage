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

Tutaj napewno ten artykul z data setem An open dataset od data lineage graphs:
An open dataset of data lineage graphs [2]
Problem badawczy: Rozwój metod badawczych w obszarze data governance jest hamowany
przez brak ogólnodostępnych, rzeczywistych zbiorów danych. Przedsiębiorstwa nie udostępniają
grafów lineage ze względu na poufność procesów biznesowych i wymogi bezpieczeństwa.
Zaproponowane rozwiązanie: Publikacja zbioru DLG-DG-23 – pierwszego otwartego ze-
stawu rzeczywistych grafów pochodzenia danych:
• Źródło: środowisko produkcyjne Huawei Cloud (dane zanonimizowane).
• Charakterystyka: 18 grafów o zróżnicowanej wielkości (278–17 085 węzłów).
• Scenariusze: infrastruktura chmurowa, obsługa klienta, analiza operacyjna.
• Model: węzły typów tabela, zadanie, pole oraz relacje przepływu i hierarchii.
Zastosowanie: Zbiór ten posłuży w niniejszej pracy jako referencyjny punkt odniesienia (gro-
und truth) w eksperymentach dotyczących rekonstrukcji grafów provenance.
Analiza krytyczna:
3.3. Metryki i zbiory danych 11
+ Unikalna wartość badawcza wynikająca z rzeczywistego pochodzenia danych (w przeciwień-
stwie do generatorów syntetycznych).
+ Możliwość wszechstronnego zastosowania (wykrywanie anomalii, wizualizacja, rekonstruk-
cja).
- Stosunkowo niewielka liczba grafów ograniczająca trenowanie dużych modeli głębokich.
- Ograniczenie atrybutów węzłów wynikające z konieczności anonimizacji.
Na pewno tez ten bo on jest glowna motywacja i inspiracja:
3.1.2 Leveraging machine learning techniques for discovering broken lineage
links [1]
Problem badawczy: Ciągłość grafów pochodzenia (lineage) ulega przerwaniu, gdy w potokach
ETL wykorzystywane są obiekty pośrednie, takie jak tabele tymczasowe lub funkcje definiowane
przez użytkownika (UDF). Elementy te mają charakter tymczasowy i są usuwane natychmiast po
zakończeniu procesu przetwarzania. W rezultacie, istniejące narzędzia klasy data governance tracą
ślad przepływu danych i nie są w stanie automatycznie powiązać trwałej tabeli źródłowej z tabelą
docelową, błędnie interpretując je jako niezależne byty.
Zaproponowane rozwiązanie: Autorzy proponują zastosowanie metod uczenia maszynowego
do problemu binarnej klasyfikacji par obiektów, celem predykcji istnienia ukrytej relacji pochodze-
nia. Podejście to obejmuje:
• Inżynieria cech: ekstrakcja metadanych i analiza podobieństwa semantycznego nazw tabel
oraz atrybutów (z wykorzystaniem miary odległości Jaro–Winkler).
• Modele klasyfikacji: przetestowano algorytmy Random Forest, RUSBoost, BalancedBag-
ging oraz LightGBM. Najlepsze wyniki w eksperymentach osiągnął klasyfikator RUSBo-
ostClassifier.
• Generowanie danych uczących: zastosowanie techniki rekurencyjnego zastępowania tabel
tymczasowych ich trwałymi źródłami w celu skonstruowania etykiet referencyjnych (ground
truth).
Zbiór danych i ewaluacja: Ze względu na brak ogólnodostępnych zbiorów danych tego typu,
autorzy wykorzystali wielkie modele językowe (LLM) do wygenerowania syntetycznych schematów
baz danych:
3.1. Metody ekstrakcji i algorytmy ML/GNN 7
• Zbiór treningowy: schemat systemu zarządzania w ochronie zdrowia wygenerowany przez
model Grok (dane wymagały ręcznej korekty i czyszczenia).
• Zbiór testowy: schemat systemu finansowego wygenerowany przez model Llama3.
Analiza krytyczna:
+ Wysoka skuteczność rekonstrukcji zerwanych zależności (miara F1-score na poziomie do
0.79).
+ Odporność metody na silnie niezbalansowane zbiory danych (gdzie liczba par bez relacji
znacznie przewyższa liczbę par powiązanych).
- Istotna zależność jakości predykcji od stosowania spójnych konwencji nazewniczych w bazie
danych.
- Konieczność weryfikacji i ręcznej korekty danych syntetycznych generowanych przez modele
LLM
nie wiem czy z tego kozystalismy Provenance Graph Kernel [4]
a reszta to raczej tylko kontekst nie korzystamy tego w pracy wiec mozna je pominac w tym rozdziale