# PDC NinjaTrader Stage-2 Parity Runbook

## Objective

Reproduce the Python PDC strategy in NinjaTrader Strategy Analyzer before any optimization.

Expected Python reference:
- strategy: PDC small-gap
- period: 2020-2025 only
- expected trades after news policy: 106
- quantity: 1 MES
- SL: 0.30 ATR14_prev
- TP: previous complete RTH close (PDC)
- forced exit: 11:30 ET
- USD High/Medium news blackout: flat T-5, no entry T-5 through T+5 inclusive

## Files

- PDCSmallGapParity.cs
- pdc_news_blackouts_et.csv
- pdc_rollover_sessions_et.csv

## NinjaTrader setup

1. Copy `PDCSmallGapParity.cs` into:
   `Documents\NinjaTrader 8\bin\Custom\Strategies\`
2. Open NinjaScript Editor and compile.
3. Open Strategy Analyzer.
4. Instrument/data:
   - MES
   - 1 Minute
   - Trading Hours: **CME US Index Futures RTH**
   - 2020-01-01 through 2025-12-31 only
   - use the same NinjaTrader merge/non-back-adjusted historical convention as the research data.
5. Strategy: `PDCSmallGapParity`.
6. Quantity is hard-coded to 1 MES for parity.
7. First parity run:
   - slippage: 0
   - include commission using the closest available template to $4.38 round trip
   - standard historical fill processing
   - NO optimizer.
8. In strategy parameters:
   - News CSV path = full local path to `pdc_news_blackouts_et.csv`
   - Rollover CSV path = full local path to `pdc_rollover_sessions_et.csv`
   - leave all frozen parameters at defaults.

## Frozen defaults

- Gap ATR min = 0.10
- Gap ATR max = 0.20
- Stop ATR multiple = 0.30
- Time exit ET = 113000
- Use news filter = true
- Use rollover reset = true
- Strict parity 2020-2025 = true

Do not optimize these during Stage 2.

## Expected mechanics

NinjaTrader stamps minute bars with their closing time. Therefore:
- 09:31 bar contains 09:30:00-09:30:59;
- first five RTH bars are labeled 09:31 through 09:35;
- signal is evaluated on the 09:35 EOB bar;
- the market entry submitted OnBarClose is intended for the next bar open at the 09:35 clock boundary.

## Parity acceptance

Export the Strategy Analyzer Trades grid and compare against the Python golden PDC file.

Target:
- expected trade count: 106
- >=99% date/side match
- <=1% trade-count difference
- no unexplained systematic timezone/rollover mismatches

Do not tune parameters to force a match.

## Known Stage-2 differences to audit

1. **Stop rounding**
   - Python research used a continuous 0.30*ATR price distance.
   - NinjaTrader requires executable tick prices.
   - This NinjaScript rounds the stop distance UP to the next MES tick, never tighter.

2. **Entry already through PDC**
   - Python skips a setup if the next-bar open has crossed the PDC before entry.
   - Standard 1-minute Strategy Analyzer cannot know that next open before submitting the market order.
   - The strategy detects such fills and immediately requests a flatten while printing a parity warning.
   - Any occurrence must be inspected manually.

3. **Intrabar stop/target sequencing**
   - Standard 1-minute historical bars do not reveal tick-by-tick order of high and low.
   - Stage 2 first checks signal parity.
   - Higher-resolution/tick fill testing belongs to Stage 3.

4. **News forced-flat sequencing**
   - The Python engine gives the T-5 minute OPEN precedence over that minute's price path.
   - NinjaTrader managed historical order processing may differ if another protective order fills in the same minute.
   - Document such cases rather than changing strategy parameters.

## After parity

Only after signal parity passes:
- test higher-resolution fills where data permits;
- test 1 tick and 2 tick slippage;
- test base/stress commissions;
- then freeze the implementation.

2026 remains closed.
