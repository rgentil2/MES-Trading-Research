# R072 — NinjaTrader Stage 3 Protocol

Status: preregistered before NinjaTrader R072 replay/live-engine results.
2026 remains CLOSED.

## Gate 0 — execution replay
Run R072SignalReplayParity:
- expected post-news trades = 145
- H30
- catastrophe stop OFF
- commission OFF
- slippage 0

Purpose:
validate execution independent of signal generation.

## Gate 1 — live-engine parity
Run R072LiveEngineParity:
- wick = 0.50
- cutoff = 11:00 ET
- H30
- Python session universe ON for parity
- Python H017 reference ON first
- no catastrophe stop
- commission OFF
- slippage 0

Compare signals against the same 145-trade golden set.

Then turn Python H017 reference OFF and compare the fully computed H017 engine block-by-block.

R072 is not deployable until the live engine generates acceptable parity without replayed signals.

## Gate 2 — explicit risk layer
After execution/live-engine parity:
- catastrophe SL = 0.70 ATR14_prev
- no fixed TP
- H30

The 0.70 ATR stop is a catastrophe cap; it was not chosen to maximize historical PF.

## Gate 3 — realistic execution
- 1 MES
- commission $1.88 RT
- slippage 1 tick
- H30
- 0.70 ATR stop

Required:
- expectancy >0 after commission
- PF >1.0
- no unexplained execution mismatch.

## Gate 4 — stress
- same rules
- slippage 2 ticks
- commission $1.88 RT

Required:
- expectancy >0 after commission
- PF >1.0

## Existing robustness limitation
R072 previously failed the clean 20/30/40-minute plateau:
- H20 was too weak under stress
- H30 strongest
- H40 remained positive

Therefore passing NinjaTrader execution tests does NOT automatically freeze R072.

Allowed conclusion after Stage 3:
- retain as provisional if execution is robust;
- freeze only after explicitly resolving/accepting the horizon-robustness limitation without additional post-hoc tuning.

## Prohibited
- no new wick values
- no new cutoff values
- no new stop values
- no TP search
- no extra horizons
- no 2026.
