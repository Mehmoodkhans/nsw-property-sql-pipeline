# Pipeline architecture and decisions

This is the technical reference for the rebuilt pipeline: what each stage does, the rules it follows, and the evidence behind every threshold. The full analysis code is not published (only the leakage-critical feature functions are, in [`../code/`](../code/)), so the reasoning and the evidence are written out here instead. Where a figure appears in the [README](../README.md) it is not repeated; where it belongs to the data itself it is in [`data_provenance.md`](data_provenance.md); full model results are in [`model_evaluation.md`](model_evaluation.md).

The earlier SQL pipeline (Stages 00–13 over a merged CSV) is **superseded** and kept in (../archive/notebooks/)(../notebooks/). Nothing here depends on it.

---

## 1. Overview

```
Raw weekly archives ──► 1 Extraction and cleaning ──► 2 Scope and segments ──► 3 Group EDA ──► 4 Models
 (10 zips, 520 extracts)   2,032,518 rows               1,978,968 dealings        six images      per-segment
                           24 automated checks          1,899,113 in scope        per segment     boosting
```

| Artefact | Rows | Columns | Content |
|---|---:|---:|---|
| Cleaned table | 2,032,518 | 78 | every field, lineage columns and flags |
| Analysis table | 2,032,518 | 35 | one column per idea, for exploration |
| Dealing scope table | 1,978,968 | 43 | one row per dealing, scope flags and a segment label |
| Result tables | | | test, validation, ablation and counter-check results |

### Design rules (held in every stage)

1. **No imputation.** A missing value stays missing and carries a reason.
2. **Flag, do not filter.** Problems become flag columns; exclusion happens only in the analysis scope, with a ledger.
3. **No step may multiply rows.** Row counts are logged before and after each step, and an automated check fails if any step increases them.
4. **Every rule logs how many rows it touched.**
5. **Thresholds follow evidence, not a better score.** Each one below is justified by a table shown here.

---

## 2. Stage 1: extraction and cleaning

**Parsing.** Every sale (B) line is read from the nested archive (yearly zip, weekly zip, district file). Lines in must equal rows out; a mismatch stops the run.

**Re-published sales.** The same sale often reappears in later extracts. Lines are compared on an identity key (district, property, dates, price, dealing number, address, strata lot, component, interest). The **latest copy is kept**, because copies sometimes differ in fields outside the key (about 2.9% of re-published groups, most often area and its unit), and the latest copy carries any correction. The **first publication date** is stored separately. Identical lines inside one extract are kept and flagged; lines sharing an identity but with a different price or settlement date are flagged as possible revisions, not removed.

**Area.** Each area value has a unit field (square metres or hectares). Area in square metres is derived per row. Area is flagged "tiny" (under 50 sqm) or "very large" (over 1,000 ha) for information; neither is treated as an error.

**Dates.** Settlement and contract dates are read from the raw files. Rows with a date problem (missing, settlement before contract, before 1990, or a gap over ten years) are flagged and kept.

**Classification.** The official property code (residential, vacant land, other) is used first; where it is the catch-all code, a mapping of the free-text purpose is used as a fallback and the source of each class is recorded. For rows with an official residential or vacant code the text never disagrees with it.

**Geography.** Each distinct (locality, postcode) pair is matched once to the postcode reference and the result copied back by position. Each match records its method and quality. Postcode-level area labels (LGA, region, remoteness) are kept under names ending `_PostcodeLevel` with a risk flag.

**Automated checks (24).** Seventeen cover row accounting (lines in equal rows out; no step multiplies rows), the no-imputation guard on nine fields, date presence in every source year, geography coverage and coordinate sanity, and class validity. Seven were added with the dealing grain:

