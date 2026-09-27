# R003 — Opening Range Breakout statistical behavior

## Motivation

R000 rejected one specific ORB trading implementation on a short June–July 2026 sample. R003 does not retest that strategy.

R003 tests the underlying statistical premise on a much larger development sample:

> After the first closing breakout of the first 15 RTH minutes, does MES continue in the breakout direction over the next 30 minutes?

No stop, target, position sizing, or entry slippage rule is introduced at this stage.

## Data isolation

- Development: 2020-01-01 through 2024-12-31.
- Validation holdout: 2025.
- Pseudo-forward: 2026.

2025 and 2026 remain unopened for R003 parameter selection.

## Timestamp convention

NinjaTrader 1-minute exports use end-of-bar timestamps.

The 15-minute opening range therefore uses exactly:

- 09:31 ET through 09:45 ET inclusive.

A session is eligible only if all 15 opening-range bars are present continuously.

## Opening range

```text
OR High = max(high, 09:31–09:45 ET)
OR Low  = min(low, 09:31–09:45 ET)
```

## Breakout event

Starting with the 09:46 ET bar, identify the first bar in the session whose close is outside the opening range.

- UPPER breakout: close > OR High.
- LOWER breakout: close < OR Low.

Only the first closing breakout of the session is used.

A session is excluded from the primary analysis when the first breakout does not have an exact continuous 30-minute forward horizon inside the same session and contract.

## Primary outcome

30-minute directional return:

```text
UPPER directional return = + forward return 30m
LOWER directional return = - forward return 30m
```

Positive values mean continuation in the breakout direction.

## Pre-registered hypotheses

### H005
The first UPPER 15-minute opening-range closing breakout has positive mean 30-minute directional return.

### H006
The first LOWER 15-minute opening-range closing breakout has positive mean 30-minute directional return.

Inference uses session-clustered standard errors.

The two primary p-values are adjusted together using Benjamini-Hochberg FDR.

## Development gate

A hypothesis advances to 2025 validation only if:

- at least 500 eligible events;
- at least 500 distinct sessions;
- FDR-adjusted q-value < 0.05;
- 95% clustered confidence interval is above zero;
- mean directional effect >= 1.0 bps;
- at least 4 of 5 development years have positive mean directional return.

## Descriptive fields

The event file also records:

- opening-range width;
- breakout time;
- MFE over the next 30 minutes;
- MAE over the next 30 minutes.

These fields are descriptive and cannot be used to retroactively change H005/H006 after results are observed.

## Outputs

- primary_hypotheses.csv
- yearly_stability.csv
- events.parquet
- SUMMARY.md
