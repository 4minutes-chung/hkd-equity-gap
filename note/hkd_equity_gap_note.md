---
title: "When the carry gap is wide, Hong Kong stocks stop moving the Hong Kong dollar"
subtitle: "An exploratory note on the HSI and USD/HKD under the Linked Exchange Rate System"
author: "Steven Chung"
date: "October 2026 (draft)"
geometry: margin=2cm
fontsize: 10pt
colorlinks: true
---

**Summary.** Under Hong Kong's peg, USD/HKD can only move between 7.75 and 7.85. Inside that band, days when the Hang Seng Index (HSI) rises usually see the Hong Kong dollar strengthen a little. I asked whether this link gets *stronger* when the US one-month rate sits far above HIBOR, the condition that pushes carry trades out of the Hong Kong dollar. The data say the opposite. When the US rate is slightly below HIBOR, a 1% HSI rise goes with USD/HKD about 4.9 pips lower. At the median gap it is 3.0 pips lower. When the US rate is about 1.2 percentage points above HIBOR (90th percentile), there is no detectable link: +0.9 pips, 95% interval -1.9 to +3.7. The pattern holds across four measures of the gap and a battery of checks. It is a correlation, not a causal estimate, and it is absent in 2020 to 2024.

# 1. What this note can and cannot claim

**It can claim** that in daily data from 2015 to 2026, the co-movement between HSI returns and USD/HKD changes fades as the previous day's USD minus HKD rate gap widens. The interaction is positive with all four gap measures, survives separate HSI slopes for every year, and beats a placebo in which the gap is shuffled in year-long blocks.

**It cannot claim** the following.

- **Causation.** The gap is not exogenous. Equity inflows raise the HKMA Aggregate Balance and push HIBOR down, so stock-market flows help set the gap that conditions the stock-FX link.
- **A stable effect.** The interaction is strong in 2015 to 2019 (+8.4) and 2025 to 2026 (+7.1) but close to zero in 2020 to 2024 (+0.8, p = 0.60). The gap moves slowly, so the sample holds a handful of gap episodes rather than 2,884 independent days.
- **A large effect.** R-squared is 0.03. The slopes are a few pips on a 1,000-pip band.
- **Clean data.** The HSI is a price index from Yahoo Finance. The USD rate is the one-month Treasury rate, which sits a little below bank funding rates. The HSI close and the bank's closing USD/HKD rate are not taken at exactly the same moment, so timing is approximate.
- **One clean test.** I computed 30 point estimates of the key coefficient across specifications. The four gap measures are highly correlated, so they are not four independent tests.

# 2. Data and method

Data: USD/HKD (Hang Seng Bank average closing middle rate), 1M HIBOR fixing and HONIA from the HKMA Monthly Statistical Bulletin (tables 6.1.3 and 6.3.3); the 1M US Treasury rate (main USD rate), SOFR and 1M AA financial commercial paper from FRED (DGS1MO, SOFR, DCPF1M); the Hang Seng Index close from Yahoo Finance (^HSI). The sample is 2,884 HSI trading days from 2015-01-05 to 2026-09-30. The estimated equation is

$$\Delta s_t = \alpha + \beta_1 r_t + \beta_2 g_{t-1} + \beta_3\, r_t g_{t-1} + \beta_4 b_{t-1} + \beta_5\, r_t b_{t-1} + \varepsilon_t,$$

where $\Delta s_t$ is the daily change in USD/HKD in pips (positive means the HKD weakened), $r_t$ is the HSI log return in percent, $g_{t-1}$ is the USD rate minus the HK rate in percentage points, and $b_{t-1}$ is the band position (0 at 7.75, 1 at 7.85). The gap and band enter with a one-day lag because US rates for a date are set after Hong Kong closes. The slope of USD/HKD on the HSI is $\beta_1 + \beta_3 g_{t-1} + \beta_5 b_{t-1}$, so a positive $\beta_3$ means the link weakens as the gap widens. Standard errors are Newey-West with 8 lags counted in trading days.

# 3. Results

**Table 1. Daily change in USD/HKD (pips).** Newey-West standard errors in parentheses. \*\*\* p < 0.01, \*\* p < 0.05, \* p < 0.1.

