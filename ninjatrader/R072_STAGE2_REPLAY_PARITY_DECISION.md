# MES R072 — Stage 2 frozen-signal replay parity (2026-10-07)

**Verdict:** R072SignalReplayParity PASSES **frozen-signal EXECUTION REPLAY parity**, NOT yet self-contained live strategy generation. The 2026 holdout remains sealed. R072 remains provisional because H20/H30/H40 did not pass local plateau robustness.

## Test configuration
- MES, 1-minute, RTH, 2020-01-01..2025-12-31.
- NinjaTrader `R072SignalReplayParity` with the frozen 145-signal CSV generated from Python; `Use catastrophe stop = false`, `Time exit minutes = 30`, commission off, slippage 0, Standard historical fills.
- USD medium/high frozen news calendar.

## Entry and exit parity: NT CSV vs Stage 2 Python golden
- Python/NT: 145/145 trades; exactly 68 longs and 77 shorts.
- 145/145 matching date/side; 145/145 matching ENTRY PRICES.
- All NT entry timestamps appear +1 minute vs Python's modeled actual entry (different bar labeling).
- 145/145 EXIT TYPES agree: 133 timed H30 and 12 news forced-exit.
- 77/145 exit prices exactly equal: all 12 news exits, plus 65 timed.
- The remaining 68 differences in H30 price: 28 at -0.25, 36 at +0.25, 2 at -0.50, 1 at +0.50 and 1 at -1.25 ES index points. Maximum price delta 5 ticks. All H30 NT exit timestamp labels are +1 minute vs Python; news labels match.
- No missing or extra entries.
- Python gross +$1,726.25; NT gross +$1,722.50, difference -$3.75 across six years.

## Execution replay gross (without any trading costs)
- NinjaTrader gross profit +$5,048.75; gross loss -$3,326.25; net +$1,722.50.
- Gross PF 1.52; gross DD $456.25; 145 trades, 79 winners / 65 losers / 1 even; worst trade -$282.50.

## *Estimated* friction scenarios (not yet executed in NT)
If applying uniform total historical RT friction of $4.38 and $6.57 to the current zero-cost NT trade P&L, respectively:
| Metric | Base $4.38 RT | Stress $6.57 RT |
|---|---:|---:|
| net | +$1,087.40 | +$769.85 |
| expectancy | +$7.50 | +$5.31 |
| PF | 1.3003 | 1.2037 |
| max DD | $500.05 | $521.95 |
| 2025 net | -$216.37 | -$268.93 |
| positive semesters | 7/11 | 7/11 |

These are arithmetic cost overlays only, NOT NinjaTrader slippage stress outcomes; historical slippage configuration can affect orders differently.

## Next validation
1. Run `R072LiveEngineParity` with H017 Python reference ON as an intermediate diagnostic, news/rollover/eligible sessions ON, stop OFF and no costs. Compare dates/sides/entries with golden.
2. Repeat the same live engine with H017 Python reference OFF for fully independent causal signal construction.
3. Only if the live engine itself passes signal parity should the risk-layer SL .70 ATR and cost stress of 1 and 2 ticks be used to evaluate potential deployability.
4. Due to the failed H20/H30/H40 neighborhood gate, R072 is still PROVISIONAL despite parity; do not call it frozen or funded-account-ready.

## Evidence source
- NinjaTrader screenshot and `NinjaTrader Grid 2026-10-07 09-17 p. m..csv` supplied 2026-10-07.
- Golden: `mes-stage2-python-golden` artifact, R072_PYTHON_GOLDEN_TRADES.csv.
