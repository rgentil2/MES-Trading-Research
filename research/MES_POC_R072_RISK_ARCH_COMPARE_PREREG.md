# MES POC/R072 Risk Architecture Comparison — Hard Stop vs Average ATR Bracket

Status: locked before validation results are inspected.
2026 remains strictly closed.

## Objective

Compare three risk architectures for POC and R072:

A. CURRENT CONTROL
- existing entry and news rules
- POC: H15 timed exit
- R072: H30 timed exit
- no stop and no target

B. HARD CATASTROPHE STOP
- same time exit and news rules
- no TP
- one hard SL designed to sit outside normal historical excursion

C. AVG ATR BRACKET
- same entry and news rules
- explicit SL and TP derived from average historical excursion
- time exit remains as a failsafe

## Data split

Design: 2020-2022 only.
Validation: 2023-2025 only.
2026 forbidden.

## Common excursion measurements

Use causal prior-session Wilder ATR14.

For each design trade calculate:
- MAE_ATR = maximum adverse excursion / ATR14_prev
- MFE_ATR = maximum favorable excursion / ATR14_prev
- net winner/loser using the current timed-exit architecture after $4.38 RT cost.

Report for all trades and separately winners/losers:
- mean, median, P75, P90, P95, P99, maximum MAE/MFE.

## Architecture B: hard catastrophe stop

The stop is frozen from design data as:

HardSL_ATR = ceil_to_0.05( 1.10 * max(
    P99 MAE of ALL design trades,
    maximum MAE of DESIGN WINNERS
))

Rationale:
- sits beyond nearly all design-path noise;
- explicitly protects against a new catastrophic excursion;
- should interfere minimally with legitimate winners.

No TP.
Existing timed exit remains.

## Architecture C: average ATR bracket

Freeze:
- AvgSL_ATR = ceil_to_0.05(mean MAE_ATR of DESIGN LOSERS)
- AvgTP_ATR = floor_to_0.05(mean MFE_ATR of DESIGN WINNERS)

Minimum level 0.05 ATR.

Rationale:
- SL represents the average adverse excursion of trades that ultimately lose;
- TP represents the average favorable excursion of trades that ultimately win;
- this directly tests the user's proposed "average SL / average TP" concept.

No parameter search around these averages in this study.

## Fill rules

For a LONG:
- SL = entry - k*ATR
- TP = entry + k*ATR

For a SHORT:
- SL = entry + k*ATR
- TP = entry - k*ATR

If SL and TP are touched in the same 1m bar:
- STOP FIRST (conservative).

Gap-through stop:
- fill at worse of stop and bar open.

Target:
- fill at target; no favorable gap improvement credited.

News forced-flat at T-5:
- occurs at the minute OPEN before that minute's path and takes precedence.

Existing time exits remain:
- POC H15
- R072 H30

Costs:
- base $4.38 RT
- stress $6.57 RT.

## Validation comparison

For CURRENT, HARD_STOP, AVG_BRACKET report:
- trades
- net P&L
- expectancy
- PF
- stress expectancy
- win rate
- max DD
- worst trade
- positive semesters
- years positive
- stop rate
- target rate
- time/news exit rate
- average win
- average loss
- payoff ratio
- risk in MES dollars implied by ATR stop (median and P90 over validation trades)

## Interpretation

Hard stop is acceptable if:
- validation expectancy >0
- validation stress expectancy >0
- PF >=1.10
- worst trade materially bounded vs current
- expectancy retains at least 70% of current when current expectancy is positive.

AVG bracket is viable if:
- validation expectancy >0
- validation stress expectancy >0
- PF >=1.15
- at least 3/6 validation semesters positive
- max DD <= current max DD
- expectancy retains at least 70% of current when current expectancy is positive.

No architecture is selected solely for having the highest P&L.
