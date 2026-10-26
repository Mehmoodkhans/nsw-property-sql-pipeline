"""
As-of price-history features for the NSW property price model.

These two functions are the leakage-critical part of the pipeline: they turn the price history
of a locality, a building or a dwelling into model inputs WITHOUT ever letting a dealing see
its own price or any later sale.

The rule, in one sentence: a dealing's features use only sales settled in STRICTLY EARLIER
MONTHS. Sales in the dealing's own month never count, even if they were settled earlier in
that month.

Conventions
-----------
* `m_idx`  integer month index (0 = the first month of the data); the only notion of time used.
* `y`      log price of the dealing.
* A dealing is identified by a `Dwelling_Key` (for strata: building + lot number).

Both functions were checked against slow brute-force implementations and with a leakage probe
(see test_price_history_features.py).
"""
import numpy as np
import pandas as pd


def asof(d, key, window, min_n, n_months):
    """Trailing mean of log price over the months [m - window, m - 1] for each dealing's key.

    Parameters
    ----------
    d : DataFrame with integer column `m_idx` (0 <= m_idx < n_months) and float column `y`.
    key : array-like of group labels, one per row (a locality, a postcode, a building, or one
          constant for a market-wide level). Missing labels give NaN.
    window : number of earlier months to look back.
    min_n : minimum number of earlier sales in the window; below it the value is NaN
            (missing, never imputed).
    n_months : total number of months in the data.

    Returns
    -------
    mean : float array, the trailing mean log price (NaN when fewer than `min_n` earlier sales).
    count : float array, the number of earlier sales that fell in the window.
    """
    if window < 1:
        raise ValueError("window must be at least 1")
    m = d["m_idx"].to_numpy()
    y = d["y"].to_numpy(dtype=float)
    if len(m) and (m.min() < 0 or m.max() >= n_months):
        raise ValueError("m_idx must lie in [0, n_months)")
    codes, uniq = pd.factorize(pd.Series(key).reset_index(drop=True), sort=False)     # accepts a list, array or Series
    codes = np.asarray(codes)
    ok = codes >= 0
    S = np.zeros((len(uniq), n_months))
    N = np.zeros_like(S)
    np.add.at(S, (codes[ok], m[ok]), y[ok])
    np.add.at(N, (codes[ok], m[ok]), 1.0)

    def window_sum(cum):
        # sum over months [m - window, m - 1] = cum[m - 1] - cum[m - window - 1]
        up_to_prev = np.zeros_like(cum)
        up_to_prev[:, 1:] = cum[:, :-1]
        before_window = np.zeros_like(cum)
        before_window[:, window + 1:] = cum[:, :-(window + 1)]
        return up_to_prev - before_window

    wS, wN = window_sum(S.cumsum(1)), window_sum(N.cumsum(1))
    mean = np.where(wN >= min_n, wS / np.maximum(wN, 1.0), np.nan)
    out_mean, out_n = np.full(len(d), np.nan), np.zeros(len(d))
    out_mean[ok], out_n[ok] = mean[codes[ok], m[ok]], wN[codes[ok], m[ok]]
    return out_mean, out_n


def prev_sale(d):
    """For each dealing, the most recent EARLIER-MONTH sale of the same dwelling.

    Parameters
    ----------
    d : DataFrame with columns `Dwelling_Key`, `m_idx` (int), `y` (log price) and
        `Mkt_Index` (an as-of market level in log price, NaN allowed).

    Returns
    -------
    prev_log_price : log price of that earlier sale (NaN if the dwelling has none).
    months_since : months between that sale and this one.
    market_adjusted : prev_log_price moved to today's market level,
                      prev_log_price + (Mkt_Index now - Mkt_Index then); NaN if either level is missing.
    n_earlier : number of earlier-month sales of the dwelling.

    Sales in the same month as the dealing are skipped, so a dealing never sees its own month.
    """
    key = d["Dwelling_Key"].to_numpy()
    m = d["m_idx"].to_numpy()
    y = d["y"].to_numpy(dtype=float)
    mk = d["Mkt_Index"].to_numpy(dtype=float)
    order = np.lexsort((m, key))                       # sort by dwelling, then month
    k, mm, yy, kk = key[order], m[order], y[order], mk[order]
    n = len(d)
    cand = np.arange(n) - 1                            # the previous row in sorted order

    def state(c):
        ca = np.where(c >= 0, c, 0)
        return ca, (c >= 0) & (k[ca] == k)             # still the same dwelling?

    ca, same = state(cand)
    for _ in range(50):                                # step back past sales in the SAME month
        same_month = same & (mm[ca] == mm)
        if not same_month.any():
            break
        cand = np.where(same_month, cand - 1, cand)
        ca, same = state(cand)
    ok = same & (mm[ca] < mm)                          # only strictly earlier months count
    prev_y = np.where(ok, yy[ca], np.nan)
    prev_m = np.where(ok, mm - mm[ca], np.nan)
    adj = np.where(ok & np.isfinite(kk) & np.isfinite(kk[ca]), yy[ca] + (kk - kk[ca]), np.nan)
    n_prev = pd.Series(mm).groupby(k).rank(method="min").to_numpy() - 1.0   # rank of the month within the dwelling, minus 1
    out = [np.empty(n) for _ in range(4)]
    for arr, val in zip(out, (prev_y, prev_m, adj, n_prev)):
        arr[order] = val
    return tuple(out)
