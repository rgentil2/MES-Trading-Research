# R063 — Final MES Volatility Regime Engine v1

Frozen: 2026-09-28.

## Scope

This is the final development specification of the project's volatility/range regime engine before any 2026 data is opened.

The engine predicts **movement magnitude / range regime**, not price direction.

No parameter in this document may be changed after 2026 validation begins.

## State vocabulary

All state variables use:

- LOW = -1
- NORMAL = 0
- HIGH = +1

Unless explicitly stated otherwise, LOW/HIGH thresholds use q20/q80 of the prior 60 eligible historical observations only.

## Feature 1 — Five-session range context

```text
AvgRange5 = mean full-RTH RangeBps over the previous 5 same-contract sessions
```

State:
- LOW <= rolling q20
- HIGH >= rolling q80
- NORMAL otherwise

This feature does **not** directly change the engine class. It is a higher-horizon support/conflict indicator.

## Feature 2 — Previous RTH-day range

```text
PrevDayRangeBps = (PrevHigh - PrevLow) / PrevClose × 10,000
```

State uses prior-60 q20/q80.

## Feature 3 — Overnight range

Overnight window:
- starts with 18:01 ET end-bar after prior RTH;
- ends with 09:30 ET end-bar before current RTH.

```text
OvernightRangeBps = (ONHigh - ONLow) / ONClose × 10,000
```

State uses prior-60 eligible overnight q20/q80.

## Stage 1 — PREOPEN, available at 09:30 ET

```text
PreOpenScore = PrevDayState + OvernightState
```

Classification:
- score <= -1 -> LOW
- score = 0 -> NORMAL
- score >= +1 -> HIGH

Five-day context supplies SUPPORT:
- ALIGNED if FiveDayState equals an extreme PREOPEN state;
- CONFLICT if FiveDayState is the opposite extreme;
- NEUTRAL otherwise.

Development calibration from B05:
- LOW expected opening-range ratio ≈ 0.704
- NORMAL ≈ 0.950
- HIGH ≈ 1.419

These are development calibration values, not guaranteed live forecasts.

## Stage 2 — OPEN15 UPDATE, available when 09:45 bar closes

First-15m range:
- 09:31–09:45 ET.

State uses q20/q80 of prior 60 same-window first-15m ranges.

```text
UpdateScore =
PrevDayState + OvernightState + First15State
```

Classification:
- score <= -1 -> LOW
- score = 0 -> NORMAL
- score >= +1 -> HIGH

Five-day context remains a support/conflict indicator only.

Development calibration from B05:
- LOW next-range ratio ≈ 0.693
- NORMAL ≈ 0.954
- HIGH ≈ 1.438

## Stage 3 — DYNAMIC 15m STATE

From the 09:45 block onward, every completed non-overlapping 15-minute block can generate a dynamic state.

For each clock-time block:

```text
Range15Bps = (High15 - Low15) / Close15 × 10,000
```

Thresholds:
- same-clock q20/q80 of prior 60 eligible sessions.

Once a new dynamic block is complete:
- dynamic LOW -> engine state LOW;
- dynamic NORMAL -> engine state NORMAL;
- dynamic HIGH -> engine state HIGH.

The latest completed dynamic block supersedes the earlier PREOPEN/OPEN15 class.

## H017 dynamic LOW override

The frozen H017 definition remains:

- RV30 <= same-minute q10 of prior 60 sessions;
- first H017 event/session;
- event time 10:01–11:30 ET.

If H017 is active:
- engine state = LOW for 30 minutes after H017 detection;
- no new entry signal is created by the engine itself;
- H017 only changes the regime label.

H017 override takes precedence over the current 15-minute state during its 30-minute window.

## Dynamic range calibration table

Development estimates from B09–B11:

| Horizon | HIGH multiplier | LOW multiplier |
|---|---:|---:|
| +15m | 1.5423 | 0.6448 |
| +60m | 1.5234 | 0.6592 |
| +120m | 1.5311 | 0.6626 |
| +180m | 1.4899 | 0.6951 |
| +240m | 1.4399 | 0.7455 |

NORMAL is reported as baseline/neutral and is not assigned a fitted multiplier beyond 1.00 in v1.

For H017:
- development next-30m range multiplier ≈ 0.611.

## Transition information

Development one-block transition matrix:

| Current | LOW next | NORMAL next | HIGH next |
|---|---:|---:|---:|
| LOW | 52.63% | 43.45% | 3.92% |
| NORMAL | 19.78% | 64.71% | 15.51% |
| HIGH | 2.52% | 43.55% | 53.93% |

At +240m:
- P(HIGH | initial HIGH) ≈ 42.99%
- P(LOW | initial LOW) ≈ 43.97%

These values are descriptive development calibration and are frozen for comparison against 2026.

## Engine output contract

At any evaluation time, the engine returns:

- timestamp ET;
- stage: PREOPEN / OPEN15 / DYNAMIC / H017_OVERRIDE;
- regime: LOW / NORMAL / HIGH;
- five-day support: ALIGNED / NEUTRAL / CONFLICT when available;
- latest component states;
- applicable expected range multiplier(s);
- minutes since last state update;
- explicit flag that no directional prediction is provided.

## What v1 does NOT do

It does not:
- predict UP/DOWN;
- produce entries/exits;
- choose stops or targets;
- size positions;
- optimize thresholds;
- use machine learning;
- change q20/q80, q10 H017, or 60-session references;
- use 2026 during construction.

## Status

FROZEN_AWAITING_2026_VALIDATION.
