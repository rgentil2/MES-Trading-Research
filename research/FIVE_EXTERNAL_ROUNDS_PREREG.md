# MES — Five External Strategy Rounds — Pre-registration

Locked before running any of the strategies below on MES 2020-2024.

## Common rules

- MES 2020-2024 only. 2025/2026 forbidden.
- One MES contract.
- Fixed round-trip cost: $4.38 = 0.876 MES points/trade.
- New intraday entries allowed only 09:30 through 11:30 ET unless source is narrower.
- Forex Factory overlay:
  - USD High/Medium scheduled events.
  - flat at exact T-5, modeled as the OPEN of the minute beginning at T-5.
  - no new entries T-5 through T+5 inclusive.
- One open position at a time per strategy.
- 1-minute ambiguity: if stop and target are touched in the same minute, stop first.
- No parameter optimization after results.
- A serious candidate must have net expectancy >0, PF >=1.25, >=5 trades/month average (>=300 trades / 60 months), >=4/5 positive years, and no single year >40% of positive P&L. This same economic gate is applied to all ten strategies; daily/swing systems are not exempt.

# Round 1 — Official NinjaTrader sample logic

## R1-S1 SampleMACrossOver
Source: NinjaTrader built-in SampleMACrossOver, forum-posted source.
- SMA Fast = 10.
- SMA Slow = 25.
- Long on CrossAbove(SMA10,SMA25,1).
- Short on CrossBelow.
- Calculate on bar close; fill next 1m open.
- Opposite signal closes/reverses; reverse entry only if within 09:30-11:30.
- No fixed SL/TP in source.
- Flat at RTH close if still open.

## R1-S2 SamplePriceModification
Source: NinjaTrader sample strategy posted in support forum.
- Calculate on bar close.
- Long if current close is above each of prior 10 closes and prior 10 opens, and current open < current close.
- Short mirror image.
- SL = 20 ticks.
- PT = 100 ticks.
- Once a long closes > entry +50 ticks, stop moves to breakeven; mirror for short.
- Entry next 1m open.
- Flat RTH close.

# Round 2 — NinjaTrader forum indicator strategies

## R2-S1 Contrarian MACD 10/10
Source: NinjaTrader Support Forum, "Simple MacD Cross Over".
- Standard MACD 12/26/9.
- MACD line cross ABOVE signal => SHORT.
- MACD line cross BELOW signal => LONG.
- SL = 10 ticks.
- PT = 10 ticks.
- Signal bar close; entry next 1m open.
- Flat RTH close.

## R2-S2 MFI + MACD 5-minute long
Source: NinjaTrader Support Forum, "MFI + MACD Simple strategy (5 min)".
- Build 5-minute RTH bars.
- MFI period = 14 (standard default).
- Standard MACD 12/26/9.
- Long when MFI <20 AND MACD Diff crosses from below 0 to above 0.
- Entry next 5m open.
- Stop = low of signal 5m candle.
- Exit when MFI >80 AND MACD Diff < prior 5m MACD Diff.
- No invented fixed target.
- Flat RTH close.

# Round 3 — NinjaTrader levels / areas

## R3-S1 ES VWAP 2-sigma mean reversion
Source: NinjaTrader Support Forum, ES Bollinger/VWAP strategy request.
- Long-only.
- Session cumulative VWAP.
- Weighted standard-deviation band = VWAP - 2 sigma.
- Distance VWAP to lower 2-sigma band must remain between 10 and 12 ES/MES points for at least 15 consecutive completed minutes.
- Signal when price touches/crosses the lower 2-sigma band.
- Entry next 1m open.
- Stop = 5 points below entry.
- Dynamic target = session VWAP.
- Flat RTH close.

## R3-S2 Bollinger 2,14 band reversal
Source: NinjaTrader Support Forum code example, "I need help with Bollinger Bands strategy".
- Bollinger period = 14, standard deviations = 2.
- Long when Close crosses above lower Bollinger band.
- Entry next 1m open.
- Exit when Close crosses below upper Bollinger band.
- No source stop; none invented.
- Flat RTH close.

# Round 4 — Published Connors mean-reversion systems

## R4-S1 Connors RSI(2)
Source: Larry Connors, Short Term Trading Strategies That Work; public reproductions.
- Daily RTH bars.
- Long only.
- Prior RTH close > SMA200.
- RSI(2) <5.
- Source entry is at close; causal MES adaptation enters next RTH open.
- Exit at RTH close when Close > SMA5.
- No stop in source.
- Position may hold across days, but frozen Forex Factory T-5 rule can force early flat.

## R4-S2 Connors Double 7
Source: Larry Connors & Cesar Alvarez; original rules restated by Cesar Alvarez.
- Daily RTH bars.
- Long only.
- Prior close > SMA200.
- Prior close is <= lowest close of its 7-day window.
- Source entry at close; causal MES adaptation enters next RTH open.
- Exit at RTH close when current close >= highest close of its 7-day window.
- No stop.
- News T-5 can force early flat.

# Round 5 — External ES/NQ gap-to-level systems

## R5-S1 Opening gap fade to prior RTH close
Source: published NQ/ES gap-fill backtest rule set.
- Gap = current 09:30 RTH open minus prior RTH close.
- Skip absolute gap <0.10%.
- At 09:30 enter AGAINST the gap.
- Target = prior RTH close.
- Stop = one full gap length beyond entry.
- EOD exit 16:00 if neither target nor stop.
- Conservative stop-first ambiguity.

## R5-S2 5-minute ES gap-fill
Source: published ES gap-fill system.
- Absolute RTH gap between 0.05% and 0.20%.
- If prior RTH close is reached during opening 5-minute bar, no trade.
- At completion of opening 5m bar, enter in direction of the prior close.
- MES causal execution = 09:35 next-minute open.
- Stop = 12 points from actual entry.
- Target = prior RTH close.
- Exit RTH close if neither hit.

# Reporting per strategy

- trades
- trades/month
- net points/trade
- net PF
- win rate
- total net points
- positive years / 5
- max positive-year contribution
- news entry skips
- forced news exits
- serious-candidate gate

No thresholds, indicator periods, time windows, stops, targets, or source interpretations may be changed after the first result is seen.
