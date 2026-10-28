# Superseded: first-version SQL pipeline

This folder holds the **first version** of the project, kept for the record: a DuckDB SQL pipeline (Stages 00 to 13) over a merged CSV of 1,697,724 rows, covering 2018 to 2025.

| Folder | Content |
|---|---|
| [`notebooks/`](notebooks/) | the SQL pipeline notebook |
| [`Visual/`](Visual/) | its 23 charts |
| [`presentation/`](presentation/) | its case-study page |

**It should not be used for results.** Rebuilding the analysis from the raw archive showed that several of its foundations did not hold: area was assumed to be in square metres when 6.9% of rows are in hectares, the 2023 "gap" was dates lost in the earlier extraction, each row was treated as a sale although one sale can span several lots, postcode-level area labels were used as if they described the locality, and its model scores came from a split that is not comparable with the time-based validation now used.

Its headline findings (for example the Metro versus Very Remote price-per-m² ratio and the LGA rankings) are **retired**. The current method and results are in the [main README](../README.md) and in [`docs/`](../docs/).
