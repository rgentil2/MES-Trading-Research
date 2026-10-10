# MES / ES Research Controls

Active additive control: 2026-10-02. Original experiments, gates and R063 rules are preserved.

## Evidence and temporal roles

MES has already researched 2020-2025. Its current authoritative policy is
2026_HOLDOUT_POLICY.md: R063 is a frozen volatility component, not a directional
strategy, and 2026 is reserved for a complete frozen strategy. R064 is superseded
and must not run. Older status labels and the R063 freeze manifest are historical
records; their old engine-only validation wording does not supersede that policy.

ES is the primary new research program. ES_HOLDOUT_POLICY.md remains authoritative:
2020-2024 development; 2025 candidate validation after freeze; 2026 final strategy
pseudo-forward after full freeze. A MES result does not validate an ES signal.
The two instruments reference the same index and are not independent replications
of one adaptively selected question. Inference must respect shared session dependence.

Original PASS/CANDIDATE labels retain their historical meaning. New discoveries
on reused development data are only PROMISING_EXPLORATORY or NOT_SUPPORTED_EXPLORATORY.
Neither a robust p-value nor a family pass authorizes a trading strategy.

No new position after 11:30 ET. Original R063 parameters and MES RT cost remain
unchanged: $1.88 commission + $2.50 slippage = $4.38 for one MES.
ES costs are not copied from MES or BTC. An ES strategy must freeze its own
commission, slippage and execution prices. Contract point value is MES $5, ES $50.
If ES generates a signal executed on MES, declare both instruments and freeze a
separate transfer/execution validation plan.

## Accumulated search ledger

SEARCH_LEDGER.json records all 73 original experiment CSV rows and the surviving
81 MES hypothesis definitions. These overlap and are not 154 independent trials.
It also retains five ES-B01 planned hypotheses as PRE_REGISTERED_NOT_RUN.
There is no retrospective global p-value or assertion that undocumented variants
have been counted. Family labels from old experiments are descriptive lineage,
not retrospectively preregistered correction families.

Register a whole scientific family before the first outcome run: include all
sides, horizons, thresholds, models, filters and both instruments if they answer
the same selection question. A new block or instrument does not reset the family.
Record originating units, exact operational formulas, endpoint, direction, data
role, research/execution instrument, all member IDs, result paths and every code/
definition dependency. ES-B01 additionally needs the existing data gate and fully
mechanical operational definitions before an outcome runner is eligible. Its five
planned IDs may enroll in a future family; they have not consumed alpha yet.
Existing ES-B01 BH requirements stay in place; the prospective family control is
an additional gate and never relaxes any original requirement.

Freeze the family and its complete code before outcomes:

    python tools/research_governance.py --freeze-family FAMILY_ID
    python tools/research_governance.py --preflight-family FAMILY_ID

Every future outcome runner/workflow must invoke preflight BEFORE loading outcomes.
New hypothesis/strategy documents and experiment implementations must be registered.
Changing members, code, definitions or budget invalidates the preflight. The
cross-commit audit prevents deleting or rewriting frozen history and allocations.
Historical entrypoint fixes require append-only before/after Git blob digests,
reason and retention of original results. Frozen original definitions/results
cannot silently be replaced. Shared library dependencies must be fingerprinted
too; listing only the thin entrypoint is not a complete freeze.

The family JSON contract retains id/index/question/origin_units/data_role/members,
definition_files/result_artifacts/independent_inference_justification. Each member
requires id/preregistration_path/definition/alternative/endpoint plus
research_instrument/analysis_kind/execution_instrument. STRATEGY additionally
requires costs.point_value_usd, commission_round_trip_usd and slippage_round_trip_usd;
cross-instrument execution requires transfer_validation_plan.

## 2026-10-09 — Prospective exploratory screen, separate from confirmation

At user direction, `research/es/ES_STAGE_GATES_EXPLORATORY_AMENDMENT_2026_10_09.md` adds a **new preliminary Gate 1 screening tier** while leaving the hash-protected original `research/es/ES_STAGE_GATES.md` unchanged for future preregistered ES/NQ/MES hypotheses intended to contribute to a multi-strategy portfolio:

