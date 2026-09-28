# B11 Decision — Extended Intraday Persistence through +240m

All five hypotheses passed the frozen development gates.

## H069 / R058 — HIGH at +180m
- N: 2,340
- Sessions: 743
- Mean expansion: +48.994%
- CI: [40.828%, 57.160%]
- 6/6 years positive
- BH q: 7.89e-32
- PASS

## H070 / R059 — LOW at +180m
- N: 2,702
- Sessions: 823
- Mean discount: +30.485%
- CI: [27.758%, 33.212%]
- 6/6 years positive
- BH q: 5.22e-106
- PASS

## H071 / R060 — HIGH at +240m
- N: 2,340
- Mean expansion: +43.989%
- Median: +19.735%
- Positive-event rate: 63.38%
- CI: [36.578%, 51.400%]
- 6/6 years positive
- BH q: 2.77e-31
- PASS

## H072 / R061 — LOW at +240m
- N: 2,702
- Mean discount: +25.448%
- Median: +41.163%
- Positive-event rate: 82.94%
- CI: [21.362%, 29.534%]
- 6/6 years positive
- BH q: 4.72e-34
- PASS

## H073 / R062 — extreme-state information at +240m
- P(HIGH at +240 | HIGH now): 42.99%
- P(LOW at +240 | LOW now): 43.97%
- unconditional reference: ~20%
- HIGH opposite state at +240: 6.03%
- LOW opposite state at +240: 9.66%
- BH q: 1.11e-139
- PASS

## Observed decay

HIGH:
- +15m: +54.23%
- +60m: +52.34%
- +120m: +53.11%
- +180m: +48.99%
- +240m: +43.99%

LOW:
- +15m: +35.52% discount
- +60m: +34.08%
- +120m: +33.74%
- +180m: +30.49%
- +240m: +25.45%

The effect is now visibly decaying, but neither HIGH nor LOW has fallen below:
- 50% of its original +15m effect;
- the +10% practical threshold.

Therefore the observed predictive life is **at least 240 minutes** under this definition. We do not claim a half-life beyond the observed window.

## Interpretation

The initial 15-minute range regime conditions movement magnitude for much of the remaining RTH session.

This still does not imply directional predictability.

2026 remains completely unopened.
