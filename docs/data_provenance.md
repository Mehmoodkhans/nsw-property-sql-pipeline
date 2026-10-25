# Data provenance, scope and limits

This document describes where the data comes from, what the cleaning did, which period the analysis covers, and, most importantly, what the data **cannot** tell you. Headline results are in the [README](../README.md); the design and the evidence behind each rule are in [`pipeline_architecture.md`](pipeline_architecture.md); full model results are in [`model_evaluation.md`](model_evaluation.md). Each figure is stated in one place and linked from the others.

---

## 1. Where the data comes from

### 1.1 Primary source: NSW Valuer General bulk sales data

The transaction data is published by the NSW Valuer General as weekly `.DAT` files inside nested zip archives: one zip per year, containing one zip per weekly extract, containing district-level files. Each file holds four record types: a header (A), a sale (B), a legal description (C) and party flags (D). A sale line has 24 semicolon-separated fields (the record type plus 23 data fields, all extracted). No schema documentation is published with the files.

| Coverage | |
|---|---|
| Yearly archives | 10 |
| Weekly extracts | 520 |
| District files | 66,747 |
| First and last extract | 4 January 2016 and 29 December 2025 |
| Sale (B) lines | 2,186,102 |

Published under Creative Commons; attribute NSW Valuer General when reusing.

### 1.2 Secondary source: the postcode reference

The Matthew Proctor Australian Postcodes file supplies locality coordinates and a postcode reference. Problems found in it during profiling, and how they were handled:

- Two localities (Birdlip and Kempton) carry impossible coordinates, in England and in the USA. They are repaired from the file's own basic latitude and longitude.
- Fifteen localities store missing precise coordinates as 0,0. They are repaired the same way.
- Ten further places had suspect coordinates (a same-name place elsewhere). **None of the ten has a single sale in the cleaned table**, so none can affect any result.
- One suburb (Edmondson Park) is missing from the reference file. It is covered by a human-reviewed entry with approximate coordinates, which serves 5,483 sales.

Each distinct (locality, postcode) pair in the sales is matched once and the result is copied back by position, so rows cannot multiply. **99.93% of sales match on the exact pair; 58 sales are unmatched.**

### 1.3 What the first version used and this one does not

- **The merged CSV** (1,697,724 rows) is replaced by direct extraction from the archive.
- **The RBA cash rate** was joined in the first version. The final models do not use it; it is listed as a possible later test.
- **ABS boundary files** were not downloaded. The area labels in the postcode file are not used by the final models (see 4.3).

---

## 2. The period: January 2016 to late October 2025

The first version analysed 2018–2025, a policy-motivated choice and not a data limit. The archive starts on 4 January 2016, and early-2016 months are as complete as later ones, so the window starts on **1 January 2016**.

| Check | Result |
|---|---|
| Start-of-archive check | January to June 2016 hold 84% to 102% of the dealings of the same months a year later (a ramp-up artefact would show ratios far below 1 in the first months only) |
| Sales settled in 2015 | 18,036 dealings, mostly partial coverage, outside the window |

### Dealings by settlement year

| Year | Dealings | Note |
|---|---:|---|
| 2016 | 207,366 | |
| 2017 | 212,202 | |
| 2018 | 191,328 | |
| 2019 | 170,412 | |
| 2020 | 184,732 | |
| 2021 | 230,964 | |
| 2022 | 189,858 | |
| 2023 | 177,979 | no gap: the earlier "2023 gap" was lost dates in the first extraction |
| 2024 | 196,879 | |
| 2025 | 197,748 | includes 40,456 in the incomplete tail (excluded) |

### The incomplete tail

Sales settled in the last 60 days before the final extract (from 30 October 2025) are flagged as incomplete and excluded from the scope. The flag is long enough: for settlements in 2022–2024, **99.5% were published within 60 days** (99.7% within 90).

### Publication got faster

| Settlement year | Median delay (days) | 95th percentile | 99th percentile |
|---|---:|---:|---:|
| 2016 | 19 | 66 | 150 |
| 2017 | 17 | 58 | 136 |
| 2018 | 12 | 52 | 115 |
| 2019 | 7 | 24 | 83 |
| 2020 | 7 | 11 | 54 |
| 2021 | 7 | 10 | 38 |
| 2022 | 7 | 10 | 52 |
| 2023 | 7 | 10 | 35 |
| 2024 | 7 | 11 | 28 |

