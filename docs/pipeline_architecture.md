# Pipeline Architecture Reference
## NSW Property Market — End-to-End Data Pipeline
**Mehmood Ahmed Khan** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

> This document is the technical reference for the NSW Property Market pipeline.
> It covers file and database structure, stage-by-stage design decisions, confirmed ML decisions,
> and the architectural choices that should not be revisited without understanding their evidence base.
> For data provenance, limitations, and research potential see [`docs/data_provenance.md`](data_provenance.md).

---

## File and Database Reference

| File | Purpose | Location |
|------|---------|----------|
| `NSW_Master.ipynb` | Stage 1: extraction and cleaning — raw `.DAT` archives to `clean` and `analysis` tables | Local; see the README for whether it is published |
| `01.NSW_Property_SQL_Pipeline.ipynb` | Stage 2: SQL analytical pipeline — Stages 00–13 | `notebooks/` |
| `australian_postcodes.csv` | Matthew Proctor postcode reference — ABS 2021 aligned | Same folder as notebook |
| `nsw_property.db` | Persistent DuckDB database — all Stage 2 pipeline tables | Same folder as notebook |
| `Visual/` | All 23 chart PNGs (Stage 2, earlier data) | `Visual/` |
| `presentation/` | 16-page HTML case study (Stage 2, earlier data) | `presentation/` |

> **Note:** Update `DB_PATH` and `CSV_GEO` at the top of Stage 00 to match your local directory
> before running Stage 2. If you have the Stage 1 notebook, set `NSW_EXTRACTION_DIR` in its configuration cell to the
> folder containing the yearly zip archives.
>
> **Counts and shares for Stage 1 are maintained in the README**, not repeated here, so that each number lives in one place.

---

## Stage 1 — Extraction Architecture (NSW_Master.ipynb)

### Design principles

1. **No imputation.** A missing value stays missing and is flagged with a reason column.
2. **No step can multiply rows.** Every stage logs rows before and after; an automated check
   fails if any step increases the count.
3. **Flag, don't filter.** Price problems, area problems, and the incomplete tail are flagged —
   filtering belongs to the analysis layer.
4. **Every rule logs how many rows it touched.**

### Stage 1 — Key decisions

**Re-published sales:**
The same sale line can appear again in later extracts. The latest copy is kept (an `earliest` option exists).
Identical lines inside one extract are kept and flagged. Sales that share an identity but differ in price or
settlement date are flagged as possible revisions, not removed.

**Area units:**
Each area value carries an `Area_Type` field (`M` = square metres, `H` = hectares). `Area_sqm` is derived from
it, so no single-unit assumption is applied. Hectare records concentrate in rural, commercial and environmental zoning.

**Dates from the raw files:**
Settlement dates are read from the raw files and are present for every source year. Rows with a date anomaly
(missing contract date, settlement before contract, a date before 1990, or a gap of more than 10 years) are
flagged, none removed.

**Geography matched per place:**
The sales hold only a few thousand distinct (locality, postcode) pairs. Each is matched once and copied back
by position, so rows cannot multiply. Every match carries a method and a quality label. A human-reviewed entry
covers a suburb missing from the reference file.

**Postcode-level label risk:**
Every area label in the postcode reference (LGA, remoteness, SA2–SA4) is identical for all localities within a
postcode. Affected columns carry `..._PostcodeLevel` naming and an `Area_Label_Risk` flag.

### Stage 1 — Output tables

| Table | Columns | Purpose |
|---|---|---|
| `clean` | 76 | Full audit table — every field, all lineage, every flag |
| `analysis` | 34 | One column per idea — for exploration and modelling |

---

## Stage 2 — Database Architecture (DuckDB)

> **Stage 2 was built on an earlier extraction and is kept as published.** Its column names and row set differ
> from the Stage 1 tables, so it cannot simply be pointed at them. Where Stage 1 revised a Stage 2 conclusion,
> this document says so in-line ("Revised by Stage 1"). A new analysis layer will be built on the `analysis` table.

### Table reference

| Table | Rows | Role | Modify? |
|-------|------|------|---------|
| `staging_transactions` | 1,697,724 | Raw data audit trail — frozen at ingestion | Never |
| `geo_raw` | 5,272 | Raw postcode reference | Never |
| `geo_reference_clean` | 617 | Clean postcode reference — one row per postcode | Never |
| `rba_cash_rate` | 32 | RBA rate timeline Q1 2018–Q4 2025 | Never |
| `clean_transactions` | 1,697,724 | Typed, flagged, Area_sqm corrected | Never |
| `enriched_transactions` | 1,697,724 | + Geo fields, density zones, distance_cbd_km | Never |
| `final_transactions` | 1,697,724 | + RBA cash rate fields | Never |
| `analytical_transactions` | 1,494,123 | Primary analysis table — 2018–2025 in scope | Read only |
| `residential_transactions` (VIEW) | 1,259,466 | ML training dataset — residential only | Read only |

