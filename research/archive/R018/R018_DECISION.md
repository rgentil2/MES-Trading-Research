# R018 Decision — REJECT H027

## Strategy
First 15-minute rolling-range edge signal while H017 is active:
- RangePosition >= 0.90 → short;
- RangePosition <= 0.10 → long;
- next-bar-open execution;
- 15-minute time exit;
- one MES;
- $4.38 round-trip modeled costs.

## Result
- Trades: 517
- Sessions: 517
- Net P&L: -$1,884.46
- Expectancy: -$3.645/trade
- Profit Factor: 0.667
- Win rate: 43.33%
- Max drawdown: $1,883.83
- p-value: 0.001398
- 95% CI of mean net P&L: [-$5.881, -$1.409]
- Positive years: 1/6

Yearly expectancy:
- 2020: -$3.85
- 2021: -$6.57
- 2022: +$0.50
- 2023: -$5.30
- 2024: -$5.07
- 2025: -$0.54

Side breakdown:
- LOWER_EDGE long: -$3.89/trade
- UPPER_EDGE short: -$3.49/trade

## Decision
H027 is rejected. The result is significantly negative rather than merely inconclusive.

H017 should not be interpreted as a simple mean-reversion regime. Low movement persistence does not imply that fading short-range extremes is profitable.

2026 remains unopened.
