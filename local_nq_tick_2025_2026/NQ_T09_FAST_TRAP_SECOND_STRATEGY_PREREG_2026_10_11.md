# NQ T09 — Second distinct short-horizon strategy: fast-breakout failure (preregistered 2026-10-11)

**Status BEFORE first T09 outcome:** `PREREGISTERED_EXPLORATORY`; not OOS, not for live/funded deployment. T09 is a separate hypothesis family from T05/T08, designed to produce a second NQ strategy with a **different trigger** for a future NQ-only portfolio. Research in MES/ES is **paused** until further user instruction.

## Deductive origin (already observed)

- T01 accelerated opening-range breakout (5-second Last bars) led to **−7.672 NQ price ticks gross signed +5 min** across 198 eligible signal opportunities on 135 eligible days Oct-25–Apr-26; only 2/7 months had positive gross signed +5m. Mechanism may be fast impulse/exhaustion rather than follow-through. It is a post-selection observation, **NOT an unbiased discovery**.
- T02 failed-breakout reversion **with slowdown in Last print rate**: +10.634 price ticks gross +5m in directional study, then 190 simulated trades / USD +8420 under T04 assumed base friction. T05 filter 377 produced 115 trades / USD +6220 base, USD +5102.50 stress and reference-risk screen only. T05 and its 233+377 subfilter are not two independent strategies.
- A separate, **causally distinguishable** hypothesis is a high-activity breakout that comes **back inside the opening range promptly**; confirmation need not rely on the T02 rate-slowdown trigger. T09 should complement the *source of opportunities*, not merely screen existing T02 signals.
- Existing independent BBO audits found substantial timestamp-order uncertainty; T09 uses **only completed Last bars** for decisions and existing Last adverse-fill simulation for outcomes. It does not infer aggressive delta/quotes/fills.

## One new mechanism and fixed controls

**Opening range** remains 09:30–09:35 ET, 5s completed Last bars; original T01 acceleration and continuation candidate definitions, 5-minute per-family cooldown, 09:40–11:10 ET for *initial breakout*, exactly as frozen in `nq_tick_short_horizon.py`. No new volume thresholds.

**Strategy T09_FAST_TRAP_60S (primary novel candidate):**
1. Observe a *completed* T01 accelerated breakout signal at 5s bar index i. Its direction is `break_side`.
2. Inspect only the **next 12 completed 5s bars** (60 seconds maximum) in chronological order; reject if a missing/incomplete bar prevents a continuous path. For `break_side=+1`, first subsequent bar close <= opening-range HIGH − **2 price ticks** confirms rapid failed upside breakout and opens a SHORT hypothesis; for `break_side=−1`, first close >= opening-range LOW + **2 price ticks** confirms rapid failed downside breakout and opens LONG hypothesis. Reuse the same 2-tick interior reentry cushion as original T02, not an optimized new threshold.
3. The signal timestamp is the END of the **confirmation bar**, never the earlier breakout time. If no confirmation occurs by 60s, there is **no trade**. Only accept confirmation before 11:10 ET.
4. No use of *future* data at signal time, no incomplete tick-count bars, no T02 slowdown requirement. Same nominal 5s causal timing and original T04 risk and stop/TP.

**Fixed family of alternatives (all considered; never sum their P&Ls):**
- `T01_CONT`: original T01 fast breakout continuation, exact 5s signal and T04 execution; disconfirm breakout sign.
- `T09_RAW_FADE`: *negate* the same T01 signal immediately at the original signal close, without waiting for reentry. It tests whether simple inversion alone accounts for any T09 edge.
- `T09_FAST_TRAP_60S`: reentry-confirmed fading as defined above.
- `T05_377`: the unchanged T02 parent signal + 377 Last-print event-bar filter (already inspected); benchmarking anchor.
- `T09_NQ_COMBINED_ROUTER`: **single account on NQ**, union of eligible T05-377 and T09_FAST_TRAP_60S signals; if they occur in the same 5s decision timestamp (even opposite), T05-377 has fixed precedence; only one active NQ position, max 2 trades/day **across both strategies**; ignore overlapping/blocked signals. T05 signals are never resurrected after filtering, no hindsight picking based on outcome. Router may act on signals of the same day, but the risk algorithm enforces a single capacity pool.

