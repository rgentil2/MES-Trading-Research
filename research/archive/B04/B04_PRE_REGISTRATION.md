# B04 / R029–R033 — Opening Microstructure

Frozen before execution: 2026-09-27.

## Common policy
- Development pool: 2020–2025.
- 2026 remains completely unopened.
- RTH full sessions only: 09:31–16:00 ET.
- Fixed opening windows are used; no intraday parameter search.
- Historical thresholds use only the prior 60 eligible sessions.
- H038–H042 are frozen simultaneously and corrected with BH/FDR.

## H038 / R029 — Strong 5m Opening Impulse Continuation
First 5 RTH bars: 09:31–09:35.
Signal:
- |5m return| >= q80 of prior 60 sessions;
- body/range >= 0.70.
Outcome:
- return from 09:35 close to 09:50 close in impulse direction.
Gate: N>=150, mean>=1bps, CI>0, >=4/6 positive years, BH q<0.05.

## H039 / R030 — 5m Opening Rejection Reversal
First-5m range >= q70 of prior 60 sessions.
Upper rejection:
- upper wick >=50% of 5m range;
- close < open;
- expected direction DOWN.
Lower rejection:
- lower wick >=50% of range;
- close > open;
- expected direction UP.
Outcome: expected-direction return from 09:35 to 09:50.
Gate: N>=100, mean>=1bps, CI>0, >=4/6 positive years, BH q<0.05.

## H040 / R031 — Wide First-15m Range Persistence
First 15m range >= q80 of prior 60 sessions.
Future window = 09:46–10:15 high-low range.
Outcome:
FutureRangeExpansionPct = (future30 range / prior60 mean future30 range - 1) × 100.
Gate: N>=200, mean>=10%, CI>0, >=4/6 positive years, BH q<0.05.

## H041 / R032 — Narrow First-15m Range Persistence
First 15m range <= q20.
Outcome:
FutureRangeDiscountPct = (1 - future30 range / prior60 mean future30 range) × 100.
Same gate as H040.

## H042 / R033 — Three-Bar Opening Sequence Continuation
First three RTH bars all bullish or all bearish.
Total volume of first 3 bars >= q70 of prior 60 sessions.
Outcome: return from 09:33 close to 09:48 close in sequence direction.
Gate: N>=100, mean>=1bps, CI>0, >=4/6 positive years, BH q<0.05.

## Holdout
2026 is not used anywhere in B04.
