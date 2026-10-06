# MES Risk Design P2 — preregistration

Status: frozen before the first stop/target result.

## Fixed signal

P2 may not change the P1 development signal anchor:

- R072 exact inverse rejection in R063 HIGH state;
- wick threshold 0.50;
- latest signal time 11:00 ET;
- one earliest qualifying trade per session;
- next exact one-minute Open entry;
- maximum holding time 30 minutes.

Identifier: W0.50_C1100_H30.

## Why the risk grid is bounded

P1C showed, in units of the causal 15-minute signal-block range:

- winner MAE: median 0.256, q75 0.385, q90 0.620, q95 0.803;
- loser MAE: median 0.634;
- winner MFE: median 0.787, q75 1.261.

Therefore P2 freezes the following coarse grid before testing P&L:

Stop distance:
- NONE
- 0.50 x block range
- 0.65 x block range
- 0.80 x block range

Profit target:
- NONE
- 0.75 x block range
- 1.00 x block range
- 1.25 x block range

Total: 16 variants including the no-stop/no-target 30-minute control.

No trailing stop, break-even move, partial exit, side-specific parameter,
time-of-day parameter or regime filter is permitted in P2.

## Execution convention

- MES tick = 0.25 point.
- Stop distance is rounded DOWN to the nearest valid tick (minimum one tick),
  making the modeled stop weakly closer and therefore conservative.
- Target distance is rounded UP to the nearest valid tick, making the target
  weakly farther and therefore conservative.
- Each one-minute bar is evaluated chronologically from the entry bar through
  the 30-minute time-exit bar.
- If both stop and target are touched in the same one-minute bar, assume
  **stop first**.
- Otherwise exit at the first touched level.
- If neither is touched, exit at the same frozen 30-minute close as P1.
- Base RT cost: $4.38. Stress RT cost: $6.57.

## Walk-forward

Use the same eight trailing-24-month training / next-semester test folds as P1.

A risk variant is eligible in a training fold only if:

- >=25 trades;
- base expectancy > 0;
- PF > 1.0;
- stress-cost expectancy > 0;
- at least half of observed training semesters have positive P&L.

Rank eligible variants by:

1. highest median semester expectancy;
2. lower training max drawdown;
3. higher PF;
4. higher expectancy;
5. deterministic stop/target order.

If none is eligible, select NO TRADE for that fold.

## Evaluation hierarchy

- Week -> diagnostic only.
- Month -> diagnostic only.
- Quarter / semester -> evaluation.
- Year -> robustness.
- R063 context -> explanation only.

Weeks/months and regime subgroups cannot select or rescue a risk rule.

## Control comparison

P2 must report both:

1. concatenated walk-forward results of the selected risk variants; and
2. the fixed no-stop/no-target 30-minute control over the same 2022–2025 test
   dates.

Report net P&L, expectancy, PF, stress expectancy, max drawdown, positive
semesters and positive years.

P2 is still development work on reused 2020–2025 data. Passing P2 does not
authorize live trading. 2026 remains completely unopened.
