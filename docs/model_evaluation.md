# Model evaluation

This document holds the full model results behind the headline figures in the [README](../README.md): every model, every segment, the ablations, where the models are weak, the counter-check with other boosting libraries, and a leakage audit. It is written to stand on its own, because the analysis code is not published. **Every table below was generated from the printed output of the executed analysis notebooks**, not typed by hand.

## 1. How to read the numbers

| Measure | Meaning |
|---|---|
| **Typical error (MdAPE)** | median absolute percentage error: half of the predictions are within this percentage of the actual price |
| **Within 10% / 20%** | share of dealings predicted within 10% (or 20%) of the actual price |
| **R² (log price)** | share of variation in log price explained. Do not compare it across segments: price spread differs by segment, so a segment with a narrower spread has a lower R² for the same relative error |
| **MAE** | mean absolute error in dollars; dominated by expensive sales |
| **Bias** | median of predicted ÷ actual, minus 1 (negative: the model under-predicts typically) |

**Protocol.** Validation fits on 2016–2023 and scores 2024; the test refits on 2016–2024 (with the tree count fixed on validation) and scores 2025 up to the tail cut-off. The test year chooses nothing. The baselines use only the information a valuer would have had at the time: the *stale median* is a frozen median of the last 12 months of the fit window, the *segment* and *locality* levels are trailing price levels from earlier months only, and *Ridge* is a linear model on the same inputs (without the previous-sale and building features).

## 2. Test results, 2025 (fit on 2016–2024)

### House

Training dealings 762,227, validation 98,059, test 82,992. Main model, chosen on validation: **Boosting + previous sale**.

| Model | Dealings | Typical error | Within 10% | Within 20% | R² (log) | MAE | Bias |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) | 82,992 | 38.9% | 13.4% | 26.7% | -0.009 | $741k | -4.8% |
| Segment price level (as-of) | 82,992 | 39.5% | 12.6% | 26.4% | -0.001 | $740k | 0.8% |
| Locality price level (as-of) | 82,992 | 17.1% | 32.0% | 56.4% | 0.683 | $376k | -4.1% |
| Ridge (linear) | 82,992 | 16.7% | 32.3% | 57.5% | 0.699 | $363k | 0.5% |
| Boosting, base inputs | 82,992 | 15.2% | 35.1% | 60.9% | 0.740 | $325k | -2.9% |
| Boosting + postcode labels | 82,992 | 15.1% | 35.5% | 61.3% | 0.741 | $324k | -3.1% |
| **Boosting + previous sale** | 82,992 | 13.4% | 39.7% | 65.0% | 0.762 | $301k | -2.4% |

- Validation / test dealings with a previous sale of the same dwelling: 32.0% / 34.4%
- Validation / test dealings with building history: 0.0% / 0.0%

### Unit

Training dealings 479,309, validation 69,935, test 51,255. Main model, chosen on validation: **Boosting + previous sale + building level**.

| Model | Dealings | Typical error | Within 10% | Within 20% | R² (log) | MAE | Bias |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) | 51,255 | 28.3% | 21.0% | 38.5% | -0.025 | $415k | -3.6% |
| Segment price level (as-of) | 51,255 | 30.9% | 19.7% | 35.3% | -0.000 | $416k | 5.6% |
| Locality price level (as-of) | 51,255 | 20.4% | 27.1% | 49.3% | 0.395 | $328k | -0.7% |
| Ridge (linear) | 51,255 | 18.6% | 29.5% | 53.0% | 0.470 | $299k | 0.8% |
| Boosting, base inputs | 51,255 | 15.9% | 33.6% | 58.9% | 0.542 | $261k | -1.3% |
| Boosting + postcode labels | 51,255 | 15.8% | 33.9% | 59.2% | 0.543 | $260k | -1.0% |
| **Boosting + previous sale + building level** | 51,255 | 10.0% | 49.9% | 75.6% | 0.717 | $189k | -1.4% |

