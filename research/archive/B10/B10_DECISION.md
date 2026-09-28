# B10 Decision — Maximum Duration & Decay through +120m

All five hypotheses passed their frozen development gates.

## H064 / R053 — HIGH at +90m
- N: 2,340
- Mean range expansion: +53.928%
- CI: [47.682%, 60.174%]
- 6/6 years positive
- BH q: 3.78e-64
- PASS

## H065 / R054 — LOW at +90m
- N: 2,702
- Mean range discount: +33.993%
- CI: [32.144%, 35.842%]
- 6/6 years positive
- BH q: 1.21e-283
- PASS

## H066 / R055 — HIGH at +120m
- N: 2,340
- Mean range expansion: +53.115%
- CI: [45.983%, 60.247%]
- 6/6 years positive
- BH q: 2.93e-48
- PASS

## H067 / R056 — LOW at +120m
- N: 2,702
- Mean range discount: +33.739%
- CI: [31.726%, 35.752%]
- 6/6 years positive
- BH q: 3.43e-236
- PASS

## H068 / R057 — state information at +120m
- P(HIGH at +120 | HIGH now): 49.27%
- P(LOW at +120 | LOW now): 50.26%
- unconditional quantile reference: ~20%
- both exact tests highly significant
- BH q: 8.44e-219
- PASS

## Decay curve

HIGH mean expansion:
- +15m: +54.23%
- +30m: +53.75%
- +45m: +53.17%
- +60m: +52.34%
- +75m: +51.91%
- +90m: +53.93%
- +105m: +53.03%
- +120m: +53.11%

LOW mean discount:
- +15m: +35.52%
- +30m: +35.27%
- +45m: +35.02%
- +60m: +34.08%
- +75m: +33.63%
- +90m: +33.99%
- +105m: +34.04%
- +120m: +33.74%

Neither state fell below half its +15m effect nor below the +10% practical threshold by +120m.

## Continuous exact-state survival

This must be distinguished from predictive persistence.

The probability of remaining continuously in the exact same extreme state declines much faster:

HIGH continuous survival:
- 15m: 53.9%
- 60m: 23.1%
- 120m: 13.7%

LOW continuous survival:
- 15m: 52.6%
- 60m: 15.4%
- 120m: 5.6%

Median continuous same-state duration after detection was 15 minutes for both HIGH and LOW.

Therefore the result is **not** that each event stays continuously classified HIGH/LOW for two hours. Rather, the initial state continues to carry strong information about future range magnitude even after intermittent transitions through NORMAL.

## Conclusion

No practical decay point was observed by +120m.

The next development step is to extend the same frozen framework toward +180 and +240 minutes before assigning a regime "life expectancy."

2026 remains unopened.