**Design principle:** Every stage creates a new table. No stage modifies an upstream table.
`staging_transactions` is the permanent audit trail — the raw data exactly as received.

---

## Stage 2 — Stage-by-Stage Design Decisions

### Stage 00 — Session Startup
Connects to `nsw_property.db`, displays all pipeline tables with row counts and OK/WARN/MISSING
status, and confirms source files are reachable.

**Always run this first.** If all tables show OK — skip directly to your working stage.

---

### Stage 01 — Raw Ingestion

- All 19 columns ingested as VARCHAR — no type coercion at load
- `geo_raw` filtered to NSW Delivery Area rows with valid coordinate bounds at load
- `staging_transactions` is frozen from this point — never modified by any downstream stage

**Why VARCHAR ingestion:** Type coercion at load would silently mask data quality issues.
Stage 02 profiles the raw types explicitly before any casting decisions are made.

---

### Stage 02 — Column Profiling and Data Quality Audit

Full null and distinct audit across all 19 columns producing a data quality scorecard.
Key profiling outputs:

- Nature_of_Property vs Primary_Purpose cross-tabulation
- Zoning distribution: R2 = 29.11%, R1 = 12.31%
- Top 40 Locality values — 4,369 distinct confirmed
- `%_Interest` distribution — revealed NSW VG government encoding convention
- `Area_(ha)` raw audit — assumed to contain square metre values despite the column name (**revised by Stage 1**: a share of rows are in hectares)
- Price vs Area null matrix — zero rows need dropping (every row has a price)
- Settlement_Date year distribution — revealed a 2023 data gap and pre-2018 records (cause identified later in Stage 1: dates lost in the earlier extraction)

**Output:** Data quality scorecard documenting all 10 findings with evidence.
`staging_transactions` remains completely untouched.

---

### Stage 03 — Clean Table Creation

| Transformation | Evidence | Decision |
|---------------|---------|---------|
| 4 columns dropped | `Sale_Code` 94% null, `Strata_Lot_Number` 63% null, `Component_Code` 41% null, `column00` is index | Removed — no analytical value |
| `3.0` → `3` in Nature_of_Property | Float artifact from source merge | Consolidated |
| Postcode float fix | `2112.0` instead of `2112` throughout | `CAST(TRY_CAST(Postcode AS INTEGER) AS VARCHAR)` |
| `Area_(ha)` renamed to `Area_sqm` | Values assumed to be square metres | Renamed. **Revised by Stage 1:** the unit varies by row (`Area_Type`) |
| Dates cast to DATE, prices to DOUBLE | VARCHAR ingestion — now safe to cast | Applied |
| `has_area` flag added | 26.9% of records have NULL area | Boolean flag for ML feature engineering |
| `property_segment` created | RESIDENTIAL / VACANT_LAND / NON_RESIDENTIAL | Derived from Nature_of_Property + Primary_Purpose |

---

### Stage 04 — Geo Reference Build

Builds `geo_reference_clean` — one clean row per postcode — from `geo_raw`.

**Source selection decision:** An earlier hand-edited extract of the postcode file (`geo_for_merge.csv`) was
set aside. Two localities in the source file itself (Birdlip and Kempton) carry impossible coordinates, in England
and in the USA, and the extract inherited them. Matthew Proctor's ABS 2021-aligned reference is used directly:
rows outside valid coordinate bounds are excluded at load (Stage 01), and distances are validated against known
NSW distances.

**Distance calculation:** `distance_cbd_km` calculated using the Haversine formula.
Sydney CBD reference: (–33.8688°S, 151.2093°E). Not trusted from source — recalculated independently.

**Validation results:**

| Postcode | Expected | Calculated |
|---------|---------|-----------|
| 2000 | ~0 km | ✓ |
| 2060 | ~4 km | ✓ |
| 2100 | ~17 km | ✓ |
| 2150 | ~23 km | ✓ |
| 2500 | ~80 km | ✓ |
| 2300 | ~160 km | ✓ |
| 2640 | ~570 km | ✓ |
| 2880 | ~940 km | ✓ |

---

### Stage 05 — Geo Enrichment JOIN

LEFT JOIN `clean_transactions` to `geo_reference_clean` on Postcode.

- **Match rate: 99.74%** — 4,434 unmatched rows out of 1,697,724
- `density_zone` assigned from ABS RA_2021 remoteness classification (a postcode-level label; see `data_provenance.md` section 4.4)
- `price_per_sqm` calculated as `Purchase_Price / Area_sqm`
- **`price_per_sqm` returns NULL where `Area_sqm < 50`** — sub-10 sqm band produces
  median $412,371/sqm, confirmed as strata components or recording errors in Stage 09

---