- Validation / test dealings with a previous sale of the same dwelling: 39.3% / 46.5%
- Validation / test dealings with building history: 60.5% / 63.8%

### Vacant land

Training dealings 177,963, validation 13,590, test 10,740. Main model, chosen on validation: **Boosting + previous sale + building level**.

| Model | Dealings | Typical error | Within 10% | Within 20% | R² (log) | MAE | Bias |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) | 10,740 | 37.2% | 11.7% | 24.5% | -0.001 | $418k | -7.0% |
| Segment price level (as-of) | 10,740 | 38.4% | 12.0% | 24.4% | -0.004 | $421k | -11.0% |
| Locality price level (as-of) | 10,740 | 18.9% | 31.1% | 52.0% | 0.336 | $326k | 0.1% |
| Ridge (linear) | 10,740 | 25.4% | 20.8% | 41.2% | 0.378 | $343k | 12.4% |
| Boosting, base inputs | 10,740 | 14.5% | 38.2% | 60.4% | 0.666 | $248k | -4.2% |
| Boosting + postcode labels | 10,740 | 14.8% | 37.1% | 59.6% | 0.662 | $245k | -4.8% |
| **Boosting + previous sale + building level** | 10,740 | 13.9% | 39.5% | 61.8% | 0.678 | $241k | -4.0% |

- Validation / test dealings with a previous sale of the same dwelling: 16.1% / 16.5%
- Validation / test dealings with building history: 0.3% / 0.2%

### Acreage residence

Training dealings 42,611, validation 4,563, test 3,986. Main model, chosen on validation: **Boosting + previous sale + building level**.

| Model | Dealings | Typical error | Within 10% | Within 20% | R² (log) | MAE | Bias |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) | 3,986 | 43.6% | 10.5% | 22.7% | -0.001 | $1,053k | 0.0% |
| Segment price level (as-of) | 3,986 | 43.7% | 11.2% | 22.2% | -0.001 | $1,054k | 1.9% |
| Locality price level (as-of) | 3,986 | 31.1% | 17.1% | 34.2% | 0.320 | $831k | -3.0% |
| Ridge (linear) | 3,986 | 31.2% | 17.5% | 34.0% | 0.329 | $828k | 2.3% |
| Boosting, base inputs | 3,986 | 26.5% | 19.2% | 38.7% | 0.518 | $692k | -5.8% |
| Boosting + postcode labels | 3,986 | 26.6% | 18.5% | 37.5% | 0.512 | $702k | -6.5% |
| **Boosting + previous sale + building level** | 3,986 | 24.0% | 21.3% | 42.5% | 0.546 | $661k | -5.1% |

- Validation / test dealings with a previous sale of the same dwelling: 24.7% / 25.5%
- Validation / test dealings with building history: 0.1% / 0.1%

### Validation year (fit on 2016–2023, score 2024)

Used to choose the number of trees and the main model. Shown so the test figures can be compared with it: they are close, which is what a model that is not tuned to its test year looks like.

**House**

| Model | Trees | Typical error | Within 10% | R² (log) |
|---|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) |  | 39.2% | 14.7% | -0.021 |
| Segment price level (as-of) |  | 40.1% | 12.2% | -0.001 |
| Locality price level (as-of) |  | 17.5% | 30.8% | 0.692 |
| Ridge (linear) |  | 17.1% | 31.4% | 0.708 |
| Boosting, base inputs | 260 | 15.3% | 35.1% | 0.752 |
| Boosting + postcode labels | 310 | 15.4% | 34.8% | 0.750 |
| Boosting + previous sale | 340 | 13.6% | 39.0% | 0.770 |

**Unit**

