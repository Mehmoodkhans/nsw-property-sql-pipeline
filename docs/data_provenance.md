# Data Provenance, Scope and Research Potential
## NSW Property Market — End-to-End Data Pipeline
**Mehmood Ahmed Khan** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

---

## Overview

This document describes the origin, scope, known limitations, and research potential of the dataset
underlying the NSW Property Market pipeline. It is intended for researchers, government analysts,
and industry practitioners who wish to understand not just what this pipeline produces — but what
the data can and cannot tell you, and where serious analytical opportunity remains.

---

## 1. Dataset Origin

### Primary Source — NSW Valuer General Bulk Data

The transaction data originates from the **NSW Valuer General** — the government authority
responsible for property valuations and the official registry of property sales across New South Wales.

The data is published weekly as `.DAT` files inside nested zip archives — one zip per year containing
one zip per weekly extract, each containing district-level files. A sale record has exactly 24
semicolon-separated fields across four record types (header, sale, legal description, party flags).
Stage 1 of this pipeline extracts and parses these archives directly from the raw files.

The archive covers property sales registered in NSW — residential, commercial, rural, and industrial
transactions — from 1990 onwards, about 36 years. Each record carries the contract and settlement dates,
purchase price, property type, land area, and geographic identifiers down to street name and postcode level.

**Archive scale accessed in this pipeline:**
10 yearly archives · 520 weekly extracts · 66,747 district files · 04 Jan 2016 – 29 Dec 2025

This pipeline's analytical layer covers **2018–2025** — a deliberate scope decision explained
in Section 2. Extension to the full historical archive is architecturally straightforward and
represents a natural next phase for any researcher or organisation requiring long-run market analysis.

### Secondary Source — Australian Postcodes Reference

Geographic enrichment uses the **Matthew Proctor Australian Postcodes** reference file — an
ABS 2021-aligned postcode dataset providing:

- ABS Remoteness Area 2021 (RA_2021) classifications
- SA4 region names
- Precise latitude and longitude coordinates

Coordinates were validated before use. Three problems were found in the source file itself and are handled
explicitly:

- Two localities (Birdlip and Kempton) carry impossible coordinates, in England and in the USA. An earlier
  hand-edited extract of the file (`geo_for_merge.csv`) inherited them. Stage 2 excludes rows outside valid
  coordinate bounds at load; Stage 1 repairs coordinates from the file's own basic latitude and longitude.
- Fifteen localities store missing precise coordinates as 0,0; these are repaired the same way.
- A review of places far from the rest of their own postcode lists about ten further suspect coordinates
  (same-name places elsewhere), pending confirmation.

Distances were checked against known NSW distances before use.

### Tertiary Source — RBA Cash Rate Records

Monetary policy context is provided by **Reserve Bank of Australia** official cash rate records
covering 32 quarters (Q1 2018 – Q4 2025). This enables direct correlation analysis between
interest rate cycles and property price movements at zone and LGA level.

---

## 2. Period Selection — Why 2018–2025

> **Note.** Figures quoted in this section and in Section 5 (+13.48%, –6.3%, 15.8×, regional resilience)
> were computed in Stage 2 on the earlier extraction. They are being re-verified on the Stage 1 foundation.

The 2018–2025 analytical window was not chosen arbitrarily. It was selected as the most
**policy-relevant and analytically rich** period available in the archive for the following reasons:

**Pre-COVID baseline (2018–2019)**
A stable two-year reference period with moderate price growth and a well-understood interest
rate environment. Essential as the foundation for measuring subsequent disruption.

**COVID-19 demand surge (2020–2021)**
The most significant external shock to the NSW property market in decades. A +13.48% median
price surge in 2021 alone (as computed in Stage 2) — the largest single-year movement in that analysis —
coinciding with historically low interest rates, government stimulus, and a shift in housing
preferences during lockdown periods. This dataset cannot attribute the cause.

**RBA rate hike cycle (2022–2023)**
The most aggressive monetary policy tightening in a generation — 4.25 percentage points across
13 increases (with pauses in April and from July to October 2023). This pipeline captures the full transmission of that cycle into property
prices, with the counterintuitive finding that the correction was far more modest than the rate
movement suggested — only –6.3% from peak in the Stage 2 analysis, despite the severity of the tightening (this figure spans
the 2023 data gap and is to be re-verified).

**Post-hike recovery (2024–2025)**
Prices recovering toward and exceeding pre-hike peaks by Q4 2025, consistent with continued
demand in the NSW market.

**In summary:** This eight-year window contains several distinct market regimes — a stable baseline, a
pandemic-era surge, the fastest rate tightening in a generation, and a recovery. It is a strong period for
understanding how the NSW property market behaves under stress, which is what policy analysts, urban
planners, and investors need to understand.

---

