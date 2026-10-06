# PDC Small-Gap — Stop Design Preregistration

Status: locked before stop results are inspected.

## Objective

Determine whether a simple causal stop can reduce the catastrophic left tail of the PDC small-gap setup without destroying its positive expectancy.

## Base setup

Frozen PDC reconstruction:
- 0.10 <= abs(RTH open - PDC) / causal ATR14 < 0.20
- PDC untouched in first 5 RTH minutes
- first-5-minute close moves toward PDC
- entry at open of sixth RTH minute
- target = PDC
- time exit = 11:30 ET
- cost = $4.38 RT
- 2026 forbidden

## Split

- Stop design: 2020-2022 only.
- Validation: 2023-2025 only.
- Validation is read once after the candidates below are frozen.

## Candidate stop families

No-stop control plus exactly these candidates:

### ATR stops
Distance from entry, opposite the PDC direction:
- 0.15 ATR
- 0.20 ATR
- 0.25 ATR
- 0.30 ATR
- 0.35 ATR

### Initial-risk stops
Let D = abs(entry - PDC), the reward distance at entry.
- 1.0 D
- 1.5 D
- 2.0 D
- 2.5 D
- 3.0 D

No other distances may be added after validation is observed.

## Execution

For each 1-minute bar after entry:
- if target only is touched: exit at PDC;
- if stop only is touched: exit at stop;
- if both target and stop are touched within the same 1-minute bar, intrabar order is unknowable from OHLC, so use the conservative assumption **STOP FIRST**;
- if neither is touched by 11:30 ET, exit at the 11:30 close;
- gap-through-stop fill uses the worse of bar open and stop;
- target gap improvement is not assumed; target fill remains PDC.

## Selection on 2020-2022

A candidate is eligible to be frozen only if all hold on design:
1. net expectancy > no-stop expectancy OR max drawdown improves by at least 30%;
2. net expectancy > 0;
3. stress expectancy at $6.57 RT > 0;
4. at least 3 semesters represented and >=30 trades total;
5. target-hit rate among surviving trades remains >=70%.

Among eligible stops, select the one with highest:
`score = net_expectancy_usd - 0.02 * abs(max_drawdown_usd)`

This score is frozen before validation. If no stop is eligible, validation still reports all candidates descriptively but no stop is promoted.

## Validation gate 2023-2025

The design-selected stop is promoted only if, versus no-stop validation control:
1. net expectancy remains > 0;
2. PF >= 1.20;
3. stress expectancy > 0;
4. max drawdown improves by >=25%;
5. total net P&L is not reduced by more than 20%;
6. at least 4 of 6 validation semesters have positive net P&L.

## Interpretation

The aim is not to maximize PF. The aim is to trade some upside for a materially safer loss distribution suitable for funded-account constraints.

No 2026 data may be opened.
