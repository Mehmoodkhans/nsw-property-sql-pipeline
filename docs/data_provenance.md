# Data Provenance, Scope and Research Potential
## NSW Property Market — SQL Data Pipeline
**Mehmood Ahmed** | [![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

---

## Overview

This document describes the origin, scope, known limitations, and research potential of the dataset
underlying the NSW Property Market SQL Data Pipeline. It is intended for researchers, government
analysts, and industry practitioners who wish to understand not just what this pipeline produces —
but what the data can and cannot tell you, and where serious analytical opportunity remains.

---

## 1. Dataset Origin

### Primary Source — NSW Valuer General Bulk Data

The transaction data originates from the **NSW Valuer General** — the government authority responsible
for property valuations and the official registry of property sales across New South Wales.

The bulk data is publicly available and covers **all property sales registered in NSW**, including
residential, commercial, rural, and industrial transactions. Records are filed at settlement date
and include purchase price, property type, land area, and geographic identifiers down to street address
and postcode level.

**A critical fact about this archive:**
The NSW Valuer General bulk data collection extends from the **early 1990s** — representing
approximately 45 years of continuous property transaction records across the entire state.

This pipeline currently covers **2018–2025** — a deliberate scope decision explained in Section 3.
Extension to the full historical archive is architecturally straightforward and represents a natural
next phase for any researcher or organisation requiring long-run market analysis.

### Secondary Source — Australian Postcodes Reference

Geographic enrichment uses the **Matthew Proctor Australian Postcodes** reference file — an
ABS 2021-aligned postcode dataset providing:

- ABS Remoteness Area 2021 (RA_2021) classifications
- SA4 region names
- Precise latitude and longitude coordinates

This reference was selected over alternatives after discovering that a manually curated geo file
contained corrupt coordinates — two NSW postcodes had been assigned coordinates in
Gloucestershire, England and Pennsylvania, USA respectively. The Proctor reference was validated
against known NSW distances before adoption.

### Tertiary Source — RBA Cash Rate Records

Monetary policy context is provided by **Reserve Bank of Australia** official cash rate records
covering 32 quarters (Q1 2018 – Q4 2025). This enables direct correlation analysis between
interest rate cycles and property price movements at zone and LGA level.

---

## 2. Period Selection — Why 2018–2025

The 2018–2025 window was not chosen arbitrarily. It was selected as the most **policy-relevant
and analytically rich** period available in the archive for the following reasons:

**Pre-COVID baseline (2018–2019)**
A stable two-year reference period with moderate price growth and a well-understood interest
rate environment. Essential as the foundation for measuring subsequent disruption.

**COVID-19 demand surge (2020–2021)**
The most significant external shock to the NSW property market in decades. A +13.48% median
price surge in 2021 alone — the largest single-year movement in the dataset — driven by
historically low interest rates, government stimulus, and a fundamental shift in housing
preferences during lockdown periods. No comparable window in the archive captures a disruption
of this scale and speed.

**RBA rate hike cycle (2022–2023)**
The most aggressive monetary policy tightening in a generation — 4.25 percentage points across
13 consecutive increases. This pipeline captures the full transmission of that cycle into property
prices, with the counterintuitive finding that the correction was far more modest than the
rate movement suggested — only -6.3% from peak despite the severity of the tightening.

**Post-hike recovery (2024–2025)**
Prices recovering toward and exceeding pre-hike peaks by Q4 2025, confirming structural demand
resilience in the NSW market independent of monetary policy cycles.

**In summary:** This eight-year window contains more structural market events per year than any
comparable window in the 45-year archive. It is the right period for understanding how the NSW
property market behaves under stress — which is precisely what policy analysts, urban planners,
and serious investors need to understand.

---

## 3. What the Pipeline Resolves

Ten quantifiable data quality issues were discovered and resolved during Stages 02–05 of the pipeline.
Full documentation is in the main [README.md](../README.md).

These resolutions cover: float-promoted postcodes, mislabelled area columns, government encoding
conventions misread as data errors, null-heavy columns removed with documented justification,
date-based scope filtering replacing unreliable year fields, and property type code normalisation.

Every resolution is documented with the original finding, the evidence, and the SQL decision applied.
The raw `staging_transactions` table is preserved frozen — no finding was applied destructively.

---

## 4. Known Limitations — An Honest Assessment

The following limitations are stated not as apologies but as **analytical boundaries** — the
honest perimeter of what this dataset can and cannot tell you. Understanding these boundaries
is as important as understanding the findings themselves.

---

### 4.1 Geographic Distance from the Market

This analysis was conducted without physical proximity to the NSW property market. The analyst
does not have firsthand knowledge of specific suburbs, local amenity quality, or the kind of
ground-level market intuition that a Sydney-based agent or developer carries naturally.

**Why this is a methodological advantage, not a weakness:**
Every finding in this pipeline derives entirely from transaction records, ABS classifications,
and RBA data — not from local intuition or anecdote. There is no confirmation bias toward
familiar suburbs. No anchoring to recent headlines. The data speaks without the analyst
filtering it through proximity bias. At 1.7M transactions across 123 LGAs and 5 density zones,
ground-level intuition would be insufficient anyway — only systematic analysis at scale
can reveal the patterns this pipeline identifies.

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

These are real and significant drivers of NSW property price movements that operate
independently of — and sometimes in opposition to — interest rate cycles. The 2021–2022
price surge, for example, reflects not just record-low interest rates but the simultaneous
effect of government stimulus, HomeBuilder grants, and pandemic-driven demand shifts that
the RBA data alone cannot explain.

**What this means for users:** Price movements in this dataset should be interpreted as
the net outcome of multiple policy forces, not attributed solely to the monetary policy
variables captured. Analysts using these findings for policy evaluation should layer in
the relevant fiscal and regulatory context for each period.

**What this opens up:** Integration of NSW government policy event data as categorical
timeline variables would substantially improve the explanatory power of the ML models
and is identified as a Phase 3 enrichment opportunity.

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

**What this means for current analysis:** Price per square metre calculations and
median price comparisons reflect zone-level and LGA-level patterns — macro geography
rather than micro property characteristics. Two properties in the same postcode with
vastly different attributes are treated identically in this dataset.

**What this opens up:** This is the most commercially significant gap in the current
dataset — and the most tractable to address. Integration with:

- **Domain or CoreLogic** property attribute data — dwelling type, bedroom count, build year
- **OpenStreetMap amenity layers** — transport nodes, schools, retail precincts
- **NSW Department of Education** school catchment boundaries
- **Transport for NSW** GTFS public transport accessibility data

...would unlock true **hedonic price modelling** — isolating the independent contribution
of each attribute to property value. This is Phase 3 of this project and represents
the most direct path to a commercially deployable valuation tool.

---

### 4.4 Text-Level Data Quality — Commercial and Rural Segments

The 10 data quality findings resolved in the pipeline cover quantifiable, systematic issues.
A second category of issues remains in progress:

**Text-level inconsistencies** in categorical fields — particularly `Primary_Purpose` — include
spelling variants (`COMMERICAL` vs `COMMERCIAL`), compound word variations (`FARM LAND` vs
`FARMLAND`), and domain terminology inconsistencies across the annual filing cohorts.

These inconsistencies disproportionately affect **commercial and rural land use classifications**
rather than the residential segment. The residential pipeline — which covers 1,259,466
transactions and is the basis for all price trend and ML analysis in this repo — is not
materially affected.

**The text audit** is being conducted separately using Python/Pandas with fuzzy text
comparison libraries (FuzzyWuzzy, RapidFuzz) and domain expert review. This forms the
basis of the **Phase 2 companion repository** — a classical exploratory notebook documenting
the raw data investigation process that preceded this SQL pipeline.

**What this means for users:** Findings on residential price trends, geographic segmentation,
RBA rate correlation, and ML modelling are robust. Users working with commercial property
classifications or rural land use analysis should treat segment-level breakdowns as
directional until the Phase 2 text audit is published.

---

### 4.5 Pre-2018 Historical Extension — Considerations

For users interested in extending this pipeline to the full 45-year archive, the following
additional challenges apply beyond those resolved for 2018–2025:

- **Field definition evolution** — column names, property type codes, and area measurement
  conventions changed across decades of the archive. Normalisation would require decade-by-decade
  schema mapping.
- **Geographic boundary changes** — LGA boundaries, postcode assignments, and ABS
  geographic classifications have changed multiple times since the 1990s. Longitudinal
  geographic analysis requires boundary-consistent reclassification.
- **Structural market breaks** — the GST introduction (2000), the Global Financial Crisis
  (2008–2009), and multiple state government policy regimes represent structural breaks
  that affect comparability across the full archive period.
- **Data completeness** — earlier cohorts have higher rates of missing fields,
  particularly for area measurements and property type codes.

None of these are insurmountable. They are enumerated here so that any extension effort
begins with clear eyes about the normalisation work required.

---

## 5. Research and Commercial Potential

The NSW Valuer General archive — properly cleaned, enriched, and extended — represents
one of the most comprehensive longitudinal property transaction datasets available in Australia.

The foundation built in this pipeline enables research and analysis across several dimensions
of significant public, academic, and commercial interest:

**Housing affordability over economic cycles**
45 years of transaction data spanning multiple interest rate cycles, government policy regimes,
and macroeconomic shocks. Long-run affordability analysis that contextualises current conditions
within a generational perspective — essential for credible housing policy design.

**Geographic transmission of monetary policy**
How do RBA rate decisions propagate differently across Metro, Inner Regional, Outer Regional,
and Remote markets? This pipeline already shows a counterintuitive finding — Inner Regional
prices rose during the rate hike cycle. A 45-year panel would establish whether this regional
resilience is structural or cyclical.

**Urban-regional price divergence**
The current 15.8× price per square metre ratio between Metro and Very Remote zones is striking.
A longitudinal view would reveal whether this divergence is widening, stable, or subject to
mean reversion — a question with direct implications for regional development policy.

**Infrastructure value uplift**
Combining transaction data with infrastructure announcement and delivery timelines —
metro extensions, motorway corridors, hospital developments — would isolate the measurable
property value uplift attributable to specific public investments. A powerful tool for
infrastructure cost-benefit analysis.

**Hedonic valuation modelling**
With Phase 3 micro-characteristic enrichment, this pipeline becomes the foundation for
a suburb-level automated valuation model (AVM) — the same class of tool used by major
banks, REITs, and property analytics platforms for mortgage underwriting and portfolio valuation.

---

## 6. Collaboration and Further Development

This pipeline and the dataset foundation it represents are available for discussion with
researchers, government agencies, and industry practitioners with serious analytical interest.

Current development roadmap:

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | SQL pipeline — Stages 00–13 | Stages 00–10 complete. Stages 11–13 in progress |
| **Phase 2** | Pandas text audit notebook — raw data investigation and commercial segment cleaning | In preparation |
| **Phase 3** | Hedonic enrichment — property attributes and amenity layers | Scoped, not started |
| **Phase 4** | Historical extension — pre-2018 archive normalisation | Architecture ready |

Enquiries welcome via LinkedIn:
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mehmood%20Ahmed-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mehmoood)

---

## 7. Data Attribution

| Source | Attribution |
|--------|-------------|
| Property transactions | NSW Valuer General — bulk property sales data (publicly available) |
| Geographic classifications | ABS Remoteness Area 2021 (RA_2021) |
| Postcode reference | Matthew Proctor — Australian Postcodes (ABS 2021 aligned) |
| Monetary policy | Reserve Bank of Australia — official cash rate records |
| CBD coordinates | Sydney CBD: -33.8688°S, 151.2093°E |

---

*This document reflects the analytical position as of the pipeline's current published state.
It will be updated as Phase 2 and Phase 3 work progresses.*