| Model | Trees | Typical error | Within 10% | R² (log) |
|---|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) |  | 28.0% | 20.0% | -0.028 |
| Segment price level (as-of) |  | 30.8% | 19.1% | 0.001 |
| Locality price level (as-of) |  | 20.1% | 27.2% | 0.444 |
| Ridge (linear) |  | 18.5% | 29.3% | 0.530 |
| Boosting, base inputs | 400 | 15.6% | 34.4% | 0.595 |
| Boosting + postcode labels | 370 | 15.5% | 34.8% | 0.595 |
| Boosting + previous sale | 470 | 12.3% | 42.3% | 0.672 |
| Boosting + building level | 360 | 12.0% | 43.5% | 0.708 |
| Boosting + previous sale + building level | 500 | 10.5% | 48.2% | 0.749 |

**Vacant land**

| Model | Trees | Typical error | Within 10% | R² (log) |
|---|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) |  | 38.3% | 13.0% | -0.001 |
| Segment price level (as-of) |  | 38.8% | 12.4% | -0.004 |
| Locality price level (as-of) |  | 22.4% | 26.8% | 0.326 |
| Ridge (linear) |  | 27.0% | 20.6% | 0.387 |
| Boosting, base inputs | 450 | 15.7% | 34.7% | 0.684 |
| Boosting + postcode labels | 430 | 16.4% | 32.6% | 0.675 |
| Boosting + previous sale | 370 | 15.8% | 35.4% | 0.691 |
| Boosting + building level | 530 | 15.9% | 35.5% | 0.681 |
| Boosting + previous sale + building level | 430 | 15.4% | 35.6% | 0.691 |

**Acreage residence**

| Model | Trees | Typical error | Within 10% | R² (log) |
|---|---:|---:|---:|---:|
| Stale median (last 12 months of the fit window) |  | 46.5% | 11.8% | -0.003 |
| Segment price level (as-of) |  | 47.8% | 11.8% | -0.001 |
| Locality price level (as-of) |  | 31.3% | 16.8% | 0.354 |
| Ridge (linear) |  | 31.7% | 17.1% | 0.368 |
| Boosting, base inputs | 180 | 26.4% | 20.1% | 0.564 |
| Boosting + postcode labels | 220 | 26.3% | 20.1% | 0.559 |
| Boosting + previous sale | 180 | 25.0% | 22.0% | 0.581 |
| Boosting + building level | 140 | 26.3% | 20.7% | 0.561 |
| Boosting + previous sale + building level | 180 | 25.0% | 22.0% | 0.581 |

## 3. What each group of inputs is worth (validation ablations)

Change in the validation typical error relative to the base inputs, in percentage points. **Negative means the added inputs help.** These describe what the model leans on in this data; they are not causal effects.

| Added to the base inputs | House | Unit | Vacant land | Acreage residence |
|---|---:|---:|---:|---:|
| Boosting + postcode labels | +0.06 | -0.09 | +0.76 | -0.17 |
| Boosting + previous sale | -1.66 | -3.34 | +0.14 | -1.41 |
| Boosting + building level | n/a | -3.61 | +0.28 | -0.19 |
| Boosting + previous sale + building level | n/a | -5.11 | -0.22 | -1.41 |

Reading it:
- **Previous sale and building history are the only additions that help clearly.** They help most for units (previous sale plus building level takes 5.1 points off the error), then houses (previous sale, 1.7 points) and acreage (previous sale, 1.4 points). For vacant land they do not help beyond noise (between -0.2 and +0.3 points).
- **Postcode-level labels add nothing.** The change is within 0.2 points for House, Unit and Acreage, and Vacant land is worse with them (+0.76). They are left out of the final models.
- **The first run also tested removing individual groups** (market level, locality level, area, zoning, coordinates). Area was the most valuable single group (removing it cost about 1.4 points for houses, 4.8 for units and 5.6 for vacant land on validation); the market-level and time columns had no measurable value, because the as-of locality level already carries the market level. Those first-run results are not repeated here because the second run did not re-run them.

## 4. Where the main model is strong and weak (test year)

### Typical error by distance from the Sydney CBD

