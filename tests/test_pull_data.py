"""Offline tests for the merge and the checks, on made-up values.

The HKMA XLS parser is tested by the live run: it asserts each column's header text
before reading it, and the content checks compare against values confirmed on HKMA's daily pages.
"""
import pandas as pd

import pull_data

HSI_DAYS = pd.to_datetime(["2015-01-02", "2025-04-03", "2025-04-07", "2025-05-06", "2025-05-07",
                           "2025-05-08", "2025-06-03", "2025-08-05"])


def make_series():
    days = pd.to_datetime(["2025-05-06", "2025-05-07", "2025-05-08", "2025-06-03"])
    return {
        "hsi_close": pd.Series([24000, 22800, 19800, 22600, 22700, 22750, 23500, 24900], index=HSI_DAYS),
        "hibor_1m": pd.Series([0.4, 1.5, 1.4, 1.2, 0.87], index=pd.to_datetime(["2015-01-02"]).append(days)),
        "usdhkd": pd.Series([7.7495, 7.75, 7.8535], index=days[:3]),  # just past the band, inside tolerance
        "agg_balance_hkd_mn": pd.Series([44_611, 161_313, 174_100], index=days[:3]),
        "sofr": pd.Series([4.3, 4.3], index=pd.to_datetime(["2025-05-06", "2025-05-09"])),  # 05-09 not an HK row
    }


def results(checks):
    return {name: ok for name, ok, _ in checks}


def test_build_panel_uses_hsi_days_without_filling():
    panel = pull_data.build_panel(make_series())
    assert panel.index.equals(pd.DatetimeIndex(HSI_DAYS, name="date"))
    assert pd.isna(panel.loc["2025-08-05", "hibor_1m"])  # HSI day with no fixing keeps its row
    assert panel["sofr"].notna().sum() == 1  # no forward-fill, US-only date dropped
    assert panel["usdhkd"].notna().sum() == 3


def test_checks_pass():
    series = make_series()
    panel = pull_data.build_panel(series)
    assert all(results(pull_data.structural_checks(panel, series)).values())
    assert all(results(pull_data.content_checks(panel)).values())


def test_checks_fail():
    series = make_series()
    series["hsi_close"] = series["hsi_close"].drop(pd.Timestamp("2015-01-02"))  # late start
    series["hsi_close"]["2025-05-06"] = 10_000  # largest fall now on the wrong day
    series["hibor_1m"] = series["hibor_1m"] + 1  # no sub-1% HIBOR
    series["usdhkd"] = pd.Series([7.86], index=pd.to_datetime(["2025-05-06"]))
    series["agg_balance_hkd_mn"] = series["agg_balance_hkd_mn"] * 2
    series["sofr"] = pd.Series([4.3, 4.3], index=pd.to_datetime(["2025-05-06", "2025-05-06"]))
    series["honia"] = pd.Series([0.1], index=pd.to_datetime(["2025-05-10"]))  # no HK row, so empty in panel
    panel = pull_data.build_panel(series)
    assert not any(results(pull_data.structural_checks(panel, series)).values())
    assert not any(results(pull_data.content_checks(panel)).values())
    detail = dict((name, d) for name, _, d in pull_data.content_checks(panel))["USD/HKD within 7.75 to 7.85, tolerance 0.005"]
    assert "2025-05-06 7.8600" in detail
