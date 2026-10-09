"""Rolling equity/FX correlation against the 1M rate gap, and the interaction regression.

Reads data/clean/panel.parquet (built by pull_data.py) and writes
  output/fig_rolling_corr_gap.png
  output/regression_table.md and output/regression_table.csv
  output/sensitivity.md (main-gap regression re-run on alternative samples)

Variables (t = HSI trading day, t-1 = previous panel row):
  ds_t    = (USD/HKD_t - USD/HKD_{t-1}) x 10,000, in pips; positive = HKD weaker
  r_t     = 100 x ln(HSI_t / HSI_{t-1}), in percent
  gap_t   = USD rate - HK rate, in percentage points; positive = USD rate above HIBOR
  band_t  = (USD/HKD_t - 7.75) / 0.10; 0 = strong side, 1 = weak side (not clipped)
Regression: ds_t on r_t, gap_{t-1}, r_t x gap_{t-1}, band_{t-1}, r_t x band_{t-1}, Newey-West SEs with lags
counted in trading days, so rows dropped for missing data leave gaps instead of becoming neighbours.
US rates are carried forward at most US_FILL rows onto HK days (US holidays); the panel itself stays unfilled.
Results are associations, not causal effects.

Run with conda base:  python analysis.py
"""
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import statsmodels.api as sm

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent
PANEL, OUT = ROOT / "data" / "clean" / "panel.parquet", ROOT / "output"
END = "2026-09-30"  # last date of the HKMA bulletin files
US_FILL = 3  # max rows a US rate is carried onto HK days
WINDOW = 60  # rolling correlation window, in trading days with both series present
TERMS = ["r", "gap_lag", "r_x_gap", "band_lag", "r_x_band"]
LABELS = {"const": "Constant", "r": "HSI return r_t (%)", "gap_lag": "Gap_{t-1} (pp)",
          "r_x_gap": "r_t x Gap_{t-1}", "band_lag": "Band_{t-1} (0 = 7.75, 1 = 7.85)",
          "r_x_band": "r_t x Band_{t-1}"}
# column label: (USD rate, HK rate, sample start)
SPECS = {
    "(1) UST 1M - HIBOR 1M": ("ust_1m", "hibor_1m", "2015-01-01"),
    "(2) UST 1M - HIBOR 1M, from 2018-04": ("ust_1m", "hibor_1m", "2018-04-03"),
    "(3) SOFR - HONIA, from 2018-04": ("sofr", "honia", "2018-04-03"),
    "(4) CP 1M - HIBOR 1M (CP sparse after 2020)": ("cp_1m_usd", "hibor_1m", "2015-01-01"),
}
INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a63", "#e4e3dd", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def gap(panel, usd_col, hk_col):
    """USD rate minus HK rate, US rate carried at most US_FILL rows onto HK days."""
    return panel[usd_col].ffill(limit=US_FILL) - panel[hk_col]


def build_vars(panel, usd_col, hk_col):
    """Regression variables on the panel's rows; differences and lags are over consecutive rows."""
    v = pd.DataFrame(index=panel.index)
    v["ds"] = panel["usdhkd"].diff() * 10_000
    v["r"] = 100 * np.log(panel["hsi_close"]).diff()
    v["gap_lag"] = gap(panel, usd_col, hk_col).shift(1)
    v["band_lag"] = ((panel["usdhkd"] - 7.75) / 0.10).shift(1)
    v["r_x_gap"] = v["r"] * v["gap_lag"]
    v["r_x_band"] = v["r"] * v["band_lag"]
    return v


def fit(v, start, end=END, terms=TERMS):
    """OLS with Newey-West SEs on the trading-day calendar of v (hac-groupsum with each row's position as its
    time label, no small-sample correction: identical to plain HAC when no rows are missing). Lag length from
    the 4(T/100)^(2/9) rule, T = calendar days spanned. Returns (result, data used, lags)."""
    d = v.loc[start:end, ["ds"] + terms].dropna()
    pos = v.index.get_indexer(d.index)
    pos = pos - pos.min()
    lags = int(np.floor(4 * ((pos.max() + 1) / 100) ** (2 / 9)))
    res = sm.OLS(d["ds"], sm.add_constant(d[terms])).fit(
        cov_type="hac-groupsum", cov_kwds={"time": pos, "maxlags": lags, "use_correction": False})
    return res, d, lags


def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def regression_table(panel):
    """Fit every column in SPECS. Returns (markdown text, long-format DataFrame)."""
    cols, rows = {}, []
    for name, (usd_col, hk_col, start) in SPECS.items():
        res, d, lags = fit(build_vars(panel, usd_col, hk_col), start)
        cell = {LABELS[k]: f"{res.params[k]:.3f}{stars(res.pvalues[k])} ({res.bse[k]:.3f})"
                for k in ["r", "gap_lag", "r_x_gap", "band_lag", "r_x_band", "const"]}
        band_mean, pct = d["band_lag"].mean(), d["gap_lag"].quantile([0.1, 0.5, 0.9])
        slope = [res.params["r"] + res.params["r_x_gap"] * g + res.params["r_x_band"] * band_mean for g in pct]
        cell.update({
            "Gap_{t-1} at p10 / p50 / p90 (pp)": " / ".join(f"{g:.2f}" for g in pct),
            "Slope of ds on r at mean band, gap p10 / p50 / p90": " / ".join(f"{s:.3f}" for s in slope),
            "N": f"{int(res.nobs):,}", "R-squared": f"{res.rsquared:.3f}", "Newey-West lags": str(lags),
            "corr(Gap_{t-1}, Band_{t-1})": f"{d['gap_lag'].corr(d['band_lag']):.2f}",
            "Sample": f"{d.index.min():%Y-%m-%d} to {d.index.max():%Y-%m-%d}",
        })
        cols[name] = cell
        rows += [{"column": name, "term": k, "coef": res.params[k], "se": res.bse[k], "p": res.pvalues[k],
                  "nobs": int(res.nobs), "r2": res.rsquared} for k in res.params.index]
    table = pd.DataFrame(cols)
    md = "| | " + " | ".join(table.columns) + " |\n|---|" + "---|" * len(table.columns) + "\n"
    md += "\n".join(f"| {idx} | " + " | ".join(table.loc[idx]) + " |" for idx in table.index)
    md += ("\n\nDependent variable: daily change in USD/HKD in pips (positive = HKD weaker). "
           "Newey-West standard errors in parentheses. *** p<0.01, ** p<0.05, * p<0.1. "
           "A negative slope of ds on r means HSI up goes with HKD stronger; stronger co-movement = more negative. "
           "Associations, not causal effects.\n")
    return md, pd.DataFrame(rows)


