# R003 Decision — REJECT H005/H006

## Development window

2020-01-01 through 2024-12-31 only.

The 2025 validation set and 2026 pseudo-forward set were not opened.

## H005 — First UPPER 15-minute OR breakout

- Eligible events: 648
- Sessions: 648
- Mean 30-minute directional return: +1.955 bps
- Median: +3.174 bps
- Continuation rate: 56.48%
- p-value: 0.0682
- FDR q-value: 0.1335
- 95% CI: [-0.146, 4.056] bps
- Positive development years: 4/5

The effect is economically interesting but does not satisfy the pre-registered statistical gate because the adjusted q-value is above 0.05 and the confidence interval crosses zero.

**Decision: FAIL.**

## H006 — First LOWER 15-minute OR breakout

- Eligible events: 630
- Sessions: 630
- Mean 30-minute directional return: -1.921 bps
- Median: -0.594 bps
- Continuation rate: 47.62%
- p-value: 0.1335
- FDR q-value: 0.1335
- 95% CI: [-4.430, 0.588] bps
- Positive development years: 2/5

The mean is opposite to the breakout-continuation hypothesis.

**Decision: FAIL.**

## Research decision

H005 and H006 do not advance to 2025 validation.

The upper-side result is recorded as a development observation, but the project will not relax the gate or open 2025 to rescue it. Any future upper-only ORB hypothesis must be registered as a new experiment with a separate rationale and frozen rules before touching holdout data.