### Stage 06 — RBA Cash Rate Table

32 quarters of official RBA cash rate records — Q1 2018 to Q4 2025.
Hardcoded from RBA public records with key policy events labelled:

| Event | Quarter | Rate |
|-------|---------|------|
| Pre-COVID baseline | Q1 2018 | 1.50% |
| COVID emergency cut | Q1 2020 | 0.50% |
| Historic low | Q3 2020 | 0.10% |
| First hike | Q2 2022 | 0.85% |
| Peak rate | Q4 2023 | 4.35% |
| First cut | Q1 2025 | 4.10% |

Rate environments: `ULTRA_LOW` (≤0.25%) · `LOW` (≤1.50%) · `RISING` (≤3.00%) · `HIGH` (≤4.35%)

---

### Stage 07 — RBA Enrichment JOIN

Joins `final_transactions` to `rba_cash_rate` on `YEAR(Settlement_Date) = r.year AND QUARTER(Settlement_Date) = r.quarter`.

Rows with NULL Settlement_Date receive no rate assignment and are excluded by the analytical scope filter in Stage 08.

---

### Stage 08 — Analytical Scope Filter

Filters `final_transactions` to produce `analytical_transactions`:

- Settlement_Date within 2018–2025
- `suspect_price = FALSE`
- `tx_year` and `tx_month` added from Settlement_Date — replaces the `Year` column, which is the source-file year (it equals the settlement year on about 98% of rows, not all)
- Result: **1,494,123 analytical records**

**Critical decision — `partial_interest` filter removed:**
NSW Valuer General encodes `%_Interest = 0` as a **full transfer** (100% interest), not zero percent
interest. Only ~5,800 genuine non-zero partial interest records exist. The filter was removed entirely
to avoid discarding the majority of legitimate transactions.

---

### Stage 08b — ML Residential View

`residential_transactions` VIEW applies three filters to `analytical_transactions`:

- `property_segment = 'RESIDENTIAL'`
- `geo_matched = TRUE` (99.74% pass rate)
- Purchase_Price between $50,000 and $10,000,000

**Why a VIEW rather than a table:** Analytical transactions are preserved intact for descriptive
analysis. The ML scope restriction is applied as a non-destructive view.

Result: **1,259,466 rows** — the ML training dataset.

---

### Stage 09 — Outlier Analysis

**Purchase_Price — key statistics:**

| Metric | Value |
|--------|-------|
| Median | $782,000 |
| Mean | $1,051,126 |
| Mean – Median gap | $269,126 (34% inflation from prestige tail) |
| IQR upper fence | $2,407,500 |
| Rows above upper fence | 81,942 (real prestige sales — retained) |

**Outlier summary:**

| Category | Rows | Pct | Treatment |
|----------|------|-----|-----------|
| Clean on both dimensions | 1,136,498 | 90.24% | Primary ML training base |
| Price outliers only | 77,507 | 6.15% | 86% Metro — real prestige, retained |
| Area outliers only | 41,026 | 3.26% | 82% Regional — large lots, retained |
| Outliers on both | 4,435 | 0.35% | Prestige acreage — retained |

**Decision: No rows dropped.** Log transformation handles distributional skew. Dropping flagged
rows would remove real market transactions — prestige sales and large rural lots are genuine,
not errors.

---

### Stage 10 — Analytical Views and Visualisations

> Findings below were computed on the earlier extraction and rest on postcode-level geography. They are being re-verified.

Seven analytical views — all dynamically calculated, no hardcoded statistics:

| View | Key Finding |
|------|------------|
| 10a Quarterly trend | 2025 Q4 $975,000 — new historical high above pre-hike peak |
| 10b Zone annual prices | Inner Regional rose during rate hike cycle — regional resilience confirmed |
| 10c Top LGAs by price | Northern Beaches $2,682,000 · Woollahra $2,175,000 · Mosman $1,950,000 |
| 10d Top LGAs by volume | Parramatta 79,475 (6.31%) · Ryde 62,263 · Blacktown 54,738 |
| 10e Rate paradox | Prices highest when rates highest — 18–24 month settlement lag |
| 10f Price per sqm gradient | Metro $3,414 vs Very Remote $216 — **15.8× ratio** |
| 10g YoY change | 2021 +13.48% COVID boom — only –6.3% correction from peak |

**2023 data note:** Only 2,861 transactions are recorded under 2023 settlement dates (vs ~190,000 in all other
years). This is a gap in the Stage 2 data, not a market event. **Revised by Stage 1:** the raw 2023 files contain
the dates; they were lost in the earlier per-year extraction, so those records had no settlement date. Stage 2
excludes 2023 from trend narratives with a documented caveat.

**Chart colour palette — consistent across all 23 charts:**