*Delay is the first publication date minus the settlement date. The early years are slower and have more corrections (see 4.4), which is one reason the analysis uses time-based validation and period panels.*

### Bulk re-publications

Some extracts re-publish many earlier sales. `Extract_Date` therefore records the date of the kept copy, not when the sale first appeared, and a separate first-publication date is kept for any timing analysis.

| Extract | Dealings | Share that are re-publications |
|---|---:|---:|
| 2025-08-11 | 32,573 | 89.0% |
| 2025-09-22 | 7,273 | 48.3% |
| 2016-11-28 | 6,025 | 30.3% |
| 2025-01-13 | 1,300 | 28.6% |
| 2016-11-21 | 5,883 | 27.0% |
| 2017-10-02 | 5,612 | 15.6% |

---

## 3. What the cleaning resolved

Design rules throughout: no imputation, flag and do not filter, no step may multiply rows, and every rule logs the rows it touches.

- **Re-published sales.** 153,584 lines (7.0%) were the same sale again in a later extract. The latest copy is kept, and the first publication date is recorded. Where copies differ in fields outside the identity key (area, zoning, purpose, locality, postcode), about 2.9% of re-published groups differ, most often in area and its unit; keeping the latest copy keeps any correction.
- **Mixed area units.** Every area has a unit field (square metres or hectares). **139,687 rows (6.9%) are in hectares.** The area in square metres is derived from the unit of each row, never assumed.
- **Dates.** Of the 2,032,518 rows, 1,130 carry a date problem, all flagged and none removed: 634 with a settlement more than ten years after the contract, 307 dated before 1990, 186 with no contract date, 2 with no settlement date, and 1 with settlement before contract.
- **The unit of a sale.** 35,377 of 1,978,968 dealings span two or more lots, with the same total price repeated on every lot. The analysis works at the dealing level. 1,091 dealing numbers appear in more than one district, so the key is the (district, dealing number) pair.
- **Zero imputed values.** A guard compares the missing-value counts of nine key fields before and after cleaning.

---

## 4. Known limitations

### 4.1 No dwelling type and no property attributes

The records contain a property class, land area, zoning, purpose text, dates, price and a location. They do **not** contain dwelling type (house, townhouse, villa, apartment), bedrooms, bathrooms, parking, building age, condition, views or amenities. Any model built on them has a ceiling set by that gap. Enrichment with attribute and amenity data would be the most direct way to raise it.

### 4.2 "House", "Unit" and "Acreage residence" are proxies

| Segment | Rule | Reading |
|---|---|---|
| Unit | residence class with at least one strata lot | strata-titled: apartments, but also strata townhouses, villas and duplexes |
| House | residence class, no strata lot, area below 2 ha or unknown | freehold residence: houses, but also freehold terraces and townhouses |
| Acreage residence | residence class, no strata lot, area at or above 2 ha | freehold residence on a large lot |

Evidence for the rules (single-lot residence dealings; 1,632,003 of them, of which 36.8% are strata):

| Measure | Value |
|---|---:|
| Strata dealings with a unit number in the address | 91.6% |
| Freehold dealings with a unit number in the address | 8,410 (0.8%) |
| Median lot area with / without a unit number (sqm) | 329 / 661 |
| Strata dealings with no recorded area | 63.1% |
| Strata dealings flagged "tiny" area (median price) | 0.7% ($545,000) |
| Purpose text exactly "RESIDENCE" | 100.0% |
| Freehold dealings at or above 20,000 sqm | 52,354 |
| Their most common zoning groups | RU1 37%, RU2 19%, R5 13%, RU4 9% |

The 2-hectare threshold is a reading of the area bands: in the 2–4 ha band, rural zoning becomes the majority (56%). **Freehold lots with a unit number** are ambiguous (the address says unit, the title does not), so they are flagged and left out of the scope, not moved into Unit.

### 4.3 Postcode-level area labels are unreliable

Every area label in the postcode reference (LGA, region, remoteness class, SA2 to SA4) is **identical for every locality in a postcode** in 629 of 634 postcodes in the NSW range (638 of 643 including border places). 35% of those postcodes span more than 20 km, and **28.5% of all sales** fall in postcodes flagged high-risk (spread over 30 km). The share differs by segment:

| Segment | Dealings in high-risk postcodes |
|---|---:|
| House | about 33% |
| Unit | about 7–8% |
| Vacant land | about 45–51% |
| Acreage residence | about 75–78% |
| Farm or rural | about 87% |
| Commercial or other | about 30–32% |

