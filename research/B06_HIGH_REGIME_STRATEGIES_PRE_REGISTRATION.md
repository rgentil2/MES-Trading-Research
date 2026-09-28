# B06 / R035–R037 — Continuation Strategies in Forecast HIGH Regime

Frozen before execution: 2026-09-28.

## Purpose

Test whether the B05 volatility-regime engine can convert previously weak continuation signals into viable MES strategies by trading them only when the current forecast is HIGH.

This is strategy development on 2020–2025, not independent validation.

2026 remains completely unopened.

## Frozen dynamic regime

For each strategy signal:

- before the 09:45 bar has closed: use B05 PREOPEN prediction;
- at/after 09:45: use B05 UPDATED prediction;
- if H017 has triggered and the signal is within the following 30 minutes: override regime to LOW.

Only signals classified HIGH are traded.

## Execution

- one MES contract;
- signal known at bar close;
- entry at next exact 1m bar Open;
- fixed time exit;
- commission RT = $1.88;
- slippage RT = $2.50;
- total cost = $4.38/trade;
- no stop/target optimization.

## H046 / R035 — ORB continuation in HIGH regime

Signal:
- 15m opening range, 09:31–09:45;
- first closing breakout;
- signal <=11:30 ET;
- direction follows breakout.

Exit: 30 minutes after signal.

## H047 / R036 — Previous RTH high/low breakout in HIGH regime

Signal:
- first close above previous RTH high or below previous RTH low;
- same contract;
- signal <=11:30 ET.

Exit: 30 minutes.

## H048 / R037 — High-volume impulse in HIGH regime

Signal:
- trailing 5m volume >= same-minute q80 of prior 60;
- ER5 >=0.70;
- first qualifying event/session;
- direction follows trailing 5m return;
- signal <=11:30.

Exit: 15 minutes.

## Primary gate for each strategy

A HIGH-regime strategy passes only if all are true:

- HIGH-regime trades >=150;
- net expectancy >= +$1.00/trade;
- clustered 95% CI of net P&L/trade entirely >0;
- raw p-value <0.05;
- BH q-value <0.05 across H046–H048;
- Profit Factor >=1.15;
- at least 4/6 years have positive expectancy;
- total net P&L >0;
- expectancy improves the same strategy's regime-eligible baseline by >=$3.00/trade;
- Profit Factor improves baseline by >=0.10.

LOW and NORMAL subsets are descriptive only.

## Holdout

2026 is not used anywhere in B06.
