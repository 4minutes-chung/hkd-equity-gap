# hkd-equity-gap

Side project (Steven's own, not under any professor).

## Question

Does the co-movement between Hong Kong equity returns and USD/HKD get stronger when the USD rate sits far above HIBOR?

## Done when

- One daily panel for 2015 to 2026 on the Hong Kong trading calendar.
- One chart: the rolling 60-day equity/FX correlation against the 1M gap.
- One regression table: USD/HKD change on the HSI return in HKD, the gap at t-1, their product, and band position at t-1 and its product with the return.

## Status (2026-10-09)

- `data/clean/panel.parquet` built: 2,887 rows, 2015-01-02 to 2026-09-30, one row per 1M HIBOR fixing date.
- Checks: no duplicate dates PASS; no empty series PASS; panel starts 2015-01-02 PASS; Aggregate Balance 44,611mn (2025-05-06) to 174,100mn (2025-05-08) PASS; 1M HIBOR min 0.525% in May to July 2025 PASS; USD/HKD within 7.75 to 7.85 with 0.005 tolerance PASS (280 days sit just past the band, by at most 0.0035; see Decisions).
- HSI not pulled yet. Gap definition not decided.
- Next: Bloomberg session Mon 2026-10-12. Export daily from 2015 as CSV into `data/raw`: 1M USD LIBOR (to its end date), 1M Term SOFR, HSI close. That settles gap option (b) and the HSI trading calendar.

## Data

| Panel column | Source | File / series | Rows in panel | Note |
|---|---|---|---|---|
| `usdhkd` | HKMA Monthly Statistical Bulletin | `T060103.xls`, col "U.S. dollar" | 2,887 | Hang Seng Bank average closing middle rate, HKD per USD |
| `hibor_1m` | HKMA MSB | `T060303.xls`, sheet "T6.3.3 (HIBOR Fixing)", col "1-month" | 2,887 | HKAB fixing, 11:15 am |
| `honia` | HKMA MSB | `T060303.xls`, sheet "T6.3.3 (HONIA)" | 2,578 | starts 2016-04-05 |
| `agg_balance_hkd_mn` | HKMA MSB | `T070102.xls`, col "Closing balance" | 2,887 | HK$ million |
| `sofr` | FRED | `SOFR` | 2,018 | starts 2018-04-03; US dates only |
| `tbill_4wk` | FRED | `DTB4WK` | 2,795 | US dates only |

- File base URL: `https://www.hkma.gov.hk/media/eng/doc/market-data-and-statistics/monthly-statistical-bulletin/`.
- Series are left-joined onto HIBOR fixing dates with no forward-fill. This drops 577 USD/HKD rows (mostly Saturdays) and 12 Aggregate Balance dates with no fixing.
- HKMA files end at the last month-end and refresh monthly (last modified 2026-10-02 to 10-06).
- Sanity values confirmed on HKMA's daily monetary statistics pages: closing Aggregate Balance HK$44,611mn (2025-05-06), HK$161,313mn (2025-05-07), HK$174,100mn (2025-05-08); 1M HIBOR fixing 0.87423% (2025-06-03). The XLS files match all four.

## Prior work

Searched 2026-10-09 by three Claude subagents using web search, IDEAS/RePEc, OpenAlex, Semantic Scholar and CitEc (keyword queries, plus citation trails of the three anchors and of Lo, Hui, Fong and Chu 2015). The "opened?" column is the subagents' report. I confirmed only that the three anchors exist, that the AMRO annex PDF exists, and the Yiu et al. abstract. **Not run yet: Google Scholar, CNKI, Airiti** (need a login or manual access). SSRN abstract pages returned 403, so SSRN items are from listings only. A "no" on a line marked "not opened" is a guess from the title or excerpt.

**Stop rule: no "yes" hit so far.** The angle stands, pending the three searches not yet run.

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
| 2026-10-09 | Gap definition open. (a) HONIA minus SOFR, from 2018. (b) 1M HIBOR minus 1M LIBOR, switching to 1M Term SOFR, from 2015, needs Bloomberg. (c) 1M HIBOR minus 4-week T-bill, from 2015, free. Recommended: (b) main, (a) robustness | open |
| 2026-10-09 | Pulls start 2015-01-01; effective sample start follows the gap choice | proposed |
| 2026-10-09 | Calendar = 1M HIBOR fixing dates until the HSI is added, then HSI trading dates | proposed |
| 2026-10-09 | Band check tolerance 0.005: the USD/HKD data check accepts 7.745 to 7.855. Why: the series is a bank closing middle rate, and 280 of 2,887 days sit just past 7.75 or 7.85 (2015: 7.7495; 2018, 2019, 2022, 2023, 2025: 7.8505 to 7.8535). Raw values are not changed. How close to 7.75/7.85 counts as "at the edge" for the band-position variable is still open | proposed |
| 2026-10-09 | The panel write is blocked only by structural checks (duplicates, empty series); the done-when content checks are reported but don't block | proposed |

## Data rule

Raw pulls go in `data/raw` and are never edited by hand.

## Run

```
python pull_data.py
python -m pytest -q
```
