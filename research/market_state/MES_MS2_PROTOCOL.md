# MES Market State V2 — calendar/data-availability correction

Version: MES-MS2-20261005

Status: frozen design before the first V2 state-map run. V1 remains immutable.

## Why V2 exists

The V1 descriptive run classified only 381 of 1,294 generic weekday rows. Two
outcome-free availability audits then identified data-construction issues:

- A1 found 15 ET-calendar-2024 dates missing because the source set stopped at
  DEC24 even though MAR25 contains the remaining 2024 rows.
- A2 found that 112 of the 169 UNKNOWN_PREVIOUS_RTH cases were caused by stray
  Saturday/Sunday Last bars being treated as a prior RTH session. About 40 more
  cases were weekday shortened sessions with roughly 204-225 observed RTH bars,
  while 16 regular sessions had 376-389 bars with both endpoints present.

No return, P&L or strategy outcome was used to make this correction.

## Fixed V2 changes

1. **Session calendar**
   - Use `pandas_market_calendars==5.4.0`, calendar `CME_Equity`.
   - The feature calendar is the CME Equity scheduled session index, not generic
     Monday-Friday dates and not every calendar date that happens to contain a
     Last record.
   - Weekend stray records cannot become the prior RTH session.

2. **Research RTH**
   - Start remains 09:31 ET because NinjaTrader one-minute timestamps are end-bar.
   - End is the earlier of the scheduled CME Equity close and 16:00 ET.
   - A session is usable only if the 09:31 bar and scheduled final research bar
     are both present and at least 95% of scheduled one-minute Last bars are
     observed.
   - Scheduled shortened sessions are therefore eligible on their true scheduled
     length. The 95% rule is a data-coverage rule, not a liquidity or outcome
     filter.

3. **Late 2024**
   - Source files may include MES MAR25 solely to complete ET-calendar 2024.
   - All rows are filtered to ET year <=2024 before feature generation.
   - No 2025 feature, return or strategy result is computed.

4. **Everything else stays fixed**
   - ATR14, Trend10, ER10 definitions;
   - 252-session lagged reference and minimum-valid rule;
   - P33/P67 thresholds and hysteresis;
   - overnight thresholds and directions;
   - CUSUM k=0.5, h=5 and five-ready-session transition window;
   - R1-R4 meanings;
   - no strategy outcomes in the state-map phase.

## Scope and holdout

Development state map: ET calendar 2020-2024 only.

MES 2025 has already been researched historically and is not treated as pristine.
MES 2026 remains fully unopened and reserved exclusively for the final frozen
strategy forward/pseudo-forward evaluation.

## Acceptance criterion for V2

The first V2 run is descriptive. It must report state coverage and every R0
reason, compare those counts with V1, and verify that no 2025/2026 feature row
exists.

Improved coverage is not evidence of profitability. Only after V2 is frozen and
audited may a separate preregistered phenomenon test use its states.
