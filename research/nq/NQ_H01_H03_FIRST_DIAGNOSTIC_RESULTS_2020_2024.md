# NQ H01–H03 first pre-registered developmental mechanism screen

**Run date:** 2026-10-09. **Authority:** 2020–2024 exploratory only, **NO stop loss, TP or live execution certification**, 2025 and 2026 **SEALED**.
**Detailed preregistration committed before results:** `NQ_H01_H03_FIXED_DIAGNOSTIC_PREREG_2026_10_09.md`.

## Data and research setup

- Original user-uploaded NQ/MNQ NinjaTrader ZIP; read ONLY 25 NQ development partitions from `development_2020_2024`.
- Explicit fixed Thursday-before-expiry-week roll, 1221 consecutive 390-bar New York RTH trading days selected, no market-data interpolation.
- One earliest causal trade signal per *hypothesis* per eligible session (not a tradable combined portfolio). H01 ORB acceptance >1.25x prior-20-session same-minute median volume; H02 first break + rejection within five bars; H03 80th quantile past-20-session VWAP deviation and 15-bar efficiency <=0.30. Primary outcome entry next-minute open to +30-minute open; +15 secondary.
- All primary results are directional close-to-fixed-horizon *event studies*. **No stop, take-profit, news filter, intrabar fill simulation or position synchronization.**
- 1 NQ dollar accounting: $20/point, 2 adverse ticks per market order on entry AND exit, $4.68 RT fees, total minimum friction **$24.68 per event**. Additional stress +1 adverse tick per side = -$10 per event. Real slippage may exceed the assumptions.
- Weekly block bootstrap (5000) of mean; weekly sign-flip randomization (5000) and BH correction across 3 hypothesis families. These tests are screening approximations, not proof of profitability.

## Results, development 2020–2024

| Question | NQ-H01 ORB acceptance | NQ-H02 failed break reversal | NQ-H03 VWAP reversion |
|---|---:|---:|---:|
| Events | 1,117 | 636 | 675 |
| Mean net at +30m | **+$3.58** | **+$38.72** | **-$78.00** |
| Aggregate nominal net +30m | +$3,997.44 | +$24,628.52 | -$52,649.00 |
| PF, no stops | 1.009 | 1.099 | 0.821 |
| Positive years / 5 | 3 | 3 | 2 |
| Bootstrap 95% interval on mean | [-$53.21, +$60.55] | **[-$46.38, +$124.69]** | [-$155.83, -$1.24] |
| Weekly sign-flip one-sided p | .43311 | .19456 | .97441 |
| BH-adjusted q across 3 families | .64967 | .58368 | .97441 |
| Nominal net with +1 extra adverse tick per side | -$7,172.56 | +$18,268.52 | -$59,399.00 |
| 7+ calendar-day intervals between signals | 2 | 23 | 30 |
| Maximum gap between signals | 15 days | 18 days | 15 days |

**NONE passes statistical significance or robust net edge.** Do not call H02 a profitable strategy. H02 positive accounting is entirely sensitive to very large, volatile events. Example H02 2022 contributes **+$22,569.68 of its total +$24,628.52**, while 2021 (-$5,140) and 2024 (-$1,051) are negative. H01 is economically negligible and becomes negative with one extra tick per side. H03 fails the initial economic screen.

### Year-level gross-to-fixed-horizon results, NQ-H02

| Year | Events | Nominal net +30m |
|---|---:|---:|
| 2020 | 120 | +$2,503.40 |
| 2021 | 125 | -$5,140.00 |
| 2022 | 124 | +$22,569.68 |
| 2023 | 130 | +$5,746.60 |
| 2024 | 137 | -$1,051.16 |

H02 win rate .478; median event net -$42.18; 5th-percentile event -$1,749.68 and worst event -$3,684.68, **with no stop**. These outcomes would be unacceptable as unprotected one-NQ exposure in the MFFU 50K $2,000 loss cushion; a protective stop could materially change the profitability and must be researched independently without cherry-picking.

## Decisions

1. **NQ-H01: no edge** (at 30m, PF~1; stress turns negative); a signal that generates daily volume without a proven edge is NOT acceptable as an MFFU inactivity workaround.
2. **NQ-H02: research watchlist**, NOT deployment, no statistical confirmation or viable MFFU stop. A hypothesis for causal failed-break market behavior may merit a STOP/TP design stage with independent temporal walk-forward, but not retroactively tune to the 2022 P&L.
3. **NQ-H03: reject present form**, as the +30m reversion is materially negative.
4. NQ-H04 overnight-to-RTH volatility expansion remains **untested**, requires causal overnight session features.
5. NQ/MNQ are the SAME index at different contract multipliers; transferring these hypothetical signals to MNQ requires separate fee, spread and execution study, and will not create independent alpha.
6. No 2025/2026 market-price file was opened. Freeze execution/risk/controller before reserved 2026 pseudo-forward. No MFFU purchase on these results.
