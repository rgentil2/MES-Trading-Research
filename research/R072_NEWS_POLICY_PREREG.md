# R072 — News Policy Characterization

Status: locked before results.

## Purpose
Test only whether the previously frozen Forex Factory USD High/Medium news-risk policy changes the risk profile of frozen R072.

This is not a new signal search and not independent validation. 2026 remains closed.

## Frozen R072
- W0.50
- cutoff 11:00 ET
- one trade per session
- next 1-minute open entry
- direction as frozen H081/R072 inverse signal
- fixed 30-minute time exit
- $4.38 RT base cost
- $6.57 RT stress cost

## News policy
- USD High/Medium scheduled events only
- block entries T-5 through T+5 inclusive
- open position is flattened at the OPEN of the minute beginning at T-5
- news exit takes precedence over that minute's path
- no stop/target added

## Variants
1. R072_BASE
2. R072_NEWS

Evaluate 2020-2025 by year, semester, PF, expectancy, stress expectancy, max DD, worst trade, and frequency.
No thresholds or signal parameters may change after results.
