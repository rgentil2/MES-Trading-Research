# R018 — H017 Short-Range Edge Reversion Strategy

Frozen before execution: 2026-09-27.

## Rationale

H017 is a confirmed regime of persistent low volatility and low absolute movement.

R016 found no evidence for blindly fading breakouts, and R017 found no value in using H017 as a blanket filter on previously rejected continuation strategies.

R018 therefore tests a strategy designed specifically for low-movement conditions: fading the edge of a short rolling range while H017 is active.

## Dataset

Strategy-development pool: 2020–2025.

2026 remains completely unopened.

## H017 regime

Unchanged:

- RV30 from exact 1m log returns;
- same-minute 10th percentile over prior 60 sessions;
- first compression event/session;
- H017 signal between 10:01 and 11:30 ET;
- active regime window = H017 event through +30 minutes, capped at 11:30 for new entries.

## Rolling range

At each eligible bar inside the active H017 window:

- use the exact trailing 15 bars including the current bar;
- RangeHigh15 = max High;
- RangeLow15 = min Low;
- RangePosition = (Close - RangeLow15) / (RangeHigh15 - RangeLow15).

## Strategy signal

First eligible range-edge signal per H017 session:

- UPPER_EDGE if RangePosition >= 0.90 → SHORT;
- LOWER_EDGE if RangePosition <= 0.10 → LONG.

If no edge is reached during the active H017 window, there is no trade.

Only one trade per session.

## Execution

- signal known at bar close;
- enter at the Open of the immediately following exact 1m bar;
- exit at the Close exactly 15 minutes after the signal timestamp;
- one MES contract;
- no stop;
- no target;
- no re-entry.

Costs:
- commission RT = $1.88;
- slippage RT = $2.50;
- total = $4.38/trade;
- MES point value = $5.

## H027

A symmetric range-edge fade inside H017 has positive net expectancy after modeled costs.

Primary metric: net P&L per trade in USD.

## Pre-registered candidate gate

H027 advances to a separate robustness phase only if all are true:

- >= 200 trades;
- >= 200 sessions;
- mean net expectancy >= +$1.00/trade;
- 95% CI of mean net P&L entirely > 0;
- p-value < 0.05;
- Profit Factor >= 1.15;
- at least 4 of 6 years have positive expectancy;
- net P&L > 0.

Side-specific LONG/SHORT results are descriptive only and cannot replace a failed combined strategy.

## Metrics

- trades;
- net P&L;
- expectancy;
- Profit Factor;
- win rate;
- avg win / avg loss;
- max drawdown;
- yearly expectancy;
- UPPER_EDGE vs LOWER_EDGE descriptive breakdown.

## Holdout

2026 is not used anywhere in R018.
