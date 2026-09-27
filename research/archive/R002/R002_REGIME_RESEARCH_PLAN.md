# R002 — VWAP excursion regime study

## Motivation

R001 found no stable unconditional mean-reversion edge after first crossings of ±2 VWAP standard deviations during 2020–2024.

R002 asks a narrower question:

> Does a ±2σ VWAP excursion behave differently when it is aligned with the current VWAP trend and when realized volatility is low, medium, or high?

This is a regime-classification study, not yet a trading strategy.

## Data isolation

- Development: 2020-01-01 through 2024-12-31.
- Validation holdout: 2025, unopened for R002 parameter selection.
- Pseudo-forward: 2026, unopened for R002 parameter selection.

All R002 thresholds are estimated only from 2020–2024 and must be frozen before validation.

## Event definition

Use the same R001 first-crossing definition at exactly 2.0σ:

- LOWER event: z_t <= -2.0 and z_(t-1) > -2.0.
- UPPER event: z_t >= +2.0 and z_(t-1) < +2.0.

Only events with:
- an exact continuous 30-minute history;
- an exact 15-minute forward horizon;
- no session or contract crossing

are eligible.

## Trend regime

VWAP trend is measured using the trailing 30-minute VWAP change:

```text
VWAP slope 30m (bps) = (VWAP_t / VWAP_(t-30m) - 1) * 10,000
```

Excursion direction:

- LOWER = -1
- UPPER = +1

Classification:

- WITH_TREND: sign(VWAP slope 30m) equals excursion direction.
- COUNTER_TREND: sign(VWAP slope 30m) opposes excursion direction.
- FLAT: exact zero slope; excluded from the two primary hypotheses.

## Volatility regime

Trailing realized volatility is calculated from 30 exact one-minute log returns:

```text
RV30 = sqrt(sum(r_1m^2)) * 10,000
```

The 33.33% and 66.67% quantiles of RV30 among eligible 2020–2024 events define:

- LOW
- MID
- HIGH

Those two numeric cutoffs are development-only parameters and must be frozen for later validation.

## Primary outcome

15-minute continuation score:

```text
Continuation score = excursion_direction * forward_return_15m * 10,000
```

Interpretation:

- positive = continuation farther away from VWAP;
- negative = reversion back toward VWAP.

## Pre-registered primary hypotheses

### H003 — Trend-aligned high-volatility continuation

For WITH_TREND + HIGH volatility events, mean 15-minute continuation score is positive.

### H004 — Counter-trend low-volatility reversion

For COUNTER_TREND + LOW volatility events, mean 15-minute continuation score is negative.

Inference uses session-clustered standard errors.

The two primary p-values are adjusted together using Benjamini-Hochberg FDR.

## Development gate

A primary hypothesis advances to validation only if all are true:

- at least 500 eligible events;
- at least 250 distinct sessions;
- FDR-adjusted q-value < 0.05;
- 95% clustered confidence interval is fully on the hypothesized side of zero;
- absolute mean effect >= 1.0 bps;
- at least 4 of 5 development years have the hypothesized sign.

Other alignment × volatility cells are descriptive context only and cannot be promoted to a primary hypothesis after seeing the results.

## Outputs

- primary_hypotheses.csv
- regime_cells.csv
- yearly_stability.csv
- regime_thresholds.json
- events.parquet
- SUMMARY.md
