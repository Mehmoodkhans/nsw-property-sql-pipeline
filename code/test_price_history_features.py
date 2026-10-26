"""
Tests for price_history_features.py. Run with:   pytest -q

All data is synthetic: nothing here needs the NSW sales files.
Strategy: compare each function with a slow, obviously-correct brute-force version, then probe for
leakage by editing one price and checking that no dealing in the same or an earlier month changes.
"""
import numpy as np
import pandas as pd
import pytest

from price_history_features import asof, prev_sale

N_MONTHS = 40


def make_asof_frame(n=3000, n_keys=12, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"m_idx": rng.integers(0, N_MONTHS, n), "y": rng.normal(13, 0.5, n), "key": rng.integers(0, n_keys, n)})


def make_dwelling_frame(n=4000, n_dwellings=500, seed=3):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"Dwelling_Key": rng.integers(0, n_dwellings, n), "m_idx": rng.integers(0, N_MONTHS, n), "y": rng.normal(13, 0.5, n)})
    d["Mkt_Index"] = 13 + 0.01 * d["m_idx"] + rng.normal(0, 0.02, n)
    d.loc[rng.choice(n, 150, replace=False), "Mkt_Index"] = np.nan          # some market levels missing
    return d


# ----------------------------------------------------------------------------- asof

@pytest.mark.parametrize("window,min_n", [(12, 5), (3, 30), (12, 1), (24, 2)])
def test_asof_matches_brute_force(window, min_n):
    d = make_asof_frame()
    mean, count = asof(d, d["key"], window, min_n, N_MONTHS)
    bf_mean, bf_count = np.full(len(d), np.nan), np.zeros(len(d))
    for i, (m, k) in enumerate(zip(d["m_idx"], d["key"])):
        earlier = d[(d["key"] == k) & (d["m_idx"] >= m - window) & (d["m_idx"] <= m - 1)]     # strictly earlier months only
        bf_count[i] = len(earlier)
        if len(earlier) >= min_n:
            bf_mean[i] = earlier["y"].mean()
    assert np.allclose(count, bf_count)
    assert np.allclose(np.nan_to_num(mean, nan=-9), np.nan_to_num(bf_mean, nan=-9))


def test_asof_never_sees_its_own_month():
    # one key; sales in months 5 (three of them), 6, 15, 20 and 35
    d = pd.DataFrame({"m_idx": [5, 5, 5, 6, 15, 20, 35], "y": [12.0, 13.0, 14.0, 99.0, 99.0, 99.0, 99.0]})
    mean, count = asof(d, np.zeros(len(d), dtype=int), window=12, min_n=1, n_months=N_MONTHS)
    assert np.isnan(mean[:3]).all() and (count[:3] == 0).all()            # the three month-5 sales do not see each other
    assert mean[3] == pytest.approx(13.0) and count[3] == 3               # month 6 sees all three, and only those
    assert mean[4] == pytest.approx((12 + 13 + 14 + 99) / 4) and count[4] == 4     # month 15: window is months 3 to 14, so all four earlier sales
    assert mean[5] == pytest.approx(99.0) and count[5] == 1               # month 20: window is months 8 to 19, which holds only the month-15 sale
    assert np.isnan(mean[6]) and count[6] == 0                            # month 35: window is months 23 to 34, which holds nothing


def test_asof_window_drops_old_sales():
    d = pd.DataFrame({"m_idx": [1, 30], "y": [10.0, 20.0]})
    mean, count = asof(d, np.zeros(2, dtype=int), window=12, min_n=1, n_months=N_MONTHS)
    assert np.isnan(mean[1]) and count[1] == 0                            # month 1 is outside [18, 29]


def test_asof_leakage_probe():
    d = make_asof_frame(seed=7)
    before, _ = asof(d, d["key"], 12, 5, N_MONTHS)
    edited = d.copy()
    i = int(edited.index[edited["m_idx"] == 20][0])
    edited.loc[i, "y"] += 5.0                                              # change ONE price in month 20
    after, _ = asof(edited, edited["key"], 12, 5, N_MONTHS)
    unaffected = (d["m_idx"] <= 20).to_numpy()                              # same month or earlier
    assert np.allclose(np.nan_to_num(before[unaffected]), np.nan_to_num(after[unaffected]))
    assert (np.abs(np.nan_to_num(before[~unaffected]) - np.nan_to_num(after[~unaffected])) > 0).any()   # later months do change


def test_asof_missing_key_gives_nan():
    d = pd.DataFrame({"m_idx": [1, 2, 3], "y": [10.0, 11.0, 12.0]})
    mean, count = asof(d, [None, None, None], window=12, min_n=1, n_months=N_MONTHS)
    assert np.isnan(mean).all() and (count == 0).all()


