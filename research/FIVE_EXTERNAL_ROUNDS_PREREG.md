# MES — Five External Strategy Rounds (5x5 = 25) — Pre-registration

Locked before running this 25-strategy block on MES 2020-2024.

## Common rules

- MES 2020-2024 only. 2025/2026 forbidden.
- One MES contract.
- Fixed round-trip cost: $4.38 = 0.876 MES points/trade.
- New intraday entries only 09:30 through 11:30 ET unless the source is narrower.
- Forex Factory overlay:
  - USD High/Medium scheduled events.
  - flat at exact T-5, modeled as the OPEN of the minute beginning at T-5.
  - no new entries T-5 through T+5 inclusive.
- One open position at a time per strategy.
- 1-minute ambiguity: if stop and target are touched in the same minute, stop first.
- No parameter optimization after results.
- Serious-candidate gate for every strategy:
  1. net expectancy >0,
  2. net PF >=1.25,
  3. >=5 trades/month average (>=300 trades / 60 months),
  4. >=4/5 positive years,
  5. no single year >40% of total positive P&L.
- Sources: exactly 15 NinjaTrader/NinjaTrader Forum, 5 TradingView open-source scripts, and 5 other published systems.
- TradingView candidates are admitted only when the public page/source exposes enough rules to implement without outcome-driven tuning.

# Round 1

## R1-S1 — NinjaTrader SampleMACrossOver
- Source: NinjaTrader built-in SampleMACrossOver / forum-posted source.
- SMA10/SMA25.
- Long CrossAbove; short CrossBelow.
- Bar-close signal; next 1m open.
- Opposite signal closes/reverses if new entry remains within 09:30-11:30.
- No fixed source SL/PT; RTH close flat.

## R1-S2 — NinjaTrader SamplePriceModification
- Source: NinjaTrader sample strategy.
- Long if current close is above each prior 10 closes and prior 10 opens and current open<close; short mirror.
- SL 20 ticks; PT 100 ticks.
- After +50 ticks favorable completed close, stop moves to breakeven.
- Entry next 1m open; RTH close flat.

## R1-S3 — NinjaTrader SMA5/30 one-tick target
- Source: NinjaTrader Support Forum, "Strategy builder stumped".
- SMA5 crosses above SMA30 within lookback 2 bars.
- Long-only; entry next 1m open.
- PT=1 tick.
- No source stop; RTH close flat.

## R1-S4 — TradingView Bollinger Bands + EMA9
- Source: TradingView open-source script by D499; source mirror confirms defaults.
- 1-minute.
- EMA9.
- Bollinger length=20, StdDev=2, Close source.
- Long signal when prior close is below lower Bollinger band.
- Entry next 1m open.
- Exit when completed Close >= EMA9; execute next 1m open.
- Long-only version from the exposed source; no invented stop.
- RTH close flat.

## R1-S5 — External Connors RSI(2)
- Source: Larry Connors/Cesar Alvarez public rule set.
- Daily RTH.
- Close>SMA200 and RSI2<5.
- Buy next RTH open.
- Exit next RTH open after completed Close>SMA5.
- No stop in original.

# Round 2

## R2-S1 — NinjaTrader EMA20/40 + RSI14,3
- Source: NinjaTrader Support Forum, "setting stop loss on an MA".
- EMA20>EMA40.
- RSI(Close,14,3) CrossAbove 60 within lookback 10.
- Long-only.
- Entry next 1m open.
- PT=200 ticks.
- Dynamic stop updated to EMA40 from completed bars.
- RTH flat.

## R2-S2 — NinjaTrader Basic Donchian20
- Source: NinjaTrader Support Forum + NT Donchian convention.
- Period=20.
- Long when Close crosses above prior completed Donchian20 upper.
- Exit when Close crosses below prior completed Donchian20 lower.
- Next-bar execution.
- No fixed stop/target; RTH flat.

## R2-S3 — NinjaTrader Contrarian MACD 10/10
- Source: NinjaTrader Support Forum, "Simple MacD Cross Over".
- MACD12/26/9.
- MACD crosses above signal => SHORT.
- MACD crosses below signal => LONG.
- SL=10 ticks; PT=10 ticks.
- Next 1m open; RTH flat.

