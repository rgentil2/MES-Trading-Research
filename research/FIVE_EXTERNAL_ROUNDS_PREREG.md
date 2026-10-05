# MES — Five External Strategy Rounds (5x5 = 25) — Pre-registration

Locked before running this 25-strategy block on MES 2020-2024.

## Common rules

- MES 2020-2024 only. 2025/2026 forbidden.
- One MES contract.
- Fixed round-trip cost: $4.38 = 0.876 MES points/trade.
- New intraday entries only 09:30 through 11:30 ET unless source is narrower.
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
- Daily systems are intentionally held to the same frequency gate; if they cannot generate the user's desired opportunity rate they are not final candidates.

# Round 1 — NinjaTrader core/sample/crossover

## R1-S1 SampleMACrossOver
Source: NinjaTrader built-in SampleMACrossOver / forum-posted source.
- SMA Fast=10, Slow=25.
- Long CrossAbove(SMA10,SMA25,1); short CrossBelow.
- Bar-close signal, next 1m open.
- Opposite signal closes/reverses; reverse entry only inside 09:30-11:30.
- No fixed source SL/PT; RTH close flat.

## R1-S2 SamplePriceModification
Source: NinjaTrader sample strategy.
- Bar-close logic.
- Long if current close is above each prior 10 closes and prior 10 opens and current open<close.
- Short mirror.
- SL 20 ticks; PT 100 ticks.
- After +50 ticks favorable close, stop moves to breakeven.
- Entry next 1m open; RTH close flat.

## R1-S3 SMA5/30 one-tick target
Source: NinjaTrader Support Forum, "Strategy builder stumped".
- SMA5 crosses above SMA30 within lookback 2 bars.
- Long-only.
- Entry next 1m open.
- PT=1 tick.
- No source stop; RTH close flat.

## R1-S4 EMA20/40 + RSI14,3
Source: NinjaTrader Support Forum, "setting stop loss on an MA".
- EMA20 > EMA40.
- RSI(Close,14,3) CrossAbove 60 within lookback 10.
- Long-only.
- Entry next 1m open.
- PT=200 ticks.
- Dynamic stop updated to EMA40 from completed bars.
- RTH close flat.

## R1-S5 Basic Donchian 20
Source: NinjaTrader Support Forum, BasicDonchian + NT Donchian help-guide convention.
- Period=20.
- Long when Close crosses above prior completed Donchian20 upper.
- Exit when Close crosses below prior completed Donchian20 lower.
- Next-bar execution.
- No fixed stop/target; RTH close flat because user trades intraday.

# Round 2 — NinjaTrader intraday/pattern/momentum

## R2-S1 Contrarian MACD 10/10
Source: NinjaTrader Support Forum, "Simple MacD Cross Over".
- Standard MACD 12/26/9.
- MACD crosses above signal => SHORT.
- MACD crosses below => LONG.
- SL=10 ticks; PT=10 ticks.
- Next 1m open; RTH flat.

## R2-S2 MFI + MACD 5-minute long
Source: NinjaTrader Support Forum, "MFI + MACD Simple strategy (5 min)".
- 5-minute RTH bars.
- MFI14 <20 AND MACD(12,26,9) Diff crosses upward through 0.
- Entry next 5m open.
- Stop=low of signal 5m candle.
- Exit when MFI>80 AND MACD Diff < prior 5m Diff.
- No invented target; RTH flat.

## R2-S3 Inside-bar directional close 10/25
Source: NinjaTrader Support Forum inside-bar thread + support's concrete 10/25 SetStopLoss/SetProfitTarget example.
- Inside bar: High<prior High and Low>prior Low.
- If inside-bar Close==High: buy stop at High+1 tick.
- If inside-bar Close==Low: sell stop at Low-1 tick.
- Orders valid only during the next 1m bar.
- SL=10 ticks; PT=25 ticks.
- RTH flat.

## R2-S4 Inside-bar structural bracket
Source: NinjaTrader Support Forum "inside bar".
- Inside bar: current Low>previous Low and current High<previous High.
- Next bar: OCO buy stop High+1 tick and sell stop Low-1 tick.
- First side touched enters; if both sides touch in the same 1m bar, skip as ambiguous.
- Long stop=inside-bar Low-1 tick; short stop=inside-bar High+1 tick.
- No source target; RTH close flat.

## R2-S5 Bollinger100 fade
Source: NinjaTrader Support Forum MultiFadeAtEachBollinger.
- Bollinger length=100, deviation=1.5.
- Short-only visible source leg: if Close > upper band, short next 1m open.
- Source PT=$2,500 and SL=$5,000.
- For one MES: PT=500 index points, SL=1,000 index points.
- RTH close flat.

# Round 3 — NinjaTrader levels / areas / prior-session prices

## R3-S1 ES/MES VWAP 2-sigma mean reversion
Source: NinjaTrader Support Forum ES VWAP strategy request.
- Long-only.
- Session cumulative VWAP and weighted sigma.
- VWAP-to-lower-2σ distance between 10 and 12 points for >=15 completed minutes.
- Signal when price touches/crosses lower 2σ.
- Entry next 1m open.
- Stop=5 points below entry.
- Dynamic target=session VWAP.
- RTH flat.

