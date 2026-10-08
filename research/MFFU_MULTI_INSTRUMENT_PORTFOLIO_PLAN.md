# MFFU — Multi-Instrument, Multi-Strategy Portfolio Plan

**Date:** 2026-10-07  
**Status:** RESEARCH PLAN / NOT DEPLOYABLE / NOT A STRATEGY FREEZE  
**Target program:** MyFundedFutures Rapid EOD 50K (also run Builder 50K as comparator).  
**Holdouts:** MES 2026 SEALED; ES 2025 validation and 2026 final SEALED; NQ holdouts to be defined before outcome inspection.

## Intent

The desired end state is **one centrally controlled, automated funded-account portfolio** with independently validated S&P 500 and Nasdaq strategy families. Signals can be generated simultaneously by several strategies, but trades are authorized by **one account-level risk/position router** rather than by independent robots sending orders directly.

- S&P 500 research/execution universe: ES and MES, selecting contract size by ex-ante dollar stop risk, costs and limits.
- Nasdaq research/execution universe: NQ and MNQ with independently preregistered hypotheses and evidence; **no NQ candidates have been approved**.
- Existing MES research candidates: PDC v1.0 frozen; POC and R072 remain research/watchlist, NOT funding-approved.
- No inference that MES thresholds or fills transfer to ES, or that ES/MES performance transfers to Nasdaq.
- MES and ES are the same underlying exposure at different multipliers; likewise MNQ/NQ. **1 ES = 10 MES, 1 NQ = 10 MNQ**, with no alpha gained merely by changing contract size.
- S&P and Nasdaq are highly correlated equity-index risks in many regimes; portfolio diversification must be empirically demonstrated, not assumed.

## MyFundedFutures external rules to encode (verify immediately before purchase)

Rapid EOD 50K:
- Evaluation goal USD 3,000; max loss limit USD 2,000 EOD trailing; 30% eval consistency; at least four trading days.
- Sim-funded EOD trailing max loss USD 2,000, locking at +USD 100 above starting balance, no extra hard daily-loss limit.
- **Floating equity matters for breach monitoring intraday** even though trailing floor steps at EOD.
- Max **3 minis or 30 micros equivalent in aggregate** across instruments, not per strategy or per ticker. Aggregate 1 mini = 10 micro contract units.
- Inactivity rule: seven consecutive calendar days without trades can close a newer account.
- Rapid Sim Funded prohibits Tier 1 news positioning. Official policy states no open positions or active orders from **2 minutes before through 2 minutes after** Tier 1 releases. Apply the stricter of the frozen research news rule and then-current firm restriction; verify collisions and flattening before live use.
- Automated trader-owned systems can be used under fair-play rules; no HFT, simulated-fill exploitation or deceptive order handling.
- No opposite simultaneous positions on the same underlying even across ES/MES or NQ/MNQ. Avoid offsetting cross-index positions used purely to circumvent hedge rules.
- Cross-instrument contract limit cannot be bypassed via simultaneously opening minis and micros.

Official rule references:
- https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look
- https://help.myfundedfutures.com/en/articles/10244682-cross-instrument-policy
- https://help.myfundedfutures.com/en/articles/12011241-hedging-what-you-should-know
- https://help.myfundedfutures.com/en/articles/8230009-news-trading-policy
- https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices
- https://help.myfundedfutures.com/en/articles/16596524-inactivity-rule-one-time-payment-model
- https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list

## Central order/risk engine — required design

1. Each research strategy publishes an immutable **candidate signal** with source version, underlying, side, entry time, risk stop, planned exit, and reason. Signals NEVER place orders directly.
2. Net exposures by underlying (S&P, Nasdaq), across large and micro contracts and across all strategy instances, before accepting any signal.
3. Reject simultaneous opposite sides on a single underlying; resolve opposing or same-side simultaneous signals using a **predefined** deterministic priority/allocation policy rather than retrospective best-trade picking.
4. Select mini or micro size from the stop distance (USD), remaining allowed account risk, commission/slippage, total equivalent contract units, and current correlated-index exposure.
5. Count *all* pending and filled orders, broker positions, protective stops, partial fills and cancellations. Enforce one protective stop per net position and conservative fail-closed behavior on mismatch or disconnect.
6. Apply global thresholds at account level (equity including unrealized P&L; firm EOD trailing floor; own tighter discretionary kill-switch, calibrated only in permitted development).
7. News/calendar/rollover/session restrictions are centralized; forced flatten triggers must close/cancel open orders and be verified via execution and order callbacks.
8. Treat S&P + Nasdaq as correlated: check joint worst-case loss, synchronized MAE, exposure at the same time, and a paired-stress crash scenario; nominal maximum contract count does **not** equal safe risk.
9. Produce an auditable event log: candidate, accept/reject reason, working order, execution, stop, position, current equity and relevant guardrail at each decision.

