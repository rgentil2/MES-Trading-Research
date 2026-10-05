# MES — NinjaTrader Community Strategy Challenge — Pre-registration

Locked before any of these strategies are run on MES 2020-2024.

## Common operational overlay

This challenge asks whether externally sourced NinjaTrader/community rules can survive under the user's actual operating constraints.

- Instrument for execution: MES.
- Development sample: 2020-2024 only.
- 2025 and 2026 forbidden.
- One MES contract.
- Fixed round-trip trading cost: $4.38 = 0.876 MES points/trade.
- New entries only from 09:30 through 11:30 ET, unless the source itself is narrower.
- Forex Factory rule is mandatory:
  - USD High/Medium only.
  - flat at T-5 minutes.
  - no new entries T-5 through T+5 inclusive.
- Full bars remain available to indicators.
- One open position at a time.
- If stop and target touch in the same 1-minute bar, count the stop first (conservative).
- No parameter optimization.

## Strategy NT-F01 — EMA 5/34 crossover

Source: NinjaTrader Support Forum, "Looking for simple EMA's crossover strategy".

Published rule/code:
- EMA fast = 5.
- EMA slow = 34.
- long if EMA5 crosses above EMA34.
- short if EMA5 crosses below EMA34.
- corrected forum code uses CrossAbove/CrossBelow lookback = 3.
- profit target = 20 ticks.
- stop loss = 15 ticks.
- calculate on bar close.

Source does not freeze a chart interval for MES. This is therefore explicitly an **adaptation**, not an exact replication:
- MES 1-minute bars.
- signal at bar close; market entry at next bar open.
- operational/news overlay above.

## Strategy NT-F02 — Official NinjaTrader RSI tutorial

Source: NinjaTrader official strategy tutorial, RSI with Stop Loss & Profit Target.

Published rule:
- RSI period 14, smooth 3.
- long when RSI crosses above 20 within the last bar.
- profit target 12 ticks.
- stop loss 6 ticks.
- calculate on bar close.
- long-only.

The tutorial is instrument/timeframe agnostic. Adaptation:
- MES 1-minute bars.
- entry next bar open.
- operational/news overlay above.

RSI uses Wilder smoothing (k = 1/period), matching NinjaTrader documentation.

## Strategy NT-F03 — Doji long

Source: NinjaTrader Support Forum, "Stop loss + Profit Target".

Published intent:
- when a doji occurs, go long.
- doji is treated literally as Open == Close, per the support response.
- stop = 2 ticks below the doji low.
- profit target in ticks = doji High-Low size in ticks.

Adaptation:
- MES 1-minute bars.
- signal on exact Open == Close.
- entry next bar open.
- target = entry + doji range.
- skip if next-bar entry is already at/below the fixed stop.
- operational/news overlay above.

No doji tolerance is introduced.

## Strategy NT-F04 — 5-bar channel breakout, ES 30m

Source: NinjaTrader Support Forum, "Reverse Position", post explicitly describing testing on ES 30-minute.

Published rule:
- if flat, place a long stop at MAX(High, 5).
- if long, exit stop at MIN(Low, 5).
- ExitOnClose = true.
- Forum support confirmed working entry/exit mechanics.

Replication on MES:
- 30-minute RTH bars built causally from underlying 1-minute MES data.
- at each 30m close, the next 30m block uses the frozen MAX5 entry or MIN5 exit level.
- fills resolved with underlying 1-minute bars.
- long-only, matching the posted ExitLong version (no invented symmetric short).
- entries only through 11:30 ET.
- news overlay above.

## Strategy NT-F05 — 09:30–10:30 range breakout

Source: NinjaTrader Support Forum, "Breakout strategy".

Published rule:
- determine highest high and lowest low from 09:30 to 10:30.
- long at highest high + 1 tick OR short at lowest low - 1 tick.
- if long, stop at lowest low - 1 tick.
- if short, stop at highest high + 1 tick.
- exit at stop or 18:00.

Interpretation:
- source times are interpreted as US Eastern Time because the range begins at the US cash open 09:30.
- entry orders become active after the 10:30 range is complete.
- user's operating overlay cancels unfilled entries after 11:30.
- OCO assumption: first side touched enters; if both sides are touched in the same 1-minute bar, that day is skipped as ambiguous.
- underlying 1-minute MES data resolve entries/stops.
- if still open, exit at the 18:00 ET bar close.
- news overlay above.

## Forum ideas screened but excluded

These are not silently parameterized:
- "higher-high scalp" for ES: attachment/rules available in search describe 1-point profit, start after 09:30 and five-bar wait, but the accessible text does not expose a complete stop/entry specification.
- MES large-candle + SMA24 multi-timeframe post: entry concept is clear, but posted stop/target code is malformed/incomplete.
- NQ/MES divergence post: Stoplossbyticks and TPbyTicks are user inputs, but accessible post does not expose frozen default values.
- 12:50 ES time-short (TP40 ticks, SL5 ticks): complete, but excluded because entry time violates the user's prior 09:30-11:30 operating constraint.
- generic indicator snippets with unspecified stop/target values are excluded.

## Promotion gate

A strategy is a serious candidate only if, after the frozen news rule and $4.38 RT cost:

1. Net expectancy > 0.
2. Net PF >= 1.25.
3. At least 5 trades/month average (>=300 trades / 60 months).
4. Positive net total in at least 4 of 5 years.
5. No single year contributes >40% of total positive P&L.
6. If promoted, only then proceed to 1.5x cost stress and parameter-neighborhood robustness.

No strategy in this challenge may be tuned after seeing its result.
