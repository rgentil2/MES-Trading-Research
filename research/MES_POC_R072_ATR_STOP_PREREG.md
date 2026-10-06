# MES Risk Design — POC + R072 ATR Stop Study

Status: locked before validation results are inspected.

## Goal

Add an explicit maximum-loss rule to POC and R072 without searching arbitrary stop grids.

2026 remains strictly closed.

## Split

- Design / stop geometry: 2020-2022 only.
- Validation: 2023-2025 only.

No 2023-2025 result may influence candidate stop construction.

## Common ATR

Use causal Wilder ATR14 from completed RTH daily true range, shifted one session.
ATR is known before the current RTH open.

## Existing strategy rules remain fixed

### POC
- current POC Breakdown signal;
- short next-minute open;
- frozen USD High/Medium T-5/T+5 news policy;
- H15 timed exit;
- no TP.

### R072
- W0.50;
- cutoff 11:00 ET;
- first valid signal/session;
- next-minute-open entry;
- frozen USD High/Medium T-5/T+5 news policy;
- H30 timed exit;
- no TP.

## MAE / MFE geometry

For each trade, from entry through its actual exit horizon/news exit:
- MAE = maximum adverse movement from entry.
- MFE = maximum favorable movement from entry.
- both expressed in ATR14_prev.

Winner/loser is defined by net P&L after $4.38 RT cost.

## Stop candidates

Construct candidates using ONLY 2020-2022 winning trades.

For each strategy:
- tight stop = winner MAE 75th percentile;
- center stop = winner MAE 85th percentile;
- wide stop = winner MAE 95th percentile.

Each value is rounded UP to the nearest 0.05 ATR.
Duplicates after rounding are collapsed; if fewer than 3 unique stops remain, add the nearest ±0.05 ATR values around the center while preserving order and positivity.

No stop distance may be manually changed after 2023-2025 is inspected.

## Stop execution

- Stop is placed opposite the trade direction at Entry ± k*ATR.
- If price gaps through stop at bar open, use the worse of stop and bar open.
- News forced-flat at T-5 takes precedence at that minute's OPEN.
- Timed exit remains H15 for POC and H30 for R072.
- No TP introduced.
- Same $4.38 base and $6.57 stress RT cost.

## Evaluation

Report for no-stop control and each stop:
- trades
- expectancy
- PF
- stress expectancy
- max DD
- worst trade
- positive semesters
- annual P&L

### Validation gate for a useful stop

A candidate is useful only if on 2023-2025:
1. expectancy > 0;
2. PF >= 1.15;
3. stress expectancy > 0;
4. max DD improves >=25% vs no-stop;
5. worst trade improves >=25% vs no-stop;
6. total P&L is not reduced by more than 25% vs no-stop when no-stop P&L is positive;
7. at least 3 of 6 semesters positive.

Selection rule:
- Prefer the CENTER candidate if it passes.
- If center fails and one neighbor passes, that neighbor becomes a research candidate.
- If multiple neighbors pass, choose the one with lower max DD, not higher historical P&L.

Passing this study creates a stop candidate; it does not make the strategy final.
