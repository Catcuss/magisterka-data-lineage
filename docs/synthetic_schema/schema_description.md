# Syntetyczny schemat bazy danych — ilustracja problemu broken lineage

> **Uwaga:** Poniższy schemat jest **ilustracyjny** — stworzony na potrzeby dokumentacji
> i prezentacji dla promotora. Dane eksperymentalne pochodzą z rzeczywistego zbioru
> DLG-DG-23 (Huawei Cloud), którego węzły są zanonimizowane UUID zgodnie ze standardami
> ochrony danych produkcyjnych. Schemat syntetyczny odwzorowuje *strukturę* typowego
> środowiska ETL, nie konkretne dane Huawei.

---

## 1. Kontekst domenowy — hurtownia danych operatora telekomunikacyjnego

Rozważamy uproszczoną hurtownię danych (data warehouse) operatora telekomunikacyjnego.
System gromadzi dane o połączeniach, klientach i rozliczeniach, przetwarza je przez
potok ETL, a wyniki ładuje do tabel analitycznych (data marts).

### 1.1 Typy obiektów (zgodne z modelem DLG-DG-23)

| Typ obiektu | Symbol | Opis |
|---|---|---|
| `Data Table` | [T] | Relacyjna tabela przechowująca dane |
| `Data Job` | [J] | Fragment kodu SQL / skrypt ETL przetwarzający dane |
| `Data Field` | [F] | Kolumna tabeli (atrybut) |

### 1.2 Typy relacji

| Typ relacji | Kierunek | Opis |
|---|---|---|
| `DATA_FLOW` | [T] → [J] lub [J] → [T] | Tabela dostarcza dane do joba lub job zapisuje wynik do tabeli |
| `PARENT_CHILD` | [T] → [F] | Kolumna należy do tabeli |

---

## 2. Pełny graf lineage (stan przed broken lineage)

### 2.1 Obiekty schematu

**Tabele źródłowe (raw layer):**
- `raw_calls` — surowe rekordy połączeń (call_id, caller_msisdn, callee_msisdn, duration_s, call_date)
- `raw_customers` — rejestr klientów (msisdn, customer_id, segment, contract_type, region)
- `raw_billing` — surowe faktury (invoice_id, msisdn, amount_pln, billing_date, status)
- `dim_region_lookup` — słownik regionów (region_code, region_name, country)

**Tabele staging (warstwa pośrednia — TYMCZASOWE):**
- `stg_daily_call_agg` — dzienne agregaty połączeń per klient (tworzona przez ETL, usuwana po załadowaniu)
- `stg_customer_enriched` — klienci wzbogaceni o dane regionalne (tworzona przez ETL, usuwana po załadowaniu)

**Joby ETL:**
- `job_load_raw_calls` — ładuje surowe połączenia z systemu CDR do `raw_calls`
- `job_aggregate_daily` — agreguje `raw_calls` do `stg_daily_call_agg`
- `job_enrich_customers` — łączy `raw_customers` z `dim_region_lookup` → `stg_customer_enriched`
- `job_build_revenue_mart` — łączy `stg_daily_call_agg` z `raw_billing` → `dm_revenue_daily`
- `job_build_customer_kpis` — łączy `stg_customer_enriched` z `stg_daily_call_agg` → `dm_customer_kpis`

**Tabele analityczne (data mart layer):**
- `dm_revenue_daily` — dzienny przychód per klient per region (customer_id, date, total_calls, total_duration_min, revenue_pln)
- `dm_customer_kpis` — KPI klientów (customer_id, segment, avg_daily_calls, avg_duration_min, churn_risk_score)

### 2.2 Graf pełny (DATA_FLOW)

```
raw_calls ──────────────→ job_load_raw_calls ──────→ raw_calls (self, pomijamy)
                                                            │
raw_calls ──────────────→ job_aggregate_daily ←────────────┘
                               │
                               ↓
                         stg_daily_call_agg ──────→ job_build_revenue_mart ──→ dm_revenue_daily
                                                              ↑
                         raw_billing ──────────────────────────┘

raw_calls ──────────────→ job_aggregate_daily
stg_daily_call_agg ─────→ job_build_customer_kpis ──→ dm_customer_kpis
stg_customer_enriched ──→ job_build_customer_kpis

raw_customers ──────────→ job_enrich_customers ──────→ stg_customer_enriched
dim_region_lookup ──────→ job_enrich_customers

raw_billing ────────────→ job_build_revenue_mart
```

