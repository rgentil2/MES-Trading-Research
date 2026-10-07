# POC Breakdown NinjaTrader Stage-2 Parity Runbook

## Objective
Reproduce the Python POC Breakdown strategy in NinjaTrader before any risk or parameter changes.

Expected Python reference:
- 2020-2025 only
- expected trades after news policy: **109**
- one MES
- SHORT only
- fixed H15 exit
- no stop/target during the first parity pass

## Files
- POCBreakdownParity.cs
- poc_news_blackouts_et.csv
- poc_rollover_sessions_et.csv
- poc_python_eligible_sessions_et.csv

## Frozen signal
1. prior complete RTH session POC:
   - typical price HLC3 per 1m bar
   - nearest 0.25 price bin
   - sum volume by bin
   - max-volume bin is POC
   - deterministic equal-volume tie break: nearest to volume-weighted profile mean
2. current RTH open > prior POC
3. FIRST bar touching prior POC must close below it
4. SHORT at next 1m open
5. time exit = 15 minutes from contact signal
6. news policy: USD High/Medium, flat T-5 and block entry T-5 through T+5
7. no prior-contract POC carried into rollover session

## NinjaTrader setup
- Instrument: MES DEC26 with Global merge policy = Merge non back adjusted
- Type: Minute
- Value: 1
- Trading hours: CME US Index Futures RTH
- Start: 2020-01-01
- End: 2025-12-31
- Break at EOD: enabled
- Order fill resolution: Standard
- Slippage: 0
- Commission: disabled for first parity run
- no optimizer

## Strategy parameters
- Contact cutoff ET = 113000
- Time exit minutes = 15
- Use news filter = true
- Require news file = true
- News CSV path = full path to poc_news_blackouts_et.csv
- Use rollover reset = true
- Require rollover file = true
- Rollover CSV path = full path to poc_rollover_sessions_et.csv
- Use Python session universe = true
- Require session universe file = true
- Session universe CSV path = full path to poc_python_eligible_sessions_et.csv
- Strict parity 2020-2025 = true
- Debug prints = false

## Acceptance
First target:
- exactly or approximately 109 trades
- >=99% date/side match against Python golden file
- investigate all extras/missing trades before judging P&L

## Risk layer after parity
Do NOT add it during the first parity run.

After signal parity is accepted:
- add/enable catastrophe SL = 0.45 ATR14_prev
- keep no fixed TP
- keep H15 timed exit
- then run realistic 1-tick + commission and 2-tick stress.

2026 remains CLOSED.
