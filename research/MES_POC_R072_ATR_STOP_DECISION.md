# MES POC/R072 ATR Stop Risk-Design Decision

Date: 2026-10-06.
2026 remained closed.

## Design
Stops were constructed only from 2020-2022 winning-trade MAE in causal Wilder ATR14 units:
- P75 / P85 / P95, rounded up to 0.05 ATR.
Validation was then read on 2023-2025.

## POC H15

Design geometry (2020-2022):
- N=69; winners=40; losers=29.
- winning MAE median: 0.035 ATR.
- winning MAE P75: 0.068 ATR.
- winning MAE P85: 0.089 ATR.
- winning MAE P95: 0.104 ATR.
- losing MAE median: 0.117 ATR.
- losing MAE P75: 0.171 ATR.

Frozen stop candidates:
- 0.05 ATR
- 0.10 ATR
- 0.15 ATR

Validation 2023-2025:

No stop:
- expectancy -$2.30/trade
- PF 0.862
- stress expectancy -$4.49
- DD $276
- worst trade -$101.88
- 3 positive semesters

0.05 ATR:
- expectancy -$1.65
- PF 0.874
- stress -$3.84
- DD $213
- worst -$34.48
- 2 positive semesters

0.10 ATR:
- expectancy -$1.14
- PF 0.924
- stress -$3.33
- DD $164
- worst -$44.38
- 4 positive semesters

0.15 ATR:
- expectancy -$2.81
- PF 0.835
- stress -$5.00
- DD $230
- worst -$61.03
- 3 positive semesters

Decision:
- **NO POC stop candidate passes.**
- 0.10 ATR meaningfully controls tail risk (about 41% DD reduction and 56% worst-trade reduction), but it does not restore positive expectancy in 2023-2025.
- Therefore POC's current issue is not primarily missing stop protection; its H15 edge weakens in the recent half of the development sample.
- Do not add an ATR stop to POC yet.
- POC requires temporal diagnosis of the already-preregistered H10/H15/H20 neighborhood before final-freeze status.

## R072 H30

Design geometry (2020-2022):
- N=60; winners=33; losers=27.
- winning MAE median: 0.072 ATR.
- winning MAE P75: 0.150 ATR.
- winning MAE P85: 0.186 ATR.
- winning MAE P95: 0.306 ATR.
- losing MAE median: 0.207 ATR.
- losing MAE P75: 0.374 ATR.

Frozen stop candidates:
- 0.15 ATR
- 0.20 ATR
- 0.35 ATR

Validation 2023-2025:

No stop:
- expectancy +$9.65/trade
- PF 1.410
- stress expectancy +$7.46
- DD $418
- worst trade -$285.63
- 4 positive semesters

0.15 ATR:
- expectancy +$5.54
- PF 1.227
- stress +$3.35
- DD $395
- worst -$112.16
- 4 positive semesters

0.20 ATR:
- expectancy +$3.68
- PF 1.139
- stress +$1.49
- DD $436
- worst -$148.09
- 2 positive semesters

0.35 ATR:
- expectancy +$7.89
- PF 1.312
- stress +$5.70
- DD $497
- worst -$255.87
- 4 positive semesters

Decision:
- **NO standard ATR stop passes the preregistered gate.**
- The no-stop H30 control is economically superior.
- 0.15 ATR sharply improves the worst trade but reduces too much aggregate P&L and barely improves DD.
- A frequently-triggered ATR stop is therefore not supported for R072.

Next risk question:
- test a separately preregistered **catastrophe stop** placed outside the normal winning-trade MAE envelope, intended only to cap rare extreme losses rather than manage ordinary trades.

## Current status

PDC:
- regular stop supported: 0.30 ATR.

POC:
- no stop supported yet; temporal/horizon weakness needs diagnosis.

R072:
- no regular stop supported; catastrophe-stop study justified.

No 2026 data opened.
