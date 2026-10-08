# PDC v1.0 — Frozen Strategy Specification

Date: 2026-10-06
Status: FROZEN after Python ↔ NinjaTrader parity and Stage-3 execution robustness.
2026 remains closed.

## Frozen rules
- Instrument: MES
- Quantity: 1 contract
- Primary data: 1-minute
- RTH research window: 09:31–16:00 ET EOB labels
- Gap: 0.10 <= |RTH open - PDC| / ATR14_prev < 0.20
- PDC untouched during first five RTH minutes
- fifth-minute close must progress toward PDC
- entry: next 1-minute open
- SL: 0.30 ATR14_prev
- TP: PDC
- max time exit: 11:30 ET
- USD High/Medium news policy: flat T-5, block new entry T-5 through T+5
- rollover handling: no prior-contract PDC carried into a new contract
- one MES

## Stage-2 parity
- Python trades: 106
- NinjaTrader trades: 106
- date/side match: 106/106
- entry-price match: 106/106
- exit type match: 106/106
- residual exit-price differences explained by executable tick rounding / 1-minute feed convention

## Stage-3 realistic execution — commission accounting corrected 2026-10-07

IMPORTANT: NinjaTrader's exported `Profit` and `Total net profit` in these tested runs already include the configured commissions. The prior figures in this document mistakenly subtracted the commission twice. The corrected figures below use the reported `Total net profit` as net; commissions remain a separate informational field, NOT an additional deduction.

Base (1 tick of slippage, $1.88 RT commission):
- 106 trades
- **NET** P&L: **+$731.97**; expectancy **+$6.91/trade**
- Reported PF 1.63; reported max DD ~$205.04
- Commissions separately reported: $199.28 (already accounted for)

Stress (2 ticks of slippage, $1.88 RT commission):
- 106 trades
- **NET** P&L: **+$591.97**; expectancy **+$5.58/trade**
- Reported PF 1.49; reported max DD ~$217.54
- Commissions separately reported: $199.28 (already accounted for)

Local stop robustness (1 tick + commission, 106 trades):
- 0.25 ATR: **+$548.22 NET**, expectancy **+$5.17**
- 0.30 ATR: **+$731.97 NET**, expectancy **+$6.91**
- 0.35 ATR: **+$711.97 NET**, expectancy **+$6.72**

The earlier inferred effective-friction comparison to Python ($6.54/trade at 2 ticks) was based on incorrectly double-deducting commissions and must not be used.

Provenance: user-supplied NinjaTrader Summary screenshots. The full individual PDC 2-tick export is not currently available in the shared evidence set, so portfolio-level trade-by-trade realized drawdown is not yet calculated for all three strategies.

Decision:
- retain 0.30 ATR as the frozen center;
- no further PDC parameter tuning before 2026;
- any future change creates a new strategy version and cannot use 2026 for tuning.