| | (1) UST 1M minus HIBOR 1M | (2) Same, from 2018-04 | (3) SOFR minus HONIA, from 2018-04 | (4) Bank CP 1M minus HIBOR 1M |
|---|---|---|---|---|
| HSI return $r_t$ | -2.344\*\* (1.111) | -2.798\* (1.604) | -3.693\*\*\* (1.422) | -2.426\*\* (0.996) |
| Gap $g_{t-1}$ | 1.719 (1.702) | 1.511 (1.683) | 0.912 (1.386) | 2.815 (1.852) |
| $r_t \times g_{t-1}$ | 4.021\*\*\* (1.364) | 3.826\*\*\* (1.355) | 2.885\*\*\* (1.033) | 5.804\*\*\* (1.680) |
| Band $b_{t-1}$ | -6.564\*\*\* (2.344) | -7.729\*\*\* (2.720) | -7.323\*\* (3.021) | -7.428\*\*\* (2.501) |
| $r_t \times b_{t-1}$ | -3.255 (2.054) | -2.402 (2.503) | -2.610 (2.616) | -4.945\*\* (2.124) |
| N | 2,884 | 2,086 | 2,084 | 2,470 |
| R-squared | 0.027 | 0.028 | 0.026 | 0.034 |

Column (4) uses the commercial-paper rate, which FRED publishes on fewer than half of days in most years after 2020.

![Implied USD/HKD response to a 1% HSI rise, by the previous day's rate gap (column 1). Shaded: 95% Newey-West band.](output/fig_slope_by_gap.png){width=78%}

The obvious mechanical explanation does not fit. A wide gap tends to push USD/HKD toward 7.85, where HKMA stops it rising further, which could mute any link. But dropping the 942 days after USD/HKD sat within 50 pips of either edge makes the interaction larger (+5.5, p = 0.005), not smaller, and the band interaction is not significant. A reading consistent with the data, though not tested here, is that wide gaps bring carry positioning that offsets equity-driven HKD demand. HKMA's then Chief Executive described this channel in words in 2010: carry trades "countered the demand for Hong Kong dollars triggered by equity-related fund inflows" (Chan, 2010).

# 4. Robustness

**Table 2. Interaction $r_t \times g_{t-1}$ under alternative checks (column 1 gap).**

| Check | Estimate | Reading |
|---|---|---|
| Separate HSI slope for every year | +4.04 (p = 0.017) | not just the link drifting over time |
| Extra HSI slope for 2025 to 2026 | +3.09 (p = 0.029) | survives |
| Control for 20-day HSI volatility and its interaction | +3.83 (p = 0.004) | not a volatility proxy |
| Leave one year out (12 runs) | +3.0 to +5.6, all p at most 0.049 | weakest when 2025 is dropped |
| Drop USD/HKD near-edge days (942) | +5.53 (p = 0.005) | not the peg cap |
| Block bootstrap, 250-day blocks | 95% CI 1.0 to 6.8 | above zero |
| Placebo: gap shuffled in 250-day blocks | actual 4.02 vs placebo range -2.50 to 2.95 (p = 0.005) | timing of the gap matters |
| Subperiods 2015-19 / 2020-24 / 2025-26 | +8.4 (p 0.01) / +0.8 (p 0.60) / +7.1 (p 0.02) | absent in 2020-24 |
| Drop 2025 and 2026 together | +2.0 (p = 0.17) | not significant |

# 5. Related work and search log

The closest work is additive. AMRO's 2026 consultation report on Hong Kong, China (Annex 1) regresses HKD spot on the USD-HIBOR spread, Southbound net buying, HKEX turnover and VIX, and argues in words that equity inflows let rate gaps persist, without testing the interaction. Yiu, Ho, Ma and Tsang (HKMA WP 10/2010) model the equity-return gap offsetting the rate gap in a target zone, in theory and simulation. Hau and Rey (2006) give the general equity-flow and exchange-rate framework for floating currencies. On 9 October 2026 I searched Google Scholar (4 queries, 2015 onward), CNKI (5 terms), and RePEc, OpenAlex and Semantic Scholar citation trails of the three closest anchors, and found no paper that tests the stock return times rate gap interaction for USD/HKD. Airiti could not be reached. The full log is in the repository README.

# 6. Reproduce

Code and data pipeline: `pull_data.py` (downloads and checks the data), `analysis.py` (tables, charts, robustness), tests in `tests/`. Run `python pull_data.py`, then `python analysis.py`. Outputs land in `output/`.

**References.** AMRO (2026), *Annual Consultation Report: Hong Kong, China*, ACR-2026-06. Chan, N. (2010), "Latest Analysis of Fund Inflows into the Hong Kong Dollar", HKMA Insight, 1 February. Hau, H. and H. Rey (2006), "Exchange Rates, Equity Prices, and Capital Flows", *Review of Financial Studies* 19(1). Yiu, M., A. Ho, Y. Ma and S. Tsang (2010), "An Analytical Framework for the Hong Kong Dollar Exchange Rate Dynamics under Strong Capital Inflows", HKMA Working Paper 10/2010.

*Draft. Code written with AI assistance (Claude) and reviewed with Grok; every number comes from the scripts in the repository.*
