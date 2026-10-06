# MES Stage 3 — NinjaTrader Robustness Protocol

Status: PRE-REGISTERED BEFORE NINJATRADER PARITY RESULTS.

Do not execute Stage 3 for a strategy until Stage 2 signal parity passes.
2026 remains closed.

## PDC

Center:
- SL 0.30 ATR
- TP=PDC
- news rule fixed

Parameter neighborhood:
- 0.25 / 0.30 / 0.35 ATR only.

Execution stresses:
- 0 ticks slippage
- 1 tick slippage
- 2 ticks slippage

Commission cases:
- base commission template approximating $4.38 RT
- stress commission approximating $6.57 RT

No new stop values may be introduced.

PDC Stage-3 pass:
- center remains net positive at 1 tick slippage + stress commission;
- at least two of three stop values remain PF >1.15 at 1 tick;
- center max DD under stressed execution does not exceed 2x zero-slippage parity DD;
- no single year produces >60% of all positive-year profit.

## POC

Parity center:
- H15

Robustness references:
- H10 / H15 / H20 only.

Execution stresses:
- 0 / 1 / 2 ticks slippage
- base / stress commission

POC Stage-3 pass:
- at least two of H10/H15/H20 remain net positive at 1 tick + stress commission;
- H15 itself remains net positive at 1 tick + stress commission;
- no unexplained fill artifact is responsible for >25% of total historical profit.

Do not switch to H20 solely because its 2020-2025 backtest is highest.

## R072

R072 is provisional after failing the Stage-1 local plateau.
Stage 3 optimization is NOT authorized yet.

Allowed:
- Stage-2 implementation parity for H30.
- execution sensitivity of the exact H30 center only.

Not allowed:
- additional wick/cutoff/horizon search before an explicit new preregistration.

## Output

For each allowed run save:
- exact parameters
- data range
- instrument/merge settings
- order fill resolution
- commission template
- slippage
- trades
- PF
- expectancy
- max DD
- yearly and semester results

No 2026 data.
