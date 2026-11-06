# NQ S0.73 — V13 robustness and 3–5 strategy portfolio (2026-11-05)

## Single final NinjaTrader validation requirement

The user elected to defer **all direct NinjaTrader 8 testing until the entire generator, risk evaluator and portfolio are integrated**. Do not request intermediate NT8 screenshots, F5 tests or exports.

## Pure C# research modules

### NQNativeRobustnessV13.cs

Inputs: **closed** NQ trade list `NQG0RiskTradeV7`, each with entry/exit, net USD, MAE, MFE from the **2020–22 development window**, plus reproducible `NQRobustnessConfigV13`.

1. Reuse the unchanged **V7/V6** economics (minimum 150 trades, 5 per calendar month for all 36 development months, net PF >= 1.25, net profit >0, provisional $2k closed DD, provisional $2k bar-extrema stress DD).
2. Apply additional **1.5× all-in cost** stress to the *already net* trade history: `netStress = netOriginal − numberOfTrades × (multiplier−1) × baselineAllInCostPerTrade`. Default $24.68 approximates $4.68 RT commission plus 4 slippage ticks at $5 each. This is conservative in some fill styles and may not match NT8 transaction costs.
3. Perform **circular moving-block bootstrap WITH replacement** over the **cost-stressed** closed trade outcomes. Defaults: 2,000 paths, 8-trade contiguous blocks, fixed seed 20261105. Report **95th percentile closed-trade max DD**, **5th percentile total net**, proportion of negative bootstrap paths.
4. `ProvisionalRobustPass` requires original V7 pass, positive cost-stressed net and bootstrap p95 DD <= $2,000.

NOT certified MFFU intrabar/trailing rules; not walk-forward, not evidence of out-of-sample profitability; the resampling cannot introduce unseen market shocks.

### NQNativePortfolioV13.cs

- Candidate set comprises **individually provisional-robust V13 candidates** only; no silent inclusion of poor, partially tested or duplicate IDs.
- Select **3–5** candidates by risk-adjusted cost-stressed net and low **monthly 2020–22 realized PnL correlation**. Default maximum **positive pairwise monthly correlation = 0.45**; if monthly returns are perfectly flat, undefined correlation fails closed as 1.0.
- Perform combined one-contract-per-component **closed equity** DD estimate; maximum **$2,000** provisional threshold. Validate maximum aggregate **observed trade-MAE overlap proxy <= $1,000**, not tick-chronological simultaneous stop risk.
- Reject if any candidate contributes >**40%** of positive combined historical PnL. Equal symbolic allocation is NOT assumed; no fractional futures contracts are invented.
- Strictly excludes all trade entries in years 2023+ from research selection.

These constraints are preliminary; portfolio risk eventually needs per-minute synchronized bar-close open-equity simulation, actual stop exposure, correlation regime checks and venue-specific limits.

## Tested only with synthetic data

C# CI compiles production modules, uses synthetic 36-month trade sequences and tests valid/invalid economics, 1.5× cost formula, repeated-seed percentiles, OOS year rejection, duplicate/identical strategies, monthly dependence, PnL concentration, closed DD and simultaneous observed MAE proxy. **No empirical profits or 2020–22 real NQ trade histories currently available in GitHub.**

## Remaining before final single NinjaTrader run

1. Runtime-safe NT8 custom Optimizer score readback / V12 feedback integration (documented NT8 `RunIteration()` returns `void`; cannot pretend its return value is a fitness).
2. A performance-optimized cached/vectorized historical evaluator for intended 100k candidates × ~1m M1 bars.
3. Walk-forward/OOS 2023–26 held-out evaluation and overfit controls; leakage tests.
4. Truly chronological floating/trailing open-equity risk for overlapping trades and actual portfolio exits/stop exposure.
5. One final Windows NT8 compile, NQ M1 replay 2020–22, held-out evaluation, and per-trade parity verification.
6. No live or funded-account trading unless each acceptance gate passes; passing CI shims is not sufficient.
