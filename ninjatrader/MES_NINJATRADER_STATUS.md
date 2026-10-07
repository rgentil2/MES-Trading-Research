# MES NinjaTrader Migration Status

Updated: 2026-10-07

2026 remains CLOSED.

## PDC — FROZEN v1.0

Signal and execution:
- parity 106/106 Python ↔ NinjaTrader
- 1 MES
- gap 0.10-0.20 ATR
- SL 0.30 ATR
- TP=PDC
- exit 11:30 ET
- news T-5/T+5
- rollover/session parity controls

Stage 3:
- realistic 1-tick + $1.88 RT commission: positive
- 2-tick stress + commission: positive
- local stop neighborhood 0.25/0.30/0.35 ATR: all positive

Decision:
- no further PDC tuning before 2026.

## POC — READY FOR PARITY

First run:
- POCBreakdownParity.cs
- 2020-2025
- expected Python trades = 109
- SHORT only
- H15
- news enabled
- commission OFF
- slippage 0
- catastrophe stop OFF

After 109-trade signal parity:
- enable catastrophe SL 0.45 ATR
- no fixed TP
- H15 remains
- note: the earliest historical trade may be unavailable to the ATR-risk layer because the 2020-starting research sample has not yet accumulated ATR14; common ATR-available historical universe is 108 trades.
- then test 1-tick + $1.88 RT and 2-tick stress.

## R072 — REPLAY READY / LIVE ENGINE PORT IN PROGRESS

Execution replay:
- 166 base Python signals
- 21 blocked by news
- 145 frozen post-news signals
- H30
- catastrophe SL 0.70 ATR available after replay parity
- no TP

Important:
- R072SignalReplayParity.cs validates execution only.
- it is not a deployable live signal generator.

Live engine port:
- dynamic HIGH state is based on 15-minute range bps versus prior-60 same-block q80
- H017 low-volatility override uses prior-60 same-minute q10 of RV30
- wick failure threshold 0.50
- first valid signal/session
- cutoff 11:00 ET
- inverse direction
- block-level Python engine reference is the parity authority
- Python streaming emulation now proves exact 166/166 pre-news signal parity:
  - block 100%
  - time 100%
  - direction 100%
  - entry price 100%
- R072LiveEngineParity.cs has been created with optional Python-H017 parity mode and fully computed H017 mode.
- block-level NinjaTrader audit CSV + automatic comparator are available.

## Automatic comparison

research/compare_ninjatrader_parity.py now supports the user's actual localized NinjaTrader export:
- semicolon-separated CSV
- comma decimals
- Market pos.
- localized AM/PM strings

For POC/R072 exports, compare:
- count
- date/side
- entry price
- systematic timestamp offset
- exit price where applicable.

## Remaining sequence

1. POC Stage-2 parity
2. POC risk/cost stress
3. POC freeze or park
4. R072 replay parity
5. R072 0.70 ATR risk/cost stress
6. complete live R072 engine port and block parity
7. decide R072 freeze/park
8. only then open 2026 for frozen deployable strategies
