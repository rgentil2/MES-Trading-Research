# MES V2 — Quantifying Discretion — Layer 1 Decision

Status: **FAIL / DO NOT PROMOTE**

Run date: 2026-10-05.

The experiment was pre-registered in `research/MES_V2_QUANTIFYING_DISCRETION_PREREG.md` before outcome analysis.

## Data policy respected

- Discovery: 2020-2022.
- Validation: 2023-2024.
- ES 2025/2026 were explicitly verified to remain Git LFS pointers and were not materialized.
- No 2025/2026 outcomes were used.

## Sample

- Total events: 1,164.
- Discovery 2020-2022: 701.
- Validation 2023-2024: 463.
- Event: first MES OR15 breakout, followed by a fixed five-minute confirmation window.

## Out-of-sample diagnostic

Logistic validation ROC AUC: **0.5262**.

Pre-registered minimum for useful discrimination: **0.55**.

Conclusion: the 25 OHLCV/context features do not contain enough stable out-of-sample information to classify profitable 30-minute continuation.

## Frozen interpretable rule

The depth-2 tree selected on discovery:

`continuation_5_atr > 0.0265048`

Discovery:
- N = 244.
- Profitable fraction = 53.28%.
- Net mean = -0.736 MES points/trade.

Validation:
- N = 142.
- Frequency = 5.92 signals/month.
- Profitable fraction = 48.59%.
- Net mean = **-0.776 points/trade**.
- Net PF = **0.830**.
- Gross 30m mean = -0.561 bps.
- Lift vs validation base = **-0.265 bps**.
- Positive years = 1/2.

By validation year:
- 2023: N=77, net mean **-2.996 points/trade**, total -230.702 points.
- 2024: N=65, net mean **+1.855 points/trade**, total +120.560 points.

## Gate

- Validation N >=120: PASS.
- Net mean >0: FAIL.
- PF >=1.15: FAIL.
- 2023 and 2024 both positive: FAIL.
- Gross lift >=3 bps: FAIL.
- Logistic AUC >=0.55: FAIL.

Overall: **FAIL**.

## Interpretation

Minute-level quantified discretion did not solve the MES problem. The experiment measured breakout displacement, candle quality, RVOL, cumulative volume, path efficiency, VWAP distance, ES confirmation/lead, and five-minute acceptance/rejection dynamics. These features did not generalize sufficiently from 2020-2022 to 2023-2024.

Do not rescue this block by changing thresholds, confirmation duration, tree depth, OR length, or target horizon.

The only justified next MES research layer is genuinely new information: tick/BidAsk microstructure (aggressor delta, trade rate, price impact, absorption, and ES/MES lead-lag at sub-minute resolution). That should be treated as a separate Layer 2 project with its own pre-registration and data gate.
