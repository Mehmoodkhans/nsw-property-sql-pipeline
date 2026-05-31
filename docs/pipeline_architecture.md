# Pipeline Architecture Reference
## NSW Property Market — SQL Data Pipeline
**Mehmood Ahmed** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

> This document serves as the technical reference for the NSW Property Market SQL pipeline.
> It covers file and database structure, stage-by-stage design decisions, confirmed ML decisions,
> and the architectural choices that should not be revisited without understanding their evidence base.
> For data provenance, limitations, and research potential see [`docs/data_provenance.md`](data_provenance.md).

---

## File and Database Reference

| File | Purpose | Location |
|------|---------|----------|
| `Merged_All_data.csv` | NSW Valuer General transactions 2018–2025 — 1,697,724 rows | Same folder as notebook |
| `australian_postcodes.csv` | Matthew Proctor postcode reference — ABS 2021 aligned | Same folder as notebook |
| `nsw_property.db` | Persistent DuckDB database — all pipeline tables | Same folder as notebook |
| `01_NSW_Property_SQL_Pipeline.ipynb` | Main pipeline notebook — Stages 00–13 | `notebooks/` |
| `visuals/` | All 10 saved chart PNGs | `visuals/` |

> **Note:** Update `DB_PATH`, `CSV_MAIN`, and `CSV_GEO` at the top of Stage 00
> to match your local directory before running.

---

## Database Architecture — Table Reference

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

## Stage-by-Stage Design Decisions

### Stage 00 — Session Startup
Connects to `nsw_property.db`, displays all pipeline tables with row counts and OK/WARN/MISSING
status, and confirms both source CSV files are reachable.

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
- `Area_(ha)` raw audit — confirmed to contain square metre values despite the column name
- Price vs Area null matrix — zero rows need dropping (every row has a price)
- Settlement_Date year distribution — revealed 2023 data gap and pre-2018 records

**Output:** Data quality scorecard documenting all 10 findings with evidence.
`staging_transactions` remains completely untouched.

---

### Stage 03 — Clean Table Creation

Transformations applied to produce `clean_transactions`:

| Transformation | Evidence | Decision |
|---------------|---------|---------|
| 4 columns dropped | `Sale_Code` 94% null, `Strata_Lot_Number` 63% null, `Component_Code` 41% null, `column00` is index | Removed — no analytical value |
| `3.0` → `3` in Nature_of_Property | Pandas float artifact from yearly file merge | Consolidated |
| Postcode float fix | `2112.0` instead of `2112` throughout | `CAST(TRY_CAST(Postcode AS INTEGER) AS VARCHAR)` |
| `Area_(ha)` renamed to `Area_sqm` | Values confirmed in square metres — legacy mislabelling in NSW VG source | Renamed — `×10,000` conversion removed |
| Dates cast to DATE, prices to DOUBLE | VARCHAR ingestion — now safe to cast | Applied |
| `has_area` flag added | 26.9% of records have NULL area | Boolean flag for ML feature engineering |
| `property_segment` created | RESIDENTIAL / VACANT_LAND / NON_RESIDENTIAL | Derived from Nature_of_Property + Primary_Purpose |

---

### Stage 04 — Geo Reference Build

Builds `geo_reference_clean` — one clean row per postcode — from `geo_raw`.

**Source selection decision:** A manually curated geo file was tested and discarded after
validation revealed corrupt coordinates — two NSW postcodes had been assigned coordinates
in Gloucestershire, England and Pennsylvania, USA respectively. Matthew Proctor's
ABS 2021-aligned reference was adopted instead and validated against known NSW distances.

**Deduplication logic:** One row per postcode, preferring rows with ABS RA_2021
classification present, then rows with valid coordinates.

**Distance calculation:** `distance_cbd_km` calculated using the Haversine formula.
Sydney CBD reference: (-33.8688°S, 151.2093°E). Not trusted from source file —
recalculated independently.

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
- `density_zone` assigned from ABS RA_2021 remoteness classification
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