Example: the town of Cessnock carries the label "Central Coast (NSW)" in the reference. Maps use locality coordinates, never shaded postcode regions, and the final models leave these labels out because they added no accuracy.

### 4.4 Prices

- **Round-number heaping.** Exactly $1,000,000 occurs 4.2 times as often as the prices around it, and exactly $2,000,000 occurs 13 times as often. Price histograms show sharp edges as a result.
- **Low-price sales.** 9,208 dealings are under $10,000, 75% of them vacant land. Round amounts dominate ($5,000 is the most common, then $1,000, $8,000, $2,000 and $100), which suggests nominal transfers, though price alone cannot prove it. Only 2.0% are partial interests, so the recorded interest percentage does not explain them. Their share fell from 0.80% of dealings in 2016 to 0.14% in 2025; the cause is unknown.
- **High-price sales.** 1,361 dealings are over $50 million, 52% of them commercial or other property. 29% span two or more lots, with the total price repeated on each, so a row-level count overstates them.
- **Revision pairs.** 201 dealings (424 rows) hold the same sale published twice with conflicting data. Of the 114 pairs with different prices, 59 differ by about a factor of 10, which looks like a typing error. The later extract has the higher price in only 39% of pairs, so there is no evidence that the later copy is the corrected one. They are flagged and excluded, and no price is ever corrected.
- **Most are concentrated in the early archive:** the revision pairs, differing-price dealings and low-price sales are all more common in 2016–2017.

### 4.5 Area

- **Structural gaps.** Strata lots carry no zoning by design, and 63.1% of single-lot strata dealings have no area. Area and zoning therefore mean different things in different segments.
- **A change over time.** The share of vacant-land dealings with no recorded area rises to 10.9% in 2022–23, against 1.4% to 3.0% in the other periods. The cause is unknown.
- **Extremes are mostly real.** 13,385 rows have an area under 50 sqm (about 90% are strata lots) and 3,731 rows exceed 1,000 hectares (all recorded in hectares, mostly farm property). Neither group is treated as an error.

### 4.6 What a property key identifies

For strata lots the property identifier names the **building**, not the unit: the most-sold key has 1,283 sales across 305 units. The share of properties with two or more sales is 25.9% by property key and 23.3% when a strata lot is identified by (property key, lot number). Repeat-sale work uses the second; validation that must keep neighbouring units together uses the first.

### 4.7 Timing

Use the first-publication date and the settlement date, not the extract date, for any timing work (see the bulk re-publications in section 2).

### 4.8 Border localities

1,023 rows carry a postcode outside 2000–2999; most are real NSW border localities with a Victorian or Queensland postcode (for example Berrigan, Tenterfield and Albury), not errors. The flag is named for what it measures, a postcode outside the usual range, and not for a fault.

### 4.9 The scope selects on price

Prices under $10,000 and over $50 million, bulk sales (5 or more lots), revision pairs and freehold lots with a unit number are excluded before modelling. Model accuracy therefore describes ordinary in-scope sales, 96.0% of all dealings.

---

## 5. What the data could support next

These are directions, not claims:

- **Attribute enrichment** (bedrooms, building age, amenity and transport layers) is the most direct way to lift accuracy, since the current ceiling is set by missing attributes.
- **Prediction intervals**, so that an estimate is a range, which would suit an interactive app.
- **A repeat-sales price index** from the 23% to 26% of properties with more than one sale.
- **Longer history.** The archive reaches earlier than 2016. Extending to it needs a decade-by-decade check of field definitions, postcodes and boundaries that has not been done.

---

## 6. Status

| Stage | State |
|---|---|
| Extraction and cleaning | complete; 24 automated checks pass |
| Scope and segments | complete |
| Group EDA and maps (static images) | complete |
| Models, ablations and counter-check | complete |
| Map app | planned |
| Presentation | planned |
| Attribute enrichment, longer history | not started |

---

## 7. Attribution

| Source | Attribution |
|---|---|
| Property transactions | NSW Valuer General, bulk property sales data, published under Creative Commons |
| Postcode reference | Matthew Proctor, Australian Postcodes (see the file's page for terms) |
| Sydney CBD reference point | −33.8688°, 151.2093° (distance is a straight-line geodesic distance from this point to each locality) |

*This document reflects the project state after the rebuild: extraction, scope and models complete, the map app and presentation planned.*
