# PDC Complete Candidate — Architecture Evaluation

Status: locked before combined news + stop results are inspected.

## Important statistical status

ATR 0.30 was identified after reviewing 2023-2025 stop outcomes. Therefore 2020-2025 is **not** an independent validation sample for the complete candidate. This block only characterizes whether the proposed architecture is coherent enough to freeze for a future untouched 2026 test.

2026 remains forbidden.

## Frozen candidate

Base event:
- 0.10 <= abs(RTH open - PDC) / causal ATR14 < 0.20
- PDC untouched in first 5 RTH minutes
- first-5-minute close moves toward PDC
- entry at open of sixth RTH minute

Execution:
- target = PDC
- stop = 0.30 * causal ATR14 from entry, opposite target direction
- time exit = 11:30 ET
- base cost = $4.38 RT
- stress cost = $6.57 RT

News:
- scheduled Forex Factory USD High or Medium only
- flat at exactly T-5 minutes, modeled as the OPEN of the 1-minute bar starting at T-5
- block new entries from T-5 through T+5 inclusive
- bars remain in all indicator calculations

Intrabar ambiguity:
- if stop and target are both touched in the same 1-minute bar, STOP FIRST
- at a news-flat minute, NEWS EXIT at bar open occurs before that minute's stop/target path
- gap through stop receives the worse bar-open fill
- target fill remains PDC

## Fixed variants for attribution

1. NO_STOP_NO_NEWS
2. STOP030_NO_NEWS
3. NO_STOP_NEWS
4. STOP030_NEWS — proposed complete candidate

No other stop value or news window is tested in this block.

## Evaluation hierarchy

- week/month: diagnostic only
- quarter/semester: evaluation
- year: robustness
- rolling 6/12m: deterioration diagnostics only
- no retrospective period selection

## Candidate-freeze criteria before 2026

The complete STOP030_NEWS architecture is eligible to be frozen for a future 2026 test only if 2020-2025 characterization shows:
1. full-sample PF >= 1.30
2. stress expectancy > 0
3. max drawdown <= $250 per one MES contract
4. at least 7 of 12 semesters positive
5. total P&L positive in both 2024 and 2025
6. news handling does not reduce total P&L by more than 25% versus STOP030_NO_NEWS
7. worst single trade >= -$175

Passing these criteria does not prove the strategy; it only permits freezing it for untouched 2026.

## NinjaTrader follow-up

If the architecture qualifies, NinjaTrader Strategy Analyzer may be used later for:
- execution/fill verification
- slippage sensitivity
- narrow local robustness around the frozen stop (0.25/0.30/0.35 ATR)
- position sizing and funded-account drawdown simulation

It must not be used as an unrestricted optimizer over many parameters before the 2026 forward test.
