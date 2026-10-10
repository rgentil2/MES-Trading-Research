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

## 2026-10-10 — Economic return and ETF benchmark gate (strategy/portfolio only)

**User-approved prospective economic objective:** for a fully specified strategy or
portfolio, require **net nominal-equivalent annualized CAGR strictly above the
maximum of (a) 15%, (b) VOO USD dividend-reinvested total-return CAGR and (c)
QQQM USD dividend-reinvested total-return CAGR**, with identical start/end
dates and a documented cost model. A 12% annualized return is a diagnostic
milestone, **not** a pass. ETF returns are measured, not presumed to be 12–15%.

This is an ADDITIVE portfolio evaluation criterion, not a replacement for
hypothesis Gate 1, any pre-existing frozen confirmatory gates, the allocated
whole-family Holm alpha, causality checks or 2025/2026 holdout controls.
Never rewrite a prior family's preregistration or a previously locked gate to
add the economic hurdle retroactively. Existing signals that fail individual
gates remain visible in the exploration library for explicit, non-validated
portfolio research.

**Temporal benchmark compatibility:** use common dates beginning **no earlier
than 2020-10-13**, the QQQM inception date, for a direct historical VOO/QQQM
comparison within 2020–2024 development. For a 2020-complete extension, QQQ
may be used only as a separately labeled `QQQM/QQQ_PROXY`; never imply QQQM
existed before its listing. Use total returns with reinvested dividends, USD,
transparent data provenance and an aligned strategy equity series.

**Funding vs investing:** USD 50k funded account size is *not* personally
invested USD 50k. Report (1) synthetic nominal USD 50k net CAGR (an explicit
normalization, not actual investor ROI), and (2) real out-of-pocket fees,
resets and withdrawals/payouts with their dates and net cash flow, using XIRR
where defined. Account fees and transaction costs cannot be double counted.

**Risk is required:** realistic instrument/funded fees, 1.5x cost stress,
closed-equity and intratrade/floating max drawdown, product-specific trailing
loss rules, contract limits, concentration/correlation, signal overlap and
risk-adjusted comparison with buy-and-hold ETFs. A higher CAGR with a funded
account breach does **not** pass. Label missing benchmark/risk evidence as
`ECONOMIC_DATA_PENDING` or `ECONOMIC_HURDLE_MET_RISK_PENDING`; never invent a
pass or treat exploratory historical results as independent.

**No auto-unsealing:** 2025 and 2026 remain sealed under their established
stage authorization rules. Achievement of this economic target alone grants
no permission to open them, make a trade or purchase a funded account.

**Authoritative addendum:**
`research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md`;
machine-readable specification:
`research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.json`.

## 2026-10-10 — Deductive combined strategies H67–H150

The user has directed the NQ program to produce **combined hypotheses and
executable multi-signal strategies**, not a new queue of unrelated isolated
entry patterns, and to use each accumulated historical finding to infer a
specific, falsifiable next-stage joint mechanism.

For each newly proposed H67+ require before any outcome read:
- references to actual prior source IDs/results, including **negative years,
  low sample sizes, uncertainty, adjusted p values, fees and other limitations**;
- a causal and timestamp-safe reason why two or more different signal/context/
  veto/router components would improve one **joint trading decision**;
- a **frozen primary incremental prediction** against every constituent parent
  and a fixed baseline router, with pre-specified leave-one-component-out
  comparisons, equal periods, positions, transaction costs and risk exposure;
- an unambiguous entry/no-trade/conflict/priority rule, no duplication of
  simultaneous NQ/MNQ/ES/MES beta, stop, TP, time exit, sizing and allowable
  holding-risk caps; AND, OR, state-dependent switching or consensus may be
  used but must be causally defined rather than retroselected;
- a complete family of all tested combinations/variants with full BH and Holm
  accounting. A follow-on variant created after outcomes is another exploratory
  test, never independent confirmation.

An isolated feature may still be assessed **as a diagnostic**. It does not
qualify as a new strategic H67+ unless there is a falsifiable **joint** decision
and measurement of its incremental contribution. A combined strategy cannot
be approved merely because two weak correlated predictors individually
appear profitable; portfolio execution, overlap, no-trade periods, costs and
funded trailing-equity survival must be assessed.

Historical facts motivating the next study include **H09 concentration in
2022**, and 67 aligned sessions shared by **H55/H56**. These have already
been viewed in **reused 2020–2024 development**; conditioning upon them cannot
create an independent p-value or authorize opening 2025/2026. Preserve all
parent signals and failed variants in the exploratory library with their
failures and lineage. The H150 target is a **ceiling**, not grounds to
manufacture 84 tests.

All combined strategies are also subject to the **economic hurdle**
defined above: net nominal equivalent CAGR strictly greater than max(15%,
VOO total-return CAGR, QQQM total-return CAGR), matching window and risk,
plus separate funded account actual fees and payout ROI. Existing Gate 1,
immutable preregistrations, alpha allocations, confirmation and holdout
policies remain unchanged.

**Rule documents:**
`research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.md`,
`research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.json`.
The roadmap `research/nq/NQ_H59_H150_DEDUCTIVE_RESEARCH_PROGRAM.md`
is amended accordingly. **H67–H150 ideas remain unregistered and untested
until each family has its own explicit preregistration and successful
source-only preflight.**
