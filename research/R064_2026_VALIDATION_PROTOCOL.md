# R064 — Final Regime Engine v1: 2026 Independent Validation Protocol

Pre-registered: 2026-09-28.

**This protocol is frozen but must not execute until a later explicit go/no-go.**

## Holdout

Validation outcomes:
- 2026-01-01 through latest available dataset date (currently expected through 2026-09-25).
- 2025 may be used only as historical warmup for rolling prior-60 thresholds at the beginning of 2026.
- All scored outcomes must have event/target dates in 2026.
- No 2026 result may be used to change v1 before pass/fail is declared.

## V1 — PREOPEN extreme separation

Use frozen R063 PREOPEN classification.

For predicted LOW:
- N >= 40
- mean opening-range discount >= 15%
- 95% CI >0

For predicted HIGH:
- N >= 40
- mean opening-range expansion >= 20%
- 95% CI >0

Additional:
- mean range ratios ordered LOW < NORMAL < HIGH.

## V2 — OPEN15 extreme separation

Use frozen R063 OPEN15 update.

For LOW:
- N >= 40
- next-range discount >= 15%
- CI >0

For HIGH:
- N >= 40
- next-range expansion >= 20%
- CI >0

Additional:
- LOW < NORMAL < HIGH mean range ratios.

## V3 — Dynamic +60m persistence

For frozen 15-minute same-clock states detected at morning anchors:

HIGH:
- N >= 150
- mean +60m expansion >= 25%
- CI >0

LOW:
- N >= 150
- mean +60m discount >= 20%
- CI >0

## V4 — Dynamic +240m persistence

HIGH:
- N >= 150
- mean +240m expansion >= 20%
- CI >0

LOW:
- N >= 150
- mean +240m discount >= 12%
- CI >0

## V5 — Transition structure

One-block self-transition:
- HIGH->HIGH >= 35%
- LOW->LOW >= 35%

One-block opposite-extreme transition:
- HIGH->LOW <= 10%
- LOW->HIGH <= 10%

At +240m:
- P(HIGH | initial HIGH) >= 30%
- P(LOW | initial LOW) >= 30%

## V6 — H017 LOW override

For 2026 H017 events:
- N >= 40
- mean next-30m range discount >= 20%
- 95% CI >0

If N < 40, V6 is INSUFFICIENT_SAMPLE rather than automatic failure.

## Overall validation decision

R063 v1 is considered independently validated only if:

- V1 passes;
- V2 passes;
- V3 passes;
- V4 passes;
- V5 passes;
- and V6 either passes or is INSUFFICIENT_SAMPLE.

No partial rescue, threshold relaxation, subgroup replacement, or parameter tuning is permitted.

## After validation

If PASS:
- freeze the regime engine as validated;
- then design a separate strategy research program that consumes its state output;
- do not claim profitability from the engine alone.

If FAIL:
- record failure exactly as observed;
- do not tune against 2026;
- v1 is archived or superseded only using future prospective data.
