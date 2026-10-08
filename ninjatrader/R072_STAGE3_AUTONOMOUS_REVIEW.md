# R072 autonomous NinjaTrader — Stage 3 stress, temporal robustness and decision

Date of analysis: 2026-10-07
Status: **HOLD / CONDITIONAL RESEARCH CANDIDATE** (NOT frozen for live/funding).
Data: NinjaTrader Grid 2026-10-07 10-44 p. m.(1).csv provided by user.
Scope: 2020–2025. 2026 remains sealed. No new optimized parameters.

## Verified test configuration
- Strategy: R072LiveEngineParity, MES, 1 minute, RTH.
- H017 Python reference OFF; Python eligible-session universe OFF; US news and rollover files ON.
- Catastrophe stop parameter ON at 0.70 * ATR14 previous session (validity of historical protective orders **not fully confirmed**).
- H30 exit, wick 0.50, cutoff 11:00 ET.
- 149 trades, 71 LONG, 78 SHORT, 1 MES.
- Commission $1.88 RT, NinjaTrader Standard fills, **2 ticks** simulated slippage.
- Trade-export Profit is NET of per-trade commission; do not subtract commission twice.
- $280.12 total commissions. $998.63 net, PF 1.253, expectancy +$6.70/trade, max DD $621.93, maximum individual loss $289.38. Approx 2.07 trades per calendar month over 72 months.

## Yearly results — net, after costs
| Year | Trades | Net | Net PF |
|---|---:|---:|---:|
| 2020 | 4 | +49.98 | 1.588 |
| 2021 | 32 | -120.16 | 0.851 |
| 2022 | 26 | +188.62 | 1.208 |
| 2023 | 27 | +239.24 | 1.653 |
| 2024 | 35 | +976.70 | 2.628 |
| 2025 | 25 | -335.75 | 0.718 |
| All | 149 | +998.63 | 1.253 |

2024 contributes **97.8%** of total net; excluding 2024, five other calendar years produce only **+$21.93**. Only 4/6 years profitable, and 7/11 sampled half-years profitable (2020 H1 has zero signals). 2025 H1 -226.95 and H2 -108.80.

## Long vs short
| Side | Trades | Net | Net PF | DD |
|---|---:|---:|---:|---:|
| LONG | 71 | -232.23 | 0.894 | 648.99 |
| SHORT | 78 | +1230.86 | 1.696 | 202.53 |

Short 2025 is **-$113.82**; long 2025 **-$221.93**. Removing long merely because they are poor over observed history would be retrospective selection, not an unbiased strategy improvement.

## 4 extra sessions after removing Python eligible-session filter
| Date | Side | Net under 2-tick stress |
|---|---|---:|
| 2021-11-26 | LONG | -100.63 |
| 2022-05-23 | LONG | +84.37 |
| 2024-08-02 | SHORT | +311.87 |
| 2025-04-04 | LONG | -61.88 |
| **Total** | | **+233.73** |

These dates do not belong to the historical Python eligible-session manifest; historical validity, early-close calendars and source-bar completeness still require independent checks.

The original 145 common trades net **+$764.90** under this same 2-tick test. Of these original 145, 2024 contributes +$664.83 (**86.9%**) and other years together +$100.07. Thus concentration persists independently of the four additional dates.

## Exit names
- R072_TIME_EXIT: 137
- R072_NEWS_EXIT: 12
- Stop executions in exported trades: 0.
- The source code calls `SetStopLoss(... CalculationMode.Ticks, round_up(0.70*ATRprev/TickSize))` before each entry, and suppresses entry if the required ATR is missing. This is code-level evidence, **not proof of stop-order installation/fill** under NinjaTrader's historical execution model. Audit working stop orders separately, preferably by controlled diagnostic runs not used for optimization.

## Decision and gates
**Do not freeze R072 as production strategy.** Current research gate requires >=5 trades/month (actual 2.07), PF >=1.25 stress (1.253 is borderline), adequate per-year stability (fails concentration and 2025), acceptable funded-account drawdown, and unbiased validation. Keep 2026 sealed; do not choose SHORT-only based on observed 2020–2025 without preregistration and separate out-of-sample validation.

Sequence:
1. Audit protective stop orders and consistency of actual ATR stop levels at each entry. Controlled diagnostic with artificially narrow SL may verify mechanics only; never use it to select returns.
2. Audit 4 extra sessions for complete bars, timestamps, rollover treatment, and exchange holiday/early close status.
3. Validate previously frozen H20/H30/H40 sensitivity, not optimize for best result; diagnose segment and regime drift as explanatory analyses.
4. Evaluate whole portfolio and cross-strategy risk overlaps using matched timestamp exports for PDC, POC, R072. Do not add individual PFs. Do not use 2026 for tuning.
5. If evidence is insufficient, stop further R072 optimization and redirect resources to ES/NQ research lab with predeclared hypotheses and separate historical OOS periods.
