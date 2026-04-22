1. Wstęp

W firmach czesto dane sa przez jakas agregacje itd sql query i powstaja table tymczasowe w sumie czesto nie sa zapisane te query i chcemy sie dpoweidzec skad te dane pochadza tak zwana historia danych zaleznosc miedzy obiektami baz danych a dokladniej chodzi o usuniecie krawedzi w grafie ktore nastepnie za pomoca roznych algorytmow bedziemi chcieli odtworzyc. jest to wazny problem bazy danych bo czesto sa table tymczasowe ktore znikaja bo sa tymczasowe lol i w suemi potem juz nie ma widocznych polaczen w bazie i my chcemy je wyszukac. chcemy wykorzystac zjawiska data lineage i data aby z jakimstam prawdopodobienstwem znalesc te zaleznosci i odtworzyc polaczenia przy pomocy algorytmow np ml 


1.1 Cel i zakres pracy
Celem pracy jest znalezienie i zbadanie jak juz instniejace algorytmy radza sobie z problemem proby odtwarzania i znajdowania tych relacji na podstawie data lineage. Dane beda przeprowadzane na algorytmach ml oraz heurystykach oraz embeddingi wezlow, a dane to z huwawiei 18 grafow dwudzielnych gdzie sa query i inen takie ktore przedstawiaja zanonimowiwane prawdziwe i realne dane jednak nie posiadaja one schematow tej bazy bo nie ma schematow bo rodo i guess ale chyba to ze dane sa realne to jest korzysne i w sumie odrazu mamy i duza i mala skale anyways mamy tez napewno 3 scenariusze podzialu danych pierwszy losowy drugi idk nei pamietam a trzeci to usuniecie widoku zamertializowanego  (w sumie jak cos to jeszcze 2 miesiace wiec mozna pozsci na innych danych zawsze) W pracy nie znajdziemy prawdziwego schematu bazy danych , wlasnego algorytmu autorskiego itd

1.2 struktura pracy:
 - w drugim rodziale zajemiemu sie przedstwieneim najwazniejszymi pojeciami takimi jak data linage data pocenance, graf lineage poral problem broken lineage itd... oraz przegladem literatury i metrykami ewaluacji 
 - w trzecim rozdziale problem i architektora rozwiazania/systemy wraz z obrazkami pochodzenie danych metodyta symulacji i zaimplementowane algorytmy 
 - w czwartym rozdziale ocena rozwiazania co nam wyszlo jaki sed neg_ratio dla wszystkich grafow na wsztstk9ich dancych przejechane 
 - uwagi koncowe i inene takie podsomowanie co jest git co nie wszyszlo i inne takie