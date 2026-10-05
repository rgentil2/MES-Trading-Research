# MES H081 Temporal Robustness Audit — preregistration

Status: post-hoc diagnostic only. Frozen before opening the archived H081 trade-level artifact.

## Purpose

The user raised a specific methodological question: could a broad 2020-2025
aggregate hide an edge that is episodic by month/week, or could the positive
aggregate itself be concentrated in a few unusually good periods?

This audit answers that question for H081 / R072, the strongest monetizable MES
candidate already discovered. It does **not** change H081's signal, direction,
entry, exit, cost model, R063 HIGH requirement, or one-trade-per-session rule.

## Source

Use only the exact archived artifact produced by successful B14 run
36427711138 (2026-09-28), artifact b14-opposite-sign-candidates.

Primary file: H081_trades.parquet.

The artifact was generated under the frozen B14 specification:
- development years 2020-2025;
- primary 30-minute exit;
- one MES;
- base RT cost $4.38;
- 1.5x cost stress $6.57;
- no 2026 outcomes.

No raw 2026 file is opened by this audit.

## Fixed diagnostics

No period is selected for trading. Every period is reported.

1. Calendar year:
   - trades, net P&L, net expectancy, stress expectancy, PF, win rate.
2. Calendar quarter:
   - same metrics for every non-empty quarter.
3. Calendar month:
   - same metrics for every non-empty month.
4. Half-year blocks:
   - Jan-Jun and Jul-Dec for each year.
5. ISO week:
   - trade count and net P&L/expectancy, descriptive only.
6. Rolling trade windows:
   - 20-trade and 40-trade rolling net expectancy;
   - fraction of windows with positive expectancy;
   - median, minimum and maximum rolling expectancy.
7. Leave-one-year-out:
   - recompute aggregate expectancy/PF after removing each year.
8. Concentration stress:
   - share of total net P&L contributed by the best calendar quarter;
   - share contributed by the five largest winning trades;
   - expectancy after removing the best quarter;
   - expectancy after removing the five largest winning trades.

## Predefined temporal-concentration flags

These are diagnostics, not promotion gates. A flag is raised if:

- best quarter contributes >50% of total net P&L;
- five largest winning trades contribute >50% of total net P&L;
- removing the best quarter makes aggregate expectancy <=0;
- removing the five largest winning trades makes aggregate expectancy <=0;
- fewer than 50% of non-empty half-years have positive expectancy;
- fewer than 50% of rolling 20-trade windows have positive expectancy;
- any leave-one-year-out aggregate expectancy is <=0.

The audit reports the number and identity of flags. It does not search for
alternative cutoffs after seeing results.

## Interpretation

- Few/no concentration flags: H081's positive development result is broadly
  distributed in time, but it remains post-hoc and statistically unconfirmed.
- Several concentration flags: the aggregate is materially dependent on a
  subset of periods/trades and should not be rescued by choosing those periods.
- Month/week tables are diagnostic only. A profitable month, quarter, weekday or
  week may not be converted into a new trading rule from this audit.

## Holdout

MES 2026 remains completely unopened and reserved for a final fully specified
strategy only.
