# R072 NinjaTrader Stage-2 Execution Replay Runbook

## Scope
This bundle is a **frozen-signal execution parity replay**, not yet the final live C# port of the R063 regime engine.

Python generates the exact 145 post-news R072 signals from 2020-2025. NinjaTrader replays them to validate:
- entry timing/fills
- H30 time exit
- news forced-flat behavior
- later catastrophe SL 0.70 ATR
- commission/slippage sensitivity

2026 remains CLOSED.

## Files
- R072SignalReplayParity.cs
- r072_python_signals_et.csv
- r072_news_blackouts_et.csv
- r072_python_eligible_sessions_et.csv
- r072_rollover_sessions_et.csv

## First parity run
- MES DEC26
- Merge non back adjusted
- 1 Minute
- CME US Index Futures RTH
- 2020-01-01 to 2025-12-31
- Break at EOD enabled
- Standard fills
- commission OFF
- slippage 0
- Time exit minutes = 30
- Use catastrophe stop = FALSE
- signal path = full local path to r072_python_signals_et.csv
- Use news exit = TRUE
- news path = full local path to r072_news_blackouts_et.csv
- Strict parity 2020-2025 = TRUE

Expected trades: **145**.

## After replay parity
Turn on:
- Use catastrophe stop = TRUE
- Catastrophe stop ATR = 0.70

Then test:
1. 1 tick slippage + $1.88 RT commission
2. 2 tick slippage + $1.88 RT commission

## Important
This validates the R072 execution/risk layer only.
A deployable R072 requires either:
- a full C# port of the R063 regime engine, or
- an explicitly designed external signal-generation architecture.

Do not call the replay file a live strategy generator.
