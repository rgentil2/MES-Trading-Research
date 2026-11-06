# NQ S0.72 — V12 fitness-guided evolution and historical M1 research loop
Date: 2026-11-05 (Colombia)

## User constraint: ONE FINAL NinjaTrader validation
**No intermediate NinjaTrader 8 runs are requested.** Continue internal C# CI development through robust evaluation and portfolios, followed by a single final integrated NT8 compile/replay with the complete package. The final validation will still be mandatory before any live use.

## What is actually implemented

1. `NQNativeEvolutionCoreV12.cs`: pure C# 20-gene evolutionary algorithm over V11's 132 directional conditions (12 OHLCV features × 11 predicates). Mutations and tournament-selected parent breeding use **previously evaluated fitness**, not random search dressed as evolution. 20 gene search domains, global canonical dedup, pairwise (condition, period) crossover, 1–4 leaves, AND/OR logic, random immigrants, elites retained without re-evaluation, stagnation restart, reproducible seed and fail-closed non-finite fitness. Exits may be frozen.
2. `NQNativeHistoricalEvaluatorV12.cs`: conservative **offline** M1 bar-level position/fill approximation. Only 2020–22, 09:35–11:27 M1 signals sampled from completed RTH bars, next-bar-open market entries, 11:28 submit / 11:29 expected time exit, NQ tick value $5, estimated $4.68 round-trip fees, 2 adverse ticks on eligible market/stop legs. When stop and TP both touch in one M1 bar, choose the stop first (worst case). Enforces the current provisional V5 daily entry and risk guards. **Not an exact NT8, tick-level, or prop-account trailing-DD simulator.** Native NT8 ATR and Standard fill behavior will differ: offline ATR is arithmetic TR average, not vendor ATR. These differences must be reconciled at final validation.
3. `NQNativeResearchPipelineV12.cs`: actually wires `NQEvolutionEngineV12.Run(genome => NQNativeHistoricalEvaluatorV12.Evaluate(bars, genome.Genes).Score)` to the **original V9 discovery economic score** and V7/V6 diagnostics, NOT to the synthetic oracle. The constructor requires NQ M1 bars supplied locally, 20 baseline genes, config, exit policy and dataset-completeness flag. Production-mode dataset gate demands all 36 months of 2020–22 and prohibits 2023+ leakage.

All 3 production C# modules are pure sources suitable for inclusion in native NT8 projects, but the end-to-end **native NT8 custom-Optimizer fitness feedback bridge is NOT DONE**. NinjaTrader's documented `RunIteration()` returns `void`, so do not invent an undocumented synchronous score readback. The next engineering task is to design and test a safe callback/queue or in-engine scorer that does not block/falsify RunIteration feedback.

## Internal QA evidence

- C# genetic synthetic objective: 14 generations, **1,016 unique evaluations**, first-best 9,488 versus final-best 9,907, 663 crossovers, 710 mutated children, 26 duplicates skipped, 1,016 unique in frozen-exit mode, 5 plateau restart triggers. **These score improvements are synthetic, not trading profits.**
- M1 synthetic price path: 2 limit-target exits, net **$310.64 across two illustrative trades** after conservative fees/entry slip; simultaneous stop+target test selects stop, 11:28 flat submits and fills at 11:29, short-direction symmetry, disallows 2023 and missing end-of-day exits. These figures are **not historical NQ results**.
- Full scored pipeline integration CI: GA receives the *actual V9 score returned on its simulated M1 trade history*; deterministic 20-gene selection and no 2023+ data. This is a synthetic-data **integration test**, not a 2020–22 real backtest.

## Data constraint

We inspected the user's connected GitHub repositories. **The complete 2020–22 NQ M1 data are not present** in either `rgentil2/MES-Trading-Research` or `rgentil2/NQ-Tick-Data` main tree; prior user context says the data reside in local NinjaTrader 8. Without those historical bars we can build and test the engine numerically, but cannot claim empirical historical profitability or full 100k real NQ backtests.

## Remaining research before final NT8 validation

- V12 native scoring synchronization design (no undocumented `RunIteration` assumptions), serial/concurrent correctness.
- Performance: existing pure M1 estimator recomputes feature windows and checks input on each candidate; caching/vectorization + memory budget needed before 100k candidates on 1M bars.
- True 132 **independent** indicators (if still desired): V11 implemented 132 **conditions**, not 132 unique indicator formulas; consider adding distinct families and arbitrary Boolean AST.
- More realistic slippage/commission, tick/path ambiguity stress, trailing account risk and chronological floating equity.
- Walk-forward/OOS 2023–26, bootstrap/Monte Carlo, correlation/dependence and 3–5 strategy portfolio allocation. Never train on final held-out years.
- Single final Windows NinjaTrader 8 compilation/import + NQ M1 Strategy Analyzer backtest + per-trade reconciliation + demo simulation. No real-money trading before final integration.

## Honest status

**V12 is a working fitness-guided genetic engine and a working M1 *estimate* pipeline in pure C#; it is not yet a fully validated, production-ready NinjaTrader StrategyQuant replacement.**