**Uproszczony widok (tylko kluczowe ścieżki):**

```
[raw_calls] ──→ [job_aggregate_daily] ──→ [stg_daily_call_agg] ──→ [job_build_revenue_mart] ──→ [dm_revenue_daily]
                                                    │                         ↑
                                                    └────────────────→ [job_build_customer_kpis] ──→ [dm_customer_kpis]
                                                                               ↑
[raw_customers] ──→ [job_enrich_customers] ──→ [stg_customer_enriched] ──────┘
[dim_region_lookup] ──→ [job_enrich_customers]
[raw_billing] ──→ [job_build_revenue_mart]
```

---

## 3. Scenariusze broken lineage

### Scenariusz A — Usunięcie tabeli staging (`stg_daily_call_agg`)

**Przyczyna:** Po zakończeniu ładowania do `dm_revenue_daily` i `dm_customer_kpis`
skrypt ETL usuwa `stg_daily_call_agg` w celu oszczędności miejsca i uproszczenia
katalogu danych. Usunięcie węzła powoduje **usunięcie wszystkich jego krawędzi DATA_FLOW**.

**Stan przed:**
```
[raw_calls] → [job_aggregate_daily] → [stg_daily_call_agg] → [job_build_revenue_mart] → [dm_revenue_daily]
                                              │
                                              └──────────────→ [job_build_customer_kpis] → [dm_customer_kpis]
```

**Stan po (broken lineage):**
```
[raw_calls] → [job_aggregate_daily]          [job_build_revenue_mart] → [dm_revenue_daily]
                                             [job_build_customer_kpis] → [dm_customer_kpis]
```

**Zerwane krawędzie (do odtworzenia przez algorytm):**
- `stg_daily_call_agg → job_build_revenue_mart`
- `stg_daily_call_agg → job_build_customer_kpis`
- `job_aggregate_daily → stg_daily_call_agg`

**Zależności transytywne do odkrycia:**
- `raw_calls` → ... → `dm_revenue_daily` (przez usuniętą tabelę staging)
- `raw_calls` → ... → `dm_customer_kpis`

**Znaczenie dla data governance:** Bez tej informacji system nie może określić,
że zmiana w `raw_calls` (np. zmiana formatu daty) wpłynie na `dm_revenue_daily`.
Impact analysis jest niemożliwa.

---

### Scenariusz B — Usunięcie UDF / funkcji transformującej (`job_enrich_customers` traci zależność od `dim_region_lookup`)

**Przyczyna:** `job_enrich_customers` korzysta z wewnętrznej funkcji UDF
`udf_normalize_region()`, która wewnętrznie odpytuje `dim_region_lookup`.
Lineage systemu nie rejestruje zależności przez UDF — krawędź
`dim_region_lookup → job_enrich_customers` nigdy nie pojawia się w grafie.

**Stan "pełny" (gdyby UDF był transparentny):**
```
[raw_customers]    → [job_enrich_customers] → [stg_customer_enriched]
[dim_region_lookup] → [job_enrich_customers]
```

**Stan rzeczywisty (broken lineage przez UDF):**
```
[raw_customers]    → [job_enrich_customers] → [stg_customer_enriched]
[dim_region_lookup]   (brak krawędzi do job_enrich_customers)
```

**Zerwana krawędź (do odkrycia):**
- `dim_region_lookup → job_enrich_customers`

**Znaczenie dla data governance:** Jeśli słownik regionów zostanie zaktualizowany,
system nie wie, że wymaga to re-uruchomienia `job_enrich_customers` i przebudowania
`dm_customer_kpis`. Kompletność danych KPI jest zagrożona.

---

### Scenariusz C — Usunięcie widoku zmaterializowanego (`mv_monthly_billing_summary`)

**Przyczyna:** W potoku miesięcznym istniał widok zmaterializowany
`mv_monthly_billing_summary` agregujący dane z `raw_billing`.
Po migracji systemu rozliczeniowego widok został zastąpiony bezpośrednim zapytaniem
w `job_build_revenue_mart`, ale w katalogu metadanych pozostał tylko nowy stan —
historyczna ścieżka lineage została utracona.