```python
COLORS = {
    'METRO'          : '#1f4e79',
    'INNER_REGIONAL' : '#2e75b6',
    'OUTER_REGIONAL' : '#70ad47',
    'REMOTE'         : '#ed7d31',
    'VERY_REMOTE'    : '#c00000',
    'rba_rate'       : '#c00000',
    'price'          : '#1f4e79',
    'bar_main'       : '#2e75b6',
    'bar_accent'     : '#ed7d31',
    'annotation'     : '#c00000',
}
```

---

### Stage 11 — ML Feature Table

| Feature | Source | Transform |
|---------|--------|-----------|
| `log_price` | Purchase_Price | LOG(Purchase_Price) — ML target variable |
| `log_area` | Area_sqm | LOG(Area_sqm) — where not NULL |
| `distance_cbd_km` | geo_reference_clean | As-is |
| `tx_year` | Settlement_Date | As-is |
| `tx_month` | Settlement_Date | As-is |
| `tx_quarter` | Settlement_Date | As-is (1–4) |
| `cash_rate_pct` | rba_cash_rate | As-is |
| `density_zone_encoded` | density_zone | METRO=0, INNER_REGIONAL=1, OUTER_REGIONAL=2, REMOTE=3, VERY_REMOTE=4 |
| `property_type_clean` | clean_transactions | Label encode (R, V, 3) |
| `has_area` | clean_transactions | Boolean as integer |
| `price_per_sqm` | enriched_transactions | Where Area_sqm ≥ 50 only |
| `lga_median_price` | Derived | Rolling median per LGA per year — training split only |

**Train/test split:** 80/20 by a deterministic hash of the dealing number (multi-lot sales stay together), stratified by `tx_year` and `density_zone`; `price_per_sqm` is excluded and `lga_median_price` is computed from the training split only  
**Target variable:** `log(Purchase_Price)` — back-transformed for reporting

---

### Stage 12 — Model Results

| Model | R² | MAE | Notes |
|---|---|---|---|
| ExtraTrees | **0.714** | **$279k** | Best overall |
| LightGBM | 0.711 | — | |
| XGBoost | 0.702 | — | |
| Ridge | 0.477 | — | Kept for coefficient interpretability |

**Feature importance (ExtraTrees):**

| Feature | Importance |
|---|---|
| LGA-year median price | 35.6% |
| Distance to CBD | 21.1% |
| Area (sqm) | 18.7% |
| Density zone | 16.9% |

---

### Stage 13 — Forecasting

Prophet forecasts for 2026 by density zone and for selected LGAs, using assumed RBA cash-rate paths. 2023 is
excluded from the training series as a filing artifact (**revised by Stage 1**: the gap comes from dates lost in
the earlier extraction). Like the other Stage 2 results, the forecasts rest on postcode-level geography.

---

## Architectural Decisions and Their Status

| # | Decision | Evidence Base | Status |
|---|----------|--------------|--------|
| 1 | Suburb standardisation abandoned — Stage 2 analyses at postcode/LGA level | 4,369+ locality variants — too noisy for reliable grouping | Stands for Stage 2. Stage 1 matches (locality, postcode) places and normalises only spacing and case |
| 2 | `geo_for_merge.csv` set aside — the Proctor ABS-aligned file is used directly | The hand-edited extract inherited impossible coordinates from the source file (England, USA) | Stands, with corrected evidence |
| 3 | `partial_interest` filter removed entirely | NSW VG convention: `%_Interest = 0` means full transfer, not zero percent | Stands |
| 4 | `tx_year` from Settlement_Date used throughout | `Year` is the source-file year; it equals the settlement year on about 98% of rows, not all | Stands, reworded |
| 5 | 2023 excluded from Stage 2 trend narratives | The Stage 2 data has only 2,861 records under 2023 settlement dates | **Revised by Stage 1:** a workaround, not a filing artifact — the dates were lost in the earlier extraction and are recovered in Stage 1 |
| 6 | `Area_(ha)` renamed to `Area_sqm`; `×10,000` conversion removed | The unit was assumed to be square metres throughout | **Revised by Stage 1:** the unit varies by row; Stage 1 derives `Area_sqm` from `Area_Type` |
| 7 | Non-residential excluded from ML training | Residential only — consistent valuation logic, 84% of analytical data | Stands for Stage 2. Stage 1 keeps all property types and flags them |
| 8 | All chart annotations dynamically calculated | No hardcoded statistics — charts remain valid if data is updated or extended | Stands |
| 9 | Median used throughout all reporting — not mean | Mean inflated $269,126 above median by prestige tail — misleading for policy use | Stands |
| 10 | Log transformation confirmed for both Purchase_Price and Area_sqm | Heavy right skew on both — std dev ≈ mean on price confirms non-normality | Stands |

---

*Pipeline architecture reference — Stage 1 complete; Stage 2 (Stages 00–13) complete on the earlier extraction and kept as published; Stage 3 planned.*
