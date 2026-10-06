# NinjaTrader MES Research — Stage 2 Runbook

Purpose: reproduce the Python MES candidate strategies in NinjaTrader Strategy Analyzer before any optimization.

## Hard boundary

**Do not include any 2026 data.**
Backtest range for parity: 2020-01-01 through 2025-12-31 only.

## Strategy Analyzer baseline settings

Use:
- primary series: MES 1 Minute;
- RTH session definition matching the Python source (09:30-16:00 ET);
- Calculate: OnBarClose for signal logic;
- quantity: 1 contract;
- slippage: 0 ticks for the first parity pass;
- commissions: enabled and configured as closely as possible to $4.38 round trip;
- no optimization;
- local historical data matching the research source/merge convention;
- do not use 2026.

NinjaTrader's historical fill processor can differ from Python's bar-path assumptions. The first goal is signal parity, not exact P&L parity.

## Files produced by Python

The Stage-2 golden artifact contains:
- PDC_PYTHON_GOLDEN_TRADES.csv
- POC_PYTHON_GOLDEN_TRADES.csv
- R072_PYTHON_GOLDEN_TRADES.csv
- per-strategy yearly counts/P&L
- PYTHON_GOLDEN_SUMMARY.csv
- PARITY_MANIFEST.json

Compare NinjaTrader exports against these files.

## Pass A — signal parity

For each strategy export at minimum:
- strategy
- date
- side
- signal time
- entry time
- entry price

Required:
- >=99% date/side match;
- trade-count difference <=1%;
- every systematic mismatch explained.

Expected counts:
- PDC: 106
- POC: 109
- R072: 145

Do not tune a parameter to make counts match. A count mismatch means implementation/data/timestamp parity must be investigated.

## Pass B — execution parity

After signals match, compare:
- entry fill
- timed exit
- PDC target
- PDC 0.30 ATR stop
- news T-5 forced flat
- commissions

For PDC, Python resolves an ambiguous same-minute target+stop bar conservatively as STOP FIRST.

## Pass C — realistic fill sensitivity

Only after Pass A/B:
- enable more granular historical fill processing where supported;
- test 1 tick slippage;
- test 2 ticks slippage;
- compare against the zero-slippage parity baseline.

These are execution stress tests, not strategy parameter optimization.

## NinjaTrader order-handling notes

NinjaTrader's OnBarUpdate is controlled by the Calculate setting. If a strategy adds additional data series, its logic must explicitly handle BarsInProgress.

For PDC, stop and target orders should be associated with the same named entry. NinjaTrader's managed SetStopLoss and SetProfitTarget methods submit protective orders when the entry fills and can be tied OCO.

## Current Stage-1 centers

PDC:
- gap 0.10-0.20 ATR
- first five minutes toward untouched PDC
- entry next open
- stop 0.30 ATR
- target PDC
- exit <=11:30
- frozen news policy

POC:
- prior POC first-contact breakdown
- short next open
- H15 time exit for parity
- frozen news policy

R072:
- W0.50
- cutoff 11:00
- H30
- frozen news policy
- provisional because local-horizon plateau did not pass

## What counts as Stage 2 complete

PDC and POC:
- NinjaTrader signal parity accepted;
- fill differences documented;
- no unexplained timezone or rollover errors.

R072:
- parity can be completed, but it remains provisional until its robustness issue is resolved.

Only then proceed to Stage 3.