| Check | What it guards |
|---|---|
| Dealing size equals the size of each (district, dealing) group | the dealing key |
| Exactly one first row per dealing | one row per dealing |
| Price per m² unchanged on single-lot dealings | the new definition does not alter old results |
| A multi-lot dealing with a lot lacking area has no price per m² | no partial areas |
| Multi-lot price per m² equals price over the sum of lot areas | the formula |
| A dealing holding an identical repeated line has no price per m² | duplicate-or-lots ambiguity |
| First publication is never after the kept copy | the new date column |

---

## 3. The dealing: the unit of a sale

A **dealing** is one sale with one total price, possibly over several lots (rows). Stage 1 repeats the total on every lot, so counting or averaging rows counts a sale more than once.

- The key is **(district, dealing number)**. 1,091 dealing numbers appear in more than one district, so the district is part of the key.
- 1,978,968 dealings; 35,377 span two or more lots; 88,927 rows (4.4%) sit in multi-lot dealings.
- **Price per m²** is total price over total area of all lots. It is missing if any lot lacks a usable area, if the dealing area is under 50 sqm, if the lots carry different prices, or if the dealing holds an identical repeated line. On multi-lot rows the old per-row figure was too high by a median factor of 2.4.

---

## 4. Stage 2: scope and segments

### 4.1 The window

Settlements from **1 January 2016** to the start of the incomplete tail (30 October 2025). Justification in [`data_provenance.md`](data_provenance.md), section 2.

### 4.2 The ledger

Rules are applied in order; each line shows what that rule alone removes from the dealings still in scope.

| Rule | Removed | Remaining |
|---|---:|---:|
| All dealings | | 1,978,968 |
| Settled before 2016 | 19,500 | 1,959,468 |
| Settled in the incomplete tail (last 60 days) | 40,456 | 1,919,012 |
| Revision pair | 193 | 1,918,819 |
| Lots disagree on one price | 18 | 1,918,801 |
| Freehold lot with a unit number | 8,204 | 1,910,597 |
| Bulk sale (5 or more lots) | 1,542 | 1,909,055 |
| Price under $10,000 | 8,721 | 1,900,334 |
| Price over $50,000,000 | 1,221 | **1,899,113** |

**Do the rules matter?** The medians in the scope table barely move: the house median stays at $800,000 and the unit median at $710,000 through every rule, and the vacant land median moves only from $346,000 to $353,000 with the price floor. The exclusions protect the models from odd rows without changing the picture.

### 4.3 Evidence for each threshold

**Bulk sales (5 or more lots).** Residence dealings in the window, by lot count:

| Lots in the dealing | Dealings | Median price | Ratio to a single lot | Strata share |
|---:|---:|---:|---:|---:|
| 1 | 1,619,134 | $756,275 | 1.00 | 36.8% |
| 2 | 19,460 | $810,000 | 1.07 | 82.9% |
| 3 | 1,735 | $1,225,000 | 1.62 | 79.3% |
| 4 | 639 | $1,310,000 | 1.73 | 81.4% |
| 5 | 174 | $2,650,000 | 3.50 | 74.1% |
| 6–9 | 267 | $3,780,000 | 5.00 | 83.2% |
| 10+ | 227 | $8,650,000 | 11.44 | 89.4% |

Three and four lots are mostly a unit with a car space or storage, a single dwelling, whose higher median reflects larger units. The real break is at five lots, where one price stops describing one property. The rule moves no median, so the threshold is low-stakes either way.

**Price tails.** Under $10,000: 9,208 dealings, 75% vacant land (6,942), 16% residence (1,505). Over $50 million: 1,361 dealings, 52% commercial or other (709). Partial interests explain only 2.0% and 2.1% of the two tails. The residence median stays at $759,000–$760,000 across all 15 combinations of low cut-offs ($1,000 to $50,000) and high cut-offs ($20 million to $100 million), so the cut-offs are cosmetic for medians.

**Revision pairs.** 201 dealings. By ratio of the two prices: same price 87, up to 1.5× 32, 1.5×–9.9× 7, about 10× 59, 10×–100× 12, over 100× 4. About ten times is the signature of a typing error. The later extract carries the higher price in only 39% of the pairs that differ, so there is no evidence the later copy is the correction. Excluded; never corrected.

