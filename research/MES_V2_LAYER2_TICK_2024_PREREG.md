# MES V2 Layer 2 — ES Tick Microstructure 2024 Feasibility Gate

Locked before outcome analysis.

## Purpose

Test whether sub-minute ES Tick Last information contains materially more signal about MES OR15 breakout quality than minute OHLCV. This is a feasibility gate, not a final strategy backtest.

## Accessible data

At the time of preregistration:
- ES MAR24 Tick Last: available in Git LFS (~2.1 GB).
- ES JUN24 / SEP24 / DEC24 Tick Last: not present in the repository; only Minute Last is accessible.
- MES 1-minute data are available for event definition/execution proxy.
- 2025 and 2026 remain out of scope and must not be materialized.

Therefore the first gate uses only the 2024 sessions actually covered by the ES MAR24 Tick Last file.

## Event

- MES OR15 = first 15 RTH one-minute bars.
- Event = first MES close outside OR15 between 09:45 and 11:24 ET.
- Direction = +1 above ORH, -1 below ORL.
- Event timestamp follows the established NinjaTrader end-of-bar convention.
- ES tick features must use only ticks observed at or before the hypothetical decision time.

## Decision time

Primary microstructure window:
- Last 60 seconds ending at the MES breakout bar close.

Secondary fixed windows:
- Last 10 seconds.
- Last 30 seconds.
- Last 120 seconds.

No windows may be added after outcomes are observed.

## Tick classification

Given Tick Last fields timestamp, Last, Bid, Ask, Volume:
- Ask aggressor: Last >= Ask.
- Bid aggressor: Last <= Bid.
- Mid/uncertain: Bid < Last < Ask.
- When Bid == Ask or quote fields are invalid, the trade is unclassified.

No tick-rule rescue is applied in this first gate.

## Pre-registered microstructure features

For each window (10s, 30s, 60s, 120s):
1. total traded volume.
2. trade count.
3. trades per second.
4. volume per second.
5. buy aggressor volume.
6. sell aggressor volume.
7. delta = buy volume - sell volume.
8. normalized delta = delta / classified volume.
9. aligned normalized delta = breakout_direction * normalized delta.
10. mean trade size.
11. max trade size.
12. bid-ask spread mean in ticks.
13. bid-ask spread 90th percentile in ticks.
14. price displacement in ticks.
15. aligned displacement in ticks.
16. path length in ticks.
17. path efficiency = abs(displacement)/path length.
18. price impact = aligned displacement / max(classified volume,1).
19. delta-impact mismatch = aligned normalized delta / max(abs(aligned displacement),1 tick).

Cross-window:
20. acceleration trades/sec: 10s rate / 60s rate.
21. acceleration volume/sec: 10s rate / 60s rate.
22. delta persistence: fraction of 10-second subwindows within last 60s whose aligned delta is positive.
23. quote pressure proxy: fraction of trades at ask minus fraction at bid in 60s.
24. large-trade share: volume from trades >= 90th percentile of trade size within the event's 120s window / total 120s volume.

## Outcome

Primary:
- MES direction-aligned gross 30-minute return from the next available 1-minute open after event close.
- Also compute net result after fixed $4.38 RT cost.

Binary diagnostic:
- net profitable at 30 minutes.

Secondary:
- 15m and 60m directional returns.

## Feasibility analysis

Because MAR24 alone is a small sample, no complex ML is permitted.

For every feature:
- compare median among 30m net winners vs losers;
- standardized rank-biserial / ROC AUC with sign chosen from the data only for descriptive magnitude;
- bootstrap 95% CI for winner-minus-loser median difference.

Then fit exactly one diagnostic logistic regression:
- standardized features,
- L2 C=1,
- leave-one-session-out cross-validation,
- report pooled ROC AUC.
This model is diagnostic only.

## Promotion gate

Tick microstructure is considered worth expanding to the rest of 2024 only if ALL are true:

1. At least 35 eligible OR15 events with valid tick coverage.
2. At least 2 pre-registered features show absolute univariate AUC >= 0.60.
3. At least one such feature has bootstrap 95% CI for winner-minus-loser median difference excluding zero.
4. Leave-one-session-out logistic pooled AUC >= 0.60.
5. Direction of the strongest feature is economically interpretable and not driven by <=3 events.

If this gate fails, do not invest resources acquiring/uploading JUN24/SEP24/DEC24 Tick data.

If it passes, next step is to acquire the rest of 2024 and repeat the same frozen feature definitions on the additional quarters.

No 2025/2026 use is allowed.

<!-- trigger QC run -->
