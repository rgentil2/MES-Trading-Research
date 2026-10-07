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

## Stage-3 realistic execution
Base:
- commission: $1.88 RT
- slippage: 1 tick in Strategy Analyzer
- center SL 0.30 ATR
- commission-adjusted P&L: +$532.69
- commission-adjusted expectancy: +$5.03/trade
- reported DD before commission accounting: ~$205
- worst trade: about -$117

Stress:
- commission: $1.88 RT
- slippage: 2 ticks
- commission-adjusted P&L: +$392.69
- commission-adjusted expectancy: +$3.70/trade
- effective total friction ~ $6.54/trade vs Python stress assumption $6.57
- PF remains >1
- DD ~$218

Local stop robustness at 1 tick + commission:
- 0.25 ATR: commission-adjusted P&L +$348.94, expectancy +$3.29
- 0.30 ATR: commission-adjusted P&L +$532.69, expectancy +$5.03
- 0.35 ATR: commission-adjusted P&L +$512.69, expectancy +$4.84

Decision:
- retain 0.30 ATR as the frozen center;
- no further PDC parameter tuning before 2026;
- any future change creates a new strategy version and cannot use 2026 for tuning.
