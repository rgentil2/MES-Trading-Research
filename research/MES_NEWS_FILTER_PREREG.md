# MES — Forex Factory News Filter Re-test — Pre-registration

Locked before re-testing strategy outcomes.

## External rule

This filter reproduces the user's prior discretionary operating rule and is not derived from MES backtest outcomes.

- Source: Forex Factory economic calendar.
- Currency: USD only.
- Impacts: High and Medium only.
- Scheduled clock-time events only.
- Flat deadline: event time minus 5 minutes.
- Entry blackout: from T-5 through T+5 inclusive.
- If a position is already open, it must be closed at T-5.
- Market bars are never deleted. ATR, VWAP, OR, volume, value area and other state variables continue to use the complete market series.
- All Day/Tentative events are not assigned an intraday blackout because no causal clock time exists.

## 1-minute execution convention

NinjaTrader minute bars are end-of-bar labeled.

For a news event at 10:00 ET:
- Flat deadline is 09:55 ET.
- An open trade exits at the first executable 1-minute price at 09:55, modeled as the OPEN of the bar that starts at 09:55 (NinjaTrader EOB label 09:56).
- No new entry whose actual entry timestamp lies within 09:55 through 10:05 inclusive is allowed.
- A new entry after 10:05 is allowed.

At the forced-flat minute, NEWS exit takes precedence before that minute's SL/TP path because the position is closed at the minute open.

## Data

- MES 2020-2024 only.
- 2025 and 2026 are forbidden.
- Calendar = Forex Factory USD High/Medium 2020-2024 built by tools/build_forexfactory_calendar.py in GMT and converted with IANA America/New_York DST rules.

## Frozen re-tests

No strategy parameters may change. Compare baseline versus the exact same strategy with the news rule.

1. OR15 first-breakout 30-minute time exit
   - First MES close beyond first 15 RTH bars.
   - Event no later than 11:30 ET.
   - Entry next minute open.
   - Exit 30 minutes later, unless news forces earlier flat.
   - This is a signal-quality benchmark, not a final funded strategy.

2. Public ORB15
   - Existing external replication rules unchanged.
   - OR 09:30-09:45.
   - First 15-minute close outside range.
   - Enter next 15-minute open before 12:00.
   - SL opposite OR edge.
   - TP 1.5R.
   - EOD exit.
   - Add only the frozen news rule.

3. Academic overnight reversal
   - Existing external replication unchanged.
   - Fade prior RTH close -> current RTH open return.
   - Entry 09:30.
   - Normal exit 10:00.
   - Add only the frozen news rule.

4. Academic intraday momentum
   - Existing external replication unchanged.
   - Prior close -> 10:00 sign.
   - Entry 15:30.
   - Exit 16:00.
   - Add only the frozen news rule.

5. Market Profile return-to-value
   - Existing external replication unchanged.
   - Prior 70% TPO value area.
   - Open outside value; first 30m remains outside; second 30m closes inside.
   - Entry next minute.
   - Target opposite value-area edge.
   - Stop 6 ticks beyond re-entry edge.
   - Add only the frozen news rule.

## Reporting

For baseline and news-filter versions report:
- trades
- trades/month
- trades skipped because entry was in blackout
- trades force-closed at T-5
- net points/trade after $4.38 round-trip cost
- net profit factor
- win rate
- total net points
- positive years out of five
- year-by-year net totals

A filter is not a rescue merely because one metric improves. A strategy remains non-promotable unless it also meets the project's existing robustness/frequency standards.

No High-only, Medium-only, ±3m, ±10m, event-name exclusions, or other post-result variants are permitted in this block.
