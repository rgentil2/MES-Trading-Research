# MES — 25 External Strategies Challenge — Decision

Status: **0 / 25 pass the primary gate**

Run date: 2026-10-05.

This block evaluated exactly 25 externally sourced strategies on MES 2020-2024:
- 15 NinjaTrader / NinjaTrader Forum
- 5 TradingView open-source
- 5 other published systems

Common constraints:
- $4.38 round-trip cost
- Forex Factory USD High/Medium news overlay
- flat at exact T-5
- no new entries T-5 through T+5
- 2025/2026 excluded
- no post-result parameter optimization

Primary gate:
1. net expectancy >0
2. PF >=1.25
3. >=300 trades / 60 months
4. >=4/5 positive years
5. no single year >40% of total positive P&L

## Outcome

**No strategy passed.**

### Best frequent/near-break-even strategy

R3-S3 PriorClose cross PT25
- trades: 896
- 14.93/month
- net expectancy: +0.0409 points/trade
- PF: 1.0104
- positive years: 1/5
- total net: +36.60 points

Interpretation: essentially break-even and unstable; not promotable.

### Positive but sparse published systems

R4-S1 Connors RSI2<5 / SMA200
- trades: 25
- 0.42/month
- net expectancy: +28.804 points/trade
- PF: 3.099
- positive years: 4/5
- largest positive-year share: 42.1%
- fails frequency and concentration gates.

R4-S2 Connors Double7
- trades: 39
- 0.65/month
- net expectancy: +26.028 points/trade
- PF: 2.006
- positive years: 4/5
- largest positive-year share: 54.6%
- fails frequency and concentration gates.

These are interesting as low-frequency swing effects but do not satisfy the project's funded-account opportunity-rate target.

### TradingView

All 5 TradingView strategies failed:
- TV Bollinger20x2 + EMA9: PF 0.579
- TV SuperTrend10x3: PF 0.809
- TV NY ORB15 fixed1.5xRange: PF 0.847
- TV ORB15 stop-order 2R: PF 0.865
- TV RSI14 40/60 TP5 SL2: PF 0.783

No TradingView candidate had positive net expectancy over the full sample.

### NinjaTrader

14 of the 15 NinjaTrader strategies were clearly negative.
The only near-break-even NinjaTrader strategy was:
- PriorClose cross PT25: PF 1.010, +0.041 points/trade, but only 1/5 positive years.

No NinjaTrader strategy passed.

### Two final roster-label corrections

The workflow summary initially showed NaN for the final two external strategies because their internal strategy labels still used earlier roster numbers. The underlying trade rows were present and were recomputed without rerunning or changing trading logic:

R5-S4 Gap fade open -> prior close
- trades: 1,001
- 16.68/month
- net expectancy: -0.7027 points/trade
- PF: 0.8977
- positive years: 1/5
- total net: -703.38 points

R5-S5 Turtle S1 20/10 + 2N
- trades: 296
- 4.93/month
- net expectancy: -0.6125 points/trade
- PF: 0.9469
- positive years: 3/5
- total net: -181.31 points

Both fail.

## Conclusion

This external-source challenge did not identify a robust, frequent, cost-surviving MES strategy.

The exercise materially broadens the evidence base beyond internally generated hypotheses:
- classic indicators
- breakouts
- mean reversion
- prior-day levels
- VWAP / bands
- gap fills
- ORB
- Turtle / Donchian
- TradingView open-source
- NinjaTrader Forum / sample strategies

No strategy met the project's promotion standard.
