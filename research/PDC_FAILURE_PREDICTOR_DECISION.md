# PDC Failure Predictor — Decision

Status: **BORDERLINE INFORMATION / DO NOT USE AS LIVE FILTER**

Run date: 2026-10-06.

The diagnostic was preregistered in `research/PDC_FAILURE_PREDICTOR_PREREG.md` before model outcomes were inspected.

## Sample

- 107 PDC small-gap events, 2020-2025.
- 18 PDC misses.
- Unconditional miss rate: 16.82%.
- 2026 remained closed.

## Leave-one-year-out results

Gap-only baseline:
- pooled OOF ROC AUC: 0.5993
- pooled OOF average precision: 0.2135

Expanded causal model:
- pooled OOF ROC AUC: **0.6473**
- pooled OOF average precision: **0.2831**
- AUC lift over gap-only: **+0.0481**

Held-out-year AUC:
- 2020: 0.8485
- 2021: 0.5625
- 2022: 0.6667
- 2023: 0.7500
- 2024: 0.6154
- 2025: 0.5733

All six held-out years were above 0.50.

## Formal gate

PASS:
- expanded AUC >=0.62
- average-precision lift over unconditional miss rate >=0.05
- >=4 held-out years above AUC 0.50
- top-risk vs bottom-risk miss ratio >=1.5

FAIL:
- AUC lift >=0.05; actual lift = **0.0481**

Therefore the preregistered promotion gate formally fails, narrowly.

## Risk-ranking result

Top predicted-risk tercile:
- N=36
- miss rate=25.0%
- total net P&L=+$816.07
- average net P&L=+$22.67/trade

Middle tercile:
- N=36
- miss rate=22.22%
- total net P&L=-$162.68
- average net P&L=-$4.52/trade

Bottom predicted-risk tercile:
- N=35
- miss rate=2.86%
- total net P&L=+$96.70
- average net P&L=+$2.76/trade

The model successfully ranks miss probability, but **miss probability is not equivalent to economic badness**. High-risk setups also have substantially larger winners when PDC is reached.

## Critical tail-risk finding

Among PDC misses, predicted miss probability is inversely related to realized loss severity:
- Spearman(predicted miss probability, loss severity) ≈ **-0.569**.

The five worst losses:
- 2025-12-12: -$365.63, predicted miss probability 4.63%
- 2025-11-06: -$289.38, predicted 38.77%
- 2023-02-13: -$161.88, predicted 21.57%
- 2025-03-19: -$104.38, predicted 52.19%
- 2023-11-01: -$79.38, predicted 23.63%

Thus the current classifier does **not** identify the catastrophic failures that dominate PDC drawdown.

Among misses:
- lower-half predicted-risk misses: average loss about -$117.44
- higher-half predicted-risk misses: average loss about -$30.63

This is the opposite of what a useful tail-risk filter should do.

## News context

The largest losses were not explained by the frozen USD High/Medium T-5/T+5 news rule:
- worst losses on 2025-12-12, 2025-11-06, 2023-02-13, and 2025-03-19 were not inside the entry blackout and did not have a scheduled High/Medium event within the next 30 minutes.
- events with a scheduled High/Medium event within 30 minutes actually had lower descriptive miss rate and higher average P&L in this small sample.

No news subgroup is promoted from this descriptive result.

## Decision

Do **not** use the expanded miss-probability model as a live PDC filter.

The PDC phenomenon remains economically interesting, but its key problem is not merely predicting whether PDC will be missed. The important unresolved problem is **tail severity conditional on a miss**.

Given only 18 misses total, and only a handful of catastrophic losses, a second machine-learning search for catastrophic-loss predictors would be too sample-starved and too vulnerable to overfitting.

Therefore:
1. retain PDC as the strongest phenomenon/candidate found under the temporal-hierarchy review;
2. do not add a model-based filter;
3. do not optimize a new stop from these 18 misses;
4. continue evaluating the next strong hypothesis/family before deciding whether MES merits another dedicated risk-design study.
