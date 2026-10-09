"""Rolling equity/FX correlation against the 1M rate gap, and the interaction regression.

Reads data/clean/panel.parquet (built by pull_data.py) and writes
  output/fig_rolling_corr_gap.png
  output/regression_table.md and output/regression_table.csv
  output/sensitivity.md (main-gap regression re-run on alternative samples)
  output/robustness.md (year-specific slopes, slope CIs, leave-one-year-out, block bootstrap, placebo)

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


def implied_slopes(res, d):
    """Slope of ds on r at the mean band and gap p10 / p50 / p90, with Newey-West 95% CIs."""
    names, band_mean, out = list(res.params.index), d["band_lag"].mean(), []
    for q, g in d["gap_lag"].quantile([0.1, 0.5, 0.9]).items():
        R = np.zeros(len(names))
        R[names.index("r")], R[names.index("r_x_gap")], R[names.index("r_x_band")] = 1, g, band_mean
        t = res.t_test(R)
        lo, hi = t.conf_int()[0]
        out.append((q, g, float(np.squeeze(t.effect)), lo, hi, float(np.squeeze(t.pvalue))))
    return out


def with_extra(v, kind, start="2015-01-01", end=END):
    """v plus extra regressors: per-year HSI slopes, one 2025-26 slope, or lagged HSI volatility."""
    w, years, extra = v.copy(), v.index.year, []
    if kind == "years":
        in_sample = v.loc[start:end, ["ds"] + TERMS].dropna().index.year  # years fit() will actually use
        for y in sorted(set(in_sample))[1:]:  # first in-sample year is the base, so dummies never span the constant
            w[f"y{y}"] = (years == y).astype(float)
            w[f"r_x_y{y}"] = w["r"] * w[f"y{y}"]
            extra += [f"y{y}", f"r_x_y{y}"]
    elif kind == "2025on":
        w["y2025on"] = (years >= 2025).astype(float)
        w["r_x_y2025on"] = w["r"] * w["y2025on"]
        extra = ["y2025on", "r_x_y2025on"]
    elif kind == "vol":
        w["vol_lag"] = w["r"].rolling(20, min_periods=15).std().shift(1)
        w["r_x_vol"] = w["r"] * w["vol_lag"]
        extra = ["vol_lag", "r_x_vol"]
    return w, extra


def block_bootstrap(d, L, reps=999, seed=0):
    """Moving-block bootstrap of the r x gap coefficient: resample runs of L consecutive rows."""
    rng = np.random.default_rng(seed)
    X = np.column_stack([np.ones(len(d))] + [d[k].to_numpy() for k in TERMS])
    y, n, k = d["ds"].to_numpy(), len(d), TERMS.index("r_x_gap") + 1
    out = np.empty(reps)
    for i in range(reps):
        idx = (rng.integers(0, n - L + 1, int(np.ceil(n / L)))[:, None] + np.arange(L)).ravel()[:n]
        out[i] = np.linalg.lstsq(X[idx], y[idx], rcond=None)[0][k]
    return out


def placebo_gap(d, L=250, reps=999, seed=1):
    """r x gap coefficients with the gap shuffled in blocks of L rows (keeps its persistence, breaks its timing)."""
    rng = np.random.default_rng(seed)
    gap, r, band, y = (d[c].to_numpy() for c in ("gap_lag", "r", "band_lag", "ds"))
    blocks = [np.arange(s, min(s + L, len(d))) for s in range(0, len(d), L)]
    out = np.empty(reps)
    for i in range(reps):
        g = gap[np.concatenate([blocks[j] for j in rng.permutation(len(blocks))])]
        X = np.column_stack([np.ones(len(d)), r, g, r * g, band, r * band])
        out[i] = np.linalg.lstsq(X, y, rcond=None)[0][3]
    return out


def robustness(panel):
    """Checks asked for by the council review (2026-10-09). Returns markdown text."""
    v = build_vars(panel, "ust_1m", "hibor_1m")
    res, d, _ = fit(v, "2015-01-01")
    b = res.params["r_x_gap"]
    fits = 1

    def cell(r):
        return f"{r.params['r_x_gap']:.3f} ({r.bse['r_x_gap']:.3f}, p = {r.pvalues['r_x_gap']:.3f})"

    md = "## A. Is it a gap effect or a shift in the HSI slope over time?\n\n"
    md += "| Specification | r_t x Gap_{t-1} (SE, p) | N |\n|---|---|---|\n"
    md += f"| Baseline, column (1) | {cell(res)} | {int(res.nobs):,} |\n"
    for label, kind in [("Adds a 2025-26 dummy and r_t x 2025-26", "2025on"),
                        ("Adds year dummies and r_t x each year", "years"),
                        ("Adds lagged 20-day HSI volatility and r_t x volatility", "vol")]:
        w, extra = with_extra(v, kind)
        r2, _, _ = fit(w, "2015-01-01", END, TERMS + extra)
        fits += 1
        md += f"| {label} | {cell(r2)} | {int(r2.nobs):,} |\n"

    md += "\n## B. Implied slope of ds on r (pips per 1% HSI), mean band, 95% Newey-West CI\n\n"
    md += "| Gap percentile | Gap (pp) | Slope | 95% CI | p (slope = 0) |\n|---|---|---|---|---|\n"
    for q, g, s, lo, hi, p in implied_slopes(res, d):
        md += f"| p{int(q * 100)} | {g:.2f} | {s:.3f} | {lo:.3f} to {hi:.3f} | {p:.3f} |\n"

    md += "\n## C. Leave one year out\n\n| Year dropped | r_t x Gap_{t-1} (SE, p) | N |\n|---|---|---|\n"
    for y in sorted(set(d.index.year)):
        r2, _, _ = fit(blank(v, v.index[v.index.year == y]), "2015-01-01")
        fits += 1
        md += f"| {y} | {cell(r2)} | {int(r2.nobs):,} |\n"

    md += "\n## D. Block bootstrap of r_t x Gap_{t-1} (999 draws)\n\n"
    md += "| Block length (trading days) | Bootstrap SE | 95% percentile CI | Share of draws at or below 0 |\n|---|---|---|---|\n"
    for L in (60, 250):
        bs = block_bootstrap(d, L)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        md += f"| {L} | {bs.std(ddof=1):.3f} | {lo:.3f} to {hi:.3f} | {(bs <= 0).mean():.3f} |\n"

    pl = placebo_gap(d)
    lo, hi = np.percentile(pl, [2.5, 97.5])
    md += ("\n## E. Placebo: gap shuffled in 250-day blocks (999 draws)\n\n"
           f"Actual r_t x Gap_{{t-1}} = {b:.3f}. Placebo 95% range {lo:.3f} to {hi:.3f}. "
           f"Share of placebo draws at least as large in absolute value: {(np.abs(pl) >= abs(b)).mean():.3f}.\n")
    md += "\n## F. Subperiods\n\n| Period | r_t x Gap_{t-1} (SE, p) | N |\n|---|---|---|\n"
    for start, end in [("2015-01-01", "2019-12-31"), ("2020-01-01", "2024-12-31"), ("2025-01-01", END)]:
        r2, _, _ = fit(v, start, end)
        fits += 1
        md += f"| {start[:4]} to {end[:4]} | {cell(r2)} | {int(r2.nobs):,} |\n"
    md += (f"\n## G. Specification count\n\nPoint estimates of r_t x Gap_{{t-1}} reported across the project: "
           f"4 (main table) + 7 (sensitivity) + {fits} (this file) = {4 + 7 + fits}, "
           "plus 2 x 999 bootstrap and 999 placebo draws. The four gap definitions are highly correlated, "
           "so they are not four independent tests.\n")
    return md


def plot_slope(panel, path):
    """Implied pips per 1% HSI rise against the lagged gap (mean band), with the 95% Newey-West band."""
    res, d, _ = fit(build_vars(panel, "ust_1m", "hibor_1m"), "2015-01-01")
    names, V = list(res.params.index), res.cov_params().to_numpy()
    grid = np.linspace(*d["gap_lag"].quantile([0.05, 0.95]), 100)
    R = np.zeros((len(grid), len(names)))
    R[:, names.index("r")], R[:, names.index("r_x_gap")] = 1, grid
    R[:, names.index("r_x_band")] = d["band_lag"].mean()
    s, se = R @ res.params.to_numpy(), np.sqrt(np.einsum("ij,jk,ik->i", R, V, R))
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.fill_between(grid, s - 1.96 * se, s + 1.96 * se, color="#b7d3f6", linewidth=0)
    ax.plot(grid, s, color=BLUE, linewidth=2)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    for q, g, sl, lo, hi, _ in implied_slopes(res, d):
        ax.plot(g, sl, "o", color=BLUE, markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
        ax.annotate(f"p{int(q * 100)}: {sl:+.1f}", (g, sl), textcoords="offset points", xytext=(6, -14),
                    fontsize=9, color=INK)
    ax.set_title("USD/HKD move per 1% HSI rise, by the previous day's rate gap", loc="left", fontsize=11, color=INK)
    ax.set_xlabel("Gap: 1M US Treasury minus 1M HIBOR (percentage points)", fontsize=9, color=MUTED)
    ax.set_ylabel("Pips per 1% HSI rise", fontsize=9, color=MUTED)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.tick_params(colors=MUTED, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    fig.text(0.01, -0.02, "Below zero: HSI up goes with HKD stronger. Shaded: 95% Newey-West band, band position at its "
             "mean, gap from its 5th to 95th percentile. Daily, 2015-01 to 2026-09.", fontsize=8, color=MUTED)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


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
    rob = robustness(panel)
    (OUT / "robustness.md").write_text(rob)
    rc, g = rolling_corr(panel)
    plot(rc, g, OUT / "fig_rolling_corr_gap.png")
    plot_slope(panel, OUT / "fig_slope_by_gap.png")
    print(md)
    print(sens)
    print(rob)
    print(f"Rolling corr: {rc.notna().sum()} days, mean {rc.mean():.3f}, min {rc.min():.3f}, max {rc.max():.3f}; "
          f"corr(rolling corr, gap) = {rc.corr(g.reindex(rc.index)):.3f}")
    print("Wrote output/regression_table.md, output/regression_table.csv, output/sensitivity.md, "
          "output/robustness.md, output/fig_rolling_corr_gap.png, output/fig_slope_by_gap.png")


if __name__ == "__main__":
    main()