Rate environments assigned: `ULTRA_LOW` (≤0.25%), `LOW` (≤1.50%),
`RISING` (≤3.00%), `HIGH` (≤4.35%).

---

### Stage 07 — RBA Enrichment JOIN

Joins `final_transactions` to `rba_cash_rate` on
`YEAR(Settlement_Date) = r.year AND QUARTER(Settlement_Date) = r.quarter`.

~183,000 rows with NULL Settlement_Date receive no rate assignment — expected and documented.
These rows are excluded by the analytical scope filter in Stage 08.

---

### Stage 08 — Analytical Scope Filter

Filters `final_transactions` to produce `analytical_transactions`:

- Settlement_Date within 2018–2025
- `suspect_price = FALSE`
- `tx_year` and `tx_month` added from Settlement_Date — replaces the unreliable `Year` column
- Result: **1,494,123 analytical records**

**Critical decision — `partial_interest` filter removed:**
The original pipeline included a filter excluding `%_Interest = 0` rows, assuming these
represented incomplete transfers. Stage 02 profiling revealed this is wrong — NSW Valuer
General encodes `0` as a **full transfer** (100% interest), not zero percent interest.
Only ~5,800 genuine non-zero partial interest records exist in the dataset.
The filter was removed entirely to avoid discarding the majority of legitimate transactions.

---

### Stage 08b — ML Residential View

`residential_transactions` VIEW applies three filters to `analytical_transactions`:

- `property_segment = 'RESIDENTIAL'`
- `geo_matched = TRUE` (99.74% pass rate)
- Purchase_Price between $50,000 and $10,000,000

**Why a VIEW rather than a table:** Analytical transactions are preserved intact for
descriptive analysis. The ML scope restriction is applied as a non-destructive view —
the full 1,494,123-row analytical dataset remains available for all Stage 10 visualisations.

Result: **1,259,466 rows** — the ML training dataset.

---

### Stage 09 — Outlier Analysis

Full distributional analysis of Purchase_Price, Area_sqm, and price_per_sqm.

**Purchase_Price — key statistics:**

| Metric | Value |
|--------|-------|
| Median | $782,000 |
| Mean | $1,051,126 |
| Mean — Median gap | $269,126 (34% inflation from prestige tail) |
| IQR upper fence | $2,407,500 |
| IQR lower fence | -$532,500 (zero genuine low outliers) |
| Rows above upper fence | 81,942 (real prestige sales — retained) |

**Area_sqm — key statistics:**

| Band | Transactions | Interpretation |
|------|-------------|----------------|
| < 200 sqm | 23.98% | Apartments and strata — Sydney density market |
| 400–800 sqm | 42.25% | Typical suburban house lot |
| > 1,525 sqm (IQR fence) | 4.9% | Large lots — retained, log transform applied |

**Outlier summary:**

| Category | Rows | Pct | Treatment |
|----------|------|-----|-----------|
| Clean on both dimensions | 1,136,498 | 90.24% | Primary ML training base |
| Price outliers only | 77,507 | 6.15% | 86% Metro — real prestige, retained |
| Area outliers only | 41,026 | 3.26% | 82% Regional — large lots, retained |
| Outliers on both | 4,435 | 0.35% | Prestige acreage — retained |

**Decision: No rows dropped.** Log transformation handles the distributional skew.
Dropping flagged rows would remove real market transactions — prestige sales and large
rural lots are genuine, not errors.

---

### Stage 10 — Analytical Views and Visualisations

Seven analytical views produced all dynamically calculated — no hardcoded statistics:

