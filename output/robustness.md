## A. Is it a gap effect or a shift in the HSI slope over time?

| Specification | r_t x Gap_{t-1} (SE, p) | N |
|---|---|---|
| Baseline, column (1) | 4.021 (1.364, p = 0.003) | 2,884 |
| Adds a 2025-26 dummy and r_t x 2025-26 | 3.087 (1.417, p = 0.029) | 2,884 |
| Adds year dummies and r_t x each year | 4.038 (1.691, p = 0.017) | 2,884 |
| Adds lagged 20-day HSI volatility and r_t x volatility | 3.832 (1.335, p = 0.004) | 2,869 |

## B. Implied slope of ds on r (pips per 1% HSI), mean band, 95% Newey-West CI

| Gap percentile | Gap (pp) | Slope | 95% CI | p (slope = 0) |
|---|---|---|---|---|
| p10 | -0.23 | -4.910 | -6.869 to -2.950 | 0.000 |
| p50 | 0.25 | -2.962 | -4.314 to -1.610 | 0.000 |
| p90 | 1.22 | 0.924 | -1.876 to 3.724 | 0.518 |

## C. Leave one year out

| Year dropped | r_t x Gap_{t-1} (SE, p) | N |
|---|---|---|
| 2015 | 4.022 (1.397, p = 0.004) | 2,638 |
| 2016 | 3.817 (1.334, p = 0.004) | 2,639 |
| 2017 | 4.014 (1.372, p = 0.003) | 2,638 |
| 2018 | 3.929 (1.383, p = 0.004) | 2,638 |
| 2019 | 3.925 (1.436, p = 0.006) | 2,638 |
| 2020 | 5.568 (1.532, p = 0.000) | 2,636 |
| 2021 | 3.965 (1.351, p = 0.003) | 2,637 |
| 2022 | 3.536 (1.441, p = 0.014) | 2,638 |
| 2023 | 4.446 (1.453, p = 0.002) | 2,641 |
| 2024 | 4.540 (1.409, p = 0.001) | 2,638 |
| 2025 | 3.022 (1.534, p = 0.049) | 2,643 |
| 2026 | 3.592 (1.404, p = 0.011) | 2,700 |

## D. Block bootstrap of r_t x Gap_{t-1} (999 draws)

| Block length (trading days) | Bootstrap SE | 95% percentile CI | Share of draws at or below 0 |
|---|---|---|---|
| 60 | 1.539 | 1.143 to 7.191 | 0.003 |
| 250 | 1.515 | 1.014 to 6.784 | 0.001 |

## E. Placebo: gap shuffled in 250-day blocks (999 draws)

Actual r_t x Gap_{t-1} = 4.021. Placebo 95% range -2.496 to 2.949. Share of placebo draws at least as large in absolute value: 0.005.

## F. Subperiods

| Period | r_t x Gap_{t-1} (SE, p) | N |
|---|---|---|
| 2015 to 2019 | 8.415 (3.269, p = 0.010) | 1,229 |
| 2020 to 2024 | 0.793 (1.502, p = 0.598) | 1,230 |
| 2025 to 2026 | 7.123 (3.015, p = 0.018) | 425 |

## G. Specification count

Point estimates of r_t x Gap_{t-1} reported across the project: 4 (main table) + 7 (sensitivity) + 19 (this file) = 30, plus 2 x 999 bootstrap and 999 placebo draws. The four gap definitions are highly correlated, so they are not four independent tests.
