# R016 Decision — H021 PASS; H022/H023 REJECT

## H021 — absolute-return persistence
Confirmatory 2025 result:
- N: 84
- Sessions: 84
- Mean absolute-return discount: +55.129%
- Median discount: +68.026%
- Positive-event rate: 88.10%
- p-value: 7.52e-34
- BH q-value: 2.26e-33
- 95% CI: [46.220%, 64.039%]
- Block gate: PASS

This strengthens H017: the low-volatility regime not only has lower realized volatility; 30-minute absolute price movement is also materially lower than its same-minute historical baseline.

## H022 — short impulse mean reversion
- N: 26
- Mean reversion: -1.827 bps
- p-value: 0.6120
- 95% CI: [-8.885, 5.231] bps
- Positive years: 5/6
- Block gate: FAIL

The sample is too small and the mean has the wrong sign.

## H023 — short-range breakout failure
- N: 506
- Mean fade score: -0.029 bps
- p-value: 0.9571
- 95% CI: [-1.071, 1.014] bps
- Positive years: 2/6
- Block gate: FAIL

There is no evidence that the first breakout after H017 systematically fails or reverts.

## Interpretation
R016 materially strengthens the characterization of H017 as a persistent low-movement regime, but does not identify a directional mean-reversion or breakout-fade edge.

Therefore no stop/target/P&L strategy is constructed from H022 or H023.

R012 remains active as a confirmed volatility-regime signal. 2026 remains unopened.
