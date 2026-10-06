# MES Parameter Stability P1B — protocol

Status: diagnostic follow-up to the frozen P1 walk-forward. P1 results are not changed.

## Purpose

P1 passed its numeric walk-forward gate but selected five different parameter
variants across eight folds and deteriorated sharply in 2025. P1B separates:

1. **parameter instability** — whether nearby values of wick threshold, cutoff
   and time exit behave similarly across years/semesters; and
2. **market-state deterioration** — whether 2025 failed because the mix of
   causal regimes changed, or because performance weakened even inside regimes
   that had previously been favorable.

## Fixed scope

- Same MES source and same 2020–2025 development history used by P1.
- Same 45 variants only:
  - wick: 0.40, 0.45, 0.50, 0.55, 0.60
  - cutoff: 10:30, 11:00, 11:30 ET
  - exit: 15, 30, 60 minutes
- Same $4.38 RT cost and $6.57 stress cost.
- Same R072 signal architecture and R063 engine.
- Same P1 fold-selection algorithm. P1B must reproduce it.
- 2026 remains completely unopened.

No new parameter value, stop, target, side rule or regime filter is introduced.

## Temporal hierarchy

- Week: not used in P1B.
- Month: not used in P1B.
- Semester/year: parameter-stability diagnostics.
- Year x regime and semester x regime: explanation.

## Parameter stability outputs

For every one of the 45 fixed variants report:

- trades, expectancy, stress expectancy and PF over 2020–2025;
- positive years / observed years;
- median and worst annual expectancy;
- positive semesters / observed semesters;
- median semester expectancy;
- 2025 expectancy and PF.

Immediate neighbors are variants differing by exactly one adjacent grid step in
one parameter while the other two parameters remain fixed. For every variant
report the fraction of immediate neighbors satisfying all descriptive conditions:

- full-development expectancy > 0;
- stress expectancy > 0;
- PF > 1.0;
- at least 4 positive years.

This is a plateau diagnostic, not a new pass/fail gate.

## Regime deterioration outputs

Reconstruct the exact concatenated P1 pseudo-OOS trades and join only causal
session context already available at entry. For each calendar year and semester,
cross-tab performance by:

- pre-open prediction;
- first-15 updated prediction;
- previous-day range state;
- overnight range state;
- five-day range state;
- pre-open support;
- open15 support.

P1B does not authorize choosing a profitable subgroup after viewing these tables.
Any regime filter considered later must be frozen in a separate P2 protocol
before its strategy results are evaluated.

## Interpretation

Classify the 2025 deterioration descriptively:

- **composition explanation** if historically weak categories become much more
  prevalent and historically favorable categories retain positive performance;
- **within-regime degradation** if historically favorable categories themselves
  turn materially negative in 2025;
- **mixed** if both occur.

No claim of independent OOS validation is permitted. 2026 stays reserved for
the final frozen strategy.
