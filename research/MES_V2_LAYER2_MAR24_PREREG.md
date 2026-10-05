# MES V2 — Layer 2 Microstructure Pilot — ES MAR24

Locked before inspecting Tick Last outcomes.

## Purpose

Decide whether ES Tick Last contains enough incremental information to justify importing the remaining 2024 Tick Last files.

This is a viability gate, not a trading-strategy optimization.

## Data

- MES one-minute execution/outcome data: 2024 dates overlapping the ES MAR24 contract.
- ES MAR24 Tick Last only.
- ES MAR24 Minute Last for OR/context alignment.
- 2025 and 2026 are forbidden.
- No JUN24/SEP24/DEC24 tick data are used in this pilot.

## Base event

- First MES close outside OR15 between 09:45 and 11:30 ET.
- One event maximum per full RTH session.
- Direction = breakout direction.
- Tick features use only information timestamped no later than the MES signal-bar close.
- Hypothetical outcome begins at next MES one-minute bar open.
- Primary outcome = direction-aligned 30-minute return after fixed $4.38 MES round-trip cost.
- Secondary outcome = gross 30-minute bps.

## Tick classification

Each ES trade record is classified:
- buyer initiated if Last >= Ask;
- seller initiated if Last <= Bid;
- otherwise neutral.

Inside-spread trades are left neutral; no tick-rule rescue.

## Fixed microstructure windows

Relative to the MES signal-bar closing timestamp:
- SIGNAL: prior 60 seconds, [t-60s, t)
- PREV: previous 60 seconds, [t-120s, t-60s)
- BASELINE: prior five minutes excluding SIGNAL, [t-360s, t-60s)

All features are causal at the next MES one-minute open.

## Microstructure features

1. aligned_delta_ratio_signal = direction * aggressive_net_volume / classified_aggressive_volume.
2. aligned_delta_ratio_prev.
3. delta_acceleration = signal aligned delta ratio - previous aligned delta ratio.
4. trades_per_second_signal.
5. trades_rate_ratio = signal trade rate / baseline trade rate.
6. volume_per_second_signal.
7. volume_rate_ratio = signal volume rate / baseline volume rate.
8. avg_trade_size_signal.
9. median_spread_ticks.
10. p95_spread_ticks.
11. aligned_ES_price_change_ticks_signal.
12. price_impact_per_1000 = aligned price change ticks / abs(net aggressive volume) * 1000.
13. absorption_ratio = positive aligned aggressive-volume ratio / max(abs(aligned price change ticks), 1).
14. aggression_persistence = fraction of 5-second buckets with aligned aggressive net volume > 0.
15. max_5s_aligned_delta_share = max aligned 5-second net aggressive volume / total signal volume.
16. classified_volume_fraction = classified aggressive volume / total signal volume.

No additional Tick features may be added after the pilot outcomes are seen.

## Baseline minute features

A fixed compact baseline is used only to measure incremental value:
- OR width / ATR14
- breakout displacement / ATR14
- MES signal candle body efficiency
- MES aligned close location
- MES same-minute RVOL
- ES same-minute RVOL
- ES same-side OR15 confirmation

## Evaluation

Because MAR24 is a pilot rather than a clean holdout:

- Sort events chronologically.
- Use TimeSeriesSplit(n_splits=5).
- Each fold fits only on earlier events and predicts later events.
- Models are fixed L2 LogisticRegression(C=1, max_iter=5000), median imputation + StandardScaler.
- Compare:
  A) baseline minute features
  B) microstructure-only features
  C) baseline + microstructure
- Primary diagnostic = pooled out-of-fold ROC AUC on profitable30.
- Fold AUCs are secondary and must not be used to tune parameters.

## Pilot promotion gate

Import the remaining 2024 Tick files only if ALL hold:

1. At least 40 eligible MAR24 events.
2. Combined-model OOF AUC >= 0.58.
3. Combined-model AUC lift over baseline >= 0.04.
4. At least 4 of 5 combined folds have AUC > 0.50.
5. Top OOF probability tercile has gross 30m mean at least 3 bps better than bottom tercile.

If the gate fails, do not spend resources importing the rest of 2024 Tick data.

No threshold, feature, window, model, OR duration, or outcome horizon may be modified after seeing the pilot result.
