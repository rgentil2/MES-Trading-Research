# NQ T10 — Pre-registro as-of Bid/Ask quality at frozen T05-377 endpoints (2026-10-11)

**Purpose:** engineering/audit gate for an eventual *NQ-only multi-strategy portfolio*. **Not a new alpha hypothesis** and not a selection of parameter, sides, months, or entry filters. T05-377 is held exactly as previously tested; T09 failed incremental contribution and is not promoted. T10 MUST NOT be used to select profitable time windows or retroactively exclude otherwise losing trades.

## Prior findings, before T10 outcome

1. T05-377 from T04/T05 frozen Last simulator: **115 trades across 135 eligible DEV dates, Oct15 2025–Apr30 2026**; baseline +USD6,220, stress +USD5,102.50. T08 Last-only indicative continuous adverse envelope DD stress USD1,825, near an *unverified* USD2,000 historical funded-account reference.
2. Separate 36-day BBO data QC on NinjaTrader Last/Bid/Ask found a **median 32.13% of Last prints outside the strictly prior BBO**, and unresolved same-timestamp sequencing affects much of this observation. Hence replacing Last synthetic entry/exit directly with historical Bid/Ask and calling it realistic broker performance is unsound.
3. An independent original 1-minute source exists privately; exact independent per-bar cross-source reconciliation has not been run yet. Do not imply minute/tick parity.

## Frozen scope

- Run **all existing DEV sessions**, Oct 2025–Apr 2026 from `nq_tick_short_horizon_month.MONTHS`, not a handpicked profitable subset. Reject non-whitelisted month, date or mixed-contract file *before opening* a source. May–Jun 2026 validation return windows remain unopened; Jul–Sep 2026 sealed; old research 2025/2026 holdouts untouched.
- Download private monthly NQ Last, Bid, Ask release archives, verify each SHA256 before use, compare exact contract ID in filenames and ET session date. Remove raw archives and extracted source at end. Never print/upload intraday quotes, bars or trade timestamps to public outputs.
- Reconstruct same **T02 signals + 377 Last-print fully completed bar prior to signal**; execute T04 exactly in **baseline and stress** cases (1 NQ, max 2/day, stop 16–48 ticks, 2R TP, 300s timeout, original 1/2-tick adverse fills and $5/$7.50 RT commission, same risk/capacity). Confirm daily **trade count / net USD / ambiguity parity** against unmodified `simulate_portfolio`; aggregator must reproduce 115 / $6,220 and 115 / $5,102.50.
- No retuning, stop/TP adjustment or new order router; raw T05 strategy remains an exploratory comparison anchor.
- Extract from original fill model only the hypothetical **entry and exit timestamps, sides, entry and exit model tick prices** for internal cross-source matching. No individual trades/times/prices leave workflow.

## Audited quote matching (endpoint-only, NOT full fill replay)

- From each day's archived **Bid** and **Ask** quote streams (strictly increasing or equal timestamps), compute latest quote `Q(t)` from that side with `quote_timestamp < requested_trade_event_timestamp`. Quote updates with **equal** timestamp are excluded, no lookahead. On repeated timestamps, the **last quote** at that timestamp becomes observable only for *strictly later* trades.
- Quote at entry: long=>Ask, short=>Bid. Opposite side quote at exit: long=>Bid, short=>Ask. For each endpoint, require BOTH sides quoted, `Bid<Ask`, quote ages <= **250ms** individually (the previously documented BBO QC threshold, not selected after trade returns). Classify `MISSING`, `LOCKED_OR_CROSSED`, `STALE_GT_250MS` or `VALID_STRICT_PRIOR_BBO`.
- Count endpoints and pairs per cost scenario; share of executed T05 trades with **both valid**; median, 90th percentile of spread ticks at entry/exit; % where hypothetical synthetic entry/exit price is outside the strictly prior BBO; and distribution of the **paired side-correct quote difference**, reported only as accounting sensitivity on fixed trade timestamps.
- Under hypothetical side-correct price substitution, net change per trade in USD is `(side * (last_exit_model_price - quote_exit_price) + side * (last_entry_model_price - quote_entry_price)) * $5/tick`, where the hypothetical snapshot prices are not actual fills. Check algebra against full old model net and profit for every complete pair. For a long, BBO ask entry and BBO bid exit; for a short, BBO bid entry and BBO ask exit.
- Crucially, these differences **DO NOT rerun the stop, take-profit, daily stop, cooldown or account drawdown**. Thus DO NOT present quote substitution as the strategy's executable new net P&L, a passing broker backtest, or a way to choose the best contracts. Quote values might be stale relative to Last due to source sequencing, cancellation, or latency.
- Report stats even if all trades lack valid quotes. **Failures are evidence**: no deletion of unfavorable rows to improve P&L. Missing/ambiguous Last exits fail closed and remain explicit.

## Primary engineering endpoint and next decision

The primary endpoint is the **fraction of the frozen T05-377 simulated trades for which BOTH entry and exit have VALID strict-prior Bid/Ask (<=250ms and positive spread)**. Secondary are actual quote ages/spreads, distance relative to Last fills, and sensitivity accounting. **No selection based on profitability**.

- `FULL_ENDPOINT_QUOTE_COVERAGE_QC` only if 100% of fixed simulated trades have valid pairs and zero source QC/parity mismatches; even then **NOT executable fill certification**.
- `INCOMPLETE_OR_AMBIGUOUS_QUOTE_COVERAGE` if any missing, stale or locked quote or source issues; preserve counts and stop any claim that T05 was confirmed by BBO. This is a deliberately strict engineering screen; research can continue with non-inferential results.
- **Always** separate: (i) Last simulated monetary outcomes already observed; (ii) matched quote availability/price sensitivity; (iii) actual broker execution unobserved; (iv) independent historical minute parity pending; (v) weekly/monthly stability and holdout pseudo-forward still reserved.
- The only admissible next work is source-quality and mechanism research, not live account purchase. Funded-account current rules must be independently verified.
