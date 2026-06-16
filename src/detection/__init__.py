"""
Detekcja chorych węzłów (broken lineage node detection).

Nowe podejście (po konsultacji z dr. P. Misiorkiem): zamiast przewidywać
konkretne brakujące krawędzie (predykcja krawędzi okazała się zbyt trudna na
rzadkich grafach DLG-DG-23), wykrywamy ZAINFEKOWANE TABELE — te, które po
usunięciu zadania (joba) straciły producenta lub konsumenta danych.

Zadanie: klasyfikacja/ranking węzłów typu Data Table wg prawdopodobieństwa,
że ich lineage jest zerwany. Protokół: indukcyjny cross-graph (trening na
podzbiorze z 18 grafów, test na pozostałych).
"""
