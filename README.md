# NSW Property Market — SQL Data Pipeline
## Mehmood Ahmed | Senior Data Analyst Case Study

End-to-end data engineering pipeline across 1.7M NSW property transactions (2018–2025).
All wrangling, profiling, enrichment and feature engineering executed in **SQL via DuckDB**.
Python serves as a thin execution and display layer only — no Pandas data processing, no memory bottlenecks.

> **Companion repository (in preparation):** A Pandas-based exploratory analysis of the same dataset covering raw data profiling, manual error discovery, and geocoding decisions. Together the two repositories address a broader question: *when is a SQL-first pipeline preferable to a Pandas notebook workflow for large government datasets?*

---

## Table of Contents

- [Project Overview](#project-overview)
- [Why Two Phases — From Pandas to SQL](#why-two-phases--from-pandas-to-sql)
- [Dataset](#dataset)
- [Technology Stack](#technology-stack)
- [Pipeline Architecture](#pipeline-architecture)
- [Data Quality Findings](#data-quality-findings)
- [Data Maturity and Roadmap](#data-maturity-and-roadmap)
- [Key Analytical Findings](#key-analytical-findings)
- [Geographic Classification](#geographic-classification)
- [ML Decisions](#ml-decisions)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Presentation](#presentation)
- [Remaining Stages](#remaining-stages)

---

## Project Overview

This repository documents the complete SQL data pipeline built for a Senior Data Analyst case study targeting the **NSW Department of Customer Service**.

The project demonstrates:
- End-to-end data engineering on raw legacy government files
- SQL-first design that scales to 1.7M rows without memory constraints
- Geocoding, enrichment, and RBA cash rate integration
- Outlier analysis with defensible, documented decisions
- ML-ready feature table with log transformations and train/test split
- Government-relevant policy insights on housing affordability and regional disparity

The pipeline story is as important as the findings — every design decision is documented and justified.

---

## Why Two Phases — From Pandas to SQL

Phase 1 used Python/Pandas for initial data exploration and quality assessment.
At 1.7M rows with geocoding, outlier analysis, and feature engineering, **Pandas hit memory ceilings** that prevented ML-scale operations.

Phase 2 rebuilt the entire pipeline in **DuckDB SQL** — same analytical logic, enterprise-grade execution:

| Dimension | Pandas Phase 1 | SQL Phase 2 (this repo) |
|-----------|---------------|------------------------|
| Memory usage | Ceiling at ~1M enriched rows | Handles 1.7M rows efficiently |
| Auditability | Cell-by-cell notebook state | Immutable stage tables as audit trail |
| Error detection | Visual, exploratory | Systematic profiling queries |
| Reproducibility | Notebook state dependent | Pure SQL, fully reproducible |
| ML readiness | Memory constrained | Full feature table — 1.1M clean rows |

---

## Dataset

| File | Description | Rows |
|------|-------------|------|
| `Merged_All_data.csv` | NSW Valuer General property transactions 2018–2025 | 1,697,724 |
| `australian_postcodes.csv` | Matthew Proctor postcode reference — ABS 2021 geographic classifications | 5,272 |
| `nsw_property.db` | Persistent DuckDB database — all pipeline tables | — |

**Source:** NSW Valuer General bulk data download (publicly available).
The CSV files are too large to include in this repository.

> **Note:** The NSW Valuer General archive extends from the early 1990s — approximately 45 years of continuous property transaction records. This pipeline covers 2018–2025 as a deliberate scope decision capturing the most policy-relevant period including COVID-19, the RBA rate hike cycle, and the subsequent recovery. Extension to the full historical archive is architecturally straightforward.

For full details on data origin, period selection rationale, known limitations, and research potential — see **[`docs/data_provenance.md`](docs/data_provenance.md)**.

**Scale:**

| Metric | Value |
|--------|-------|
| Raw records ingested | 1,697,724 |
| Analytical records (2018–2025, in scope) | 1,494,123 |
| Residential records | 1,259,466 |
| ML training dataset (clean on both dimensions) | 1,136,498 |
| Geographic coverage | 99.74% |
| Distinct LGAs | 123 |
| Distinct postcodes | 621 |
| Density zones | 5 (ABS RA_2021) |
| RBA quarters covered | 32 (Q1 2018 – Q4 2025) |

---

## Technology Stack

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL-FFC832?logo=duckdb&logoColor=black)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualisation-11557C)

- **DuckDB** — all SQL wrangling, profiling, enrichment, and feature engineering
- **Python** — thin execution layer only (`con.execute()` + display)
- **Matplotlib / Seaborn** — 10 analytical visualisations
- **Jupyter Notebook** — development environment
- **ABS RA_2021** — official remoteness area classification for density zones
- **Haversine formula** — CBD distance calculation (Sydney CBD: -33.8688, 151.2093)

---

## Pipeline Architecture

```
Raw CSV Files
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 00  │  Session startup — connect & verify tables     │
│  Stage 01  │  Raw ingestion → staging_transactions          │
│  Stage 02  │  Column profiling & data quality audit         │
│  Stage 03  │  Clean table → clean_transactions              │
│  Stage 04  │  Geo reference build → geo_reference_clean     │
│  Stage 05  │  Geo enrichment JOIN → enriched_transactions   │
│  Stage 06  │  RBA cash rate table → rba_cash_rate           │
│  Stage 07  │  RBA enrichment JOIN → final_transactions      │
│  Stage 08  │  Analytical scope filter → analytical_transactions │
│  Stage 08b │  ML residential VIEW → residential_transactions │
│  Stage 09  │  Outlier analysis — documented findings        │
│  Stage 10  │  Analytical views — LGA medians, trends        │
│  Stage 11* │  ML feature table — train/test split           │
│  Stage 12* │  Model training — ExtraTrees, XGBoost, LightGBM│
│  Stage 13* │  Time series forecasting — ARIMA / Prophet     │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
 Policy insights + ML predictions + 2026 forecast
```
*Stages 11–13 in progress — results will be updated fortnightly.*

**Database tables — current state:**

| Table | Rows | Status |
|-------|------|--------|
| `staging_transactions` | 1,697,724 | Frozen — raw audit trail |
| `geo_raw` | 5,272 | Frozen |
| `geo_reference_clean` | 617 | Frozen |
| `rba_cash_rate` | 32 | Frozen |
| `clean_transactions` | 1,697,724 | Read only |
| `enriched_transactions` | 1,697,724 | Read only |
| `final_transactions` | 1,697,724 | Read only |
| `analytical_transactions` | 1,494,123 | Read only |
| `residential_transactions` (VIEW) | 1,259,466 | Read only |

---

## Data Quality Findings

10 data quality issues discovered and resolved during Stages 02–05:

| # | Finding | Resolution |
|---|---------|-----------|
| 1 | `Year` column = file year, not transaction year | Replaced with `tx_year` from `Settlement_Date` |
| 2 | Postcode stored as float (`2112.0`) | `CAST(TRY_CAST(Postcode AS INTEGER) AS VARCHAR)` |
| 3 | `Nature_of_Property` code `3.0` vs `3` — same code | Consolidated to `3` in `clean_transactions` |
| 4 | 2023 data gap — transactions filed under 2024 filename | Excluded from trend narratives with documented caveat |
| 5 | Pre-2018 historical records (~600 rows) | Excluded via date scope filter |
| 6 | `%_Interest = 0` means full transfer — NSW VG encoding convention | `partial_interest` filter removed entirely |
| 7 | 4 columns dropped: `Sale_Code` 94% null, `Strata_Lot_Number` 63% null, `Component_Code` 41% null, `column00` index | Documented and removed in Stage 03 |
| 8 | `Primary_Purpose` typo variants (`COMMERICAL`, `FARM LAND` vs `FARMLAND`) | Noted — ML uses `property_segment` instead |
| 9 | `Area_(ha)` column misnamed — values confirmed in square metres | Renamed to `Area_sqm` throughout; `× 10000` conversion removed |
| 10 | `Area_sqm < 50` produces absurd `price_per_sqm` | `price_per_sqm` set NULL for `Area_sqm < 50`; purchase prices retained |

---

## Data Maturity and Roadmap

This pipeline operates on a dataset with well-understood scope and honest boundaries.
The 10 data quality findings above represent issues that were **quantifiable and resolvable in SQL**.
A second category — text-level inconsistencies in commercial and rural classification fields —
requires fuzzy text comparison and domain expertise, and forms the basis of the Phase 2 Pandas notebook.

This distinction matters for users:

- **Residential price trend and geographic analysis** — robust and production-ready
- **Commercial and rural land use segmentation** — directional until Phase 2 text audit completes
- **Historical extension pre-2018** — architecturally ready, normalisation work required

The absence of property micro-characteristics (dwelling type, bedroom count, amenity proximity)
means current ML models predict at zone and LGA level rather than individual property level.
Phase 3 hedonic enrichment addresses this directly.

> For the complete analytical boundaries, research potential, and development roadmap
> see **[`docs/data_provenance.md`](docs/data_provenance.md)** — recommended reading for
> anyone intending to extend or build on this pipeline.

---

## Key Analytical Findings

All values dynamically calculated — no hardcoded statistics in any chart or query.

| Finding | Statistic |
|---------|-----------|
| NSW residential median price 2018–2025 | **$782,000** |
| New 2025 historical high | **$975,000** (Q4 2025 — above pre-hike peak) |
| COVID boom | **+13.48% in 2021** — largest single-year surge in the dataset |
| Rate hike correction | Only **-6.3% from peak** — modest despite 4.25% rate rise |
| Regional resilience | Inner Regional prices **rose** during the rate hike cycle |
| Outer Regional growth | **+70.8% 2018–2025** — fastest growing density zone |
| Distance gradient | Metro $3,414/sqm vs Very Remote $216/sqm = **15.8× ratio** |
| Settlement lag | Prices highest at peak rates — **18–24 month lag** between hike and correction |
| Market concentration | **Top 4 LGAs = 19.9%** of all NSW residential transactions |
| Top LGA by price | Woollahra median **$2,175,000** |
| Top LGA by volume | Parramatta **79,475 transactions** (6.31% of total) |

---

## Geographic Classification

Density zones use the official **ABS Remoteness Area 2021 (RA_2021)** classification.
Distance to CBD independently calculated using the **Haversine formula** — Sydney CBD (-33.8688, 151.2093).

| Zone | ABS Classification | Median Price | Avg CBD Distance |
|------|--------------------|-------------|-----------------|
| METRO | Major Cities of Australia | $890,000 | 31 km |
| INNER_REGIONAL | Inner Regional Australia | $685,000 | 186 km |
| OUTER_REGIONAL | Outer Regional Australia | $435,000 | 316 km |
| REMOTE | Remote Australia | $250,000 | 539 km |
| VERY_REMOTE | Very Remote Australia | $155,000 | 634 km |

---

## ML Decisions

Confirmed decisions from Stage 09 outlier analysis — not revisited:

| Decision | Evidence |
|----------|---------|
| **Log transform `Purchase_Price`** | Pearson skew ≈ 0.288 — heavy right tail; std dev ≈ mean |
| **Log transform `Area_sqm`** | Right skew confirmed — large rural lots pull distribution |
| **All reporting uses MEDIAN** | Mean inflated $269k above median by prestige tail |
| **No rows dropped** | Log transform handles outliers — all 122,968 flagged rows are real transactions |
| **ML clean base: 1,136,498 rows** | 90.24% clean on both IQR fences |
| **`price_per_sqm` NULL for `Area_sqm < 50`** | Sub-10 sqm median $412,371/sqm confirmed as strata components, not genuine |
| **Models: ExtraTrees, XGBoost, LightGBM** | Previous work: ExtraTrees MAE ≈ $234k, RMSE ≈ $473k, R² ≈ 0.79 |

---

## Repository Structure

```
nsw-property-sql-pipeline/
│
├── README.md                          ← This file
│
├── notebooks/
│   └── 01_NSW_Property_SQL_Pipeline.ipynb   ← Main pipeline (Stages 00–13)
│
├── visuals/
│   ├── chart09_1_price_distribution.png
│   ├── chart09_2_area_distribution.png
│   ├── chart09_3_outlier_by_zone.png
│   ├── chart10_1_quarterly_price_rba.png
│   ├── chart10_2_zone_price_trend.png
│   ├── chart10_3_lga_top_price.png
│   ├── chart10_4_ppsqm_by_zone.png
│   ├── chart10_5_price_band_distribution.png
│   ├── chart10_6_yoy_price_change.png
│   └── chart10_7_volume_by_zone.png
│
├── presentation/
│   └── NSW_Property_Market_Case_Study.html  ← Full 16-page case study
│
└── docs/
    ├── data_provenance.md             ← Data origin, limitations and research potential
    └── pipeline_architecture.md       ← Stage decisions, DB schema, ML feature plan
```

---

## Getting Started

**Requirements:**
```
python >= 3.10
duckdb
pandas
matplotlib
seaborn
jupyter
```

**Install:**
```bash
pip install duckdb pandas matplotlib seaborn jupyter
```

**Run:**
1. Download source data files — see `data/README.md`
2. Place `Merged_All_data.csv` and `australian_postcodes.csv` in the same folder as the notebook
3. Open `notebooks/01_NSW_Property_SQL_Pipeline.ipynb`
4. Run **Stage 00** first — confirms all tables and source files are reachable
5. If all tables show `OK` — skip to any stage directly

> **Note:** Update `DB_PATH`, `CSV_MAIN`, and `CSV_GEO` at the top of Stage 00 to match your local directory.

---

## Presentation

A full 16-page HTML case study is included in `presentation/NSW_Property_Market_Case_Study.html`.

**To view:** Open in Chrome or Edge for best font rendering.

**To export PDF:** `File → Print → Save as PDF` — A4 paper, no margins, enable Background graphics.

The presentation covers: Executive Summary, Data Challenge, Methodology, 4 Key Findings, Predictive Modelling, Policy Implications, and Appendix.

---

## Remaining Stages

| Stage | Description | Status |
|-------|-------------|--------|
| **11** | ML feature table — log transforms, 12 features, train/test split | In progress |
| **12** | Model training — ExtraTrees, XGBoost, LightGBM | Pending Stage 11 |
| **13** | Time series forecasting — ARIMA / Prophet at LGA and zone level | Pending Stage 12 |

*README updated fortnightly as stages are completed.*

---

## Author

**Mehmood Ahmed** — Senior Data Analyst
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

Case study for NSW Department of Customer Service application.

---

*Data source: NSW Valuer General — bulk property sales data (publicly available).
Geographic classifications: ABS Remoteness Area 2021 via Matthew Proctor Australian Postcodes.*
