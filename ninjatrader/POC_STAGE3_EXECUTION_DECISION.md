# MES POC Breakdown — Stage 3 execution assessment (2026-10-07)

Status: **HOLD / RESEARCH WATCHLIST**. Stage 2 trade parity passed, Stage 3 baseline/stress remain net positive, but the strategy is NOT final-frozen or authorized for a funded account. 2026 remains sealed.

## Parity
- 109/109 Python ↔ NinjaTrader matched date/side and entry price in Stage 2.
- After the H15/news collision fix: exit type 109/109 (99 H15, 10 news).
- Remaining exit-price differences generally 1–2 MES ticks owing to the different historical fill convention; no signal mismatch.
- Introducing the 0.45 ATR catastrophe stop reduces the common historical trading universe from 109 to 108 because the earliest trade lacks a causal 14-session ATR; that one trade must not be counted as a stop-related improvement.
- Stop has not triggered in the 108-trade Stage 3 simulations. Future activation correctness is not yet directly verified by a triggered trade.

## Frozen test configuration
- MES 1-min, CME US Index Futures RTH, 2020-01-01 to 2025-12-31.
- SHORT only: open above prior-session volume-proxy POC; first POC touch closes below; next-bar open entry.
- H15 exit; USD Medium/High scheduled news flat T-5, block T-5 through T+5.
- 1 MES.
- Catastrophe stop ON at 0.45 ATR14 previous session; no fixed TP.
- Cost template: $1.88 round-trip commission; NinjaTrader Standard historical fill, slippage 1 or 2 ticks (configured).
- Both cases use Python-eligible session universe for parity only; this is not a deployable live-session filter.

## Aggregates
| Metric | 1 tick + commission | 2 ticks + commission |
|---|---:|---:|
| Trades | 108 | 108 |
| Net profit incl. commission | +$546.96 | +$314.46 |
| Expectancy/trade | +$5.06 | +$2.91 |
| Profit factor (net) | 1.37 | 1.20 |
| Max drawdown (net) | $331.32 | $365.71 |
| Win rate | 53.70% | 52.78% |
| Worst trade | -$118.13 | -$120.63 |
| Time exits | 98 | 98 |
| News exits | 10 | 10 |
| Stop exits | 0 | 0 |

Gross before commission, 2-tick scenario: +$517.50 (= net $314.46 + commission $203.04).

## 2-tick annual net (verified against NinjaTrader trade export)
| Year | N | Net |
|---|---:|---:|
| 2020 | 20 | -$215.10 |
| 2021 | 28 | +$184.86 |
| 2022 | 21 | +$510.52 |
| 2023 | 12 | -$272.56 |
| 2024 | 9 | +$78.08 |
| 2025 | 18 | +$28.66 |
| **Total** | **108** | **+$314.46** |

- 2023–2025: **-$165.82**.
- Positive semesters: **5/12**.
- 1-tick to 2-tick: same 108 entry timestamps and same 108 exit labels; cumulative net decrease $232.50.
- 1-tick and 2-tick settings are NOT an independent temporal out-of-sample test.

## Decision / next step
- Stop further POC parameter search on 2020–2025 to avoid retrospective selection.
- Preserve current candidate and evidence for later unbiased validation or a future preregistered alternative.
- Do NOT claim it meets funding/robustness gates.
- Proceed to independent R072 verification. R072 is provisional because H20/H30/H40 did not show a sufficiently broad performance plateau, and its CSV replay is not yet a deployable live signal generator.
- Do not open 2026 merely to improve POC results.

## Data provenance
- NinjaTrader Strategy Analyzer screenshots and exports supplied by the user on 2026-10-07.
- 1-tick export: `NinjaTrader Grid 2026-10-07 08-34 p. m..csv` (108 trades).
- 2-tick export: `NinjaTrader Grid 2026-10-07 09-04 p. m..csv` (108 trades).
- All monetary amounts USD per single MES contract.