| Band | House | Unit | Vacant land | Acreage residence |
|---|---:|---:|---:|---:|
| 0-10 km | 15.2% (6,272) | 12.7% (14,148) | 43.9% (46) | n/a |
| 10-20 km | 13.3% (8,551) | 9.6% (13,027) | 49.6% (45) | 21.8% (5) |
| 20-40 km | 11.8% (15,614) | 8.3% (11,211) | 8.6% (1,475) | 21.9% (176) |
| 40-80 km | 11.7% (14,381) | 8.4% (4,772) | 11.9% (2,488) | 25.0% (454) |
| 80-160 km | 12.8% (14,806) | 9.7% (3,167) | 13.2% (2,461) | 24.0% (614) |
| 160-320 km | 14.9% (10,547) | 11.2% (1,909) | 15.9% (1,914) | 22.7% (1,273) |
| 320+ km | 17.0% (12,819) | 12.0% (3,017) | 20.8% (2,311) | 25.4% (1,464) |

*Main model typical error, with the number of test dealings in brackets. Bands with very few dealings are noisy.*

### Where a locality price level exists, and where the label risk is high

| Segment | Typical error, locality level available | Typical error, no locality level | High-risk postcode label | Low-risk postcode label |
|---|---:|---:|---:|---:|
| House | 13.3% (81,588) | 26.7% (1,404) | 14.5% | 12.8% |
| Unit | 9.9% (50,276) | 17.3% (979) | 10.5% | 10.1% |
| Vacant land | 11.2% (8,529) | 32.8% (2,211) | 16.2% | 13.7% |
| Acreage residence | 22.3% (1,437) | 25.2% (2,549) | 24.0% | 23.7% |

- **Dealings without a recent locality price level are much harder** (for houses the error roughly doubles), and they are most of the Acreage segment.
- **Remote places are the weakest area:** for houses the typical error is about 30% in the Remote and Very Remote classes, on few dealings.
- **Inner Sydney is not the easiest area:** the 0–10 km band has a higher error than the middle bands in every segment that has enough dealings there.

### Calibration by predicted price

The fair bias check: given a prediction, is the prediction right on average? Values near 1.00 mean unbiased. (A view grouped by *actual* price makes any model look compressed and is not used here.)

| Predicted-price decile (1 = lowest) | House | Unit | Vacant land | Acreage residence |
|---|---:|---:|---:|---:|
| 1 | 0.922 / 21.4% | 0.988 / 9.4% | 0.865 / 32.1% | 0.849 / 34.3% |
| 2 | 0.956 / 14.1% | 0.983 / 8.3% | 0.953 / 16.0% | 0.893 / 23.3% |
| 3 | 0.962 / 11.2% | 0.988 / 7.8% | 0.976 / 14.9% | 0.949 / 22.4% |
| 4 | 0.970 / 11.6% | 0.980 / 9.0% | 0.959 / 12.2% | 0.985 / 21.4% |
| 5 | 0.983 / 12.4% | 0.973 / 8.6% | 0.952 / 11.9% | 0.974 / 22.7% |
| 6 | 0.972 / 13.1% | 0.985 / 8.7% | 0.948 / 12.9% | 0.948 / 23.2% |
| 7 | 0.982 / 12.0% | 0.999 / 10.1% | 0.960 / 8.9% | 0.947 / 21.0% |
| 8 | 0.991 / 11.6% | 0.996 / 14.1% | 0.975 / 7.3% | 0.989 / 21.6% |
| 9 | 0.996 / 13.2% | 0.980 / 13.1% | 0.973 / 10.8% | 0.979 / 25.8% |
| 10 | 1.010 / 16.7% | 0.996 / 15.4% | 0.967 / 27.1% | 0.966 / 29.1% |

*Each cell: median predicted ÷ actual / typical error.*

A ratio below 1 means the prediction is typically below the actual price. Units are closest to unbiased (ratios between 0.97 and 1.00). Houses, vacant land and acreage are typically a few percent low through most of the range (mostly 0.95 to 1.00) and lowest in the cheapest predicted decile (0.85 to 0.92), where the error is also largest. Error is highest at both ends of the price range in every segment: the cheapest and the dearest properties differ in ways the data cannot see.

