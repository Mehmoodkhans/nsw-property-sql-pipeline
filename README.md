# NSW Property Market — End-to-End Data Pipeline

**Mehmood Ahmed Khan** | Data Scientist & Analytics Engineer

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.5.1-FFC832?logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)](https://jupyter.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial-139C5A)](https://geopandas.org/)

An end-to-end data pipeline across **2 million+ NSW property transactions** — from raw legacy government archives to ML-ready analytical tables, geographic enrichment, and predictive modelling. Built in two complementary layers: a **Python extraction and cleaning engine** that handles the format complexity and audit trail, and a **SQL analytical layer in DuckDB** that scales wrangling, enrichment, and feature engineering without memory constraints.

> The pipeline story is as important as the findings. Every design decision is documented, every anomaly is traced to its source, and every assumption is tested against the raw files.

---

## Pipeline Architecture

```
NSW Valuer General
Weekly .DAT Archives
(10 yearly zips → 520 weekly extracts → 66,747 district files)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1 — EXTRACTION & CLEANING  (Python · NSW_Master.ipynb)  │
│                                                                 │
│  01  Parse nested zips → 2,186,102 B-record lines              │
│  02  Validate: lines-in = rows-out; no silent failures          │
│  03  Deduplicate re-published sales → 2,032,518 unique records  │
│  04  Dates from raw files; area units read from Area_Type field │
│  05  Classification standardised; 0 imputed values             │
│  06  Geography matched per place (99.93% exact match)          │
│  07  Two outputs: clean (76 cols) · analysis (34 cols)         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2 — SQL ANALYTICAL PIPELINE  (DuckDB · 01.NSW_...)      │
│                                                                 │
│  00  Session startup — connect & verify tables                  │
│  01  Raw ingestion → staging_transactions (1,697,724)          │
│  02  Column profiling & data quality audit (10 findings)       │
│  03  Clean table → clean_transactions                          │
│  04  Geo reference build → geo_reference_clean                 │
│  05  Geo enrichment JOIN → enriched_transactions               │
│  06  RBA cash rate table → rba_cash_rate (32 quarters)         │
│  07  RBA enrichment JOIN → final_transactions                  │
│  08  Analytical scope filter → analytical_transactions         │
│  08b ML residential VIEW → residential_transactions            │
│  09  Outlier analysis — IQR fences, log transform confirmed    │
│  10  7 analytical views + 23 visualisations                    │
│  11  ML feature table — 12 features, train/test split          │
│  12  Model training — ExtraTrees, XGBoost, LightGBM, Ridge    │
│  13  Prophet forecasting — 2026 by density zone & LGA          │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
  Policy insights · ML predictions · 2026 market forecast
```

---

## Stage 1 — Extraction and Cleaning

### The source format

NSW Valuer General publishes weekly property sale extracts as `.DAT` files inside nested zip archives — one yearly zip containing one zip per week, each containing district files. A sale (B) line has exactly 24 semicolon-separated fields across four record types (header, sale, legal description, party flags). There is no schema documentation.

```
YYYY.zip
 └─ YYYYMMDD.zip              weekly extract
     ├─ creative_commons.txt
     └─ NNN_SALES_DATA_NNME_DDMMYYYY.DAT
          A;...  file header
          B;...  SALE record   ← 23 fields extracted
          C;...  legal description
          D;...  party flags
```

**Coverage:** 10 yearly archives · 520 weekly extracts · 66,747 district files · 04 Jan 2016 – 29 Dec 2025

### Engineering decisions

The extraction layer follows four non-negotiable rules:

1. **No imputation.** A missing value stays missing and is flagged with a reason column.
2. **No step can multiply rows.** Every stage logs rows before and after; an automated check fails if any step increases the count.
3. **Flag, don't filter.** Price problems, area problems, and the incomplete tail are flagged — filtering belongs to the analysis layer.
4. **Every rule logs how many rows it touched.**

### What was found

**Re-published sales.** 153,584 sale lines (7.0%) appear again in later extracts with the same identity. The latest copy is kept; 424 rows that differ in price or settlement date are flagged as possible revisions, not removed.

**Area units are mixed.** Each area value carries an `Area_Type` field (`M` = square metres, `H` = hectares). 139,687 rows (6.9%) are recorded in hectares, concentrated in rural and commercial zoning. `Area_sqm` is derived correctly from `Area_Type`; no conversion assumption is applied.

| Zoning group | Rows in hectares |
|---|---|
| Rural (RU) | 58.6% |
| Commercial (C) | 19.3% |
| Environmental (E) | 17.9% |
| Residential (R) | 2.2% |

**Dates from the raw files.** Settlement dates are present for 100% of rows in every source year. 1,130 rows carry a date anomaly (missing contract date, settlement before contract, date before 1990, or >10-year gap) — all flagged, none removed.

**Strata lots.** 34.2% of rows are strata lots. They structurally carry no zoning and mostly no area — by construction, not by data loss. Zoning and `Component_Code` are missing in exactly the same rows, so one cannot be filled from the other.

**Geography matched per place.** The sales hold only a few thousand distinct (locality, postcode) pairs. Each is matched once against the postcode reference and the result is copied back by position, so rows cannot multiply. 99.93% matched exactly; 5,483 matched through a reviewed entry for Edmondson Park; 58 remain unmatched.

> **Postcode-level label risk.** Every area label in the postcode reference (LGA, remoteness, SA2–SA4) is identical for all localities within a postcode. Where a postcode spans several council areas the label can be wrong for a specific locality. Affected columns are named `..._PostcodeLevel` and carry an `Area_Label_Risk` flag.

### Output tables

| Table | Columns | Purpose |
|---|---|---|
| `clean` | 76 | Full audit table — every field, all lineage, every flag |
| `analysis` | 34 | One column per idea — for exploration and modelling |

**Scale after Stage 1:**

| Metric | Value |
|---|---|
| Raw B-lines extracted | 2,186,102 |
| After deduplication | 2,032,518 |
| Imputed values | **0** |
| Geography match rate | 99.93% |
| Rows with date anomaly | 1,130 (0.06%) — flagged |
| Rows with area in hectares | 139,687 (6.9%) — correctly converted |

---

## Stage 2 — SQL Analytical Pipeline

### Why SQL (DuckDB)

At 1.7M+ enriched rows with geocoding, RBA join, outlier analysis, and feature engineering, Pandas hit memory ceilings. DuckDB runs the full pipeline as immutable SQL stage tables — no memory constraints, full audit trail, and every transformation reproducible from a single `con.execute()` call.

| Dimension | Pandas | DuckDB SQL |
|---|---|---|
| Memory | Ceiling at ~1M enriched rows | Handles 1.7M+ rows efficiently |
| Auditability | Notebook cell state | Immutable stage tables |
| Error detection | Visual, exploratory | Systematic profiling queries |
| Reproducibility | Notebook-state dependent | Pure SQL, fully reproducible |
| ML readiness | Memory constrained | Full feature table — 1.1M+ clean rows |

### Database tables

| Table | Rows | Status |
|---|---|---|
| `staging_transactions` | 1,697,724 | Frozen — raw audit trail |
| `geo_reference_clean` | 617 | Frozen |
| `rba_cash_rate` | 32 quarters | Frozen |
| `clean_transactions` | 1,697,724 | Read only |
| `enriched_transactions` | 1,697,724 | Read only |
| `final_transactions` | 1,697,724 | Read only |
| `analytical_transactions` | 1,494,123 | Read only |
| `residential_transactions` (VIEW) | 1,259,466 | Read only |

### Data quality findings (Stage 2 profiling — 10 documented)

| # | Finding | Resolution |
|---|---|---|
| 1 | `Year` column = file year, not transaction year | Replaced with `tx_year` from `Settlement_Date` |
| 2 | Postcode stored as float (`2112.0`) | `CAST(TRY_CAST(Postcode AS INTEGER) AS VARCHAR)` |
| 3 | `Nature_of_Property` code `3.0` vs `3` — same code | Consolidated to `3` |
| 4 | 2023 data gap — transactions filed under 2024 filename | Excluded from trend narratives with documented caveat |
| 5 | Pre-2018 historical records (~600 rows) | Excluded via date scope filter |
| 6 | `%_Interest = 0` means full transfer — VG encoding convention | `partial_interest` filter removed entirely |
| 7 | 4 columns dropped: `Sale_Code` 94% null, `Strata_Lot_Number` 63% null, `Component_Code` 41% null, `column00` index | Documented and removed |
| 8 | `Primary_Purpose` typo variants (`COMMERICAL`, `FARMLAND` vs `FARM LAND`) | Noted — ML uses `property_segment` |
| 9 | `Area_(ha)` column misnamed — values confirmed in square metres | Renamed to `Area_sqm`; `×10,000` conversion removed |
| 10 | `Area_sqm < 50` produces absurd `price_per_sqm` | `price_per_sqm` set NULL for `Area_sqm < 50`; purchase prices retained |

### Key analytical findings

All values dynamically calculated — no hardcoded statistics in any chart or query.

| Finding | Statistic |
|---|---|
| NSW residential median price 2018–2025 | **$782,000** |
| New 2025 historical high | **$975,000** Q4 2025 — above pre-hike peak |
| COVID boom | **+13.48% in 2021** — largest single-year surge |
| Rate hike correction | Only **–6.3% from peak** despite 4.25% rate rise |
| Outer Regional growth | **+70.8% 2018–2025** — fastest growing density zone |
| Inner Regional resilience | Prices rose during the rate hike cycle |
| Distance gradient | Metro $3,414/sqm vs Very Remote $216/sqm = **15.8× ratio** |
| Settlement lag | Prices highest at peak rates — 18–24 month lag between hike and correction |
| Market concentration | **Top 4 LGAs = 19.9%** of all NSW residential transactions |
| Top LGA by price | Northern Beaches median **$2,682,000** |
| Top LGA by volume | Parramatta **79,475 transactions** |

### Geographic classification

Density zones use the official **ABS Remoteness Area 2021 (RA_2021)** classification. CBD distance independently calculated using the **Haversine formula** (Sydney CBD: –33.8688°, 151.2093°).

| Zone | Median Price | Avg CBD Distance | $/sqm |
|---|---|---|---|
| Metro | $890,000 | 31 km | $3,414 |
| Inner Regional | $685,000 | 186 km | $890 |
| Outer Regional | $435,000 | 316 km | $504 |
| Remote | $250,000 | 539 km | $312 |
| Very Remote | $175,000 | 634 km | $216 |

### ML decisions (from Stage 09 outlier analysis — not revisited)

| Decision | Evidence |
|---|---|
| Log transform `Purchase_Price` | Pearson skew ≈ 0.288 — heavy right tail |
| Log transform `Area_sqm` | Right skew confirmed — large rural lots pull distribution |
| All reporting uses **median** | Mean inflated $269k above median by prestige tail |
| No rows dropped | Log transform handles outliers; 122,968 flagged rows are real transactions |
| Models: ExtraTrees, XGBoost, LightGBM, Ridge | Ridge kept for coefficient interpretability |

### Model results (Stage 12 — held-out test split, 185,160 records)

| Model | R² | MAE | Notes |
|---|---|---|---|
| ExtraTrees | **0.714** | **$279k** | Best overall |
| LightGBM | 0.711 | — | Close second |
| XGBoost | 0.702 | — | |
| Ridge | 0.477 | — | Kept for interpretation |

**Feature importance (ExtraTrees):**

| Feature | Importance |
|---|---|
| LGA-year median price | 35.6% |
| Distance to CBD | 21.1% |
| Area (sqm) | 18.7% |
| Density zone | 16.9% |

---

## Visualisations

23 charts across all stages — all produced from live query results, no hardcoded values.

| Group | Charts |
|---|---|
| Stage 09 — Outlier analysis | Price distribution · Area distribution · Outlier flags by zone |
| Stage 10 — Market trends | Quarterly price + RBA overlay · Zone price trends · Top LGA prices · Price/sqm by zone · Price band distribution · YoY change · Volume by zone |
| Stage 10c — Technical | CBD distance vs price (scatter + trend) · Log transform justification · Rate environment boxplot |
| Stage 10d — Geographic | NSW density zone map · Sydney zone zoom · NSW median price choropleth · Sydney median price zoom |
| Stage 12–13 — Model | Actual vs predicted · Feature importance · Ridge coefficients · Zone forecasts · LGA forecasts |

---

## Repository Structure

```
nsw-property-sql-pipeline/
│
├── README.md
│
├── notebooks/
│   ├── NSW_Master.ipynb                       Stage 1: extraction & cleaning
│   └── 01.NSW_Property_SQL_Pipeline.ipynb     Stage 2: SQL pipeline (Stages 00–13)
│
├── Visual/                                    All 23 charts (PNG)
│
├── presentation/
│   └── NSW_Property_Market_Case_Study.html    16-page interactive case study
│
└── docs/
    ├── data_provenance.md
    └── pipeline_architecture.md
```

---

## Getting Started

**Requirements:**
```
python >= 3.10
duckdb pandas numpy matplotlib seaborn geopandas jupyter
```

**Install:**
```bash
pip install duckdb pandas numpy matplotlib seaborn geopandas jupyter
```

**Stage 1 — Extraction:**
1. Download yearly zips from NSW Valuer General and `australian_postcodes.csv`
2. Set `NSW_EXTRACTION_DIR` in the configuration cell of `NSW_Master.ipynb`
3. Run top to bottom — nothing is written to disk unless `SAVE_CHECKPOINT = True`

**Stage 2 — SQL pipeline:**
1. Place `Merged_All_data.csv` and `australian_postcodes.csv` alongside the notebook
2. Open `notebooks/01.NSW_Property_SQL_Pipeline.ipynb`
3. Run **Stage 00** first — confirms all tables and source files are reachable
4. If all tables show `OK` — skip to any stage directly

> Update `DB_PATH`, `CSV_MAIN`, and `CSV_GEO` at the top of Stage 00 to match your local directory.

---

## Data Sources

| Source | Description | Link |
|---|---|---|
| NSW Valuer General | Weekly `.DAT` property sale extracts, published under Creative Commons | [valuation.property.nsw.gov.au](https://valuation.property.nsw.gov.au/embed/propertySalesInformation) |
| Australian Postcodes (Matthew Proctor) | Postcode reference with coordinates, LGA, SA4 and remoteness labels | [matthewproctor.com/australian_postcodes](https://matthewproctor.com/australian_postcodes) |
| RBA Cash Rate | Official cash rate history — quarterly targets 2018–2025 | [rba.gov.au](https://www.rba.gov.au/statistics/cash-rate/) |
| ABS ASGS Edition 3 | Remoteness Area 2021 (RA_2021) official boundary files | [abs.gov.au](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3) |

*Sales data used under Creative Commons licence — attribute NSW Valuer General when reusing.*

---

## Author

**Mehmood Ahmed Khan** — Data Scientist & Analytics Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)
[![GitHub](https://img.shields.io/badge/GitHub-Mehmoodkhans-181717?logo=github&logoColor=white)](https://github.com/Mehmoodkhans)

*Case study for NSW Department of Customer Service application.*