def test_asof_independent_of_row_order():
    d = make_asof_frame(seed=11)
    a, _ = asof(d, d["key"], 12, 5, N_MONTHS)
    perm = np.random.default_rng(0).permutation(len(d))
    shuffled = d.iloc[perm].reset_index(drop=True)
    b, _ = asof(shuffled, shuffled["key"], 12, 5, N_MONTHS)
    unshuffled = np.empty_like(b); unshuffled[perm] = b
    assert np.allclose(np.nan_to_num(a, nan=-9), np.nan_to_num(unshuffled, nan=-9))


def test_asof_rejects_bad_input():
    d = pd.DataFrame({"m_idx": [0, 1, N_MONTHS], "y": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError):
        asof(d, np.zeros(3, dtype=int), 12, 1, N_MONTHS)                   # month index out of range
    with pytest.raises(ValueError):
        asof(d.iloc[:2], np.zeros(2, dtype=int), 0, 1, N_MONTHS)           # window must be positive


# ----------------------------------------------------------------------------- prev_sale

def brute_force_prev(d):
    n = len(d)
    months, count = np.full(n, np.nan), np.zeros(n)
    for i, (k, m) in enumerate(zip(d["Dwelling_Key"], d["m_idx"])):
        earlier = d[(d["Dwelling_Key"] == k) & (d["m_idx"] < m)]            # strictly earlier MONTH
        count[i] = len(earlier)
        if len(earlier):
            months[i] = m - earlier["m_idx"].max()
    return months, count


def test_prev_sale_matches_brute_force():
    d = make_dwelling_frame()
    prev_y, prev_m, adj, n_prev = prev_sale(d)
    months, count = brute_force_prev(d)
    assert np.allclose(np.nan_to_num(prev_m, nan=-1), np.nan_to_num(months, nan=-1))
    assert np.allclose(n_prev, count)


def test_prev_sale_price_is_a_real_earlier_sale_and_adjustment_is_correct():
    d = make_dwelling_frame(seed=5)
    prev_y, prev_m, adj, _ = prev_sale(d)
    for i in np.flatnonzero(np.isfinite(prev_y)):
        pool = d[(d["Dwelling_Key"] == d["Dwelling_Key"].iloc[i]) & (d["m_idx"] == d["m_idx"].iloc[i] - prev_m[i])]
        assert np.isclose(pool["y"], prev_y[i]).any()                       # it is a genuine sale of the same dwelling, that many months earlier
        if np.isfinite(adj[i]):
            expected = [prev_y[i] + d["Mkt_Index"].iloc[i] - mk for mk in pool["Mkt_Index"] if np.isfinite(mk)]
            assert any(np.isclose(adj[i], e) for e in expected)             # prev price + (market now - market then)


def test_prev_sale_same_month_sales_do_not_count():
    # dwelling 1: two sales in month 10, one in month 12
    d = pd.DataFrame({"Dwelling_Key": [1, 1, 1], "m_idx": [10, 10, 12], "y": [12.0, 13.0, 14.0], "Mkt_Index": [13.0, 13.0, 13.5]})
    prev_y, prev_m, adj, n_prev = prev_sale(d)
    assert np.isnan(prev_y[0]) and np.isnan(prev_y[1])                      # the two month-10 sales never see each other
    assert (n_prev[:2] == 0).all()
    assert prev_m[2] == 2 and n_prev[2] == 2                                # month 12 sees both, 2 months earlier
    assert prev_y[2] in (12.0, 13.0)
    assert adj[2] == pytest.approx(prev_y[2] + 13.5 - 13.0)


def test_prev_sale_leakage_probe():
    d = make_dwelling_frame(seed=9)
    before = prev_sale(d)
    edited = d.copy()
    i = int(edited.index[edited["m_idx"] == 20][0])
    edited.loc[i, "y"] += 5.0
    after = prev_sale(edited)
    unaffected = (d["m_idx"] <= 20).to_numpy()
    for b, a in zip(before, after):
        assert np.allclose(np.nan_to_num(b[unaffected]), np.nan_to_num(a[unaffected]))


def _unperm(x, perm):
    out = np.empty_like(x)
    out[perm] = x
    return out


def test_prev_sale_independent_of_row_order():
    d = make_dwelling_frame(seed=13)
    a = prev_sale(d)
    perm = np.random.default_rng(1).permutation(len(d))
    b = prev_sale(d.iloc[perm].reset_index(drop=True))
    # months-since and the count of earlier sales must not depend on row order. (The previous PRICE can legitimately differ when
    # several earlier sales of one dwelling share the same month: any of them is a valid answer, so it is not compared here.)
    assert np.allclose(np.nan_to_num(a[1], nan=-1), np.nan_to_num(_unperm(b[1], perm), nan=-1))
    assert np.allclose(a[3], _unperm(b[3], perm))