## R2-S4 — TradingView SuperTrend Long/Short
- Source: TradingView open-source "SuperTrend Strategy [Long/Short]".
- ATR length=10, factor=3.0.
- Standard RMA ATR / SuperTrend.
- Bullish flip: close short and enter long.
- Bearish flip: close long and enter short.
- SuperTrend line acts as dynamic stop.
- Entries only if flip execution is within 09:30-11:30; exits remain allowed later.
- RTH close flat.

## R2-S5 — External Connors Double 7
- Source: Cesar Alvarez original-rule restatement.
- Daily RTH.
- Close>SMA200.
- Close<=lowest close of 7-day window.
- Buy next RTH open.
- Exit next RTH open after completed Close>=highest close of 7-day window.
- No stop.

# Round 3

## R3-S1 — NinjaTrader MFI + MACD 5-minute long
- Source: NinjaTrader Support Forum.
- 5-minute RTH bars.
- MFI14<20 AND MACD(12,26,9) Diff crosses upward through 0.
- Entry next 5m open.
- Stop=low of signal 5m candle.
- Exit when MFI>80 AND MACD Diff<prior 5m Diff.
- RTH flat.

## R3-S2 — NinjaTrader inside-bar directional close
- Source: NinjaTrader Support Forum.
- Inside bar High<prior High and Low>prior Low.
- Close==High => buy stop High+1 tick.
- Close==Low => sell stop Low-1 tick.
- Order valid for next 1m bar only.
- SL=10 ticks; PT=25 ticks.
- RTH flat.

## R3-S3 — NinjaTrader inside-bar structural bracket
- Source: NinjaTrader Support Forum.
- Inside bar Low>prior Low and High<prior High.
- Next bar OCO buy stop High+1 tick / sell stop Low-1 tick.
- If both sides touch in same 1m bar, skip.
- Long stop=inside-bar Low-1 tick; short stop=inside-bar High+1 tick.
- No source target; RTH flat.

## R3-S4 — TradingView NY Opening Range Breakout - fixed RR
- Source: TradingView open-source strategy by shui2967.
- OR=09:30-09:45 ET.
- Long after completed candle closes above OR high; short after close below OR low.
- Entry next candle, restricted by user cutoff to <=11:30.
- Stop at opposite OR edge.
- Fixed target = entry +/- 1.5 * OR range, matching the published fixed-RR/range option.
- One trade per direction per day.
- RTH close flat.

## R3-S5 — External Larry Williams Oops + FPO
- Source: Larry Williams Oops descriptions.
- If current RTH open<prior RTH Low, buy stop at prior Low.
- If current RTH open>prior RTH High, sell stop at prior High.
- Initial stop=current day extreme observed through entry.
- Exit at first subsequent session open profitable versus entry (FPO).
- News flat can close earlier.

# Round 4 — External + TradingView

## R4-S1 — External Connors RSI(2)
- Daily RTH; Close>SMA200 and RSI2<5.
- Buy next RTH open.
- Exit next RTH open after completed Close>SMA5.
- No stop in original.

## R4-S2 — External Connors Double 7
- Daily RTH; Close>SMA200 and Close<=lowest close of 7-day window.
- Buy next RTH open.
- Exit next RTH open after completed Close>=highest close of 7-day window.
- No stop.

## R4-S3 — External Larry Williams Oops + FPO
- If current RTH open<prior RTH Low, buy stop at prior Low.
- If current RTH open>prior RTH High, sell stop at prior High.
- Initial stop=current day extreme observed through entry.
- Exit at first subsequent profitable session open.
- News flat can close earlier.

## R4-S4 — TradingView Bollinger Bands + EMA9
- Source: TradingView open-source script by D499; public source mirror confirms defaults.
- 1-minute, long-only exposed source.
- EMA9.
- Bollinger length=20, StdDev=2, Close source.
- Signal when prior Close is below current lower Bollinger band.
- Entry next 1m open.
- Exit next 1m open after completed Close>=EMA9.
- No invented stop; RTH close flat.

## R4-S5 — TradingView SuperTrend Long/Short
- Source: TradingView open-source SuperTrend Strategy [Long/Short].
- ATR length=10; factor=3.0.
- Bullish flip closes short/opens long; bearish flip closes long/opens short.
- SuperTrend line is the dynamic stop.
- New reversal entry only if execution is <=11:30; exits remain active later.
- RTH close flat.

# Round 5 — TradingView + structural external systems

