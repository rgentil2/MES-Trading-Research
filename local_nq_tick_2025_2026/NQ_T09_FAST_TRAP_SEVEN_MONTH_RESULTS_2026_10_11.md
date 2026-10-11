# NQ T09 fast-trap: seven DEV months and NQ-only shared-risk portfolio (2026-10-11)

**GitHub Actions:** [run 38176029358](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38176029358), 7/7 month jobs and synthetic causal/parity tests **SUCCESS**, final aggregator SUCCESS. Preregistration committed **before** execution: `NQ_T09_FAST_TRAP_SECOND_STRATEGY_PREREG_2026_10_11.md`.

**Scope:** NQ Last **2025-10-15..2026-04-30**, 135 eligible sessions, 140 source days, seven development months. Last-only simulated fills are not real executable trades. May–Jun 2026 outcomes and Jul–Sep 2026 pseudo-forward **unopened**; the original 2025/2026 minute-program holdouts are also untouched. 1 NQ, at most two operations/day and only one open position; frozen T04 stop 16–48 ticks, TP2R, 300s max, USD5 RT + one adverse tick/side base or USD7.50 + two ticks/side stress. No broker/firm fee validation.

## Result: incremental PORTFOLIO hypothesis FAILED

These are **five alternative portfolios**; their P&Ls MUST NOT be added together.

| Alternative | Net BASE USD | Net STRESS USD | Research outcome |
|---|---:|---:|---|
| Original accelerated T01 breakout continuation | **−2,345** | −3,677.50 | Not supported under T04 execution |
| T09 raw immediate reversal of T01 | **−2,385** | −4,197.50 | Simple inversion does not solve weakness |
| T09 **rapid failure confirmed inside opening range within 60 sec** | **+160** | **−2,087.50** | No cost-robust edge; retain in library |
| **T05-377** unchanged baseline | **+6,220** | **+5,102.50** | Existing exploratory risk-screen candidate only |
| **T05 + T09, single-capacity router** | **+3,520** | **+630** | **FAIL** incremental contribution and stress PF gate |

**Primary pre-registered comparison:** shared-capacity router minus T05-377 alone = **−USD2,700 BASE** on 135 eligible sessions (**−USD20.00 per eligible session**). Under stress, reduction is **−USD4,472.50**. The predeclared hypothesis of positive marginal portfolio value **failed**.

**Portfolio attribution by actually simulated executed trade, not simply signal:**
- T05-377 in shared router: **86 trades / +USD2,610 BASE**.
- T09 fast-trap in shared router: **84 trades / +USD910 BASE**.
- Combined **170 trades / +USD3,520 BASE**, reconciled exactly to original T04 simulator.
- Compared with T05-alone **115 trades / +USD6,220 BASE**, 29 fewer T05 trades were executed as a result of shared capacity/overlap on this historical simulation. Activity increased but **capital efficiency fell**. No extra leverage was granted to the router.

**Other preregistered preliminary gates:** distinct T09 executions PASS; >=5 trades in each month of shared portfolio PASS; positive stress net PASS; all T04 simulator attribution/parity PASS; **incremental net FAIL and PF stress >=1.25 FAIL**. No continuous joint floating-DD was calculated, so portfolio cannot be called funded-eligible regardless of positives.

## All months preserved — net simulated BASE USD

| Month | T05-377 alone | T09 confirmed alone | T05+T09 shared |
|---|---:|---:|---:|
| 2025-10 | +495 | **−2,845** | **−2,135** |
| 2025-11 | +830 | +110 | +980 |
| 2025-12 | +1,655 | +930 | +1,535 |
| 2026-01 | +1,710 | **−1,195** | **−1,080** |
| 2026-02 | −725 | +230 | +25 |
| 2026-03 | +1,520 | +1,380 | +1,050 |
| 2026-04 | +735 | +1,550 | +3,145 |
| **Total** | **+6,220** | **+160** | **+3,520** |

Initial accelerated-breakout candidate count = **198** (original T01); quick-failure confirmations by month 15,11,19,14,17,19,31 = **126** signals (not 126 filled orders). NQ combo has 170 *executed trades* attributable to 86 T05 and 84 T09; this is not the sum of standalone fills since capacity and order priority changed.

**Why the weak strategy isn't rescued by filtering on favorable months:** Oct-25 and Jan-26 were particularly adverse while Mar-Apr26 looked strong. It would be selection on already-read development returns to exclude the two losing months, label a regime after seeing them, or switch 60s to a different confirmation period to maximize profits. Any new regime must be causal, preregistered and assessed with appropriate multiplicity/independent validation.

## Deduction for future NQ portfolio

1. **T05-377 remains the benchmark**, not a production approval. Its high-level simulated drawdown under earlier T08 stress was USD1,825 as Last envelope and therefore close to historical 50K reference, with actual broker quote execution/fees and regulations still unverified.
2. T01 continuation, raw countertrend T01, and T09 rapid range-reentry have not produced a standalone robust second strategy. **Signal-source diversification is not profit diversification**; combined portfolio performed worse even though it executed more trades.
3. Keep T09 as `NOT_SUPPORTED_EXPLORATORY`. Preserve its mechanism (fast breakout then return inside opening range), monthly regime sensitivity and original unprofitable variants in the hypothesis library, but **do not deploy** T09 or keep testing arbitrary faster/slower confirmation intervals on the same 7 months.
4. Next NQ-only work: (a) independent Minute Last vs Tick Last exact-contract pilot held privately; (b) quote-timestamp **as-of** BBO execution-quality bounds for frozen T05 entries and stops on DEV Last/Bid/Ask; (c) a new causal *different* signal mechanism if justified by those findings, not a post-hoc filter to T09. Any NQ-only combined portfolio must share an execution router and drawdown.
5. The study still lacks a credible years-long track record for NQ tick strategies, actual fills, robust independent OOS, annual benchmark VOO/QQQM full comparables and funded account simulation. Do not invent CAGR or payout expectations from this development P&L.

**Formal decision:** `T09_NQ_PORTFOLIO_FAIL_INCREMENTAL`; maintain `T05_377_EXPLORATORY_RISK_CANDIDATE`; 2026 May–Sep return data remain closed. No MES/ES joint portfolio work until user reauthorizes its resumption.
