# Test cross-dataset — przegląd konfiguracji na grafie DUT

Analiza poboczna (nie wchodzi do głównej tabeli pracy). Trening: małe+średnie DLG-DG-23; ewaluacja: graf zewnętrzny DUT (Dutkiewicz, train+test scalone).

- Graf DUT: {'Data Table': 21, 'Data Job': 14, 'Data Field': 21}, krawędzie {'DATA_FLOW': 33, 'PARENT_CHILD': 21}
- Powtórzenia na konfigurację: 25; removal_ratio ∈ [0.2, 0.3, 0.4]


## Wariant: napompowany

### removal_ratio = 0.2  (śr. #infected ≈ 6.6)

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| degree_anomaly | 0.851 | 0.680 | 0.603 | 0.173 |
| boundary | 0.828 | 0.659 | 0.576 | 0.510 |
| low_job_connectivity | 0.851 | 0.680 | 0.603 | 0.167 |
| completeness | 0.500 | 0.316 | 0.350 | 0.316 |
| rule_root | 0.705 | 0.479 | 0.538 | 0.309 |
| RandomForest | 0.758 | 0.717 | 0.605 | 0.175 |
| RUSBoost | 0.627 | 0.496 | 0.499 | 0.217 |
| LightGBM | 0.794 | 0.750 | 0.625 | 0.242 |
| LineageDetector | 0.767 | 0.730 | 0.624 | 0.139 |

### removal_ratio = 0.3  (śr. #infected ≈ 8.5)

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| degree_anomaly | 0.866 | 0.768 | 0.644 | 0.194 |
| boundary | 0.847 | 0.752 | 0.639 | 0.526 |
| low_job_connectivity | 0.866 | 0.768 | 0.644 | 0.159 |
| completeness | 0.500 | 0.406 | 0.371 | 0.406 |
| rule_root | 0.723 | 0.577 | 0.611 | 0.290 |
| RandomForest | 0.793 | 0.802 | 0.675 | 0.194 |
| RUSBoost | 0.681 | 0.658 | 0.599 | 0.208 |
| LightGBM | 0.813 | 0.828 | 0.689 | 0.231 |
| LineageDetector | 0.812 | 0.814 | 0.704 | 0.147 |

### removal_ratio = 0.4  (śr. #infected ≈ 12.2)

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| degree_anomaly | 0.881 | 0.871 | 0.752 | 0.233 |
| boundary | 0.873 | 0.865 | 0.744 | 0.562 |
| low_job_connectivity | 0.881 | 0.871 | 0.752 | 0.142 |
| completeness | 0.500 | 0.581 | 0.561 | 0.581 |
| rule_root | 0.779 | 0.760 | 0.764 | 0.225 |
| RandomForest | 0.847 | 0.909 | 0.782 | 0.165 |
| RUSBoost | 0.765 | 0.845 | 0.731 | 0.179 |
| LightGBM | 0.845 | 0.909 | 0.785 | 0.176 |
| LineageDetector | 0.843 | 0.905 | 0.792 | 0.145 |


## Wariant: uczciwy (exclude_isolated)

### removal_ratio = 0.2  (śr. #infected ≈ 3.9)

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| degree_anomaly | 0.766 | 0.365 | 0.333 | 0.161 |
| boundary | 0.726 | 0.329 | 0.280 | 0.431 |
| low_job_connectivity | 0.766 | 0.365 | 0.333 | 0.191 |
| completeness | 0.500 | 0.211 | 0.221 | 0.211 |
| rule_root | 0.630 | 0.328 | 0.377 | 0.346 |
| RandomForest | 0.646 | 0.462 | 0.347 | 0.190 |
| RUSBoost | 0.484 | 0.209 | 0.211 | 0.180 |
| LightGBM | 0.663 | 0.482 | 0.364 | 0.297 |
| LineageDetector | 0.654 | 0.503 | 0.390 | 0.159 |

### removal_ratio = 0.3  (śr. #infected ≈ 4.5)

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| degree_anomaly | 0.762 | 0.430 | 0.332 | 0.180 |
| boundary | 0.725 | 0.394 | 0.325 | 0.407 |
| low_job_connectivity | 0.762 | 0.430 | 0.332 | 0.196 |
| completeness | 0.500 | 0.263 | 0.278 | 0.263 |
| rule_root | 0.622 | 0.374 | 0.403 | 0.349 |
| RandomForest | 0.618 | 0.511 | 0.410 | 0.221 |
| RUSBoost | 0.483 | 0.262 | 0.271 | 0.222 |
| LightGBM | 0.664 | 0.559 | 0.432 | 0.304 |
| LineageDetector | 0.646 | 0.534 | 0.452 | 0.183 |

### removal_ratio = 0.4  (śr. #infected ≈ 5.4)

| Metoda | AUC-ROC | AUC-PR | P@k | Brier |
|---|---|---|---|---|
| degree_anomaly | 0.748 | 0.550 | 0.431 | 0.224 |
| boundary | 0.727 | 0.530 | 0.412 | 0.342 |
| low_job_connectivity | 0.748 | 0.550 | 0.431 | 0.208 |
| completeness | 0.500 | 0.384 | 0.287 | 0.384 |
| rule_root | 0.686 | 0.556 | 0.574 | 0.316 |
| RandomForest | 0.680 | 0.687 | 0.496 | 0.224 |
| RUSBoost | 0.504 | 0.395 | 0.328 | 0.264 |
| LightGBM | 0.656 | 0.660 | 0.524 | 0.249 |
| LineageDetector | 0.684 | 0.685 | 0.555 | 0.211 |


_Wygenerowano skryptem run_cross_dataset_dut_sweep.py, czas 427s._
