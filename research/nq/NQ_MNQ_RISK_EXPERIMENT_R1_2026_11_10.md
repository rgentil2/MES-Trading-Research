# NQ vs MNQ — experimental risk-sizing R1 (2026-11-10)

**Research only. This is NOT a PF1 amendment, NOT a historical backtest and NOT trading authorization.**

## Why this exists
- PF1 v1.0.0 is frozen for **1 NQ**, 2020–2022 IS, 2023–Oct 2026 OOS sealed.
- PF1 E4 has a diagnostic central replay; E5 native compilation/backtest still needs user-side verification in NinjaTrader 8 Strategy Analyzer.
- Legacy `NQNativeATRExitMathV5` caps ATR stops at **55 ticks = 13.75 NQ points**, independently of the $200 NQ risk cap. Changing only the contract multiplier would not rescue ATR stops that V5 already rejects.
- This experiment evaluates NQ baseline versus **1–5 MNQ** with unchanged original stop distances and a fixed $200 per-entry planned-risk budget. It is isolated from PF1 and historical V19–V25 goals.

## Explicit cost hypotheses (not fill guarantees)
| Assumption | NQ | MNQ |
|---|---:|---:|
| $ per tick per contract | 5.00 | 0.50 |
| Round-trip commission / contract | 4.68 | 1.90 |
| Adverse slippage | 2 ticks entry + 2 exit | 2 ticks entry + 2 exit |
| Assumed round-trip cost / contract | 24.68 | 3.90 |
| Maximum contracts | 1 | 5 |
| Risk limit per entry | 200.00 | 200.00 |

Per-contract planned risk = stop ticks × tick dollar value + assumed round-trip cost. The maximum permitted *integer* size is selected (up to 5 MNQ); if even 1 MNQ cannot fit, the entry is rejected. Stops are never compressed, and costs are not applied twice to pre-netted trades. This is an **ex-ante** estimate only; gaps / bad fills can exceed the limit.

The separate experimental ATR conversion accepts **1–400 stop ticks** (100 points) with a multiplier 1.0–3.0; it does not alter V5 or allow those wider stops in PF1. If ATR leads beyond this configured range, the entry is rejected rather than capped to fit. Price calculations remain in original NQ price points.

## Executable source and evidence
- Risk model: `research/nq/ninjatrader/NQMnqRiskSizingExperimentR1.cs`.
- C# self-test and numerical comparison: `tools/nq-mnq-risk-experiment`.
- CI: `.github/workflows/nq-mnq-risk-experiment-r1.yml` on a separate branch.
- With .NET 8: `dotnet run --project tools/nq-mnq-risk-experiment/NQMnqRiskExperimentR1.csproj -- --self-test`.
- `--examples` prints illustrative stops only. **Neither command reads NQ/MNQ price series**.

## Gates before moving beyond R1
1. In the existing NinjaTrader Strategy Analyzer, finish/check **PF1 E5** on 2020–2022 NQ (3 integration portfolios first). Capture E5 reason codes for rejected NQ portfolios. No changes to PF1 thresholds.
2. In a **separate MNQ NinjaScript Research Strategy**, compute the same 100k genomes' entry signals *before* the NQ $200 gate and before the old V5 55-tick ATR cap; apply the R1 sizing model. Do not reuse only NQ-approved trades or only the three E4 portfolios as the search universe.
3. Use **genuine MNQ bars** to validate execution assumptions, and keep a shared chronological account with maximum one position at a time, at most 5 MNQ, and same preventative account protections as the NQ comparator.
4. Compare NQ versus MNQ using exactly the same IS sample and report candidates examined, risk rejects, portfolios proposed, executed trades, net PF, 36 monthly counts, daily/closed/M1 adverse DD, cost stress and contribution. Record missing input rather than marking a gate PASS.
5. Monte Carlo and native fill reconciliation on the surviving frozen candidates, **then** untouched OOS. Neither MNQ OOS nor new selection criteria should be examined or tuned during this research. A new formal contract requires separate user approval.

## Current limitation
R1 only proves mathematical sizing and tests invalid inputs/boundaries. It is **not yet connected to NinjaTrader Strategy Analyzer** or the user-side PF1 E4+E5 script (which was delivered in chat rather than committed as source). Thus no real-market P&L, candidate recovery rate, walk-forward, Monte Carlo or MNQ profitability claims are authorized. Do not run order submissions with this code.
