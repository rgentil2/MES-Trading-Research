# B11 / R058–R062 — Extended Intraday Regime Persistence

Frozen before execution: 2026-09-28.

## Purpose

Extend the frozen B09/B10 range-regime framework from +120 minutes to +180 and +240 minutes.

This remains development research on 2020–2025.

2026 remains completely unopened.

## Frozen state definition

Unchanged from B09/B10:

- full RTH sessions only;
- anchor 15-minute blocks end at 09:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15, 11:30 ET;
- Range15Bps = (High15 - Low15) / Close15 × 10,000;
- same-clock historical reference uses prior 60 eligible sessions only;
- LOW <= q20;
- HIGH >= q80;
- NORMAL otherwise;
- future outcomes remain within the same RTH session and contract.

Future horizons are evaluated every 15 minutes from +15 through +240 minutes.

## H069 / R058 — HIGH persists to +180m

Primary outcome:
future +180m block range relative to its same-clock prior-60-session historical mean.

Gate:
- N >= 1,000
- sessions >= 500
- mean expansion >= +10%
- 95% CI > 0
- all mean effects from +15 through +165 > 0
- >=4/6 years positive at +180
- BH q <0.05

## H070 / R059 — LOW persists to +180m

Gate:
- N >= 1,000
- sessions >= 500
- mean discount >= +5%
- CI >0
- all mean effects +15 through +165 >0
- >=4/6 years positive
- BH q <0.05

## H071 / R060 — HIGH persists to +240m

Gate:
- N >= 1,000
- sessions >= 500
- mean expansion >= +5%
- CI >0
- all mean effects +15 through +225 >0
- >=4/6 years positive
- BH q <0.05

## H072 / R061 — LOW persists to +240m

Gate:
- N >= 1,000
- sessions >= 500
- mean discount >= +5%
- CI >0
- all mean effects +15 through +225 >0
- >=4/6 years positive
- BH q <0.05

## H073 / R062 — Extreme-state information remains at +240m

Tests:
- P(+240 HIGH | current HIGH) > 20%
- P(+240 LOW | current LOW) > 20%

Primary p-value = max(two one-sided exact binomial p-values).

Gate:
- HIGH events >=1,000
- LOW events >=1,000
- HIGH-at-+240 >=25%
- LOW-at-+240 >=25%
- both p-values <0.05
- BH q <0.05

## Descriptive decay outputs

At +15, +30, ..., +240 report:
- mean effect;
- median effect;
- same-state probability;
- opposite-state probability.

Report:
- first horizon below 50% of +15m effect;
- first horizon below +10% practical effect;
- effect at +120, +180, +240;
- state probabilities at +120, +180, +240.

If no decay threshold is reached by +240m, report >240m and do not extrapolate.

## Holdout

2026 is not used anywhere in B11.