## 5. Which inputs the main models use most

Permutation importance on the validation year: the increase in log-price absolute error when one input is shuffled. Inputs that duplicate each other share credit, so read it as a ranking, not a split.

| Rank | House | Unit | Vacant land | Acreage residence |
|---|---:|---:|---:|---:|
| 1 | Loc_Mean12 (0.187) | Bld_Mean24 (0.115) | log_area (0.471) | Distance_CBD_KM (0.185) |
| 2 | log_area (0.095) | log_area (0.079) | Longitude (0.283) | Longitude (0.185) |
| 3 | Distance_CBD_KM (0.086) | Prev_Sale_Log (0.056) | Distance_CBD_KM (0.234) | Latitude (0.137) |
| 4 | Pc_Mean12 (0.074) | Distance_CBD_KM (0.047) | Latitude (0.212) | log_area (0.078) |
| 5 | Latitude (0.072) | Loc_Mean12 (0.037) | zone_code (0.115) | Pc_Mean12 (0.053) |
| 6 | Longitude (0.063) | Longitude (0.033) | Loc_Mean12 (0.091) | zone_code (0.028) |
| 7 | Prev_Adj (0.047) | Latitude (0.024) | Pc_Mean12 (0.080) | Prev_Sale_Log (0.020) |
| 8 | Prev_Sale_Log (0.021) | Prev_Adj (0.020) | Loc_N12 (0.043) | Prev_Adj (0.020) |

Time, month, market level, lot counts and the missing-value flags carry essentially no weight in any segment: the trailing locality price level already carries the market level.

Input names: `Loc_Mean12` the locality price level over the previous 12 months; `Pc_Mean12` the same at postcode level (a fallback); `Prev_Sale_Log` and `Prev_Adj` the previous sale of the same dwelling (and its value moved to the current market level); `Bld_Mean24` the price level of the same building over the previous 24 months; `log_area` the log of the dealing's area.

## 6. Counter-check: LightGBM and XGBoost

A separate, independent notebook re-fitted the current model and two alternatives under identical conditions (same inputs, split and scope), each alternative tuned on a small grid using the validation year only, with three random seeds where the training set exceeds the row cap. Random forest was deliberately not tried.

**Decision rule, fixed before any result:** a candidate replaces the current model for a segment only if (1) its validation error is lower, (2) its test error is lower by more than 0.5 percentage points, and (3) the paired bootstrap 95% interval of the test difference excludes zero. If nothing passes, the notebook is shelved.

| Test typical error (mean over seeds) | House | Unit | Vacant land | Acreage residence |
|---|---:|---:|---:|---:|
| Current model (scikit-learn boosting) | 13.44% | 10.04% | 13.91% | 23.97% |
| LightGBM | 13.34% | 9.93% | 14.09% | 24.41% |
| XGBoost | 13.54% | 9.88% | 14.97% | 24.90% |
| Blend of the three | 13.28% | 9.73% | 13.95% | 24.06% |

| Segment | Candidate | Validation difference (points) | Test difference (points) | Bootstrap 95% interval (test) | Passes the rule |
|---|---|---:|---:|---:|---:|
| House | LightGBM | -0.10 | -0.10 | [-0.20, -0.06] | no |
| House | XGBoost | +0.02 | +0.10 | [+0.06, +0.23] | no |
| House | Blend of the three | -0.18 | -0.17 | [-0.22, -0.12] | no |
| Unit | LightGBM | -0.12 | -0.11 | [-0.22, -0.05] | no |
| Unit | XGBoost | -0.19 | -0.17 | [-0.29, -0.11] | no |
| Unit | Blend of the three | -0.33 | -0.31 | [-0.41, -0.27] | no |
| Vacant land | LightGBM | -0.30 | +0.18 | [-0.20, +0.51] | no |
| Vacant land | XGBoost | +0.49 | +1.07 | [+0.72, +1.42] | no |
| Vacant land | Blend of the three | -0.63 | +0.04 | [-0.23, +0.29] | no |
| Acreage residence | LightGBM | -0.69 | +0.44 | [-0.04, +1.07] | no |
| Acreage residence | XGBoost | -0.40 | +0.94 | [+0.29, +1.50] | no |
| Acreage residence | Blend of the three | -0.67 | +0.09 | [-0.33, +0.54] | no |

