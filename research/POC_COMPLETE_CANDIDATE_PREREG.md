# POC Breakdown — Complete Candidate Characterization

Status: locked before news-filter result is inspected.

## Purpose

Characterize the already-reconstructed POC Breakdown setup under the same manual news-risk policy used for PDC, then compare the two MES candidates on equal footing.

This is not independent validation. 2026 remains forbidden.

## Frozen POC setup

- Prior RTH POC from 1-minute HLC3 price bins (0.25 point) weighted by volume.
- Current RTH open above prior POC.
- First bar that touches prior POC must close below it.
- Short entry at next 1-minute open.
- Fixed 15-minute time exit.
- Cost = $4.38 RT.
- Stress cost = $6.57 RT.
- No stop is introduced in this block.

## News policy

Forex Factory USD High/Medium:
- block entries from T-5 through T+5 inclusive;
- if position is open at T-5, exit at the OPEN of the minute beginning at T-5;
- bars remain in all indicator calculations.

## Variants

1. POC_BASE
2. POC_NEWS

No other changes are permitted.

## Evaluation

- week/month: diagnostic only
- quarter/semester: evaluation
- year: robustness
- full 2020-2025: architecture characterization
- 2026 closed

Metrics:
- trades / month
- expectancy
- PF
- stress expectancy
- max drawdown
- worst trade
- positive semesters
- yearly P&L
- news exits / blocked entries

The result will be compared with:
- PDC STOP030_NO_NEWS
- PDC STOP030_NEWS

No strategy is promoted solely because it wins this comparison.
