# Bieg kanoniczny — jedno źródło prawdy dla rozdziału 4

Wszystkie liczby w pracy pochodzą z TEGO biegu. Nie mieszać z plikami
`wyniki_detekcja_v2.csv` / `_det_v2.txt` — były niespójne (inna wersja
detektora) i zostają jako archiwum.

## Ustawienia (cytuj je w rozdz. 3 i 4)
- Grafy: wszystkie 18 (DLG1–DLG18)
- removal_ratio = 0.10, side = both
- Powtórzenia: 3 (seedy 42, 43, 44)
- Protokół: indukcyjny, leave-one-graph-out
- MIN_POS = 5 (graf „wiarygodny", jeśli ma ≥5 zainfekowanych tabel w teście)
- Agregacja: średnia po grafach wiarygodnych (reliable=True)

## Pliki
| Wariant | Surowe (per graf) | Log/podsumowanie | Agregat CSV | Tabela LaTeX |
|---|---|---|---|---|
| UCZCIWY (exclude_isolated) — GŁÓWNY | `wyniki_detekcja_canon.csv` | `_det_canon.txt` | `agregat_detekcja.csv` | `tabela_detekcja.tex` |
| NAPOMPOWANY (z przeciekiem) — dla kontrastu | `wyniki_detekcja_napompowany.csv` | `_det_napompowany.txt` | `agregat_detekcja_napompowany.csv` | `tabela_detekcja_napompowany.tex` |

Regeneracja:
```
python -m src.detection.run_detection_experiments --all --exclude-isolated \
    --removal-ratio 0.10 --repeats 3 --seed 42 --csv results/wyniki_detekcja_canon.csv
python -m src.detection.run_detection_experiments --all \
    --removal-ratio 0.10 --repeats 3 --seed 42 --csv results/wyniki_detekcja_napompowany.csv
python scripts/aggregate_detection.py            # tabela główna
```

## Wyniki — wariant UCZCIWY (główny), 8 grafów wiarygodnych
| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| Anomalia stopnia | 0.427 | 0.165 | 0.142 | 0.134 |
| Brzeg (root/leaf) | 0.455 | 0.137 | 0.146 | 0.745 |
| Niska łączność jobów | 0.324 | 0.112 | 0.094 | 0.226 |
| Reguła korzenia | 0.574 | 0.168 | 0.180 | 0.469 |
| Kompletność (peer-consistency)* | 0.559 | 0.206 | 0.240 | 0.144 |
| Random Forest | 0.749 | 0.425 | 0.380 | 0.117 |
| RUSBoost | 0.631 | 0.249 | 0.340 | 0.152 |
| LightGBM | 0.720 | 0.381 | 0.398 | 0.147 |
| **LineageDetector*** | **0.771** | **0.435** | **0.443** | **0.106** |

\* wkład własny. LineageDetector najlepszy na WSZYSTKICH metrykach.

## Wyniki — wariant NAPOMPOWANY (kontrast), 10 grafów wiarygodnych
RF 0.816, LightGBM 0.805, LineageDetector 0.842; heurystyki `boundary` 0.600,
`low_job_connectivity` 0.518. W wariancie uczciwym te heurystyki spadają
(0.455 / 0.324) — „żyły z przecieku izolowana ⟹ chora".

## ⚠️ HACZYK do opisania w rozdz. 4.3
Warianty mają RÓŻNĄ liczbę grafów wiarygodnych: uczciwy = 8, napompowany = 10.
Powód: wykluczenie izolowanych zmniejsza liczbę pozytywów, więc 2 grafy
spadają poniżej MIN_POS=5. Dlatego NIE odejmuj liczb 1:1 między tabelami —
każdy wariant uśredniony jest po SWOIM zbiorze wiarygodnych grafów. Jeśli
chcesz „czystego" porównania spadku przez przeciek, policz je na wspólnym
podzbiorze grafów (te same ID w obu wariantach) — to zadanie do rozdz. 4.3.

## Uwaga o metrykach P@k = R@k = Hits@k
W tym biegu k = liczba zainfekowanych, więc Precision@k = Recall@k (i Hits@k
się z nimi pokrywa). W tabeli można zostawić jedną z nich albo opisać relację
w tekście, żeby nie sugerować trzech niezależnych metryk.