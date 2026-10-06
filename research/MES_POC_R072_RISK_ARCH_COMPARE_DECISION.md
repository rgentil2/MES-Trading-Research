# MES Risk Architecture Comparison — POC and R072

Date: 2026-10-06.
2026 remains strictly closed.

## Purpose

Compare:
1. existing time-exit architecture;
2. a wide catastrophe stop;
3. an "average SL / average TP" ATR bracket.

The split study used 2020-2022 to construct levels and 2023-2025 for validation.

## Important scope note

POC has 109 trades in the existing Stage-1 study. The ATR risk comparison contains 108 because the earliest POC trade occurs before a causal ATR14 is available from the 2020-starting dataset. Comparisons below therefore use the common ATR-available universe.

R072 retains all 145 trades.

# 1. Excursion geometry

## POC — full known development sample 2020-2025

All trades:
- mean MAE: 0.0882 ATR
- P95 MAE: 0.2709 ATR
- P99 MAE: 0.3455 ATR
- max MAE: 0.3798 ATR

Winners:
- mean MAE: 0.0485 ATR
- P95 MAE: 0.1140 ATR
- max MAE: 0.2530 ATR
- mean MFE: 0.2194 ATR
- P95 MFE: 0.4667 ATR

Losers:
- mean MAE: 0.1342 ATR
- P95 MAE: 0.3252 ATR
- max MAE: 0.3798 ATR
- mean MFE: 0.0687 ATR

## R072 — full known development sample 2020-2025

All trades:
- mean MAE: 0.1621 ATR
- P95 MAE: 0.4558 ATR
- P99 MAE: 0.6021 ATR
- max MAE: 0.6259 ATR

Winners:
- mean MAE: 0.0967 ATR
- P95 MAE: 0.2726 ATR
- max MAE: 0.4600 ATR
- mean MFE: 0.2968 ATR
- P95 MFE: 0.6491 ATR

Losers:
- mean MAE: 0.2302 ATR
- P95 MAE: 0.4909 ATR
- max MAE: 0.6259 ATR
- mean MFE: 0.1081 ATR

# 2. Preregistered split-study levels

Using 2020-2022 only:

POC:
- hard SL = 0.35 ATR
- average bracket SL = 0.15 ATR
- average bracket TP = 0.20 ATR

R072:
- hard SL = 0.70 ATR
- average bracket SL = 0.30 ATR
- average bracket TP = 0.25 ATR

# 3. Validation 2023-2025

## POC

Current H15:
- N=39
- P&L -$89.57
- expectancy -$2.30
- PF 0.862
- stress expectancy -$4.49
- DD $276.29
- worst trade -$101.88

Hard SL 0.35 ATR:
- no stop triggered in 2023-2025
- metrics identical to current
- median implied max risk at entry about $100
- P90 implied max risk about $135

Average bracket SL 0.15 / TP 0.20 ATR:
- P&L -$183.93
- expectancy -$4.72
- PF 0.724
- stress expectancy -$6.91
- DD $214.70
- worst trade -$61.03
- stop rate 28.2%
- target rate 15.4%

Conclusion:
- average bracket reduces tail size but worsens the already-weak validation expectancy.
- not preferred.
- hard-stop approach preserves behavior because it sits outside normal path noise.

## R072

Current H30:
- N=85
- P&L +$820.20
- expectancy +$9.65
- PF 1.410
- stress expectancy +$7.46
- DD $417.58
- worst trade -$285.63

Hard SL 0.70 ATR:
- no stop triggered in 2023-2025
- metrics identical to current
- median implied max risk at entry about $218
- P90 implied max risk about $300

Average bracket SL 0.30 / TP 0.25 ATR:
- P&L +$497.99
- expectancy +$5.86
- PF 1.245
- stress expectancy +$3.67
- DD $426.57
- worst trade -$219.94
- stop rate 9.4%
- target rate 27.1%

Conclusion:
- average bracket remains profitable but sacrifices about 39% of validation expectancy and does not improve validation DD.
- not preferred.
- 0.70 ATR hard stop is consistent with a catastrophe-stop philosophy.

# 4. Full-sample descriptive comparison 2020-2025

Common ATR-available universe:

POC:
- current: PF 1.341, expectancy +$4.73, DD $332.57, worst -$118.13
- hard 0.35: PF 1.345, expectancy +$4.77, DD $332.57, worst -$113.82
- avg bracket: PF 1.362, expectancy +$4.94, DD $280.94, worst -$71.79

The average bracket looks attractive in the full sample, but it fails the later 2023-2025 validation. Do not select it from the full sample.

R072:
- current: PF 1.302, expectancy +$7.53, DD $497.55, worst -$285.63
- hard 0.70: identical to current because the stop never triggers
- avg bracket: PF 1.171, expectancy +$4.32, DD $426.57, worst -$219.94

The average bracket reduces tails but materially degrades edge.

# 5. Catastrophe-stop proposal using the complete development history

The user's objective is to know maximum trade risk at entry, even if the stop almost never triggers.

Because all 2020-2025 data are already development history and 2026 is the untouched holdout, a final catastrophe-stop proposal can be defined from the full known MAE:

Catastrophe SL = ceil_to_0.05(1.10 × maximum 2020-2025 MAE)

This gives:

## POC
- max historical MAE = 0.3798 ATR
- +10% buffer = 0.4177 ATR
- proposed catastrophe stop = **0.45 ATR**

## R072
- max historical MAE = 0.6259 ATR
- +10% buffer = 0.6885 ATR
- proposed catastrophe stop = **0.70 ATR**

These are deliberately NOT optimized to improve PF.

By construction they sit beyond every observed 2020-2025 MAE in the ATR-available universe, so they preserve the historical strategy while defining a hard maximum-loss level.

Approximate one-MES risk at entry including $4.38 base RT cost:

POC 0.45 ATR:
- median historical implied risk ≈ $125.59
- P90 ≈ $213.84
- observed range ≈ $69 to $302

R072 0.70 ATR:
- median historical implied risk ≈ $211.62
- P90 ≈ $328.28
- observed range ≈ $114 to $687

Important: ATR risk is known at entry but is not a constant dollar amount. A later funded-account layer may impose a maximum-dollar-risk rule or skip unusually high-ATR trades, but that would be a separate preregistered portfolio/risk study.

# Recommendation

Do not use the average SL/TP bracket as the primary architecture.

Preferred research specification before NinjaTrader:
- PDC: SL 0.30 ATR, TP=PDC, time exit 11:30.
- POC: catastrophe SL 0.45 ATR, no fixed TP, H15 time exit.
- R072: catastrophe SL 0.70 ATR, no fixed TP, H30 time exit.

POC and R072 catastrophe stops are risk caps, not edge-enhancement parameters.

2026 remains closed.
