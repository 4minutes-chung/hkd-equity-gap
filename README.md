# hkd-equity-gap

Side project (Steven's own, not under any professor).

## Question

Does the co-movement between Hong Kong equity returns and USD/HKD get stronger when the USD rate sits far above HIBOR?

## Done when

- One daily panel for 2015 to 2026 on the Hong Kong trading calendar.
- One chart: the rolling 60-day equity/FX correlation against the 1M gap.
- One regression table: USD/HKD change on the HSI return in HKD, the gap at t-1, their product, and band position at t-1 and its product with the return.

## Status (2026-10-09)

Done with free data. Bloomberg (1M LIBOR / Term SOFR) is an optional fifth gap column.

- Panel: `data/clean/panel.parquet`, 2,896 HSI trading days, 2015-01-02 to 2026-10-09 (usable to 2026-09-30, where the HKMA files end). All 7 data checks pass.
- Chart: `output/fig_rolling_corr_gap.png`. Regression table: `output/regression_table.md` (and `.csv`). Sensitivity checks: `output/sensitivity.md`.

## Result

**In this data the stock/FX link gets weaker, not stronger, when the USD rate sits far above HIBOR.** At the average band position, a 1% HSI rise goes with USD/HKD 4.9 pips lower (HKD stronger) when the gap is at its 10th percentile (-0.23 pp), 3.0 pips lower at the median (0.25 pp) and 0.9 pips higher at the 90th percentile (1.22 pp). The r x gap coefficient is +4.0 (p = 0.003) and positive in all four gap definitions. It survives dropping the May to August 2025 gap spike, dropping days with HSI moves above 5%, and capping returns; it drops to +2.0 (p = 0.17) if 2025 and 2026 are left out. Associations, not causal effects. Gap and band position move together (correlation about 0.55).

## Data

| Panel column | Source | File / series | Rows in panel | Note |
|---|---|---|---|---|
| `hsi_close` | Yahoo Finance | `^HSI` close | 2,896 | price index, no dividends; sets the calendar |
| `usdhkd` | HKMA Monthly Statistical Bulletin | `T060103.xls`, col "U.S. dollar" | 2,888 | Hang Seng Bank average closing middle rate, HKD per USD |
| `hibor_1m` | HKMA MSB | `T060303.xls`, sheet "T6.3.3 (HIBOR Fixing)", col "1-month" | 2,887 | HKAB fixing, 11:15 am |
| `honia` | HKMA MSB | `T060303.xls`, sheet "T6.3.3 (HONIA)" | 2,578 | starts 2016-04-05 |
| `agg_balance_hkd_mn` | HKMA MSB | `T070102.xls`, col "Closing balance" | 2,890 | HK$ million |
| `ust_1m` | FRED | `DGS1MO` | 2,802 | 1-month Treasury, constant maturity; US dates only |
| `sofr` | FRED | `SOFR` | 2,025 | starts 2018-04-03; US dates only |
| `cp_1m_usd` | FRED | `DCPF1M` | 1,571 | 1-month AA financial commercial paper; missing about 70% of days from 2021 |

- File base URL: `https://www.hkma.gov.hk/media/eng/doc/market-data-and-statistics/monthly-statistical-bulletin/`.
- Series are left-joined onto HSI trading days with no forward-fill. HSI has 3 days with no HIBOR fixing (2025-08-05, 2025-09-08, 2025-09-24, likely severe-weather days).
- HSI date check: its largest one-day fall is on 2025-04-07 (-14.2% log), so dates are not shifted.
- HKMA files end at the last month-end and refresh monthly (last modified 2026-10-02 to 10-06).
- Sanity values confirmed on HKMA's daily monetary statistics pages: closing Aggregate Balance HK$44,611mn (2025-05-06), HK$161,313mn (2025-05-07), HK$174,100mn (2025-05-08); 1M HIBOR fixing 0.87423% (2025-06-03). The XLS files match all four.

## Prior work

Searched 2026-10-09 by three Claude subagents using web search, IDEAS/RePEc, OpenAlex, Semantic Scholar and CitEc (keyword queries, plus citation trails of the three anchors and of Lo, Hui, Fong and Chu 2015). The "opened?" column is the subagents' report. I confirmed only that the three anchors exist, that the AMRO annex PDF exists, and the Yiu et al. abstract. Google Scholar and CNKI were then searched in a browser the same day (see Manual search below); **Airiti not reachable from this network**. SSRN abstract pages returned 403, so SSRN items are from listings only. A "no" on a line marked "not opened" is a guess from the title or excerpt.

**Stop rule: no "yes" hit.** The angle stands. Only Airiti is left unsearched.

Format: title | authors | year | link | opened? | equity x gap

Closest (unclear):

- Annex 1, Inside the LERS: Why HKD Stability Can Coexist with Wide Rate Differentials (AMRO ACR-2026-06) | Ng, Kim (per annex footnote, not confirmed) | 2026 | https://amro-asia.org/wp-content/uploads/2026/08/Selected-Issue-1_Inside-the-LERS-Why-HKD-Stability-Can-Coexist-with-Wide-Rate-Differentials_final.pdf | full text of annex | unclear: regresses HKD spot on the rate spread, Southbound buying, HKEX turnover and VIX additively; says in words that equity inflows slow the carry arbitrage, but does not test the interaction
- An Analytical Framework for the Hong Kong Dollar Exchange Rate Dynamics under Strong Capital Inflows (HKMA WP 1005) | Yiu, Ho, Ma, Tsang | 2010 | https://ideas.repec.org/p/hkg/wpaper/1005.html | abstract | unclear: theory and simulation, the equity-return gap "counter-balances" the rate gap; functional form not seen
- Analysis on the determinants of HIBOR-LIBOR spreads (HKMA RM 07/2017) | not confirmed | 2017 | https://www.hkma.gov.hk/media/eng/publication-and-research/research/research-memorandums/2017/RM07-2017.pdf | not opened (search excerpt) | unclear: equity returns help set the spread (reverse direction)
- The Impact of Quantitative Easing and Carry Trades on HKEX-listed Equities | Strøbek (Princeton senior thesis) | 2026 | https://theses-dissertations.princeton.edu/entities/publication/f337d442-a1ee-4273-b61e-9a101bda69eb | abstract | unclear: equity is the outcome, no USD/HKD
- Hong Kong's Financial Market Interactions with the US and Mainland China in Crisis and Tranquil Times (HKMA WP 0910) | He, Zhang, Wang | 2009 | https://ideas.repec.org/p/hkg/wpaper/0910.html | abstract | unclear: equity, money and FX jointly, additive
- Identifying the Signs of Currency Speculation in Hong Kong's Linked Exchange Rate (MPRA 35279) | Li | 2011 | https://ideas.repec.org/p/pra/mprapa/35279.html | abstract | unclear: HSI to FX dynamic correlation, no rate gap seen

Checked, no:

- How Credible Is Hong Kong's Currency Peg? (NBER w34300) | Jermann, Wei, Yue | 2025 | https://ideas.repec.org/p/nbr/nberwo/34300.html | abstract and first pages | no
- Is the Hong Kong Dollar Exchange Rate "Bounded" in the Convertibility Zone? (HKMA WP 0713) | Hui, Fong | 2007 | https://ideas.repec.org/p/hkg/wpaper/0713.html | not opened | no (title only): no close citer among 9
- AMRO Annual Consultation Report on Hong Kong, China (ACR-2026-06) | AMRO | 2026 | https://amro-asia.org/wp-content/uploads/2026/08/1.-AMRO-Annual-Consultation-Report-on-Hong-Kong-China_2026_for-Publication.pdf | Annex 1 only | 0 citers found
- The credibility of "The Link" from the perspective of modern financial theory (HKMA WP 0902) | Genberg, Hui | 2009 | https://ideas.repec.org/p/hkg/wpaper/0902.html | full text | no: GARCH of USD/HKD and rate differential, no equity
- Assessing the Credibility of the Convertibility Zone of the Hong Kong Dollar (HKMA WP 0719) | Fung, Yu | 2007 | https://ideas.repec.org/p/hkg/wpaper/0719.html | full text | no
- How Do Macroeconomic Developments in Mainland China Affect Hong Kong's Short-term Interest Rates? (HKMA WP 0717) | He, Leung, Ng | 2007 | https://ideas.repec.org/p/hkg/wpaper/0717.html | full text | no: HIBOR VAR, equity flows only in words
- Stock market uncertainty and uncovered equity parity deviation: Evidence from Asia (J. Asian Econ. 73) | Jung, Jung | 2021 | https://ideas.repec.org/a/eee/asieco/v73y2021ics1049007820301512.html | abstract and poster | no: interacts with equity volatility, not a rate gap
- How Rational Are the Option Prices of the Hong Kong Dollar Exchange Rate? (J. Derivatives) | Drapeau, Wang, Wang | 2020 | https://doi.org/10.3905/jod.2020.1.120 | abstract | no
- Off-the-record target zones: theory with an application to Hong Kong's currency board (SNDE 17(4)) | Chen, Funke, Glanemann | 2013 | https://doi.org/10.1515/snde-2012-0034 | abstract-level summary | no
- Southbound capital flows and stock return predictability (PBFJ 93) | Ding, Song, Bian, Zhang | 2025 | https://ideas.repec.org/a/eee/pacfin/v93y2025ics0927538x25002240.html | abstract | no
- Effects of Capital Flow on the Equity and Housing Markets in Hong Kong (GRU WP 2017-012) | Cheung, Chow, Yiu | 2017 | https://www.cb.cityu.edu.hk/ef/doc/GRU/WPS/GRU%232017-012%20Cheung%20Chow%20Yiu.pdf | abstract and first pages | no
- Exchange rates change, asset-denominated currency difference and stock price fluctuation (Applied Econ. 51(60)) | Zheng, Jiang, Long | 2019 | https://ideas.repec.org/a/taf/applec/v51y2019i60p6517-6534.html | abstract | no
- Fast Interface for New Issuance and the Hong Kong Dollar Interbank Market during IPOs (SSRN 7446763) | Cheung, Luk, Yip | 2026 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7446763 | not opened | no (listing only): IPO to HIBOR
- Interest Rate Differentials Under an Exchange Rate Convertibility Zone (SSRN 4548132) | Fung, Lam | not confirmed | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4548132 | not opened | no (listing only)
- Linked Exchange Rate System Operations: Mechanism and Theory (HKMA RM 11/2018) | HKMA | 2018 | https://www.hkma.gov.hk/media/eng/publication-and-research/research/research-memorandums/2018/RM11-2018.pdf | not opened | no (excerpt only)

Manual search, 2026-10-09 (browser, no login):

- Google Scholar, from 2015, first 2 result pages each: `"Hong Kong dollar" "stock market" "interest rate differential"`; `"Hong Kong dollar" Southbound "exchange rate"`; `"Hang Seng" "USD/HKD" correlation`; plus page 1 of `"Hong Kong dollar" "carry trade" equity`. No "yes". Checked further:
  - The Credibility of Hong Kong's Currency Board System: Looking Through the Prism of MS-VAR Models with Time-Varying Transition Probabilities (Oxford Bull. Econ. Stat. 78(6)) | Blagov, Funke | 2016 | https://www.econstor.eu/handle/10419/212801 | full text (BOFIT DP 15/2014, searched for equity terms) | no: Hang Seng volatility drives credibility regime switches; no equity return x gap
  - Funding Stress and Housing Market Dynamics in Hong Kong (SSRN 6500524) | Wong | 2026 | https://doi.org/10.2139/ssrn.6500524 | abstract (Crossref) | no: housing model
  - Uncovered interest rate parity, carry trade, and country equity return differentials (Global Economy Journal) | Kanchanapoom, Padungsaksawasdi et al. | 2018 | Scholar listing | not opened | no (snippet only): Hong Kong dollar excluded
  - Exchange Rate Expectations, Cross-Border Equity Flows, and the Onshore-Offshore Exchange Rate Spreads | Ma, Zhu | not confirmed | SSRN listing | not opened | no (snippet only): RMB onshore/offshore spread, not USD/HKD
- CNKI (oversea.cnki.net), 5 terms (港元 匯率 股市: 134 hits; 港元 利差 套息交易: 2; 南向資金 港元 匯率: 8; 聯繫匯率 資金流 港股: 0, also 0 in Simplified, broadened to 聯繫匯率 港股: 88; 港元 HIBOR 南向: 3). Almost all newspaper pieces. No academic paper close. Closest:
  - Hong Kong dollar market analysis framework and recent trend interpretation (China Forex 2025(13), pp. 54-58) | Liu Hongshao, Liu Xiaokai (Agricultural Bank of China) | 2025 | DOI 10.13539/j.cnki.11-5475/f.2025.13.016 | abstract | no: practitioner piece, names carry trades and stock-driven flows in words, no estimates
- Airiti: www.airitilibrary.com drops the TLS connection from this network (same network where the HKMA API is blocked). Web search found no indexed Airiti page for the terms. Not searched.
- Motivation quote worth citing: Norman Chan (HKMA), "Latest Analysis of Fund Inflows into the Hong Kong Dollar", HKMA Insight, 1 Feb 2010, https://www.hkma.gov.hk/eng/news-and-media/insight/2010/02/20100201/ : in 2006 and 2007 a wide HKD-USD spread led to carry trades that "countered the demand for Hong Kong dollars triggered by equity-related fund inflows". Narrative only, not a test.

Framework to cite (abstracts only): Hau and Rey (2006, RFS); Camanho, Hau and Rey (2022, RFS); Cenedese, Payne, Sarno and Valente (2016, Review of Finance); Curcuru, Thomas, Warnock and Wongswan (2014, JIMF).

Notes for Steven (not actions):

- The gap may be driven by equity flows (endogeneity): AMRO's mechanism runs from equity flows through the Aggregate Balance to HIBOR, and HKMA RM 07/2017 has equity returns setting the spread (search excerpt only).
- USD/HKD barely moves under the peg, so the dependent variable has tiny variance. A referee may ask for distance to the convertibility undertaking or forward points instead.
- Jung and Jung (2021) find uncovered equity parity flips sign in Asia, so the Hau and Rey sign prior is not safe here.

## Decisions

| Date | Decision | Status |
|---|---|---|
| 2026-10-09 | Folder renamed to `hkd-equity-gap` (Desktop) | decided (Steven) |
| 2026-10-09 | Python from conda `base`, no uv or venv | proposed |
| 2026-10-09 | HKMA data from the Monthly Statistical Bulletin XLS files, not the Open API the plan named. The API returns HTTP 405 from this network; the files are the same official series and match HKMA's daily pages | proposed |
| 2026-10-09 | Aggregate Balance from T070102 "Closing balance", not T070202 (which differs on discount-window days, per a 34-date check against daily pages) | proposed |
| 2026-10-09 | USD/HKD: old-basket sheet before 2020-01-02, new-basket sheet from then on; the script asserts they agree on the overlap | proposed |
| 2026-10-09 | Main gap = 1-month US Treasury rate (FRED DGS1MO) minus 1M HIBOR, positive when the USD rate is above HIBOR. Why: free and complete daily from 2015; the bank commercial-paper rate (DCPF1M) is missing about 70% of days from 2021. Robustness: same gap from 2018-04, SOFR minus HONIA, commercial paper on the days it exists; Bloomberg LIBOR/Term SOFR later | proposed |
| 2026-10-09 | Pulls start 2015-01-01; effective sample start follows the gap choice | proposed |
| 2026-10-09 | Calendar = HSI trading days (Yahoo ^HSI). US rates carried forward at most 3 days onto HK days in the analysis only; gap and band enter at t-1 (US rates for a date are set after the HK close) | proposed |
| 2026-10-09 | Band check tolerance 0.005: the USD/HKD data check accepts 7.745 to 7.855. Why: the series is a bank closing middle rate, and 280 of 2,887 days sit just past 7.75 or 7.85 (2015: 7.7495; 2018, 2019, 2022, 2023, 2025: 7.8505 to 7.8535). Raw values are not changed. How close to 7.75/7.85 counts as "at the edge" for the band-position variable is still open | proposed |
| 2026-10-09 | The panel write is blocked only by structural checks (duplicates, empty series); the done-when content checks are reported but don't block | proposed |

## Data rule

Raw pulls go in `data/raw` and are never edited by hand.

## Run

```
python pull_data.py
python analysis.py
python -m pytest -q
```
