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
    res, d, lags = analysis.fit(v, "2015-01-01", None)
    X = np.column_stack([np.ones(len(d))] + [d[k] for k in analysis.TERMS])
    ols = np.linalg.lstsq(X, d["ds"].to_numpy(), rcond=None)[0]
    assert np.allclose(res.params.to_numpy(), ols)  # same point estimates as plain least squares
    for k, b in beta.items():
        assert res.params[k] == pytest.approx(b, abs=0.1)
    assert lags == int(np.floor(4 * (n / 100) ** (2 / 9)))
