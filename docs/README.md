# As-of price-history features

The two functions in `price_history_features.py` are the part of this project most open to doubt: they build model inputs from price history **without letting a dealing see its own price or any later sale**.

**The rule:** a dealing's features use only sales settled in *strictly earlier months*. Sales in the dealing's own month never count.

| Function | What it returns |
|---|---|
| `asof(d, key, window, min_n, n_months)` | the trailing mean log price of a locality, postcode, building or whole segment over the previous `window` months, and the count behind it (NaN below `min_n` sales, never imputed) |
| `prev_sale(d)` | for each dealing, the log price of the most recent earlier-month sale of the same dwelling, the months since it, that price moved to the current market level, and the number of earlier sales |

## Check them

```
pip install numpy pandas pytest
cd code
pytest -q
```

15 tests, all on synthetic data (no sales files needed). They compare both functions with slow brute-force versions, and run a **leakage probe**: edit one price in month 20 and confirm that nothing for any dealing in month 20 or earlier changes while later months do. They also check that results do not depend on row order, and that missing keys, out-of-range months and an invalid window are handled.

## What this proves, and what it does not

It shows that these two functions do what the documentation says. It does **not** show that the whole pipeline is free of leakage (the split, the de-duplication and the scope rules are separate); that argument is in [`docs/model_evaluation.md`](../docs/model_evaluation.md), section 7.