## 3. What the Pipeline Resolves

Counts and shares for every item below are maintained in the project README (Stage 1 findings), so that
each number lives in one place.

**Stage 1** resolves format-level challenges inherent in the raw source:

- Sales re-published in later extracts are de-duplicated — the latest copy is retained and possible revisions are flagged
- Mixed area units (hectares and square metres) — the `Area_Type` field is read and `Area_sqm` is derived correctly
- Settlement dates are read from the raw files, so no source year loses its dates
- Geography is matched per unique (locality, postcode) place, with each match labelled by method and quality
- Zero imputed values — every gap is flagged with a documented reason

**Stage 2** resolves analytical-layer challenges discovered during SQL profiling:

Ten quantifiable data quality issues were documented and resolved during Stages 02–05.
Full documentation is in [`pipeline_architecture.md`](pipeline_architecture.md).

These cover: float-promoted postcodes, government encoding conventions misread as data errors, null-heavy
columns removed with documented justification, date-based scope filtering replacing the source-file year,
and property type code normalisation. The raw `staging_transactions` table is preserved frozen — no finding
was applied destructively.

**Two Stage 2 conclusions were later revised by Stage 1:**

- The area column was assumed to hold square metres throughout. Stage 1 found that a share of rows are in hectares.
- The 2023 gap was attributed to a filing artifact. Stage 1 found that the dates had been lost in the earlier
  extraction; the raw files contain them.

Stage 2 is kept as published, on the earlier extraction; a new analysis layer will be built on the Stage 1 tables.

---

## 4. Known Limitations — An Honest Assessment

The following limitations are stated not as apologies but as **analytical boundaries** — the honest
perimeter of what this dataset can and cannot tell you. Understanding these boundaries is as important
as understanding the findings themselves.

---

### 4.1 No On-the-Ground Market Knowledge

This analysis was conducted without on-the-ground familiarity with individual Sydney suburbs, local amenity
quality, or the market intuition a Sydney-based agent or developer carries.

Rather than assume which features matter, the models test it from the transaction records, ABS
classifications, and RBA data. This is a deliberate choice, and it has a limit: suburb-level findings have
not been checked against local market knowledge. They should be reviewed by someone who knows the area
before being used for decisions.

---

### 4.2 Government Policy and Fiscal Intervention Gaps

This pipeline captures **monetary policy** through the RBA cash rate integration.
What it does not capture:

- State government stamp duty reforms and exemptions
- Federal and state first home buyer grant schemes and their withdrawal
- Foreign investment restriction policy changes
- Social housing supply announcements and delivery
- Infrastructure investment decisions (metro extensions, motorway corridors)
- Zoning and density policy changes at LGA level
- COVID-era border closure effects on interstate migration demand

These are real and significant drivers of NSW property price movements that operate independently of —
and sometimes in opposition to — interest rate cycles. The 2021–2022 price surge, for example,
reflects not just record-low interest rates but the simultaneous effect of government stimulus,
HomeBuilder grants, and pandemic-driven demand shifts that the RBA data alone cannot explain.

**What this means for users:** Price movements in this dataset should be interpreted as the net
outcome of multiple policy forces, not attributed solely to the monetary policy variables captured.

**What this opens up:** Integration of NSW government policy event data as categorical timeline
variables would substantially improve the explanatory power of the ML models and is identified
as a Phase 4 enrichment opportunity.

---

### 4.3 Absence of Property Micro-Characteristics

Transaction records contain property type codes, land area, and geographic identifiers.
They do not contain:

- Dwelling type at granular level (house, apartment, townhouse, studio)
- Number of bedrooms, bathrooms, or car spaces
- Construction year, renovation status, or building quality
- Proximity to transport infrastructure (train stations, bus routes)
- Proximity to educational institutions (school catchment zones)
- Access to commercial amenity (shopping centres, medical, hospitality)
- Proximity to natural amenity (parks, coastline, river frontage)
- Heritage overlay or planning restriction status

**What this means for current analysis:** Price per square metre calculations and median price
comparisons reflect zone-level and LGA-level patterns — macro geography rather than micro property
characteristics. Two properties in the same postcode with vastly different attributes are treated
identically in this dataset.

**What this opens up:** Integration with Domain or CoreLogic property attribute data, OpenStreetMap
amenity layers, NSW Department of Education school catchment boundaries, and Transport for NSW GTFS
public transport accessibility data would unlock true **hedonic price modelling** — isolating the
independent contribution of each attribute to property value. This is Phase 4 of this project and
represents the most direct path to a commercially deployable valuation tool.

---

### 4.4 Postcode-Level Area Label Risk

Every area label in the Matthew Proctor postcode reference (LGA, region, remoteness, SA2–SA4) is identical
for all localities within a postcode. Where a postcode spans several council areas the label can be wrong
for a specific locality (example: the town of Cessnock is labelled "Central Coast (NSW)" in the reference).