**Acreage threshold (20,000 sqm).** Freehold single-lot residence dealings in the window, by area:

| Area band | Dealings | Median price | Median per sqm | Rural-zoned |
|---|---:|---:|---:|---:|
| under 300 sqm | 77,101 | $1,150,000 | $4,879 | 0.3% |
| 300–600 | 329,510 | $845,000 | $1,777 | 0.8% |
| 600–1,000 | 401,519 | $750,000 | $1,041 | 2.8% |
| 1,000–2,000 | 99,125 | $670,000 | $549 | 13.9% |
| 2,000–5,000 | 34,628 | $695,000 | $227 | 27.9% |
| 5,000 sqm–1 ha | 13,749 | $820,000 | $115 | 28.1% |
| 1–2 ha | 14,762 | $901,000 | $65 | 37.4% |
| **2–4 ha** | 16,143 | $998,500 | $40 | **56.1%** |
| 4–10 ha | 10,631 | $800,000 | $13 | 67.9% |
| 10 ha and over | 22,859 | $812,500 | $3 | 76.9% |

Rural zoning becomes the majority at 2 hectares, so that is where "house" stops and "acreage residence" begins.

### 4.4 Segment rules

| Segment | In documents | Rule | Raw fields used |
|---|---|---|---|
| Bulk sale | bulk sale | 5 or more lots | dealing number, district |
| Unit | strata unit or townhouse | residence class with at least one strata lot | property code, strata lot number |
| Acreage residence | acreage residence | residence class, no strata lot, area at or above 20,000 sqm | the above, area and its unit |
| House | freehold house or similar | residence class, no strata lot, area below 20,000 sqm or unknown | the above |
| Vacant land, Farm or rural, Commercial or other, Unknown | by class | official code first, purpose text as the fallback | property code, purpose text |

Segment sizes in scope: House 943,278; Unit 600,499; Vacant land 202,293; Acreage residence 51,160; Commercial or other 68,767; Farm or rural 26,700; Unknown 6,416. The limits of these labels are in [`data_provenance.md`](data_provenance.md), section 4.2.

---

## 5. Stage 3: group EDA

For each segment, the same six images (volume map, price map, Sydney zoom of the price map, price distribution, price by distance and remoteness, yearly trend and area), each over four periods: 2016–19, 2020–21, 2022–23 and 2024–25 (to late October). Rules: **one dot per locality at its own coordinates** (never shaded postcode regions); a locality needs five dealings in a period to get a price colour; a distance band needs 30; the colour scale is shared across the four periods and clipped at the 5th and 95th percentiles; the median-price axis starts at zero.

---

## 6. Stage 4: models

### 6.1 Protocol

| Step | Fit on | Scored on | Used for |
|---|---|---|---|
| Validation | 2016–2023 | 2024 | choosing the number of trees and the main model; all ablations |
| Test | 2016–2024 | 2025 to the tail cut-off | the final report; chooses nothing |

Target: log price at the dealing level, scored back in dollars. One model family per segment (House, Unit, Vacant land, Acreage residence); Farm or rural and Commercial or other stay descriptive.

### 6.2 Inputs

| Group | Inputs | Notes |
|---|---|---|
| Time | months since January 2016, month of year | no measurable value |
| Segment level | trailing 3-month mean log price of the segment (at least 30 earlier sales) | no measurable value |
| Location | latitude, longitude, distance from the Sydney CBD | locality coordinates |
| Area | log area and a missing flag | the most valuable single group |
| Zoning | zoning code (category) and a missing flag | |
| Lots | lots and strata lots in the dealing | |
| Locality level | trailing 12-month mean log price of the locality (at least 5 earlier sales), its count, and the postcode-level fallback (at least 10) | the strongest input for houses |
| Previous sale | log price of the most recent earlier sale of the same dwelling, months since, the same moved to the current market level, and the number of earlier sales | |
| Building level | trailing 24-month mean log price of the same building (at least 2 earlier sales), and its count | strata only |
| Postcode labels | remoteness class, LGA name, label risk | tested; **excluded** from the final models |