- **N > 150** independent eligible events (151 minimum);
- effect sign matches the preregistered prediction and the net effect after explicitly frozen costs is positive;
- a two-sided **90% confidence interval entirely above zero** for an expected positive net directional effect, appropriately adjusted for clustered calendar events;
- preregistered-family **Benjamini–Hochberg q <= 0.10**, **screening only**;
- expected effect sign in **at least 3/5 years (2020–2024)**;
- no retrospective regime/year/threshold/horizon rescue, complete family/search logging.

Passing permits only `PROMISING_EXPLORATORY`: **not** `PASS_OOS`, `CONFIRMED` or a tradable strategy. Original frozen experiment thresholds (including pre-existing N>=300, 95% CI, q<=.05 and 4/5 requirements where preregistered), the **whole-family Holm alpha budget**, preflight and immutable 2025/2026 holdout restrictions are **NOT weakened**. This is an additive *prospective* screen, not a retroactive relabeling of the historical H01-H03 NQ findings or of any prior ES-B01/MES family.

Independent confirmation and strategy approval still require the stricter original statistical governance, sealed 2025 evaluation when authorized, then costed execution/risk, walk-forward and portfolio gates before the final frozen 2026 pseudo-forward. In particular, a 90% CI and q<=.10 **cannot replace** a family's confirmatory Holm criterion. The original NQ preregistration text is retained for provenance.

## Whole-family correction

Apply Holm across every declared member. Missing outcomes block evaluation.
Explicit NOT_ESTIMABLE members receive p=1 and stay in the denominator.
Family k receives alpha_k=0.05/(k*(k+1)); first=.025, second=.0083333333,
and the infinite sum is .05. Failed families consume their allocations; no recycling.
This controls the prospective union of family errors only when the underlying
p-values are valid for the selection/inference process. It cannot repair adaptive
reuse of the already-viewed sample or incomplete human declarations.

    python tools/research_governance.py --check
    python tools/research_governance.py --evaluate-family FAMILY_ID

The development adapter accepts stored 2020-2024 reports only and never opens
independent/holdout outcomes. Once any declared family artifact exists, CI requires
all declared artifacts/member results and automatically applies the full correction.
MES's historical 2020-2025 research role is retained; this conservative adapter
does not authorize additional 2025 reading. Independent evaluation or an expanded
MES diagnostic requires a separately scoped adapter and the existing freeze gates.

## Robustness diagnostics

tools/audit_research_robustness.py supplies reusable MES/ES event diagnostics:
session-cluster t inference, HC3 sensitivity, calendar-HAC20, 10,000 moving calendar
block bootstrap samples, removal of the best one/two whole days, leave-one-day/year
out, yearly attribution and 1.5x cost stress. It also supplies daily regression
OLS/HC3/calendar-HAC20 sensitivity. HC3 by itself does not solve session dependence;
HAC t inference is approximate. Sparse bootstrap results are unavailable rather
than assigned a reassuring interval. All diagnostics retain inactive calendar
days and original event weighting. They do not tune parameters or change gates.

The installed MES run recomputes exact H080/H081 B14 signals on 2020-2024 only,
using frozen definitions and $4.38 cost. This is a subset diagnostic, not a rerun
of the original 2020-2025 primary gate. Only the twenty 2020-2024 contract files
are selected. Dates outside 2020-2024 are excluded before any features/outcomes;
late timestamps in DEC24 exports do not become 2025 outcomes.

ES-B01 has no executed directional outcome table. Its diagnostics are available
for later use after the data gate and operational family freeze. No ES robustness
or profitability claim is made today; Last-only data cannot produce primary BBO
delta. Raw exports remain unchanged and no paid data is purchased by this audit.

## Additional ES implementation correction

Backward quote joins now require explicit contract identifiers and use the contract
as a grouping key. Five-minute flow aggregation retains that key; overlapping
contracts cannot contaminate each other's delta/OHLC. Missing counterpart quotes
remain unclassified. Locked Bid=Ask is unclassified because both aggressor rules
would otherwise match; crossed/nonfinite BBO aborts QC. No stale-quote threshold
or tick-rule fallback is introduced before the existing data-quality gate.
The old implementation version remains identifiable in the ledger/Git history.

## References

- CME contract multipliers: https://www.cmegroup.com/articles/faqs/frequently-asked-questions-micro-e-mini-equity-index-futures.html
- Robust covariance methods: https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html
- Holm correction: https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
