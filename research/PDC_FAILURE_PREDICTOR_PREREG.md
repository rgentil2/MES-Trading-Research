# PDC Small-Gap — Failure Predictor Diagnostic Preregistration

Status: locked before inspecting model outcomes.

## Purpose

The PDC small-gap phenomenon is strong but has fat-tail failures. The question is not whether PDC is frequently touched; that is already established. The question is whether information available **before entry** can distinguish PDC misses from PDC hits well enough to justify a simple causal risk filter.

This is a diagnostic/promotion test, not permission to optimize a threshold after seeing results.

## Base setup

Use the frozen PDC reconstruction:
- 0.10 <= abs(RTH open - prior day close) / causal ATR14 < 0.20
- PDC untouched during first 5 RTH minutes
- first-5-minute close moves toward PDC
- entry at open of sixth RTH one-minute bar
- target = PDC
- no stop
- time exit = 11:30 ET
- 2026 forbidden

## Primary label

`pdc_miss = 1` if PDC is not touched by 11:30 ET after entry.

This label is chosen because it is structural and does not depend on an arbitrary P&L threshold.

## Frozen causal features

Numeric:
1. `gap_atr`
2. `first5_progress_frac` = movement from RTH open toward PDC / initial gap distance
3. `first5_range_atr`
4. `first5_efficiency` = abs(first5 close - RTH open) / first5 high-low
5. `first5_adverse_atr` = maximum excursion away from PDC during first 5 minutes / ATR
6. `first5_volume_rvol` = first-5-minute volume / causal rolling-20-session median first-5-minute volume

Categorical:
7. `preopen_prediction` from frozen R063
8. `overnight_state` from frozen R063
9. `five_day_state_label` from frozen R063
10. `preopen_support` from frozen R063

News:
11. `news_blackout_entry` = whether entry falls inside the previously frozen USD High/Medium Forex Factory T-5/T+5 blackout
12. `news_within_30m_after_entry` = scheduled USD High/Medium event occurs > entry and <= entry + 30m

No feature may use information after the entry timestamp.

## Evaluation

Because the total sample is small, no single year is designated as a new untouched holdout. Use leave-one-year-out (LOYO) cross-validation across 2020-2025:

- Each fold trains on five years and predicts the held-out year.
- Median imputation, one-hot categorical encoding, standardization of numeric features.
- L2 LogisticRegression, C=1.0, class_weight='balanced', max_iter=5000.
- No hyperparameter tuning.
- Compare:
  A) base model = `gap_atr` only
  B) expanded causal model = all frozen features

Primary diagnostics:
- pooled OOF ROC AUC
- pooled OOF average precision
- AUC lift vs gap-only baseline
- fold AUCs where the held-out year contains both classes

Risk-ranking diagnostic:
- compare PDC miss rate and net P&L in top predicted-risk tercile vs bottom predicted-risk tercile.

## Promotion interpretation

Call the feature set **informative enough for a second-stage simple filter study** only if:
1. expanded pooled OOF AUC >= 0.62
2. AUC lift over gap-only baseline >= 0.05
3. pooled OOF average precision exceeds the unconditional miss rate by >= 0.05
4. at least 4 held-out years with both classes have AUC > 0.50
5. top predicted-risk tercile has at least 1.5x the miss rate of the bottom tercile

Failure of this gate does not invalidate the PDC phenomenon. It means the current pre-entry information is insufficient to identify its failures reliably.

## Prohibited rescue

After results are observed, do not:
- change the 0.10-0.20 ATR gap band
- add/remove features based on coefficient sign
- search probability thresholds
- redefine a miss using P&L
- alter the first-5-minute window
- tune logistic hyperparameters
- use 2026

A later filter, if justified, must be a separate preregistered study.
