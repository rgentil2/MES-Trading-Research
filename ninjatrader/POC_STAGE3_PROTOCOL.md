# POC — NinjaTrader Stage 3 Protocol

Status: preregistered before NinjaTrader POC parity results.
2026 remains CLOSED.

## Gate 0 — signal parity
First reproduce the existing POC architecture:
- 109 Python trades
- H15
- news policy on
- catastrophe stop OFF
- commission OFF
- slippage 0

Do not inspect/tune risk settings until parity is accepted.

## Gate 1 — explicit risk layer
After signal parity:
- Use catastrophe stop = TRUE
- Catastrophe stop ATR = 0.45
- no fixed TP
- H15 retained

Because the Python research sample starts in 2020, the earliest POC event occurs before ATR14 is available. The common ATR-available development universe is therefore expected to be 108 trades. This historical warm-up issue is not relevant to a 2026 deployment because ATR history will already exist.

The 0.45 ATR stop is a catastrophe cap derived from 110% of the maximum observed 2020-2025 MAE, rounded upward. It is not selected to improve P&L.

## Gate 2 — realistic execution
With SL 0.45 ATR:
- commission = $1.88 RT
- slippage = 1 tick
- Standard historical fills
- no target
- H15

Required:
- net expectancy > 0 after commission
- PF after commission > 1.0
- no unexplained fill artifact
- maximum loss is explicitly bounded by the stop/fill model.

## Gate 3 — stress
Same strategy:
- commission = $1.88 RT
- slippage = 2 ticks

Required:
- stress expectancy > 0
- PF after commission > 1.0

## Gate 4 — time-exit neighborhood
Only the already-frozen local references are allowed:
- H10
- H15 center
- H20

Use 1 tick + commission + 0.45 ATR catastrophe stop.

Purpose:
- robustness only;
- do not switch to H20 merely because historical P&L is higher.

Interpretation:
- at least two of H10/H15/H20 should remain economically positive;
- H15 itself should remain positive;
- if H15 collapses under realistic execution, POC is parked rather than retuned.

## Prohibited
- no new stop values
- no fixed TP search
- no new timing values
- no news-window changes
- no 2026.
