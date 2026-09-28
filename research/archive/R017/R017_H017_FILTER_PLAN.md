# R017 — H017 as a Trading Filter

Frozen before execution: 2026-09-27.

## Objective

H017 is now a confirmed low-movement regime. R017 tests whether avoiding continuation-style trades while H017 is active improves actual MES strategy performance.

This is the first H017 experiment where P&L, Profit Factor and drawdown are primary strategy metrics.

## Dataset

Strategy-development pool: 2020-01-01 through 2025-12-31.

This is **not** an OOS test of the strategies because 2020–2025 has already contributed to research.

2026 remains completely unopened.

## Frozen H017 regime

Definition remains unchanged:

- RV30 from exact 1m log returns;
- compression threshold = same-minute 10th percentile of the prior 60 sessions;
- first H017 compression event per session;
- event window 10:01–11:30 ET.

A strategy signal is classified as **INSIDE H017** if:

```text
H017_event_time <= signal_time <= H017_event_time + 30 minutes
```

Otherwise it is OUTSIDE H017.

The 30-minute active window is frozen because H017/H021 demonstrated persistence over the following 30 minutes.

## Execution model

All strategies use one MES contract.

Because the signal is known only after the signal bar closes:

- signal timestamp = end-of-bar timestamp;
- entry = Open of the immediately following 1m bar;
- entry must be exactly one minute after the signal row in the data;
- time exit uses the Close at the frozen horizon measured from signal close;
- no trade may cross session or contract.

Economic assumptions:

- MES value = $5 per index point;
- commission round trip = $1.88;
- slippage round trip = $2.50;
- total modeled cost = **$4.38/trade**.

No stop loss, target or parameter optimization is introduced in R017.

## Candidate strategies frozen simultaneously

### H024 / S1 — Morning ORB continuation
Signal:
- OR = 09:31–09:45 ET;
- first closing breakout after the OR;
- signal <= 11:30 ET;
- direction follows breakout.

Exit: 30-minute time exit.

### H025 / S2 — Previous RTH high/low breakout
Signal:
- first close above prior RTH high or below prior RTH low;
- same contract required;
- signal <= 11:30 ET.

Exit: 30-minute time exit.

### H026 / S3 — High-volume directional impulse
Signal:
- trailing 5m volume >= same-minute 80th percentile of prior 60 sessions;
- ER5 >= 0.70;
- direction = sign of trailing 5m return;
- first event/session;
- signal <= 11:30 ET.

Exit: 15-minute time exit.

## Statistical comparison

For each strategy:

```text
Filter delta = Mean net P&L OUTSIDE H017 - Mean net P&L INSIDE H017
```

The filter delta is estimated with OLS and session-clustered standard errors.

Primary p-values for H024–H026 are adjusted together with Benjamini-Hochberg FDR.

## Strategy metrics

For baseline, H017-active subset, and filtered strategy:

- trades;
- net P&L;
- expectancy/trade;
- Profit Factor;
- win rate;
- average win;
- average loss;
- max drawdown.

## Pre-registered gate

A strategy advances as an H017-filter candidate only if all are true:

- INSIDE H017 trades >= 30;
- filtered trades >= 150;
- filter delta >= +$3.00/trade;
- 95% CI of filter delta entirely > 0;
- BH q-value < 0.05;
- filtered expectancy > $0/trade;
- filtered expectancy improves baseline by >= $0.50/trade;
- filtered Profit Factor >= 1.10;
- filtered Profit Factor improves baseline by >= 0.05;
- filtered max drawdown is no worse than baseline.

## Interpretation

Passing R017 would justify a separate frozen strategy-validation protocol before 2026 is opened.

Failing R017 does not invalidate H017; it means H017 did not improve these three continuation-style strategies under the frozen execution rules.