## Validation program and hard order of operations

### Phase A — portfolio reconstruction, 2020–2025 MES only
- Import verified NinjaTrader 2-tick + commission **trade-by-trade exports** for PDC (106 trades), POC (108), R072 autonomous (149); store original hashes and instrument/timezone settings.
- The repo currently stores the POC/R072 financial **reports**, not all their canonical execution CSV rows: **do not claim a synchronized 363-trade execution simulation until exact records are in the same runtime**. Historical aggregate sum (USD 1,905.06) is NOT a time-synchronized portfolio return or margin/equity calculation.
- Deterministically merge events by entry, exit, stop and news boundary; establish simultaneous exposure and precedence, no opposite same-underlying positions.
- Evaluate 7-calendar-day inactivity; EOD balance/trailing MLL and mark-to-market floating equity breach; payout/consistency/day rules; run both Rapid EOD and Builder for comparison.
- Run clear scenarios: one MES per signal reference, instrument-family exclusion, risk-capped sizing, global synchronized exposure. Candidate exclusion is a *new portfolio policy*, not a retroactive signal improvement.
- Stop-order correctness: R072 149 protective order groups audited, but fills under stop trigger/gaps not observed; four additional R072 session-quality dates unresolved.
- Explicitly mark **unavailable** any historical floating drawdown where intrabar/tick-path data are missing; do not substitute closed-trade drawdown.

### Phase B — Monte Carlo and risk model, before opening 2026
- Include block-bootstrap of chronologically ordered **portfolio trading days/weeks**, preserving correlated losses and inactivity gaps; avoid naive independent resampling of strategies.
- At least 10,000 paths and sensitivity to slippage, missed fills, stop gaps, 1.5x costs, correlated double losses, and 1–3 skipped trades.
- Quantify probability of touching USD -2,000 EOD/floating threshold, completion time to USD +3,000, percentage of inactivity violations, and remaining P&L buffer for payouts.
- Predeclare acceptable gates based on risk tolerance and feasible sample size, not by tuning to maximize 2020–2025.

### Phase C — independent ES + Nasdaq investigation
- ES 2020–2024 development source prepared in project; do not open ES 2025/2026 outcomes until protocol gates. MES hypotheses inspire but never automatically transfer.
- Nasdaq (NQ/MNQ) requires its own data QC and hypothesis program; prioritize mechanisms complementary to S&P signals.
- Seek independent economic signals, not an arbitrary numerical target of strategies. ES/MES and NQ/MNQ are execution sizes, not four independent alphas.
- Reconstruct a **joint multi-asset** hypothetical account; recompute global risk with synchronized positions, without looking ahead.

### Phase D — freeze + chronological OOS
- Freeze versions of each strategy, router priority/position-sizing, all limits, cost model, holiday/calendar rules, and acceptance criteria, with commit SHA before opening reserved outcomes.
- Run MES/ES/NQ 2026 as applicable *chronological pseudo-forward*, with no parameter revision, choosing PASS / FAIL / INSUFFICIENT DATA.
- Historical 2026 replay is **not** live forward observation; then conduct platform simulation/market-replay and live-sim monitoring of order handling under current market feed before buying MFFU evaluation.
- Purchase only when full *portfolio* is robust, account-policy compliant and economically viable. Buying a larger contract to hit the target is not a substitute for positive expectancy.

## Immediate next tasks

1. Resolve canonical 2-tick row input provenance for POC and R072 from prior uploaded reports or an approved reconstructible output; PDC is available in this conversation. Do **not** request repetitions of data whose results are already documented merely to summarize history.
2. Complete the four extra-session R072 data QC and the stop execution/stop-gap caveat.
3. Build a deterministic multi-asset, multi-strategy, account-level replay engine (no 2026 read) and test conflict resolution, cross-instrument position cap, float DD and news barriers.
4. Complete staged Monte Carlo and write risk gate report.
5. Only if MES portfolio is not eligible, extend with ES/NQ modules after their own validation gates; still test a *joint* portfolio before any funding decision.
