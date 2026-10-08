# R072 Stage 3 — Autonomous engine stress decision
Date: 2026-10-07
Status: **HOLD / RESEARCH ONLY**. Not approved for funded or live use. 2026 remains sealed.

Source: User-uploaded NinjaTrader Grid 2026-10-07 10-44 p. m..csv; R072LiveEngineParity, MES 1 contract, 1-minute RTH, 2020–2025, independent H017/session computation, news and rollover files active, catastrophe stop 0.70 ATR enabled, commission $1.88 round-trip, slippage 2 ticks. Net P&L already deducts commission.

## Execution
- 149 trades: 71 long, 78 short; 137 timed exits and 12 news exits, NO recorded stop exits. Stop order placement/protection remains unverified.
- Net +$998.63; PF 1.2526; expectancy +$6.70/trade; max DD $621.93; commission $280.12.
- 1 tick + commission: +$1,343.63, PF 1.36; 2 ticks + commission +$998.63, PF 1.25.
- Previously established: all 145 original Python-parity trades preserved with 4 additional sessions after session-universe filter removal. Additional session quality unresolved.

## Yearly net and PF: 2-tick stress
| Year | Trades | Net | PF |
|---|---:|---:|---:|
| 2020 | 4 | +$49.98 | 1.588 |
| 2021 | 32 | -$120.16 | 0.851 |
| 2022 | 26 | +$188.62 | 1.208 |
| 2023 | 27 | +$239.24 | 1.653 |
| 2024 | 35 | +$976.70 | 2.628 |
| 2025 | 25 | -$335.75 | 0.718 |
| Total | 149 | +$998.63 | 1.253 |

- 2020–2024 development period: 124 trades (fails >=150 gate); +$1,334.38 net; 2024 accounts for 73.2% of net (fails <40% dependence gate).
- 2024 contributes 97.8% of the 2020–2025 $998.63 net; without 2024 +$21.93. 2024H2 alone +$879.27 (88.1% of six-year net).
- Only 7 of 11 semestres with trades positive, and 4 of 6 years. Frequency 149/72 = 2.07 trades per month (fails >=5 gate).
- LONG (71 trades) -$232.23, SHORT (78) +$1,230.86 at 2-tick stress; do not retroactively disable LONG based on in-sample performance. Both LONG and SHORT lost in 2025.

## Four additional dates: 2-tick net
| Date | Direction | Net |
|---|---|---:|
| 2021-11-26 | LONG | -$100.63 |
| 2022-05-23 | LONG | +$84.37 |
| 2024-08-02 | SHORT | +$311.87 |
| 2025-04-04 | LONG | -$61.88 |

## Required checks before another deployment decision
1. Audit order logs for both-side 0.70 ATR stop (placed, working, canceled at close); no historical stop fills means activation is NOT proven.
2. Verify all four additional dates from raw 1-minute coverage, duplicates/missing minutes, early-close schedule, and rollover. Do not declare valid based on P&L.
3. No retrospective parameter search against repeatedly examined 2020–2025. Use causal regime study as diagnostic only, then preregister new independent hypotheses.
4. Check funded-account drawdown, daily risk, concurrent strategy exposures, and tick-resolution execution prior to any live use.
5. 2025 already reviewed many times and is no longer a truly untouched holdout. Keep 2026 sealed until full strategy is frozen; an OOS historical test in 2026 is not a real-time forward test.

Decision: Stage 2 signal parity and stage 3 positive stress demonstrated, but statistical stability, frequency, annual dependence, and stop/data validation insufficient. Keep R072 on watchlist rather than freeze. Next research priority: multi-instrument ES/NQ/MES/MNQ modular hypothesis lab instead of curve-fitting R072.