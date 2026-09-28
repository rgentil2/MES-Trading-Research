# B09 Decision — Regime Persistence, Duration & Transitions

All five pre-registered hypotheses pass their development gates.

## H059 / R048 — HIGH persists into next 15m
- N: 2,340 events
- Sessions: 743
- Next-15m range expansion: +54.228%
- Median: +38.441%
- Positive-event rate: 76.84%
- 95% CI: [46.544%, 61.912%]
- BH q: 1.64e-43
- Positive years: 6/6

## H060 / R049 — LOW persists into next 15m
- N: 2,702
- Sessions: 823
- Next-15m range discount: +35.517%
- Median: +41.956%
- Positive-event rate: 89.93%
- 95% CI: [34.006%, 37.027%]
- BH q effectively 0 at numerical precision
- Positive years: 6/6

## H061 / R050 — HIGH persists to +60m
- N: 2,340
- +60m range expansion: +52.339%
- 95% CI: [45.913%, 58.764%]
- BH q: 2.79e-57
- Positive years: 6/6
- Intermediate mean effects:
  - +15m: +54.228%
  - +30m: +53.752%
  - +45m: +53.172%
  - +60m: +52.339%

There is very little decay over the tested one-hour horizon.

## H062 / R051 — LOW persists to +60m
- N: 2,702
- +60m range discount: +34.079%
- 95% CI: [32.346%, 35.812%]
- BH q effectively 0
- Positive years: 6/6
- Intermediate mean effects:
  - +15m: +35.517%
  - +30m: +35.268%
  - +45m: +35.021%
  - +60m: +34.079%

Again, there is little decay through one hour.

## H063 / R052 — Extreme-state self-transition
One-block transition matrix:

| Current | Next LOW | Next NORMAL | Next HIGH |
|---|---:|---:|---:|
| LOW | 52.63% | 43.45% | 3.92% |
| NORMAL | 19.78% | 64.71% | 15.51% |
| HIGH | 2.52% | 43.55% | 53.93% |

- HIGH current events: 2,340
- P(HIGH next | HIGH now): 53.93%
- LOW current events: 2,702
- P(LOW next | LOW now): 52.63%
- Unconditional quantile reference: ~20%
- Both one-sided exact binomial p-values < 1.1e-287
- BH q: 1.74e-287

Direct transitions from one extreme to the opposite extreme are rare:
- HIGH -> LOW: 2.52%
- LOW -> HIGH: 3.92%

## Conclusion

The key result is no longer merely "volatility sometimes clusters."

Under the frozen same-clock definition, an extreme 15-minute range state has strong predictive persistence:
- HIGH remains high-movement for at least the tested next hour;
- LOW remains low-movement for at least the tested next hour;
- the effect decays only slightly from +15 to +60 minutes;
- extreme-to-opposite-extreme transitions are uncommon.

This is development evidence on 2020–2025, not independent confirmation.

2026 remains completely unopened.
