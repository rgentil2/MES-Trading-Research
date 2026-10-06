# MES Fixed-Base Path Diagnostic P1C

Status: diagnostic only, after the P1 development decision.

## Frozen base

- Signal: R072 exact inverse rejection in R063 HIGH state.
- Wick threshold: 0.50.
- Latest signal: 11:00 ET.
- Baseline time exit: 30 minutes.
- One earliest qualifying trade per session.
- Entry: next exact one-minute Open.
- Base cost: $4.38 RT; stress cost: $6.57 RT.

No signal parameter is changed in P1C.

## Purpose

Determine whether the 2025 deterioration is dominated by a small number of
large adverse excursions that a later stop/target design could plausibly control,
or whether losses are broad across trades.

## Required outputs

Using the same MES 2020–2025 development data:

- Week and month: diagnosis only.
- Quarter and semester: evaluation.
- Year: robustness.
- Existing R063 context: explanation.
- MFE/MAE over the fixed 30-minute holding window.
- MFE and MAE normalized by the causal 15-minute signal-block range.
- Quantiles overall, winners, losers and 2025.
- Worst individual trades.
- Loss concentration: share of total gross losses attributable to the worst
  1, 3 and 5 losing trades, overall and in 2025.

P1C does not select a stop or target. Its distributions may be used to define
a coarse preregistered P2 risk grid.

2026 remains completely unopened.