The combined router uses original T04 `simulate_portfolio` sequential fill engine; no extra leverage, size increase, or change to stop mechanics. **Attribution** must be reconstructed by replay and must exactly equal its T04 aggregate net, counts, ambiguous/aborted signals.

## Execution and costs (frozen before T09 outcome)

- Only NQ Last DEV `2025-10-15..2026-04-30`, 140 source days / 135 eligible in previous tests; no May–Jun P&L, Jul–Sep sealed, H01–H78 original holds unchanged. GitHub private Dev archive SHA256 checked before extracting.
- NQ **one contract**; stop = ceil(25% of 09:30–09:35 opening range) bounded **16–48 price ticks**, target **2R**, timed exit **300s**, cutoff **11:30 ET**; 2 trades/day and no new entries when closed day P&L <=−$600, no signal overlap; same `simulate_single_trade` stop-first/ambiguous timestamps. None are optimized using T09 returns.
- Costs base $5 round-trip commission + adverse entry AND exit one price tick each; stress $7.50 RT + two adverse ticks each side. Fees/unfillable prices are **hypothetical**, not company-verified.
- Report entire seven-month family, including months with loss/0 trades, T09-only contribution, overlap and collisions with T05, per-trade expectation/PF, activity/month, session activity, max closed-day DD, approximated Last DD from month summaries, **not** certified continuous joint floating/trailing DD. If promising, require a T08-like stitched-equity audit for the *combined portfolio* before any funded claims.
- Source 08:00 ET event-time session reset may differ from NinjaTrader all-session chart.

## Primary prediction and falsification

**Primary incremental endpoint:** net USD per eligible day of `T09_NQ_COMBINED_ROUTER` **minus** `T05_377`, **same seven-month days and same 1-NQ max risk**, baseline. This tests whether a second signal adds usable capital-level P&L, not whether separately summing two profitable strategies looks attractive. **Prediction:** positive. A secondary requirement for potential advancement is net stress >0, PF stress >=1.25 and *no increase in Last DD that breaches the prior indicative $2,000 risk reference*, at least 5 trades in each calendar month and identifiable nonduplicate T09 executed trades.

**Fail** incremental promotion if endpoint <=0, T09 adds zero trade executions, net stress <=0, PF stress below gate, DD / frequency / risk concentration deteriorates, or the portfolio's added profitability relies on one aberrant month. A result above zero is exploration only; positive tests do not prove a new independent edge. No unreported filtering of losing months, new 20s/45s windows, new reentry cushions, or switched priority after seeing results: any such changes require a *different* preregistered family with multiplicity controls.

**Comparators/ablations:** original T01 continuation; opposite-direction T01 raw fade; confirmed fade; T05 377; combined router, with calendar and cost parity. Record number of T09 first-break opportunities, confirmations, duplicates and accepted contributions, skip reasons; preserve every negative result.

## Holdouts and research governance

This is a **new NQ tick pilot T09**, not a confirmation of old H01–H78 NQ minute research. The old 2020–24 + original sealed 2025/2026 studies remain distinct. The NQ tick study has Oct25–Apr26 DEV, May–Jun26 internal validation **unopened for outcomes**, Jul–Sep26 historical pseudo-forward **fully sealed**. No one should call post-selected DEV p-values independent; statistical testing Holm/BH required for future confirmatory multi-hypothesis families with independent data. 150 hypothesis ceiling is not a test quota.

No repo license-sensitive raw ticks, individual trade paths or private event logs in public workflow artifacts. If T09 is favorable, validate execution against independently sourced 1-min bars and quote sequencing and freeze T09/T05 router before opening fresh test periods.

**Advance only if the distinct mechanism adds **net** portfolio value after fees and shared risk; never promote solely because standalone T09 made a profit.**
