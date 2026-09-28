# B09 / R048–R052 — Regime Persistence, Duration & Transitions

Frozen before execution: 2026-09-28.

## Purpose

Measure directly whether recent movement/range states persist, how long they persist, and how they transition between LOW / NORMAL / HIGH.

This block focuses on **range/volatility persistence**, not direction.

## Common data policy

- Development pool: 2020-01-01 through 2025-12-31.
- 2026 remains completely unopened.
- Full RTH sessions only.
- RTH 1-minute timestamps are end-of-bar.
- Current-state anchors are non-overlapping 15-minute blocks ending at:
  09:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15, 11:30 ET.
- Each 15-minute block range is:
  ```text
  Range15Bps = (High15 - Low15) / Close15 × 10,000
  ```
- LOW / NORMAL / HIGH state is defined **separately for each clock-time block** using only the prior 60 eligible sessions:
  - LOW <= same-block q20
  - HIGH >= same-block q80
  - NORMAL otherwise
- Future block baselines and quantiles use only prior 60 eligible sessions for the corresponding future clock-time block.
- Outcomes may extend after 11:30 ET.
- No outcome crosses RTH session or contract.

## H059 / R048 — HIGH persists into the next 15-minute block

Event:
- current 15-minute block is HIGH.

Outcome:
```text
Next15ExpansionPct =
(next 15m range / historical mean next-block range - 1) × 100
```

Hypothesis:
a HIGH 15-minute block is followed by a next block at least 10% above its historical same-time baseline.

Gate:
- N >= 500
- sessions >= 300
- mean expansion >= +10%
- clustered 95% CI entirely > 0
- at least 4/6 years positive
- BH q < 0.05

## H060 / R049 — LOW persists into the next 15-minute block

Event:
- current 15-minute block is LOW.

Outcome:
```text
Next15DiscountPct =
(1 - next 15m range / historical mean next-block range) × 100
```

Gate:
- N >= 500
- sessions >= 300
- mean discount >= +10%
- clustered 95% CI entirely > 0
- at least 4/6 years positive
- BH q < 0.05

## H061 / R050 — HIGH persists for one hour

Event:
- current block is HIGH.

Primary outcome:
range of the block ending exactly 60 minutes after the current block, relative to that future block's prior-60-session mean.

```text
Plus60ExpansionPct =
(future block +60m range / historical same-block mean - 1) × 100
```

Gate:
- N >= 300
- sessions >= 250
- mean +60m expansion >= +5%
- 95% CI entirely > 0
- mean effects at +15m, +30m, +45m are all > 0
- at least 4/6 years positive at +60m
- BH q < 0.05

## H062 / R051 — LOW persists for one hour

Event:
- current block is LOW.

Primary outcome:
```text
Plus60DiscountPct =
(1 - future block +60m range / historical same-block mean) × 100
```

Gate:
- N >= 300
- sessions >= 250
- mean +60m discount >= +5%
- 95% CI entirely > 0
- mean effects at +15m, +30m, +45m are all > 0
- at least 4/6 years positive at +60m
- BH q < 0.05

## H063 / R052 — Extreme-state self-transition

For every eligible current block with a next block:

- HIGH self-transition = P(next state = HIGH | current state = HIGH)
- LOW self-transition = P(next state = LOW | current state = LOW)

Because q20/q80 define an unconditional reference frequency near 20%, test each self-transition probability against p0 = 0.20 using a one-sided exact binomial test.

Primary H063 p-value:
```text
max(p_high_self, p_low_self)
```
This conservative rule requires both sides to be significant.

Gate:
- HIGH current events >= 500
- LOW current events >= 500
- HIGH self-transition >= 30%
- LOW self-transition >= 30%
- both exact one-sided p-values < 0.05
- BH q < 0.05

## Descriptive duration outputs

For current HIGH and LOW events, report the future-state/range effect at:
- +15m
- +30m
- +45m
- +60m

Also report:
- 3×3 transition matrix LOW/NORMAL/HIGH → LOW/NORMAL/HIGH
- self-transition probabilities
- probability of still being the same extreme state after 2, 3 and 4 blocks where available
- effect by anchor clock time
- yearly stability

These are descriptive unless explicitly part of the gates above.

## Multiple testing

H059–H063 are primary hypotheses and their primary p-values are adjusted together using Benjamini-Hochberg FDR.

## Holdout

2026 is not used anywhere in B09.
