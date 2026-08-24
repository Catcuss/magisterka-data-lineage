# Test cross-dataset — DLG-DG-23 → graf Dutkiewicza (DUT)

Sprawdzenie przenośności detektora **poza** zbiór treningowy: model uczony
wyłącznie na DLG-DG-23 ocenia się na zewnętrznym grafie zbudowanym z repozytorium
Dutkiewicz–Misiorek–Wrembel (`github.com/dudenzz/lineage`, baza Northwind +
syntetyczne scenariusze SQL).

## Schemat
- **Trening:** grafy MAŁE + ŚREDNIE z DLG-DG-23 (13 grafów) — zgodnie ze schematem
  `run_scale_generalization.py`.
- **Test:** grafy DUŻE z DLG-DG-23 (5) **oraz** graf zewnętrzny **DUT** (21 tabel,
  14 zadań, 33 krawędzie DATA_FLOW). Model NIE jest douczany na DUT.
- Adapter: [src/data/dutkiewicz_adapter.py](../src/data/dutkiewicz_adapter.py) —
  agreguje lineage wierszowy (`DataLineage.csv`) do modelu tabela–zadanie–DATA_FLOW.
- Dane źródłowe: `data/external/dutkiewicz/{train,test}_DataLineage.csv`.

## Odtworzenie
```bash
# wariant napompowany (izolowane włączone)
python src/detection/run_cross_dataset.py --repeats 15 --removal-ratio 0.2
# wariant uczciwy (bez przecieku izolacji)
python src/detection/run_cross_dataset.py --repeats 20 --removal-ratio 0.3 \
    --exclude-isolated --csv results/wyniki_cross_dataset_uczciwy.csv
```

## Pliki wyników
- `wyniki_cross_dataset.csv` — wariant napompowany.
- `wyniki_cross_dataset_uczciwy.csv` — wariant uczciwy (główny w pracy).

## Główny wynik (graf zewnętrzny DUT)
| Wariant | LineageDetector AUC-ROC | AUC-PR | Brier | LightGBM AUC-ROC | RF AUC-ROC |
|---|---|---|---|---|---|
| napompowany | 0.773 | 0.721 | **0.141** | 0.797 | 0.776 |
| uczciwy     | 0.641 | 0.521 | **0.187** | 0.674 | 0.625 |

Odniesienie wewnątrz zbioru (duże grafy DLG, wariant uczciwy): LineageDetector 0.623,
LightGBM 0.605, RF 0.617.

## Wnioski i zastrzeżenia
- **Transfer działa:** modele uczone nie załamują się na grafie z innego źródła —
  AUC-ROC na DUT jest porównywalne (lub lepsze) niż na dużych grafach DLG.
- **LineageDetector zachowuje najlepszą kalibrację** (Brier) w obu wariantach.
- ⚠ DUT jest bardzo mały (21 tabel) → liczba infected spada poniżej MIN_POS=5
  w wariancie uczciwym; wynik ma charakter jakościowy (proof of concept).
- ⚠ Na łańcuchowej topologii DUT trywialne heurystyki stopnia zawyżają AUC-ROC
  (0.751), a **score kompletności załamuje się** (0.500) — peer-consistency wymaga
  rozgałęzień, których brak w liniowych łańcuchach. Dlatego LineageDetector nie
  zyskuje tu przewagi nad czystym LightGBM.
- Kierunek dalszy: większy, rozgałęziony graf zewnętrzny (patrz rozdz. 5 pracy).