## R3-S2 Bollinger(2,14) lower-to-upper
Source: NinjaTrader Support Forum Bollinger strategy example.
- Bollinger period=14, std dev=2.
- Long when Close crosses above lower band.
- Entry next 1m open.
- Exit when Close crosses below upper band.
- No source stop; RTH flat.

## R3-S3 SMA5/Close stop-entry 1R
Source: NinjaTrader Support Forum "Declaring variables and performing calculations".
- Long stop-entry level=min(SMA5,Close); short stop-entry level=max(SMA5,Close), as posted.
- Long risk reference=lowest Low of prior 10 completed bars.
- Short risk reference=highest High of prior 10 completed bars.
- Target=1:1 from entry-level risk.
- Entry orders valid during following 1m bar only; if both directions could trigger same bar, skip.
- RTH flat.

## R3-S4 Prior-day high/low breakout with signal-bar stop
Source: NinjaTrader Support Forum "Setting the stop at the low of entry candle".
- Long if Close crosses above prior RTH High and Close>current RTH Open.
- Short if Close crosses below prior RTH Low and Close<current RTH Open.
- Entry next 1m open.
- Long stop=signal-bar Low-1 tick.
- Short stop=signal-bar High+1 tick.
- No target; RTH flat.

## R3-S5 Prior-day close cross 100/200
Source: NinjaTrader Support Forum "Prior Day Close Script Problem".
- Short when Close crosses below prior RTH Close, using the corrected condition from NinjaTrader support.
- Entry next 1m open.
- SL=100 ticks.
- PT=200 ticks.
- RTH flat.

# Round 4 — Published mean-reversion / reversal systems

## R4-S1 Connors RSI(2)
Source: Larry Connors/Cesar Alvarez public rule set.
- Daily RTH.
- Close>SMA200 and RSI2<5.
- Causal adaptation: buy next RTH open.
- Exit next RTH open after a completed daily Close>SMA5.
- No stop in original.

## R4-S2 Connors Double 7
Source: Cesar Alvarez original-rule restatement.
- Daily RTH.
- Close>SMA200.
- Close<=lowest close of 7-day window.
- Buy next RTH open.
- Exit next RTH open after Close>=highest close of 7-day window.
- No stop.

## R4-S3 Larry Williams Oops + FPO
Source: Larry Williams Oops descriptions / X-Trader.
- If today's RTH open < prior RTH Low, buy stop at prior Low.
- If today's RTH open > prior RTH High, sell stop at prior High.
- Long initial stop=current day's low observed through entry; short stop=current day's high observed through entry.
- Exit at first subsequent session open profitable versus entry (FPO).
- News flat can close earlier.

## R4-S4 Connors RSI2 symmetric 30m
Source: published MQL5 reproduction of Connors RSI2.
- 30-minute RTH bars.
- Long: RSI2<5 and Close>SMA200.
- Short: RSI2>95 and Close<SMA200.
- Entry next 30m open if actual entry <=11:30.
- Long exit: Close>SMA5 or Close<SMA200; short mirror.
- Stop distance=0.15% of entry.
- No fixed target.
- RTH flat.

## R4-S5 Published Donchian 20/10 long-only
Source: public Donchian 20/10 rule set.
- Daily RTH.
- Long when completed Close exceeds highest High of prior 20 completed sessions.
- Entry next RTH open.
- Exit next RTH open after Close falls below lowest Low of prior 10 completed sessions.
- No pyramiding or added stop.

# Round 5 — Structural breakouts / gaps / Turtle systems

## R5-S1 Opening gap fade to prior RTH close
Source: published NQ/ES gap-fill backtest rule set.
- Gap=current 09:30 open-prior RTH close.
- Skip abs gap<0.10%.
- Enter against gap at 09:30.
- Target=prior RTH close.
- Stop=one full gap length beyond entry.
- RTH close exit.

## R5-S2 5-minute ES gap fill
Source: published ES gap-fill system.
- Absolute RTH gap 0.05%-0.20%.
- If prior RTH close touched in opening 5m, no trade.
- Enter at 09:35 next-minute open toward prior close.
- Stop=12 points.
- Target=prior RTH close.
- RTH close exit.

## R5-S3 Turtle System 1 shape
Source: original Turtle rules.
- Long break above prior 20-session High; short break below prior 20-session Low.
- Entry on intraday break using 1m data.
- Exit long on prior 10-session Low; short on prior 10-session High.
- Protective stop=2N from entry; N=20-day Wilder ATR.
- No pyramiding.

## R5-S4 Turtle System 2 shape
Source: original Turtle rules.
- Long break above prior 55-session High; short break below prior 55-session Low.
- Exit on opposite 20-session breakout.
- Protective stop=2N; N=20-day Wilder ATR.
- No pyramiding.

## R5-S5 Donchian four-week 20/20
Source: Donchian four-week rule / public Donchian tests.
- Long break above prior 20-session High; short break below prior 20-session Low.
- Reverse/exit on opposite prior 20-session boundary.
- No extra target or stop.
- No pyramiding.

# Reporting

For every strategy report:
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
