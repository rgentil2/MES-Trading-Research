# MES Risk Follow-up — POC Horizon Stability + R072 Catastrophe Stop

Status: locked before results.
2026 remains closed.

## A. POC temporal horizon diagnosis

Already-preregistered horizons:
- H10
- H15 center
- H20

No new horizon is introduced.

Question:
Did the POC phenomenon disappear in 2023-2025, or did the useful holding horizon change?

Report each horizon separately for:
- 2020-2022
- 2023-2025
- each year
- each semester

This block is diagnostic only. A better recent H20 result does NOT automatically authorize switching H15 to H20.

## B. R072 catastrophe-stop study

Base:
- frozen R072 W0.50 / cutoff 11:00 / H30
- one MES
- frozen news policy
- no TP
- causal Wilder ATR14

Design period:
- 2020-2022 only.

Define the normal winner MAE envelope as:
- E = winner maximum MAE in ATR, rounded UP to nearest 0.05 ATR.

Catastrophe-stop candidates:
1. E
2. 1.5 * E, rounded UP to nearest 0.05 ATR
3. 2.0 * E, rounded UP to nearest 0.05 ATR

These stops are intentionally outside/at the edge of all observed design winners rather than inside their ordinary MAE distribution.

Validation:
- 2023-2025 only.

Catastrophe stop gate:
1. expectancy > 0
2. PF >= 1.25
3. stress expectancy > 0
4. worst trade improves >=25% vs no-stop
5. max DD improves >=15% vs no-stop
6. total P&L reduction <=10% vs no-stop
7. >=4 positive validation semesters

Selection:
- prefer the middle catastrophe stop if it passes;
- otherwise select a passing neighbor with lower DD;
- if none passes, retain time exit without stop and treat tail risk at account/portfolio layer later.

No new stop values after validation is inspected.