- **Verdict: keep the current model in all four segments.** The counter-check is shelved.
- **The re-fitted current model reproduced the original scores to two decimal places** in every segment, which shows the features, split and scope are identical and the results are stable.
- **House and Unit show small, real gains** (the best is the three-model blend for units, 0.31 points) that are far below the 0.5-point margin and not worth maintaining three models for.
- **For Vacant land and Acreage the candidates looked better on validation and not on test.** This is why the test year is held out; those two segments have the smallest test sets (10,740 and 3,986 dealings).
- **XGBoost was clearly worse on Vacant land** (+1.07 points). One possible reason is that it reads the zoning code as an ordinal number while the others treat it as a category; this was not tested.
- **Tuning matters little.** For the Unit segment the eight tuned settings (four per library) differ by about 0.1 points in validation error.
- **This tests the model family and reproducibility, not leakage:** the same inputs and the same leakage rules were used.

## 7. Leakage audit

| Risk | Control | Evidence | Status |
|---|---|---|---|
| A feature built from the dealing's own price or from later sales | Price-history features use only sales settled in strictly earlier months; the dealing's own month never counts | Compared with a slow brute-force calculation on random data; a probe that edits one price confirmed nothing in that month or earlier changes | Controlled |
| A price-derived input (price per m²) | Never used as an input | By construction | Controlled |
| The same sale appearing in training and test | Re-published copies removed in extraction; one row per dealing; revision pairs and repeated lines excluded from scope | Row ledger and automated checks | Controlled |
| A multi-lot sale counted several times | Dealing is the unit; price per m² uses total price over total area | Dealing-key and price-per-m² checks | Controlled |
| Category lists learned from the test period | Zoning and LGA lists are learned from the training years only | By construction | Controlled |
| Model choice made on the test year | Trees and the main model chosen on 2024; the test refit uses the fixed tree count | By design | Controlled |
| The test year was seen during design | The history features were added after seeing the first run's results | None possible | **Residual risk:** final test figures are slightly flattering |
| The same properties on both sides of the split | Intended: a valuation model is used on properties it has seen. 34.2% of test houses and 87.6% of test units were already in the fit window | Accuracy for unseen properties is not reported separately | **Open:** not reported |
| Sales not yet published when valuing | Price levels assume last month's sales are known; the median publication delay is about a week, and 99.5% of sales are published within 60 days | Publication-lag analysis in the extraction | **Residual risk:** slightly optimistic |
| No grouped validation inside the training years | Planned, but not implemented; the headline numbers rely on the time-based split alone | n/a | **Not done** |
| Selection through the scope | Prices under $10,000 and over $50 million, bulk sales and revision pairs are excluded before modelling | Row ledger | **Limitation:** accuracy applies to in-scope sales |
| Independent reproduction | A separate notebook re-fitted the model and matched it to two decimals | Counter-check, section 6 | Shows determinism and code consistency; **not** proof of no leakage |

**Overall.** There is no sign of leakage by construction or by test, and no result looks too good to be true: the top input in every segment is the trailing price level of the neighbourhood or building, which is what one would expect. That is evidence of care, not proof. The residual risks above are the ones to keep in mind when quoting the results.

## 8. What is not shown

- Accuracy separately for properties and buildings seen before versus new ones.
- Prediction intervals (a range around each estimate).
- A repeat-sales price index, and macro-economic inputs such as the cash rate.
- Random forest, and any model family other than scikit-learn boosting, Ridge, LightGBM and XGBoost.
- The two descriptive segments (Farm or rural, Commercial or other), which mix very different property kinds.
