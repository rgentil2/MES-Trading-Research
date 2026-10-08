# R072 — fully autonomous NinjaTrader stress audit (2026-10-07)

**State: HOLD / NOT approved for funded live deployment. 2026 remains sealed.**

## Configuration

- Strategy: `R072LiveEngineParity` (signal generation within NinjaScript, without historical Python H017 reference or Python eligible-session CSV).
- Instrument: one MES, NinjaTrader `MES DEC26` with non-back-adjusted merge, 1-minute, RTH.
- Period: 2020-01-01 through 2025-12-31.
- Frozen wick threshold = 0.50; signal cutoff = 11:00 ET; time exit = H30.
- USD high/medium news and rollover input CSVs retained.
- Catastrophe stop enabled: 0.70 prior-session ATR.
- Commission $1.88 round trip; slippage 2 ticks in Strategy Analyzer.
- Source: user's export `NinjaTrader Grid 2026-10-07 10-44 p. m..csv`.

## Overall outcome

| Metric | Value |
|---|---:|
| Trades | 149 |
| Total net profit inclusive of commission | +$998.63 |
| Round-trip commissions total | $280.12 |
| Average net per trade | +$6.70 |
| Profit Factor (net) | 1.253 |
| Win rate | 48.99% |
| Maximum closed-trade drawdown | $621.93 |
| Largest net loss | -$289.38 |
| Longs | 71 |
| Shorts | 78 |
| Time exits | 137 |
| News exits | 12 |
| Stop exits | 0 |

**Caution:** No catastrophe-stop exits is not proof that actual stop orders are reliably submitted; order/audit trace remains necessary. Across the 145 Python-referenced entries all reported MAE values were below the nominal 0.70 × ATR × $5 stop threshold (largest MAE/threshold ratio approx 0.912). For the four extra trades, causally computed ATR and order placement require independent validation.

## Yearly stress results

| Year | N | Net USD | PF | Exp/trade |
|---|---:|---:|---:|---:|
| 2020 | 4 | +49.98 | 1.588 | +12.50 |
| 2021 | 32 | -120.16 | 0.851 | -3.75 |
| 2022 | 26 | +188.62 | 1.208 | +7.25 |
| 2023 | 27 | +239.24 | 1.653 | +8.86 |
| 2024 | 35 | +976.70 | 2.628 | +27.91 |
| 2025 | 25 | -335.75 | 0.718 | -13.43 |

- 2024 accounts for 97.8% of the total six-year net; exclude it and the other five years sum to **+$21.93**.
- 2024H2 alone = +$879.27.
- 2025H1 = -$226.95 and 2025H2 = -$108.80.
- 4/6 years positive, or 3/5 among 2021–2025.
- 7/11 observed (non-empty) semesters positive (2020H1 has no trades).

## Direction splits

| Side | N | Net USD | PF |
|---|---:|---:|---:|
| Long | 71 | -232.23 | 0.894 |
| Short | 78 | +1,230.86 | 1.696 |

**Direction annual net (LONG / SHORT)**:
- 2020: +101.87 / -51.89
- 2021: -265.06 / +144.90
- 2022: -154.45 / +343.07
- 2023: -99.46 / +338.70
- 2024: +406.80 / +569.90
- 2025: -221.93 / -113.82

Both directions negative in 2025; filtering out losing LONGs from this in-sample result would require preregistration and independent validation, not retroactive claiming.

## Four extras compared with Python's 145-signal reference

The autonomous engine retains 145/145 matching signal times/sides and adds four new trades outside the Python-complete-session universe.

| Date | Side | Net with 2 ticks |
|---|---|---:|
| 2021-11-26 | Long | -$100.63 |
| 2022-05-23 | Long | +$84.37 |
| 2024-08-02 | Short | +$311.87 |
| 2025-04-04 | Long | -$61.88 |
| **Total** | | **+$233.73** |

- 2024-08-02's +$311.87 is ~31.2% of entire 149-trade result.
- Excluding all 4 extra trades reverts net P&L to **+$764.90**, consistent with earlier 145-trade replay's 2-tick stress, but that alone is not an independent data-quality proof.
- 2021-11-26 falls on the Friday after US Thanksgiving, a modified US-market holiday session; verify precise exchange session hours and Ninja historical data.
- Determine whether each of four excluded Python days is a legitimate early close, a missing minute, an incomplete contract, or a data-vendor difference before any production use.
- Do not impose Python's research universe as a live filter.

## Research decision

**Not frozen for funded account deployment.** Although stress-test expectancy and PF are nominally positive, major issues:
1. Strong temporal concentration in 2024, weak 2025, and long-side drag.
2. 149 trades over approximately six calendar years ~2.07 trades/month; below the previously discussed 5 trades/month aspirational target.
3. 149 historical trades <150 and only 124 trades in 2020–2024, should a gate require 150 in those five years.
4. 2-tick PF = 1.253, effectively borderline vs a 1.25 hurdle.
5. Catastrophe-stop order-placement and precise 1-minute historical fill fidelity not yet demonstrated.
6. Four extra sessions need data-quality verification before they count as research evidence.
7. Strong performance on SHORTs is not enough to change direction rules on the same data.

## Recommended next actions
1. Audit all four unusual dates (session completeness, rollover, holiday/early close, bar timestamps).
2. Export NinjaTrader **Orders**/**Executions** or enable order tracing for a designated test to prove the protective 0.70 ATR orders are active. Separately use a non-scored sandbox run with a deliberately tight SL solely to exercise the stop pathway, then restore frozen 0.70 ATR.
3. Review temporally pre-specified stress by year/semester and assess whether to close/park R072; no in-sample parameter rescue and no 2026 opening.
4. Evaluate independent strategies/instruments (ES/NQ) on frozen pre-2026 data with explicit experiment budgets and proper market-regime isolation.
