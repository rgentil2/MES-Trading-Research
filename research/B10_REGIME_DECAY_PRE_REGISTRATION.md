# B10 / R053–R057 — Maximum Duration & Decay of Volatility Regimes

Frozen before execution: 2026-09-28.

## Purpose

Extend B09 beyond +60 minutes and estimate how long HIGH and LOW 15-minute range regimes retain predictive information.

This is development research on 2020–2025, not independent validation.

2026 remains completely unopened.

## Common definition

Identical to B09:

- full RTH sessions only;
- non-overlapping 15-minute blocks;
- anchor blocks end at 09:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15, 11:30 ET;
- Range15Bps = (High15 - Low15) / Close15 × 10,000;
- same-clock rolling reference uses only the prior 60 eligible sessions;
- LOW <= q20;
- HIGH >= q80;
- NORMAL otherwise;
- outcomes remain in the same RTH session and contract.

Future horizons:
+15, +30, +45, +60, +75, +90, +105, +120 minutes.

## H064 / R053 — HIGH persists to +90 minutes

Event:
current 15-minute block is HIGH.

Primary outcome:
```text
Plus90ExpansionPct =
(future +90m block range / historical same-clock mean - 1) × 100
```

Gate:
- N >= 1,000
- sessions >= 500
- mean expansion >= +20%
- 95% CI entirely > 0
- mean effects at +15, +30, +45, +60, +75 all > 0
- >=4/6 years positive at +90
- BH q <0.05

## H065 / R054 — LOW persists to +90 minutes

Primary outcome:
```text
Plus90DiscountPct =
(1 - future +90m block range / historical same-clock mean) × 100
```

Gate:
- N >= 1,000
- sessions >= 500
- mean discount >= +15%
- CI >0
- intermediate +15 through +75 mean effects all >0
- >=4/6 years positive
- BH q <0.05

## H066 / R055 — HIGH persists to +120 minutes

Gate:
- N >= 1,000
- sessions >= 500
- mean +120m expansion >= +15%
- CI >0
- all intermediate mean effects +15 through +105 >0
- >=4/6 years positive
- BH q <0.05

## H067 / R056 — LOW persists to +120 minutes

Gate:
- N >= 1,000
- sessions >= 500
- mean +120m discount >= +10%
- CI >0
- all intermediate mean effects +15 through +105 >0
- >=4/6 years positive
- BH q <0.05

## H068 / R057 — Extreme-state information remains above unconditional at +120m

For current HIGH and LOW events, classify the +120m future block using its own same-clock q20/q80.

Tests:
- P(+120 HIGH | current HIGH) > 20%
- P(+120 LOW | current LOW) > 20%

Primary p-value = max(one-sided exact binomial p-values).

Gate:
- HIGH events >= 1,000
- LOW events >= 1,000
- HIGH-at-+120 rate >= 30%
- LOW-at-+120 rate >= 30%
- both p-values <0.05
- BH q <0.05

## Descriptive duration / decay outputs

For HIGH and LOW separately report at every horizon:
- mean effect;
- median effect;
- same-state probability;
- opposite-state probability.

Also report continuous-run survival:
- probability the regime remains continuously HIGH/LOW for at least 15, 30, 45, 60, 75, 90, 105 and 120 minutes;
- median continuous same-state run length, censored at 120m;
- first horizon where mean effect falls below 50% of its +15m effect;
- first horizon where mean effect falls below the practical threshold:
  - HIGH: +10%
  - LOW: +10%.

If no such horizon occurs by +120m, report ">120m"; do not extrapolate beyond observed data.

## Multiple testing

H064–H068 primary p-values are adjusted together with Benjamini-Hochberg FDR.

## Holdout

2026 is not used anywhere in B10.
