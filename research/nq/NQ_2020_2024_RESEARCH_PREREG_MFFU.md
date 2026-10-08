# NQ / MNQ — Independent strategy discovery for MFFU 50K

**Registered:** 2026-10-07 (Colombia). **STATUS:** DESIGN ONLY; **NO NQ HISTORICAL DATA FOUND IN REPO**; no statistical edge is claimed.

## Research objective

Build at least one *independently supported* Nasdaq-100 setup suitable for a centrally managed ES/MES+NQ/MNQ strategy portfolio, with plausible trade-frequency and risk/cost profile for MFFU Rapid EOD 50K. **Do not target an arbitrary fixed number of strategies**, and do not infer that Nasdaq has independent risk from S&P: shared equity beta must be controlled.

## Temporal splits (lock now)

- Development **2020-01-01 to 2024-12-31** only.
- Validation **2025** closed until candidate/threshold/horizon freeze.
- Final chronological pseudo-forward **2026** closed until all signal/stop/exit/portfolio rules freeze.
- RTH entry events **09:30–11:30 New York**. Prior day/overnight market context may be used causally.
- **Data not yet available**, so no backtest, Monte Carlo or directional inference is authorized.

## Data ingestion gate

- First acquire **NQ individual quarterly Minute Last** 2020–2024 (MAR/JUN/SEP/DEC), as UTC EOB minute exports and checksummed manifest. The same price signals are usable to size MNQ, but executions and costs differ.
- Keep a separate `data_nq_staging/` directory and contract-specific raw files; do not combine with MES/ES or use back-adjusted rollover by default.
- Verify rows by contract, 0.25-point price grid, positive volume, expected RTH timestamps, duplicate timestamps, partial sessions, rollover boundaries, UTC→ET DST transitions, and equality to NinjaTrader sample.
- Tick Last/Bid/Ask is a **second-stage** request after initial hypotheses warrant it, not a prerequisite for minute-level structural ideas; use tick source for stop order/queue quality later.
- Do not mass-download full 2025/2026 and then accidentally load them into analysis. Holdout raw storage is permissible; outcome inspection is not.

## Initial separate hypotheses (NO thresholds selected from outcomes)

**NQ-H01: Opening-range breakout acceptance**. A breakout closing outside the 15-minute opening range with above-past-day-relative volume and continued price acceptance could predict +15/+30-minute continuation.

**NQ-H02: Failed opening-range break / rejection**. A 15-minute range breach followed by causal close back inside during the first 90 minutes could predict reversion toward VWAP or opening-range midpoint within +15/+30 minutes.

**NQ-H03: VWAP mean reversion under low morning directional efficiency**. Large distance from causal session VWAP, with past-only volatility normalization and low directional efficiency, could predict +15/+30 minute reversion. Do not construct today's full-day VWAP.

**NQ-H04: Pre-market compression to RTH volatility expansion**. Previous overnight realized range and first 15-minute compression may predict absolute +30-minute move *magnitude*. This is **not** a directional trading edge until a separately preregistered directional trigger is established.

These are **hypotheses to test**, not proposed production orders. Initial family length 4 for multiplicity control. Set economically meaningful effect sizes and precise feature quantiles on development data, using past-only measurements and pre-specified within-development walk-forward; record adjustments to the search registry.

## Candidate gates

1. Complete minute-level source/QC first; report signals and testing universe per year, with no post-hoc year selector.
2. Primary horizon +30 min, +15 min secondary, no use of post-entry information in features.
3. N>=300 independent events where feasible, BH-adjusted q<=0.05 for four hypotheses, years in agreement >=4/5, robustness to costs, and stability across at least several forward folds. An effect-only candidate **does not automatically become a strategy**.
4. Build bracket with known stop/TP/time exit; include MFFU RT costs: NQ **$4.68**, MNQ **$1.90** (verify at execution), conservative slippage, and tick-accurate execution before live eligibility.
5. Count *incremental* MFFU 7-day-gap coverage only after synchronizing with S&P strategy signals and excluding prohibited hedges.
6. Test portfolio-level correlated losses, overlapping stop risk, EOD trailing $2,000 threshold including open equity, contract unit caps (3 minis/30 micros), consistency target and news restrictions.
7. **Freeze** strategy and account router versions before opening 2025/2026; 2025 strategy validation only after candidate lock, 2026 reserved for final pseudo-forward evaluation after all rules frozen.

## Data gate priority

Our already completed ES PDC transport diagnostic on ES 2020–2024 is an **S&P strategy and sizing test**, not an independent source of order flow. Prioritize adding NQ 1-minute history and complementary hypothesis testing over re-optimizing the frozen PDC gap/stop parameters to fit MFFU evaluations.

See `research/MFFU_MULTI_INSTRUMENT_PORTFOLIO_PLAN.md` and `research/es/ES_HOLDOUT_POLICY.md` for correlated-risk and general holdout standards.