### 6.3 Leakage controls

- Every price-history input uses **only sales settled in strictly earlier months**; a dealing's own month never counts. This was verified against a brute-force calculation on random data, and with a probe that edits one price and checks that nothing in that month or earlier changes.
- Category lists (zoning, LGA) are learned from the training years only.
- `Price per m²` is never an input.
- The building level is computed only where it is feasible (strata) and skipped for houses, where each property is its own key and the dwelling history already covers it.
- The full audit, with its residual risks, is in [`model_evaluation.md`](model_evaluation.md), section 7.

### 6.4 Model and baselines

**Model:** scikit-learn histogram gradient boosting, learning rate 0.10, up to 600 trees chosen on validation (by mean absolute error on log price), 63 leaves, at least 50 dealings per leaf, L2 regularisation 1.0, a training cap of 400,000 rows (a random sample).

**Baselines the model must beat:** the frozen median of the last 12 months of the fit window; the segment's trailing price level; the locality's trailing price level (with postcode and segment fallbacks); and Ridge (linear) on the same inputs without the previous-sale and building features.

**Ablations (validation only):** base inputs, plus postcode labels, plus previous sale, plus building level, plus both. A first run also removed single groups (market level, locality level, area, zoning, coordinates).

**Main model per segment:** chosen on validation among three configurations fixed in advance (base, base plus postcode labels, base plus the history inputs). It is the previous-sale model for House and the previous-sale-plus-building model for the other three.

### 6.5 Counter-check

A separate, independent run re-fitted the current model, LightGBM and XGBoost (through their native interfaces, each tuned on four settings using the validation year only) and their average, with three seeds where the training set exceeds the row cap. A candidate replaces the current model only if its validation error is lower, its test error is lower by more than 0.5 percentage points, and the paired bootstrap 95% interval of the test difference excludes zero. None passed in any segment, so the counter-check is shelved. Details in [`model_evaluation.md`](model_evaluation.md), section 6.

---

## 7. Decisions and their status

| # | Decision | Evidence | Status |
|---|---|---|---|
| 1 | Extract from the raw archive, not a merged CSV | merged file had lost lines and dates | Stands |
| 2 | Keep the latest copy of a re-published sale; store the first publication date | copies differ outside the key in about 2.9% of groups | Stands |
| 3 | Read the area unit from each row | 6.9% of rows in hectares | Stands |
| 4 | Dealing is the unit of a sale; key is (district, dealing number) | 35,377 multi-lot dealings; 1,091 numbers span districts | Stands |
| 5 | Window starts 1 January 2016 | start-of-archive check; early months complete | Replaces the 2018 start |
| 6 | Exclude the last 60 days | 99.5% published within 60 days | Stands |
| 7 | Bulk sale at 5 or more lots | table in 4.3 | Stands; low-stakes |
| 8 | Price cut-offs $10,000 and $50 million | tails characterised; medians insensitive | Stands |
| 9 | Exclude revision pairs and freehold lots with a unit number; never correct a price | pair ratios; ambiguity of unit number | Stands |
| 10 | Segments are proxies; no dwelling-type field | evidence in `data_provenance.md` | Stands, documented |
| 11 | Maps use locality coordinates, not postcode regions | labels identical across a postcode; 28.5% of sales in high-risk postcodes | Stands |
| 12 | Postcode labels excluded from the models | no accuracy gain in any segment; worse for vacant land | Stands |
| 13 | Time-based validation with as-of price inputs | leakage controls in 6.3 | Stands |
| 14 | One model family per segment; Farm and Commercial descriptive | those two segments mix very different property | Stands |
| 15 | Keep the scikit-learn boosting model | counter-check: no candidate cleared the rule | Stands |
| 16 | Grouped cross-validation inside the training years | planned | **Not implemented** |
