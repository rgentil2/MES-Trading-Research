# B12 Decision — HIGH-Regime Strategy Architecture Discovery

All three architectures fail their frozen 30-minute primary gates.

## H074 / R065 — Direct dynamic breakout
- Trades/sessions: 577
- 30m gross expectancy: -$1.27
- 30m net expectancy: -$5.65
- Net P&L: -$3,262.26
- PF: 0.828
- Win rate: 47.49%
- Max DD: $4,574.51
- 95% CI: [-$12.44, +$1.13]
- p: 0.1024
- BH q: 0.1438
- Positive years: 2/6
- REJECT

## H075 / R066 — Breakout + pullback
- Trades/sessions: 476
- 30m gross expectancy: -$0.92
- 30m net expectancy: -$5.30
- Net P&L: -$2,524.88
- PF: 0.833
- Win rate: 48.32%
- CI: [-$12.42, +$1.81]
- Positive years: 3/6
- REJECT

## H076 / R067 — NORMAL→HIGH breakout
- Trades/sessions: 404
- 30m gross expectancy: -$1.61
- 30m net expectancy: -$5.99
- PF: 0.787
- CI: [-$12.58, +$0.61]
- Positive years: 2/6
- REJECT

Secondary 60m H076 produced +$2.87 gross/trade but remained -$1.51 net/trade. It cannot rescue the failed 30m primary hypothesis.

## Interpretation

R063 correctly identifies environments with larger future movement, but a first-close breakout of the immediately preceding 15m range does not identify the direction of that movement.

Average 30m MFE and MAE are both substantial and similar in size, consistent with high movement but weak directional edge.

Descriptive LONG/SHORT differences are not promoted.

No B12 architecture advances to stop/target optimization.

2026 remains unopened.