| View | Key Finding |
|------|------------|
| 10a Quarterly trend | 2025 Q4 $975,000 — new historical high above pre-hike peak |
| 10b Zone annual prices | Inner Regional rose during rate hike cycle — regional resilience |
| 10c Top LGAs by price | Woollahra $2,175,000 — Mosman $1,950,000 — Ku-ring-gai $1,800,000 |
| 10d Top LGAs by volume | Parramatta 79,475 (6.31%) — Ryde 62,263 — Blacktown 54,738 |
| 10e Rate paradox | Prices highest when rates highest — 18–24 month settlement lag |
| 10f Price per sqm gradient | Metro $3,414 vs Very Remote $216 — **15.8× ratio** |
| 10g YoY change | 2021 +13.48% COVID boom — 2022→2024 genuine cooling +1.2% only |

**2023 data note:** Only 2,861 transactions recorded under 2023 settlement dates
(vs ~190,000 in all other years). Cause: source files filed under 2024 filename during
manual merge. This is a data filing artifact — not a COVID event, not a market event.
Excluded from all trend narratives with documented caveat.

**Chart colour palette — consistent across all 10 charts:**

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

## Stage 11 Plan — ML Feature Table

Features confirmed for engineering:

| Feature | Source | Transform |
|---------|--------|-----------|
| `log_price` | Purchase_Price | LOG(Purchase_Price) — ML target variable |
| `log_area` | Area_sqm | LOG(Area_sqm) — where not NULL |
| `distance_cbd_km` | geo_reference_clean | As-is |
| `tx_year` | Settlement_Date | As-is |
| `tx_month` | Settlement_Date | As-is |
| `tx_quarter` | Settlement_Date | As-is (1–4) |
| `cash_rate_pct` | rba_cash_rate | As-is |
| `density_zone_encoded` | density_zone | Label encode: METRO=0, INNER_REGIONAL=1, OUTER_REGIONAL=2, REMOTE=3, VERY_REMOTE=4 |
| `property_type_clean` | clean_transactions | Label encode (R, V, 3) |
| `has_area` | clean_transactions | Boolean as integer |
| `price_per_sqm` | enriched_transactions | Where Area_sqm ≥ 50 only |
| `lga_median_price` | Derived | Rolling median per LGA per year |

**ML filter:** `residential_transactions` + `Area_sqm IS NOT NULL`
**Train/test split:** 80/20, stratified by `tx_year` and `density_zone`
**Target variable:** `log(Purchase_Price)` — back-transform predictions for reporting

---

## Confirmed Architectural Decisions — Do Not Revisit

These decisions were made with full evidence. Each has a documented rationale.
Revisiting them without new evidence would introduce inconsistency.

| # | Decision | Evidence Base |
|---|----------|--------------|
| 1 | Suburb standardisation abandoned — analysis at postcode/LGA level | 66,000+ locality variants — too noisy for reliable grouping |
| 2 | `geo_for_merge.csv` discarded — replaced with Matthew Proctor ABS-aligned file | Corrupt coordinates found: Gloucestershire England and Pennsylvania USA |
| 3 | `partial_interest` filter removed entirely | NSW VG convention: `%_Interest = 0` means full transfer, not zero percent |
| 4 | `Year` column abandoned — `tx_year` from Settlement_Date used throughout | `Year` = source file year, not transaction year — misleads trend analysis |
| 5 | 2023 excluded from trend analysis narratives | Filing artifact — 2,861 records vs ~190,000 normal year — not a market event |
| 6 | `Area_(ha)` renamed to `Area_sqm` — `×10,000` conversion removed | Values confirmed in square metres throughout — legacy column mislabelling |
| 7 | Non-residential excluded from ML training | Residential only — consistent valuation logic, 85% of analytical data |
| 8 | All chart annotations dynamically calculated | No hardcoded statistics — charts remain valid if data is updated or extended |
| 9 | Median used throughout all reporting — not mean | Mean inflated $269,126 above median by prestige tail — misleading for policy use |
| 10 | Log transformation confirmed for both Purchase_Price and Area_sqm | Heavy right skew on both — std dev ≈ mean on price confirms non-normality |

---

*Pipeline architecture reference — current as of Stages 00–10 complete.
Updated as Stages 11–13 are finalised.*