def blank(v, rows):
    """Copy of v with the given rows set to NaN (kept on the calendar, so lags still count trading days)."""
    out = v.copy()
    out.loc[rows] = np.nan
    return out


def sensitivity(panel):
    """Column (1) re-run on alternative samples. Dropped days are blanked, not deleted, so the
    Newey-West lags still count trading days. Returns markdown text."""
    v = build_vars(panel, "ust_1m", "hibor_1m")
    w = v.copy()
    lo, hi = v.loc[:END, ["ds"] + TERMS].dropna()["r"].quantile([0.01, 0.99])  # cut-offs from the regression sample
    w["r"] = w["r"].clip(lo, hi)
    w["r_x_gap"], w["r_x_band"] = w["r"] * w["gap_lag"], w["r"] * w["band_lag"]
    runs = [
        ("Baseline, column (1)", v, END, TERMS),
        ("Ends 2024-12-31 (drops 2025 to 2026)", v, "2024-12-31", TERMS),
        ("Drops 2025-05-01 to 2025-08-31 (largest gap spike)", blank(v, v.loc["2025-05-01":"2025-08-31"].index), END, TERMS),
        ("Drops days with HSI move above 5%", blank(v, v.index[v["r"].abs() > 5]), END, TERMS),
        ("HSI return capped at its 1st and 99th percentiles", w, END, TERMS),
        ("Without the band terms", v, END, ["r", "gap_lag", "r_x_gap"]),
        ("Drops days after USD/HKD within 50 pips of 7.75 or 7.85 (Band_{t-1} below 0.05 or above 0.95)",
         blank(v, v.index[(v["band_lag"] < 0.05) | (v["band_lag"] > 0.95)]), END, TERMS),
    ]
    md = "| Sample | N | r_t (p) | r_t x Gap_{t-1} (p) | r_t x Band_{t-1} (p) |\n|---|---|---|---|---|\n"
    for name, data, end, terms in runs:
        res, _, _ = fit(data, "2015-01-01", end, terms)
        cell = [f"{res.params[k]:.3f} ({res.pvalues[k]:.3f})" if k in terms else "n/a" for k in ("r", "r_x_gap", "r_x_band")]
        md += f"| {name} | {int(res.nobs):,} | " + " | ".join(cell) + " |\n"
    return md + "\nMain gap (UST 1M minus HIBOR 1M). Newey-West p-values in parentheses.\n"


def rolling_corr(panel):
    """60-day rolling corr(r, ds) on rows where both exist, and the main gap, both up to END."""
    v = build_vars(panel, "ust_1m", "hibor_1m").loc[:END]
    pair = v[["r", "ds"]].dropna()
    rc = pair["r"].rolling(WINDOW, min_periods=WINDOW).corr(pair["ds"])
    return rc, gap(panel, "ust_1m", "hibor_1m").loc[:END]


def plot(rc, g, path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, facecolor=SURFACE,
                                   gridspec_kw={"height_ratios": [1, 1], "hspace": 0.35})
    for ax, s, color, title in [
        (ax1, rc, BLUE, "Rolling 60-day correlation: HSI daily return vs USD/HKD daily change"),
        (ax2, g, ORANGE, "1M rate gap: US Treasury 1M minus HIBOR 1M (percentage points)"),
    ]:
        ax.set_facecolor(SURFACE)
        ax.plot(s.index, s.values, color=color, linewidth=1.6)
        ax.axhline(0, color=MUTED, linewidth=0.8)
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.tick_params(colors=MUTED, labelsize=9)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
    fig.text(0.01, 0.005, "Below zero: HSI up goes with HKD stronger (USD/HKD down); more negative = stronger "
             "co-movement. Sources: HKMA, Yahoo Finance (^HSI), FRED (DGS1MO). Daily, 2015-01 to 2026-09.",
             fontsize=8, color=MUTED)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    panel = pd.read_parquet(PANEL)
    md, long = regression_table(panel)
    (OUT / "regression_table.md").write_text(md)
    long.to_csv(OUT / "regression_table.csv", index=False)
    sens = sensitivity(panel)
    (OUT / "sensitivity.md").write_text(sens)
    rc, g = rolling_corr(panel)
    plot(rc, g, OUT / "fig_rolling_corr_gap.png")
    print(md)
    print(sens)
    print(f"Rolling corr: {rc.notna().sum()} days, mean {rc.mean():.3f}, min {rc.min():.3f}, max {rc.max():.3f}; "
          f"corr(rolling corr, gap) = {rc.corr(g.reindex(rc.index)):.3f}")
    print("Wrote output/regression_table.md, output/regression_table.csv, output/sensitivity.md, "
          "output/fig_rolling_corr_gap.png")


if __name__ == "__main__":
    main()
