# ES Stage Gates

Frozen framework: 2026-09-28.

## Gate 0 — Data integrity

Required before ES-B01:
- individual quarterly contracts identified;
- timezone convention confirmed;
- prices on 0.25-point grid;
- positive Last trade volume;
- Bid <= Ask outside documented transient anomalies;
- no unexplained timestamp reversals;
- Minute Last and Tick Last reconcile after timestamp convention is resolved;
- rollover boundaries explicit;
- no forward outcome crosses a contract boundary;
- quote-age distribution reported before choosing a stale-quote exclusion rule.

## Gate 1 — Hypothesis evidence, 2020–2024

A primary directional candidate normally requires:
- N >= 300 events when feasible;
- effect direction matches the hypothesis;
- 95% CI excludes zero;
- BH-adjusted q <= 0.05 across the primary family;
- at least 4 of 5 development years share the effect sign;
- no post-hoc subgroup rescue.

Passing Gate 1 creates a **candidate**, not a trading strategy.

## Gate 2 — 2025 validation

Before opening 2025 freeze feature formula, event definition, thresholds/past-only quantile rule, horizon and exclusions.

## Gate 3 — Strategy design

Only after a statistical candidate exists. Freeze entry, exit, stop/target, costs, size, cutoff and re-entry.

Initial targets: >=150 trades if feasible, net expectancy >0, PF >=1.20, positive net P&L and no obvious single-period dependence.

## Gate 4 — Robustness

Targets: IS PF >=1.30; validation/OOS PF >=1.15; positive OOS expectancy; >=200 total trades where feasible; >=50–60 validation trades; majority positive walk-forward windows; profitable at 1.5x costs; stable neighboring parameters; compatible drawdown.

## Gate 5 — Monte Carlo

At least 10,000 sequences. Report drawdown percentiles, losing streaks, loss-limit breach probability and cost/order sensitivity.

## Gate 6 — 2026 pseudo-forward

Open only after final strategy freeze. Replay chronologically and report every trade, expectancy, PF, win rate, max DD, losing streak, monthly stability and comparison with development/Monte Carlo.
