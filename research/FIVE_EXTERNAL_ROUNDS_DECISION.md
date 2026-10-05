# MES — Five External Strategy Rounds (5x5 = 25) — Decision

Run date: 2026-10-05.
Status: **0/25 PRIMARY GATE PASSES — NO FREQUENT ROBUST CANDIDATE**

This block was preregistered in `research/FIVE_EXTERNAL_ROUNDS_PREREG.md` before the 25-strategy outcomes were viewed.

## Common execution policy

- MES 2020-2024 only.
- 2025/2026 not used.
- One MES contract.
- Cost: $4.38 round trip = 0.876 MES points/trade.
- Intraday entry window: 09:30-11:30 ET unless source was narrower.
- Forex Factory USD High/Medium rule:
  - flat at exact T-5 minute open,
  - no entries T-5 through T+5.
- One open position per strategy.
- Stop-first for same-1m-bar stop/target ambiguity.
- No post-result parameter tuning.

Primary gate:
1. net expectancy >0,
2. PF net >=1.25,
3. >=300 trades / 60 months,
4. >=4/5 positive years,
5. no single year >40% of positive P&L.

## Round 1 — NinjaTrader core/sample

| Strategy | Trades | /mo | Net pts/trade | PF | Positive years | Result |
|---|---:|---:|---:|---:|---:|---|
| SampleMACrossOver 10/25 | 6032 | 100.53 | -0.8450 | 0.7469 | 0/5 | FAIL |
| SamplePriceModification 20/100 BE50 | 5866 | 97.77 | -0.8802 | 0.7889 | 0/5 | FAIL |
| SMA5/30 lookback2 PT1 | 5918 | 98.63 | -0.8056 | 0.0000 | 0/5 | FAIL |
| EMA20/40 + RSI14s3 PT200 dynEMA40 | 4765 | 79.42 | -0.8621 | 0.5835 | 0/5 | FAIL |
| Basic Donchian20 long | 2051 | 34.18 | -0.9210 | 0.8039 | 0/5 | FAIL |

## Round 2 — NinjaTrader intraday/pattern

| Strategy | Trades | /mo | Net pts/trade | PF | Positive years | Result |
|---|---:|---:|---:|---:|---:|---|
| Contrarian MACD 10/10 | 10236 | 170.60 | -0.9025 | 0.4383 | 0/5 | FAIL |
| MFI14 + MACD 5m long | 9 | 0.15 | -3.7371 | 0.0000 | 0/5 | FAIL |
| InsideBar directional SL10 PT25 | 1238 | 20.63 | -1.1892 | 0.5224 | 0/5 | FAIL |
| InsideBar structural bracket | 4611 | 76.85 | -0.6419 | 0.8019 | 0/5 | FAIL |
| Bollinger100 fade | 1165 | 19.42 | -1.1760 | 0.8673 | 1/5 | FAIL |

## Round 3 — NinjaTrader levels / areas

| Strategy | Trades | /mo | Net pts/trade | PF | Positive years | Result |
|---|---:|---:|---:|---:|---:|---|
| VWAP lower2 10-12pt mean reversion | 61 | 1.02 | -2.6699 | 0.4163 | 0/5 | FAIL |
| Bollinger(2,14) lower-to-upper | 2365 | 39.42 | -0.7397 | 0.8187 | 0/5 | FAIL |
| PriorClose cross PT25 | 896 | 14.93 | +0.0409 | 1.0104 | 1/5 | FAIL |
| PriorHighLow breakout signal-bar stop | 1057 | 17.62 | -1.2443 | 0.6666 | 0/5 | FAIL |
| PriorClose cross short SL100 PT200 | 560 | 9.33 | -0.9358 | 0.8919 | 1/5 | FAIL |

The only frequent positive-expectancy result in this level/area round was PriorClose PT25, but its PF was essentially 1.0 and all positive P&L came from 2023. It is not robust.

## Round 4 — Published mean-reversion / reversal

| Strategy | Trades | /mo | Net pts/trade | PF | Positive years | Max positive-year share | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Connors RSI2<5 / SMA200 | 25 | 0.42 | +28.8040 | 3.0986 | 4/5 | 42.10% | FAIL frequency + concentration |
| Connors Double7 | 39 | 0.65 | +26.0278 | 2.0058 | 4/5 | 54.60% | FAIL frequency + concentration |
| Larry Williams Oops FPO | 271 | 4.52 | -3.9572 | 0.4774 | 0/5 | — | FAIL |
| Connors RSI2 symmetric 30m | 250 | 4.17 | -0.7549 | 0.8375 | 2/5 | 74.07% | FAIL |
| Donchian20/10 long-only | 24 | 0.40 | +68.6969 | 3.4170 | 5/5 | 39.36% | FAIL frequency only |

Important: Donchian20/10 long-only passed expectancy, PF, year stability and concentration, but produced only 24 trades in five years. It is a real sparse phenomenon worth recording, not a strategy compatible with the user's >=5 trades/month objective. Do not relax the frequency gate after observing this result.

## Round 5 — Structural breakouts / gaps / Turtle

| Strategy | Trades | /mo | Net pts/trade | PF | Positive years | Result |
|---|---:|---:|---:|---:|---:|---|
| Gap fade open -> prior close | 1001 | 16.68 | -0.7027 | 0.8977 | 1/5 | FAIL |
| 5m gap fill 0.05-0.20% SL12 | 183 | 3.05 | -0.1588 | 0.9507 | 2/5 | FAIL |
| Turtle S1 20/10 +2N | 296 | 4.93 | -0.6125 | 0.9469 | 3/5 | FAIL |
| Turtle S2 55/20 +2N | 189 | 3.15 | -0.8311 | 0.9182 | 3/5 | FAIL |
| Donchian four-week 20/20 | 296 | 4.93 | -0.5061 | 0.9557 | 3/5 | FAIL |

## Overall interpretation

- 0/25 passed the full primary gate.
- Frequent intraday strategies overwhelmingly failed after costs.
- Level/area strategies were explicitly represented (VWAP, Bollinger areas, prior close, prior high/low, gaps).
- R3-S3 PriorClose PT25 was almost break-even but not stable: PF 1.0104, only 1/5 positive years, dominated by 2023.
- Three sparse daily systems had positive results:
  - Connors RSI2,
  - Connors Double7,
  - Donchian20/10 long-only.
- Donchian20/10 was strongest on quality: PF 3.417, positive 5/5 years, max positive-year share 39.36%, but only 24 trades in five years.
- The positive daily results show MES is not necessarily devoid of all exploitable long-horizon effects. They do not solve the stated goal of a frequent, funded-account-compatible intraday system.
- No parameter rescue, threshold relaxation, or frequency-gate relaxation is permitted based on these outcomes.

Decision: **No frequent robust MES candidate from the 25-strategy external challenge.**
