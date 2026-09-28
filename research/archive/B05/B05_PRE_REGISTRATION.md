# B05 / R034 — Staged Volatility-Regime Forecast

Frozen before execution: 2026-09-28.

## Purpose

Build a transparent, non-optimized regime-forecasting system from the volatility/range persistence signals already discovered in 2020–2025.

This is **development synthesis**, not independent validation.

2026 remains completely unopened.

## Regime states

Every range feature is converted into one of three states using only historical data available at that moment:

- LOW = value <= rolling q20 of prior 60 eligible sessions
- NORMAL = between q20 and q80
- HIGH = value >= rolling q80

State encoding:
- LOW = -1
- NORMAL = 0
- HIGH = +1

No weights are optimized.

## Stage A — 09:30 pre-open forecast (H043)

Inputs:
1. previous RTH-day range state;
2. current overnight-range state.

Score:
```text
PreOpenScore = PrevDayState + OvernightState
```

Prediction:
- LOW if score <= -1
- HIGH if score >= +1
- NORMAL if score = 0

Target:
current 09:31–10:00 opening range, classified LOW/NORMAL/HIGH against q20/q80 of prior 60 opening ranges.

Primary requirements:
- predicted LOW N >= 200;
- predicted HIGH N >= 200;
- LOW mean range discount >= 10% with CI > 0;
- HIGH mean range expansion >= 10% with CI > 0;
- LOW precision for actual LOW >= 30%;
- HIGH precision for actual HIGH >= 30%;
- mean target ratio ordered LOW < NORMAL < HIGH.

## Stage B — 09:45 updated forecast (H044)

Add:
3. first-15m range state.

```text
UpdateScore = PrevDayState + OvernightState + First15State
```

Prediction uses the same thresholds: <=-1 LOW, >=+1 HIGH, else NORMAL.

Target:
range of 09:46–10:15, classified against q20/q80 of prior 60 same-window ranges.

Same gate as H043.

## Stage C — H017 dynamic LOW override (H045)

H017 definition remains frozen:
- RV30 <= same-minute q10 of prior 60 sessions;
- first H017 event/session;
- event time 10:01–11:30 ET.

At an H017 event, the next-30m high-low range is compared with its same-minute prior-60-session baseline.

Prediction is always LOW.

Requirements:
- N >= 100;
- mean next-30m range discount >= 25%;
- CI entirely > 0;
- actual LOW precision (future range <= same-minute q20) >= 40%.

## Combined operating rule

The staged forecaster is intended to work as:

1. 09:30: PREOPEN forecast.
2. 09:45: replace with UPDATED forecast.
3. If H017 later appears: override current regime to LOW for the next 30 minutes.

## Metrics

For H043/H044:
- counts by predicted class;
- mean target range / baseline ratio;
- low/high range discount/expansion;
- class precision;
- confusion matrix;
- exact accuracy;
- extreme-only accuracy.

For H045:
- N;
- mean/median next30 range discount;
- CI/p-value;
- actual LOW precision.

## Holdout

2026 is not used anywhere in B05.
