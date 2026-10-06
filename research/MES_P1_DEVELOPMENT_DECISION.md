# MES P1 development decision — fixed signal base for risk design

Date: 2026-10-05 / 2026-10-06 UTC run boundary.

## Decision

For the next development block, freeze the signal base at:

- R072 exact-inverse HIGH-regime rejection architecture;
- wick threshold: **0.50**;
- latest signal time: **11:00 ET**;
- time exit baseline: **30 minutes**;
- one earliest qualifying trade per session;
- next exact one-minute Open entry;
- base round-trip cost: **$4.38**;
- stress cost: **$6.57**.

Identifier: **W0.50_C1100_H30**.

## Why this point

P1B did not select the largest historical P&L. It selected a development anchor
for risk-design work based on local stability.

W0.50_C1100_H30:
- 166 trades over 2020–2025;
- net expectancy: +$5.26/trade;
- stress expectancy at 1.5x costs: +$3.07/trade;
- PF: 1.192;
- 4 positive years;
- median annual expectancy: +$6.29/trade;
- highest immediate-neighbor robustness fraction in the P1B table: 0.50.

The nearby original R072 point W0.50_C1130_H30 remains positive but has lower
neighbor robustness (0.40).

## Important failure

This base is **not approved**. In 2025 it produced:
- 27 trades;
- expectancy: -$11.65/trade;
- PF: 0.740.

Moreover, P1B showed within-regime deterioration in 2025: categories that were
strong in 2022–2024 (HIGH pre-open/update/overnight and aligned support) turned
negative. Therefore an existing R063 regime filter cannot be post-hoc used to
rescue P1.

## Next step

Before optimizing stops/targets, run one fixed-base path diagnostic:
- week/month for diagnosis;
- quarter/semester for evaluation;
- year for robustness;
- regime for explanation;
- loss concentration;
- MFE/MAE distributions normalized by the causal 15-minute block range.

This diagnostic may define a coarse risk grid, but it cannot alter the frozen
signal base above.

MES 2026 remains completely unopened.
