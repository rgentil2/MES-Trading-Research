# MES Stage 1 — Local Robustness Decision

Date: 2026-10-06.

Status: **STAGE 1 COMPLETE**

2026 remained strictly closed.
Each strategy was treated as one independent MES contract.
All tests retained the frozen Forex Factory USD High/Medium T-5/T+5 policy.

## PDC — PASS

Local stop neighborhood:
- 0.25 ATR: PF 1.342, expectancy +$4.19, stress +$2.00, DD $176, 9/12 positive semesters
- 0.30 ATR: PF 1.536, expectancy +$5.89, stress +$3.70, DD $212, 9/12 positive semesters
- 0.35 ATR: PF 1.507, expectancy +$5.70, stress +$3.51, DD $229, 9/12 positive semesters

All preregistered local-robustness criteria passed.

Interpretation:
- the PDC edge is not isolated at 0.30 ATR;
- 0.30 and 0.35 are especially close;
- 0.25 remains positive and robust, though weaker;
- retain **0.30 ATR** as the neutral center rather than selecting 0.35 based on hindsight.

Stage-1 status: **READY FOR NINJATRADER PARITY IMPLEMENTATION**.

## POC Breakdown — PASS AS A PHENOMENON / KEEP H15 CENTER FOR PARITY

Time-exit neighborhood:
- 10m: PF 1.524, expectancy +$6.47, stress +$4.28, DD $252, 6/12 positive semesters
- 15m: PF 1.303, expectancy +$4.28, stress +$2.09, DD $333, 5/12 positive semesters
- 20m: PF 1.562, expectancy +$8.45, stress +$6.26, DD $356, 9/12 positive semesters

All preregistered neighborhood criteria passed because both neighboring horizons remain economically positive.

However, the shape is not a flat plateau: 15m is weaker than both 10m and 20m. Because 15m was the pre-existing center and the neighborhood was inspected after development, **do not switch to H20 based only on these data**.

Retain H15 for implementation parity first. H10/H20 become robustness references for NinjaTrader, not newly selected parameters.

Stage-1 status: **READY FOR NINJATRADER PARITY IMPLEMENTATION, EXIT HORIZON NOT FINAL-FROZEN**.

## R072 — FAIL LOCAL PLATEAU

Time-exit neighborhood:
- 20m: PF 1.060, expectancy +$1.58, stress **-$0.61**, DD $624, 6/11 positive semesters
- 30m: PF 1.302, expectancy +$7.53, stress +$5.34, DD $498, 7/11 positive semesters
- 40m: PF 1.193, expectancy +$6.15, stress +$3.96, DD $646, 6/11 positive semesters

Preregistered plateau gate failed:
- H20 stress expectancy is negative;
- H20 PF <1.10.

Interpretation:
- H30 is materially stronger than H20;
- H40 remains positive, so H30 is not a single-point spike, but the short-horizon neighbor is too weak for a clean plateau;
- do not call R072 final or robust yet.

Stage-1 status: **PROVISIONAL; MAY BE IMPLEMENTED FOR PARITY, BUT NOT ELIGIBLE FOR FINAL FREEZE YET**.

## Stage 1 outcome

Advance to Stage 2:
1. PDC — primary candidate.
2. POC — primary candidate, H15 center retained for parity.
3. R072 — provisional comparison candidate only.

Stage 2 objective:
- reproduce Python entries/exits in NinjaTrader Strategy Analyzer;
- validate timestamps, fills, news handling, commissions, and trade counts;
- do not optimize;
- 2026 remains closed.