**Stan przed migracją:**
```
[raw_billing] → [job_refresh_mv] → [mv_monthly_billing_summary] → [job_build_revenue_mart] → [dm_revenue_daily]
```

**Stan po migracji (broken lineage):**
```
[raw_billing] → [job_build_revenue_mart] → [dm_revenue_daily]
(mv_monthly_billing_summary i job_refresh_mv usunięte z katalogu)
```

**Dodatkowe zerwanie:** Historyczne dane w `dm_revenue_daily` za poprzednie miesiące
faktycznie pochodziły z `mv_monthly_billing_summary`, ale ten fakt jest teraz niewidoczny.
Algorytm musi odtworzyć brakujące ogniwo w historycznym lineage.

**Zerwane krawędzie:**
- `raw_billing → job_refresh_mv`
- `job_refresh_mv → mv_monthly_billing_summary`
- `mv_monthly_billing_summary → job_build_revenue_mart`

**Znaczenie dla data governance:** Audyt jakości danych nie może stwierdzić,
z jakiego źródła pochodzą dane historyczne w `dm_revenue_daily`.
Compliance wymaga pełnego śladu danych (data lineage audit trail).

---

## 4. Metodyka symulacji broken lineage w eksperymentach

W eksperymentach nie usuwamy węzłów (bo to wymaga znajomości rzeczywistych
scenariuszy ETL), lecz **symulujemy broken lineage przez usunięcie krawędzi DATA_FLOW**:

### 4.1 Podejście standardowe (Random Edge Removal)

```
Wszystkie krawędzie DATA_FLOW (E_total)
   ↓ podział losowy (seed=42)
80% → E_train  (widoczne dla algorytmu podczas treningu/ewaluacji)
20% → E_test   (ukryte — "usunięte" krawędzie, które algorytm ma odtworzyć)
```

**Uzasadnienie:** Losowe usuwanie jest standardem w literaturze link prediction
(Liben-Nowell & Kleinberg, 2007). Odpowiada sytuacji, gdy tabele tymczasowe są
usuwane niezależnie od struktury grafu (np. po każdym przebiegu ETL).

### 4.2 Interpretacja wyników

| Metryka | Interpretacja w kontekście broken lineage |
|---|---|
| **Precision** | Jaki % zaproponowanych zależności rzeczywiście istnieje (unikanie fałszywych alarmów) |
| **Recall** | Jaki % utraconych zależności zostaje odtworzony (kompletność rekonstrukcji) |
| **F1-score** | Balans precision/recall — główna metryka |
| **AUC-ROC** | Zdolność rankingowania par (brak utraconej zależności vs. krawędź) niezależnie od progu |

### 4.3 Próbkowanie negatywne

Algorytm musi odróżniać brakujące krawędzie (pozytywne) od par węzłów,
między którymi zależność nigdy nie istniała (negatywne). Negatywne próbki
są generowane losowo z zachowaniem zgodności typów:
- Para (Data Table, Data Job) lub (Data Job, Data Table) — poprawna dla DATA_FLOW
- Para (Data Table, Data Table) — niemożliwa (wykluczona z próbkowania)

---

## 5. Mapowanie do DLG-DG-23

| Element schematu syntetycznego | Odpowiednik w DLG-DG-23 |
|---|---|
| `raw_calls`, `raw_customers`, `raw_billing` | `Data Table` z niskim stopniem wejściowym |
| `stg_daily_call_agg`, `stg_customer_enriched` | `Data Table` usunięte ze struktury (symulowane przez usunięcie krawędzi) |
| `job_aggregate_daily`, `job_enrich_customers`, etc. | `Data Job` (węzły pośrednie) |
| `dm_revenue_daily`, `dm_customer_kpis` | `Data Table` z wysokim stopniem wejściowym (data marts) |
| Usunięte krawędzie (20% split) | Brakujące krawędzie DATA_FLOW do odtworzenia |

Rzeczywiste grafy DLG-DG-23 mają od 24 do ~1220 krawędzi DATA_FLOW,
co odpowiada znacznie bardziej złożonym potokom ETL niż schemat illustracyjny.
Nazwy węzłów są zastąpione UUID ze względu na poufność danych produkcyjnych Huawei Cloud.
