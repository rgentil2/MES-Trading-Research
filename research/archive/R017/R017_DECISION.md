# R017 Decision — REJECT H024/H025/H026

## Purpose
Test whether H017 improves continuation-style strategies by excluding trades opened during the confirmed 30-minute low-volatility regime.

Execution used one MES contract, next-bar-open entry, fixed time exits, and $4.38 round-trip modeled costs.

## H024 — Morning ORB
- Total trades: 1,520
- H017 trades: 88
- Baseline expectancy: -$2.38/trade
- H017 expectancy: -$6.03/trade
- Filtered expectancy: -$2.16/trade
- Baseline PF: 0.900
- Filtered PF: 0.911
- Outside-minus-inside delta: +$3.87/trade
- 95% CI: [-$3.51, +$11.25]
- BH q-value: 0.406

H017 trades were descriptively worse, but the difference was not statistically reliable and the filtered strategy remained unprofitable.

## H025 — Previous RTH high/low breakout
- Total trades: 1,171
- H017 trades: 28
- Baseline expectancy: -$3.24/trade
- H017 expectancy: +$3.88/trade
- Filtered expectancy: -$3.41/trade
- Filter delta: -$7.29/trade

Filtering H017 made the strategy worse.

## H026 — High-volume directional impulse
- Total trades: 1,089
- H017 trades: 56
- Baseline expectancy: -$5.27/trade
- H017 expectancy: +$0.11/trade
- Filtered expectancy: -$5.56/trade
- Filter delta: -$5.66/trade

Filtering H017 again made the strategy worse.

## Decision
No R017 candidate passes the pre-registered filter gate.

H017 remains a confirmed low-movement regime, but it is not supported as a blanket exclusion filter for these three rejected continuation strategies.

2026 remains unopened.