## R5-S1 — TradingView NY Opening Range Breakout
- Source: TradingView open-source strategy by shui2967.
- OR=09:30-09:45 ET.
- Completed close above OR high => long next bar; below OR low => short next bar.
- User entry cutoff reduces source's noon cutoff to 11:30.
- Stop=opposite OR edge.
- Fixed target=entry +/-1.5*OR range.
- One trade per direction per day.
- RTH close flat.

## R5-S2 — TradingView 15-Min ORB 2R
- Source: TradingView open-source strategy by Hardest_Easy_Money.
- OR=first 15 minutes.
- Source's one-pip/two-pip buffers translated once, before outcomes, to one/two MES minimum ticks.
- Buy stop=OR high+1 tick; sell stop=OR low-1 tick.
- Long SL=OR low-2 ticks; short SL=OR high+2 ticks.
- TP=2R, the published preferred target.
- Cancel unfilled orders one hour after OR completion.
- Opposite order canceled after trigger.
- Optional breakeven/runner/time-exit variants are not used.
- RTH close flat.

## R5-S3 — TradingView RSI14 40/60 TP/SL
- Source: TradingView open-source RSI Strategy With TP/SL - Lower TF.
- RSI period=14.
- Buy when RSI crosses below 40.
- Short when RSI crosses above 60.
- Direction frozen as Both.
- TP=5%; SL=2%.
- Entry next 1m open.
- RTH close flat.

## R5-S4 — External opening-gap fade
- Gap=current 09:30 open-prior RTH close.
- Skip abs gap<0.10%.
- Enter against gap at 09:30.
- Target=prior RTH close.
- Stop=one full gap length beyond entry.
- RTH close exit.

## R5-S5 — External Turtle System 1
- Long break above prior 20-session High; short below prior 20-session Low.
- Execute with underlying 1m.
- Exit long at prior 10-session Low; short at prior 10-session High.
- Protective stop=2N; N=20-day Wilder ATR.
- No pyramiding.

# Reporting

For every strategy report:
- source family (NinjaTrader / TradingView / External)
- trades
- trades/month
- net points/trade after $4.38 RT
- net PF
- win rate
- total net points
- max drawdown
- positive years / 5
- max positive-year contribution
- news-entry skips
- forced-news exits
- primary gate pass/fail

No thresholds, indicator periods, time windows, stops, targets, direction rules, or source interpretations may be changed after first outcomes from this 25-strategy block are viewed.


---

## Pre-result roster audit

This section was added **after the workflow completed but before any strategy-result logs/artifacts were inspected**. It does not change code, parameters, or strategy logic. It corrects the documentation roster to match the already-frozen implementation in `research/five_external_rounds.py`.

Exact implemented composition:

### NinjaTrader / NinjaTrader Forum (15)
1. R1-S1 SampleMACrossOver 10/25
2. R1-S2 SamplePriceModification 20/100 BE50
3. R1-S3 SMA5/30 lookback2 PT1
4. R1-S4 EMA20/40 + RSI14s3 PT200 dynEMA40
5. R1-S5 Basic Donchian20 long
6. R2-S1 Contrarian MACD 10/10
7. R2-S2 MFI14+MACD 5m long
8. R2-S3 InsideBar directional close SL10 PT25
9. R2-S4 InsideBar structural bracket
10. R2-S5 Bollinger100 1.5dev short $2500/$5000
11. R3-S1 VWAP lower2 10-12pt mean reversion
12. R3-S2 Bollinger(2,14) lower-to-upper long
13. R3-S3 PriorClose cross PT25
14. R3-S4 PriorHighLow breakout signalbar stop
15. R3-S5 PriorClose cross short SL100 PT200

### TradingView open-source (5)
16. R4-S4 TV-Bollinger20x2 + EMA9 long
17. R4-S5 TV-SuperTrend10x3 L/S
18. R5-S1 TV-NY ORB15 fixed1.5xRange
19. R5-S2 TV-ORB15 stop-order 2R
20. R5-S3 TV-RSI14 40/60 TP5 SL2

### Other published systems (5)
21. R4-S1 Connors RSI2<5 / SMA200
22. R4-S2 Connors Double7
23. R4-S3 Larry Williams Oops FPO
24. R5-S4 Gap fade open -> prior close
25. R5-S5 Turtle S1 20/10 + 2N

The common gates, MES 2020-2024 sample, $4.38 round-trip cost, Forex Factory USD High/Medium T-5/T+5 overlay, and 2025/2026 exclusion remain unchanged.
