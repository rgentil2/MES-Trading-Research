# ES Stage Gates

Frozen framework: 2026-09-28.
Prospective amendment: 2026-10-09 — Gate 1 **exploratory screening only**. Previous experiment preregistrations, holdout locks, and confirmatory family policies remain unchanged.

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

## Gate 1 — Hypothesis evidence, 2020–2024 (prospective exploratory screen)

**Purpose:** admit low-frequency but plausible mechanisms for further investigation in a future multi-strategy portfolio. This screen **does not statistically confirm an edge** and is not permission to trade, open a holdout, or buy a funding evaluation.

For **newly preregistered** ES/NQ (and relevant MES) hypothesis families, all of the following are required:

1. **Sample size:** **N > 150** eligible independent events (**151 minimum**). Disclose the event clustering/dependence and counts by year. Below 151 = insufficient evidence for this screen; no passing status.
2. **Predicted direction and economics:** the signed effect must match the *preregistered* direction, and the **mean net economic effect after the frozen fee/slippage assumptions must be > 0**. A hypothesis only about volatility magnitude must use its own preregistered endpoint, and is not automatically a directional trading signal.
3. **Uncertainty:** the **two-sided 90% confidence interval** of the signed net effect must lie **entirely on the expected side of zero**. Use day/week-cluster or blocked resampling when event outcomes are dependent; disclose the method.
4. **Multiple testing:** **Benjamini–Hochberg-adjusted q <= 0.10**, computed over **every preregistered primary member** of the corresponding family. Do not omit unsuccessful variants; q = 0.10 is a *screening* threshold, not confirmatory significance.
5. **Temporal consistency:** **at least 3 of 5 development years** (2020–2024) must show the preregistered effect sign. Show all five annual outcomes and their signal counts. A single unusually profitable year cannot be used to erase a materially negative full-sample result.
6. **Research integrity:** **no post-hoc subgroup, hour, year, horizon, threshold, or parameter selection to rescue a failure**. All new variants count as new tests and must be registered before outcomes.

**Passing status: `PROMISING_EXPLORATORY` only** — a candidate for *independent validation*, **not** `CONFIRMED`, `PASS_OOS`, or a deployable strategy. Failed/missing metrics require `NOT_SUPPORTED_EXPLORATORY` or `INSUFFICIENT_EVIDENCE`, not a pass.

### Confirmatory boundary (unchanged)

- The previously frozen **N >= 300 / two-sided 95% CI / BH q <= 0.05 / 4 of 5 years** gates remain part of any experiment whose original preregistration already requires them. **This amendment does not retroactively change historical verdicts.**
- New independent confirmation must satisfy the project's *stricter preregistered confirmatory controls*, including whole-family **Holm correction with non-recyclable alpha allocation** (see `research/RESEARCH_CONTROLS_POLICY.md`), and chronological OOS validation **after the hypothesis is frozen**.
- A development result already observed under old rules may be described under the new exploratory lens, **but must not be reclassified as a new independent discovery or treated as a confirmed pass**. No reusing 2025/2026 to re-optimize a candidate.
- This Gate 1 concerns **hypotheses**. Gate 3/4 metrics such as strategy Profit Factor, stop/TP, maximum drawdown, market execution, monthly trade frequency and Monte Carlo remain separate.

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
