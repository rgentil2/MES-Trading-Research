# MES — 25 External Strategy Challenge — Decision

Run date: 2026-10-05.

Status: **0 / 25 strategies passed the frozen primary gate.**

## Frozen sample and operating overlay

- MES 2020-2024 only.
- 2025/2026 excluded.
- $4.38 round-trip cost.
- USD Forex Factory High/Medium:
  - forced flat at exact T-5 minute open,
  - no new entries T-5 through T+5.
- Intraday new-entry window 09:30-11:30 ET where applicable.
- No post-result optimization.

## Composition

- 15 NinjaTrader / NinjaTrader Support Forum strategies.
- 5 TradingView open-source strategies.
- 5 other published systems.

## Primary gate

All required:
1. net expectancy > 0;
2. PF >= 1.25;
3. >= 300 trades / 60 months;
4. >= 4 of 5 years positive;
5. no single year > 40% of positive P&L.

No strategy passed all five.

## Main results

### NinjaTrader

All 15 failed.

Best by net expectancy:
- PriorClose cross PT25: N=896, +0.041 points/trade, PF=1.010, only 1/5 years positive.
- All other NinjaTrader tests had negative net expectancy.

Selected examples:
- SampleMACrossOver 10/25: N=6032, -0.845 pts/trade, PF=0.747, 0/5 positive.
- SamplePriceModification: N=5866, -0.880, PF=0.789, 0/5.
- Contrarian MACD 10/10: N=10236, -0.903, PF=0.438, 0/5.
- Inside-bar structural bracket: N=4611, -0.642, PF=0.802, 0/5.
- VWAP lower-2sigma mean reversion: N=61, -2.670, PF=0.416, 0/5.
- PriorHigh/Low breakout: N=1057, -1.244, PF=0.667, 0/5.

### TradingView

All 5 failed.

- Bollinger20x2 + EMA9 long: N=2485, -0.916 pts/trade, PF=0.579, 0/5.
- SuperTrend10x3 L/S: N=2495, -0.740, PF=0.809, 0/5.
- NY ORB15 fixed 1.5x range: N=1543, -1.119, PF=0.847, 1/5.
- ORB15 stop-order 2R: N=1193, -0.984, PF=0.865, 1/5.
- RSI14 40/60 TP5% SL2%: N=3874, -1.010, PF=0.783, 0/5.

### Other published systems

Connors RSI2:
- N=25.
- +28.804 points/trade.
- PF=3.099.
- 4/5 years positive.
- Maximum positive-year contribution=42.1%.
- Fails opportunity frequency by a very large margin and slightly fails the <=40% concentration rule.

Connors Double7:
- N=39.
- +26.028 points/trade.
- PF=2.006.
- 4/5 years positive.
- Maximum positive-year contribution=54.6%.
- Fails opportunity frequency and concentration.

Larry Williams Oops FPO:
- N=271.
- -3.957 pts/trade.
- PF=0.477.
- 0/5 positive.

Gap fade open -> prior close:
- Due to a reporting-label mismatch, the automated summary row showed NaN even though trades were generated.
- Recovered from trades.csv:
  - N=1001.
  - 16.68/month.
  - -0.703 pts/trade.
  - PF=0.898.
  - 1/5 years positive.
  - total=-703.376 pts.
  - max DD=-963.326 pts.
- FAIL.

Turtle System 1 20/10 + 2N:
- Due to the same reporting-label mismatch, the automated summary row showed NaN even though trades were generated.
- Recovered from trades.csv:
  - N=296.
  - 4.93/month.
  - -0.613 pts/trade.
  - PF=0.947.
  - 3/5 years positive.
  - max positive-year contribution=67.7%.
  - total=-181.309 pts.
- FAIL.

## Interpretation

1. The broad intraday external-strategy challenge does not provide evidence of a tradable MES edge under the user's actual operating constraints and cost model.
2. Explicit level/area systems were included: VWAP bands, Bollinger bands, prior close, prior high/low, opening range, gap-to-prior-close, Donchian/Turtle boundaries.
3. The only strong positive phenomena in this challenge are the low-frequency Connors daily mean-reversion systems. They are not candidates for the current goal because they produce only 25 and 39 trades in five years and fail the frozen opportunity-rate gate.
4. PriorClose cross PT25 is effectively break-even rather than a viable edge: PF=1.010 and positive in only one year.
5. No TradingView strategy survived.
6. No NinjaTrader strategy survived.

Do not rescue any failed strategy through threshold/parameter tuning inside this block.
