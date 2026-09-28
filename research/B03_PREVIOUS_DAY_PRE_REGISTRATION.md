# B03 / R024–R028 — Previous-Day Context

Frozen before execution: 2026-09-27.

## Common policy
- Development pool: 2020-01-01 through 2025-12-31.
- 2026 remains completely unopened.
- RTH = 09:31–16:00 ET.
- Current opening window = 09:31–10:00 ET.
- Previous-day features require same contract.
- Thresholds use only prior 60 eligible sessions.
- H033–H037 are frozen simultaneously.
- Primary p-values use Benjamini-Hochberg FDR.

## H033 — Previous-Day Narrow Range Persistence
Previous RTH range <= q20 of prior 60 eligible previous-day ranges.
Outcome = (1 - current opening range / prior60 opening-range mean) × 100.
Gate: N>=200, mean >=10%, CI>0, >=4/6 positive years, BH q<0.05.

## H034 — Previous-Day Wide Range Persistence
Previous RTH range >= q80.
Outcome = (current opening range / prior60 opening-range mean - 1) × 100.
Same gate as H033.

## H035 — Previous Trend-Day Continuation
Signal:
- |previous open-to-close return| >= q75;
- previous efficiency >=0.35;
- bullish return requires CLV>=0.80;
- bearish return requires CLV<=0.20.
Outcome = next 09:30–10:00 return in previous-day direction.
Gate: N>=150, mean>=1bps, CI>0, >=4/6 positive years, BH q<0.05.

## H036 — Previous Late-Day Impulse Continuation
Previous 15:31–16:00 absolute return >= q80.
Outcome = next 09:30–10:00 return in late-day direction.
Gate: N>=200, mean>=1bps, CI>0, >=4/6 positive years, BH q<0.05.

## H037 — Previous Close-to-VWAP Stretch Reversion
Previous full-RTH VWAP uses Typical Price weighted by volume.
|log(previous close / previous VWAP)| >= q80.
Outcome = next 09:30–10:00 return opposite the previous VWAP-stretch direction.
Gate: N>=200, mean>=1bps, CI>0, >=4/6 positive years, BH q<0.05.

## Holdout
2026 is not used anywhere in B03.