36% of NSW postcodes span more than 20 km, and roughly 28% of sales fall in postcodes flagged as
high-risk. In Stage 1 the affected columns are named `..._PostcodeLevel` and carry an `Area_Label_Risk` flag.

**Stage 2 is affected too.** Its density zones, the LGA rankings (stages 10c and 10d), and the LGA-year
median price feature in the model all rest on postcode-level labels, so they carry the same limitation.

An optional boundary-based LGA step (official ABS boundary files via GeoPandas) replaces postcode-level
labels with spatially exact assignments. It is implemented in Stage 1 and has so far been tested only with a
synthetic boundary file.

---

### 4.5 Pre-2016 Historical Extension — Considerations

For users interested in extending this pipeline to the full archive (about 36 years, from 1990), the following additional
challenges apply:

- **Field definition evolution** — column names, property type codes, and area measurement conventions
  changed across decades of the archive. Normalisation requires decade-by-decade schema mapping.
- **Geographic boundary changes** — LGA boundaries, postcode assignments, and ABS geographic
  classifications have changed multiple times since the 1990s. Longitudinal geographic analysis
  requires boundary-consistent reclassification.
- **Structural market breaks** — the GST introduction (2000), the Global Financial Crisis (2008–2009),
  and multiple state government policy regimes represent structural breaks that affect comparability
  across the full archive period.
- **Data completeness** — earlier cohorts may have higher rates of missing fields; this has not yet been examined.

None of these are insurmountable. They are enumerated here so that any extension effort begins with
clear eyes about the normalisation work required.

---

## 5. Research and Commercial Potential

The NSW Valuer General archive — properly extracted, cleaned, enriched, and extended — represents
a comprehensive longitudinal property transaction dataset.

The foundation built in this pipeline enables research and analysis across several dimensions of
significant public, academic, and commercial interest:

**Housing affordability over economic cycles**
About 36 years of transaction data spanning multiple interest rate cycles, government policy regimes, and
macroeconomic shocks. Long-run affordability analysis that contextualises current conditions within
a generational perspective — essential for credible housing policy design.

**Geographic transmission of monetary policy**
How do RBA rate decisions propagate differently across Metro, Inner Regional, Outer Regional, and
Remote markets? Stage 2 already shows a counterintuitive finding — Inner Regional prices rose
during the rate hike cycle (earlier data; to be re-verified). A 36-year panel would establish whether this regional resilience is
structural or cyclical.

**Urban-regional price divergence**
The Stage 2 figure of 15.8× for price per square metre between Metro and Very Remote zones is striking, but it
was computed on the earlier data and is affected by the area-unit issue; it is being re-verified.
A longitudinal view would reveal whether this divergence is widening, stable, or subject to mean
reversion — a question with direct implications for regional development policy.

**Infrastructure value uplift**
Combining transaction data with infrastructure announcement and delivery timelines — metro
extensions, motorway corridors, hospital developments — would isolate the measurable property value
uplift attributable to specific public investments. A powerful tool for infrastructure cost-benefit
analysis.

**Hedonic valuation modelling**
With Phase 4 micro-characteristic enrichment, this pipeline becomes the foundation for a
suburb-level automated valuation model (AVM) — the same class of tool used by major banks, REITs,
and property analytics platforms for mortgage underwriting and portfolio valuation.

---

## 6. Development Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Stage 1** | Extraction and cleaning — raw `.DAT` archives to verified `clean` and `analysis` tables | Complete |
| **Stage 2** | SQL analytical pipeline — Stages 00–13, ML, forecasting | Complete on the earlier extraction; kept as published |
| **Stage 3** | EDA and models on the `analysis` table, with property-grouped splits | Planned |
| **Phase 4** | Hedonic enrichment — property attributes and amenity layers | Scoped, not started |
| **Phase 5** | Historical extension — pre-2016 archive normalisation | Not started; the extraction reader should apply, but schema differences are expected |

Enquiries welcome via LinkedIn:
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

---

## 7. Data Attribution

| Source | Attribution |
|--------|-------------|
| Property transactions | NSW Valuer General — bulk property sales data, published under Creative Commons |
| Geographic classifications | ABS Remoteness Area 2021 (RA_2021) |
| Postcode reference | Matthew Proctor — Australian Postcodes (ABS 2021 aligned); see the file's page for terms |
| Monetary policy | Reserve Bank of Australia — official cash rate records |
| CBD coordinates | Sydney CBD: –33.8688°S, 151.2093°E |

---

*This document reflects the analytical position as of the project's current state: Stage 1 complete, Stage 2 kept as published on the earlier extraction, Stage 3 planned. It will be updated as the project progresses.*
