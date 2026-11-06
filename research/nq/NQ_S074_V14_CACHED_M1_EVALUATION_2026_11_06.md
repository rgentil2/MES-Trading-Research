# NQ S0.74 — V14 cached M1 research evaluation (6 Nov 2026)

## Goal and strict user constraint

Improve actual research throughput while keeping **trade-by-trade deterministic parity with the existing conservative V12 *offline* estimator**. **No intermediate NinjaTrader tests** are requested; the user has explicitly reserved a **single final complete integration test inside NinjaTrader 8**.

## Implemented

- `research/nq/ninjatrader/NQNativeSignalCacheV14.cs`: creates an immutable, date-validated snapshot of 2020–22 supplied M1 bars. Per (condition 0–131, period 4–30) it lazily constructs one compact **byte per 09:30–11:27 completed RTH bar**. Each signal calculation sees only the prefix already closed within its own research day, with same V11 formulas and warmup. Dedicated bounded LRU cache for these signals.
- If **every recorded session** has all 120 contiguous 09:30–11:29 bars, V14 evaluates only this research window (rather than the full overnight M1 stream). Otherwise it retains the complete source: do not silently drop needed 11:28/11:29 flat-exit bars.
- ATR for all dynamic protective exit modes is computed from the **full, original M1 source**, including overnight bars, in exactly the original V12 summation order. An independent bounded LRU memoizes those ATR arrays by period; if one ATR array exceeds the cap, ATR falls back to per-index calculation.
- `NQNativeHistoricalEvaluatorV12.cs` receives an optional **validated, immutable, cached signal and ATR callback**. The original public method, original order fill logic, slippage, stop-first simultaneous hits, costs, time exits and V9/V7 score formulas are untouched.
- `NQNativeCachedPipelineV14` links the **original V12 genetic engine** to the cached evaluator, providing the same original V9 economic fitness for each genome.
- Production completeness no longer means simply “one bar in each calendar month.” V14 requires **at least 15 fully observed contiguous 09:30–11:29 research sessions in every one of the 36 2020–2022 months**. This is a provisional data-presence heuristic, NOT a full exchange-calendar, continuity, rollover, timezone, contract selection or quote-correction audit.
- Cache budgets limit **cached signal byte arrays** and **cached ATR double arrays**, not the source OHLCV objects, source snapshots, fixed index arrays or managed-runtime overhead. Defaults: configurable signal budget, 64 MiB ATR budget.

## Numerical source tests — **all on synthetic OHLCV, not real historical NQ**

GitHub Actions workflow: `.github/workflows/nq-v14-cache-qa.yml`.

1. Exact comparison of **560,736 signal states** across all 132 condition IDs and periods 6/12/24 against direct-prefix V11 evaluation.
2. Exact trade-by-trade differential validation for **120 unique V11 genomes** with all exits, stop/target collisions, fees, MAE/MFE, signal gates and total V9 score. Source includes 08:00–12:29 pre/post RTH bars; ATR must match full data.
3. End-to-end GA comparison: **same 66 unique candidate genomes, same order, same per-candidate scores and same winner over 3 generations** between uncached V12 pipeline and V14 pipeline.
4. Immutable original snapshot, no OOS 2023+ leakage, strict signal/ATR cache caps and LRU evictions, fallback to full source if 11:29 missing, and minimum 15 complete sessions for 36 months production heuristic.
5. Synthetic scale benchmark: 45 full 24-hour days = **64,800 M1 bars** with 160 unique genomes; V14 filters to **5,400 research bars**. Initial CI run (runner and JIT dependent): original V12 **606 ms**, V14 cold **489 ms**, V14 warm **37 ms**. Warm-cache ratio **16.4x** on this specific synthetic fixture. Do **not** extrapolate the speed ratio to 100,000 strategies on real NQ.

## What is still not done

- We have not run a **real historical NQ 2020–22 backtest**. The complete NQ M1 data are not in the GitHub repositories: they are in the user's local NinjaTrader environment.
- No parity has been established with **NinjaTrader's proprietary Standard fill engine**. This is **strict differential parity with the V12 offline conservative estimator** only.
- V12's custom genetic fitness scoring is valid *offline* but **not wired to the native Strategy Analyzer's custom Optimizer score feedback**. Official NT8 API documents `RunIteration()` as returning void; do not invent supported synchronous callbacks or say native V12 GA works until formally bridged.
- True contract/roll/timezone and holiday-calendar validation; full intratrade floating DD and actual funded trailing loss; dynamic ATR vendor parity; OOS / walk-forward 2023–26; portfolio combinatorial exploration with chronological open risk; data-source manifest.
- The 132 condition codes represent **12 distinct OHLCV feature families × 11 directional conditions**, not 132 independent indicators.
- Native end-to-end final NT8 compile and one integrated historical replay, **after** the entire architecture is ready, remains mandatory before deployment.

## Decision

Use V14 as the faster **offline generation/evaluation backend** for the existing V12 fitness-guided GA. Preserve V11 native strategy and V13 portfolio as separate, unchanged modules. Next engineering milestones are (a) robust NT8 historical data adapter / documented integration for final validation, (b) chronology-aware portfolio risk, and (c) held-out walk-forward/OOS acceptance without leakage. No live trading.
