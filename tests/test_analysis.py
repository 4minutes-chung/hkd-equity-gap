"""Tests for the analysis variables and the regression, on made-up values."""
import numpy as np
import pandas as pd
import pytest

import analysis


def toy_panel():
    idx = pd.date_range("2020-01-01", periods=6, freq="B", name="date")
    return pd.DataFrame({
        "usdhkd": [7.80, 7.81, 7.79, 7.85, 7.75, 7.78],
        "hsi_close": [100.0, 110.0, 99.0, 99.0, 108.9, 108.9],
        "ust_1m": [2.0, np.nan, np.nan, np.nan, np.nan, 3.0],  # 4-row US gap: only 3 rows get filled
        "hibor_1m": [1.0, 1.5, 1.0, 1.0, 1.0, 1.0],
    }, index=idx)


def test_gap_fill_limit_and_lag():
    p = toy_panel()
    g = analysis.gap(p, "ust_1m", "hibor_1m")
    assert g.tolist()[:4] == [1.0, 0.5, 1.0, 1.0]  # 2.0 carried 3 rows
    assert np.isnan(g.iloc[4])  # 4th missing row stays missing
    v = analysis.build_vars(p, "ust_1m", "hibor_1m")
    assert np.isnan(v["gap_lag"].iloc[0])
    assert v["gap_lag"].iloc[2] == g.iloc[1]  # gap_{t-1} is the previous row's gap


def test_ds_r_band_and_interactions():
    v = analysis.build_vars(toy_panel(), "ust_1m", "hibor_1m")
    assert v["ds"].iloc[1] == pytest.approx(100.0)  # 7.80 -> 7.81 is 100 pips
    assert v["r"].iloc[1] == pytest.approx(100 * np.log(1.1))
    assert v["band_lag"].iloc[1] == pytest.approx(0.5)  # 7.80 sits mid-band
    assert v["band_lag"].iloc[4] == pytest.approx(1.0)  # previous row at 7.85
    assert v["r_x_gap"].iloc[2] == pytest.approx(v["r"].iloc[2] * v["gap_lag"].iloc[2])
    assert v["r_x_band"].iloc[3] == pytest.approx(v["r"].iloc[3] * v["band_lag"].iloc[3])


def test_fit_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    n = 3000
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    v = pd.DataFrame({"r": rng.normal(0, 1, n), "gap_lag": rng.uniform(-1, 4, n),
                      "band_lag": rng.uniform(0, 1, n)}, index=idx)
    v["r_x_gap"], v["r_x_band"] = v["r"] * v["gap_lag"], v["r"] * v["band_lag"]
    beta = {"r": -3.0, "gap_lag": 0.5, "r_x_gap": -1.0, "band_lag": 2.0, "r_x_band": 1.5}
    v["ds"] = 0.2 + sum(b * v[k] for k, b in beta.items()) + rng.normal(0, 0.5, n)
    v.iloc[1000:1500] = np.nan  # a 500-day hole: lags and HAC must still count calendar days
    res, d, lags = analysis.fit(v, "2015-01-01", None)
    assert len(d) == n - 500
    assert lags == int(np.floor(4 * (n / 100) ** (2 / 9)))  # from the calendar span, not len(d)
    for k, b in beta.items():
        assert res.params[k] == pytest.approx(b, abs=0.1)
    # benchmark: hand-built Newey-West with the hole kept as zero rows
    X = np.column_stack([np.ones(len(d))] + [d[k] for k in analysis.TERMS])
    u = d["ds"].to_numpy() - X @ res.params.to_numpy()
    S = np.zeros((n, X.shape[1]))
    S[v.index.get_indexer(d.index)] = X * u[:, None]
    meat = S.T @ S
    for lag in range(1, lags + 1):
        g = S[lag:].T @ S[:-lag]
        meat += (1 - lag / (lags + 1)) * (g + g.T)
    bread = np.linalg.inv(X.T @ X)
    assert np.allclose(res.bse.to_numpy(), np.sqrt(np.diag(bread @ meat @ bread)))


def synthetic(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    v = pd.DataFrame({"r": rng.normal(0, 1, n), "gap_lag": np.cumsum(rng.normal(0, 0.05, n)),
                      "band_lag": rng.uniform(0, 1, n)}, index=pd.date_range("2015-01-01", periods=n, freq="B"))
    v["r_x_gap"], v["r_x_band"] = v["r"] * v["gap_lag"], v["r"] * v["band_lag"]
    v["ds"] = -3 * v["r"] + 2 * v["r_x_gap"] + rng.normal(0, 1, n)
    return v


def test_implied_slopes_match_manual_delta_method():
    res, d, _ = analysis.fit(synthetic(), "2015-01-01", None)
    names, V = list(res.params.index), res.cov_params().to_numpy()
    for q, g, s, lo, hi, p in analysis.implied_slopes(res, d):
        R = np.zeros(len(names))
        R[names.index("r")], R[names.index("r_x_gap")], R[names.index("r_x_band")] = 1, g, d["band_lag"].mean()
        assert s == pytest.approx(R @ res.params.to_numpy())
        assert (hi - lo) / 2 == pytest.approx(1.959964 * np.sqrt(R @ V @ R), rel=1e-4)


def test_bootstrap_and_placebo_are_reproducible_and_centred():
    d = synthetic().dropna()
    bs = analysis.block_bootstrap(d, 60, reps=200)
    assert np.array_equal(bs, analysis.block_bootstrap(d, 60, reps=200))  # fixed seed
    assert abs(np.median(bs) - 2) < 0.3  # centred near the true r x gap coefficient
    pl = analysis.placebo_gap(d, L=100, reps=200)
    assert abs(np.median(pl)) < 0.5  # shuffled gap has no effect
