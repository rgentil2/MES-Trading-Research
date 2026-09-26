# R002 Decision — REJECT H003/H004

## Development window

2020-01-01 through 2024-12-31 only.

The 2025 validation set and 2026 pseudo-forward set were not opened.

## Frozen regime thresholds

Trailing 30-minute realized-volatility terciles among eligible development events:

- LOW / MID cutoff: 13.710 bps
- MID / HIGH cutoff: 23.193 bps

## H003 — WITH_TREND + HIGH volatility

- N: 2,763
- Sessions: 659
- Mean 15m continuation score: +0.056 bps
- p-value: 0.9282
- FDR q-value: 0.9282
- 95% CI: [-1.163, 1.275]
- Development years with hypothesized sign: 3/5

**Decision: FAIL.**

## H004 — COUNTER_TREND + LOW volatility

- N: 80
- Sessions: 62
- Mean 15m continuation score: -0.666 bps
- p-value: 0.4895
- FDR q-value: 0.9282
- 95% CI: [-2.556, 1.223]
- Development years with hypothesized sign: 2/4

**Decision: FAIL.**

H004 also fails the pre-registered minimum-sample requirement.

## Decision

Neither primary R002 hypothesis advances to 2025 validation.

Descriptive regime cells may be used to understand the data, but none may be promoted retrospectively into a primary R002 hypothesis.
