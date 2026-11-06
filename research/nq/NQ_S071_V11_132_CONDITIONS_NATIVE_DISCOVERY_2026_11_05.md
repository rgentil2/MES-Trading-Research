# NQ S0.71 / V11 — native 132-condition discovery (2026-11-05)

## Scope & exact claim

A working **source implementation**, in the V11 research branch, of **132 directional signal conditions**: **12 distinct numerical OHLCV feature families × 11 independently parameterized directional predicates**. This **does not** mean 132 distinct technical indicators. No fitness-guided evolution, arbitrary AST trees, portfolio, Monte Carlo, Windows NT8 compilation, historical backtest, or financial edge has yet been demonstrated.

The original V5 and V10 source files are unchanged; V11 is a separate NinjaTrader 8 strategy/optimizer/fitness series.

## 12 numerical feature families (type = family index * 11 + predicate index)

| Family index | Numerical feature | Notes |
|---:|---|---|
| 0 | (Close − SMA) / simple ATR | directional trend location |
| 1 | (Close − recursive EMA) / simple ATR | trend location |
| 2 | (SMA(n) − EMA(2n)) / simple ATR | fast/slow trend spread |
| 3 | (Close − WMA) / simple ATR | weighted-average location |
| 4 | Wilder RSI centered: (avg gain − avg loss)/(sum) | bounded -1 to 1 |
| 5 | CCI/(150) | price typical versus mean deviation |
| 6 | (Close − Close[n])/(ATR × sqrt(n)) | volatility-normalized ROC |
| 7 | 2 × (Close − n-bar low)/(n-bar high − low) − 1 | stochastic location |
| 8 | (EMA(n) − EMA(2n))/simple ATR | normalized MACD-style spread |
| 9 | (Close − SMA)/(2 × population standard deviation) | Bollinger-style position |
| 10 | (positive money flow − negative)/(sum) | centered MFI |
| 11 | mean close-location value weighted by volume | intrabar volume pressure |

The EMA uses a **fixed finite historical warmup**; ATR uses simple TR averaging. These are documented custom formulas, **not** claimed numerically identical to every native NinjaTrader indicator.

Predicates 0–10: sign, first difference, centerline cross, ±0.15 level, ±0.35 level, ±0.60 level, ±0.15 cross, ±0.35 cross, reversion from ±0.60, second difference, and two-bar persistence.

A condition ID is `family * 11 + predicate` (0 through 131). `NQNativeConditionsV11.Name(id)` gives the precise identity. Bulls and bears never intentionally coexist within one leaf.

## Historic strategy integration

- New `NQNativeSignalLabV11` uses **only completed one-minute bars** from 09:30 to 11:27 **in the NinjaTrader chart/session time** (configure Eastern time) for signal feature calculations.
- Intra-session warmup is `3*period + 22` completed RTH bars; optimizer explores periods 6,9,12,15,18,21,24, and 1–4 Boolean leaves with left-associative AND/OR.
- Every feature is computed from the past + current CLOSED bar, never the next fill bar.
- The V11 historical strategy is **explicitly disabled in realtime**, restricts scores to **2020–2022**, requires NQ M1, and copies the V5 order, exit, approximate risk and cost contract. No funded-account approval is implied.
- Pure `NQNativeBooleanCanonicalV11` and `NQNativeExitCanonicalV11` prevent cross-version aliasing. The **effective** Boolean expression is deduplicated together with real exit/risk settings.
- Native `NQNativeResearchOptimizerV11` uses internal broad seeded domains, not necessarily the parameter grid Min=Max; all 20 genes still must be selected. As with V10, a real NT8 parameter setter may refuse an out-of-GUI-range value — V11 then **fails closed**.
- `NQNativeDiscoveryFitnessV11` reuses V9 economic discovery score — **discovery ranking, not strict G0 approval**.

## Source map

1. `research/nq/ninjatrader/NQNativeConditionsV11.cs` — 132 pure-C# conditions
2. `research/nq/ninjatrader/NQNativeBooleanCanonicalV11.cs` — canonical Boolean structure
3. `research/nq/ninjatrader/NQNativeExitCanonicalV11.cs` — effective exit identity
4. `research/nq/ninjatrader/NQNativeUniqueSearchV11.cs` — seeded search/uniqueness
5. `research/nq/ninjatrader/NQNativeSignalLabV11.cs` — historical-only NQ NT8 strategy
6. `research/nq/ninjatrader/NQNativeResearchOptimizerV11.cs` — native NT8 optimizer
7. `research/nq/ninjatrader/NQNativeDiscoveryFitnessV11.cs` — discovery fitness
8. `research/nq/ninjatrader/tests/NQNativeConditionsV11Test.cs` — mathematical CI
9. `research/nq/ninjatrader/tests/NQNativeResearchOptimizerV11ShimTest.cs` — optimizer C# API-shim CI
10. `.github/workflows/nq-v11-conditions-qa.yml` — CI compile/numerical checks and V5 risk/order diff guard

## Validation plan and limitations

1. CI **must pass** numerical tests of every condition: array bounds, flat markets, warmup, synthetic price/volume scaling, mutual exclusivity, deterministic condition names.
2. CI **must pass** 1000 reproducible unique candidate generations (including all 132 types actually selected as active leaves), 500 with exits unchanged, strict Min=Max fail-closed handling and unchanged order/risk code regions versus V5.
3. **Still pending:** a real Windows NinjaTrader 8 compile/import of all 7 V11 NinjaScript files, with the existing V9 dependencies present.
4. **Still pending:** NT8 historical Strategy Analyzer 20-run smoke on NQ Last M1 2020–2022 with proper continuous-contract history, Eastern chart time, commissions, 2-tick slippage and conservative bar-based fills. Export trades and compare with audit.
5. **Still pending:** performance profiling, controlled OOS 2023–2026, evolutionary fitness-guided GA, robust Monte Carlo/walk-forward and portfolio allocator.

Do NOT equate source-shim green checks with actual NinjaTrader backtest validation. Do NOT use V11 live.
