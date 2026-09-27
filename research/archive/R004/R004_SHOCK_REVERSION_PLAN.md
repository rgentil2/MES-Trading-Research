# R004 — Standardized 5-minute return shock reversion

## Question

After an unusually large 5-minute MES return relative to recent one-minute volatility, does price mean-revert over the next 15 minutes?

This experiment is independent of VWAP and opening-range rules.

## Data isolation

- Development: 2020-01-01 through 2024-12-31.
- Validation holdout: 2025.
- Pseudo-forward: 2026.

No 2025 or 2026 data may be used to choose R004 parameters.

## Shock construction

One-minute log returns are calculated only when adjacent bars are exactly one minute apart.

Trailing 5-minute log return:

```text
r5_t = log(Close_t / Close_(t-5m))
```

Trailing one-minute volatility uses the previous 60 exact one-minute log returns:

```text
sigma1_60 = std(r_1m, last 60 minutes)
```

Expected 5-minute volatility:

```text
sigma5_expected = sigma1_60 * sqrt(5)
```

Standardized shock:

```text
shock_z = r5_t / sigma5_expected
```

A bar is eligible only with an exact continuous 60-minute history and exact 5-minute return window.

## Event definition

First crossing of the threshold:

- POSITIVE_SHOCK: shock_z >= +2.0 and previous shock_z < +2.0.
- NEGATIVE_SHOCK: shock_z <= -2.0 and previous shock_z > -2.0.

Multiple events may occur in a session, so inference uses session-clustered standard errors.

## Primary outcome

15-minute reversion score:

```text
POSITIVE_SHOCK score = - forward return 15m
NEGATIVE_SHOCK score = + forward return 15m
```

Positive score means mean reversion after the shock.

Forward returns must span exactly 15 elapsed minutes within the same session and contract.

## Pre-registered hypotheses

### H007
After a POSITIVE_SHOCK, mean 15-minute reversion score is positive.

### H008
After a NEGATIVE_SHOCK, mean 15-minute reversion score is positive.

The two primary p-values are adjusted together using Benjamini-Hochberg FDR.

## Development gate

A hypothesis advances to 2025 validation only if:

- at least 1,000 events;
- at least 500 sessions;
- FDR-adjusted q-value < 0.05;
- 95% clustered CI is above zero;
- mean reversion effect >= 1.0 bps;
- at least 4 of 5 development years have positive mean reversion score.

## Frozen parameters

- Shock lookback: 5 minutes.
- Volatility lookback: 60 minutes.
- Shock threshold: 2.0.
- Forward horizon: 15 minutes.

No sensitivity sweep is permitted before the primary R004 decision.

## Outputs

- primary_hypotheses.csv
- yearly_stability.csv
- events.parquet
- SUMMARY.md
