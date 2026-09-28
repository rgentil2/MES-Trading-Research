# B02 / R019–R023 — Overnight & Opening Structure

Frozen before execution: 2026-09-27.

## Common data policy

- Development pool: 2020-01-01 through 2025-12-31.
- 2026 remains completely unopened.
- NinjaTrader 1m timestamps are end-of-bar.
- RTH bars: 09:31–16:00 ET.
- Overnight window for a current RTH session:
  - starts at the 18:01 ET end-bar after the previous RTH session;
  - ends at the 09:30 ET end-bar immediately before current RTH;
  - same contract required;
  - sessions without valid overnight boundaries are excluded.
- Reference thresholds use only prior eligible sessions.
- All five primary p-values are adjusted together with Benjamini-Hochberg FDR.

## R019 / H028 — Overnight Inventory Correction

Overnight return:

```text
ON_return = log(ON_close_09:30 / ON_open_18:00)
```

Strong overnight move:
```text
|ON_return| >= q80 of the prior 60 eligible sessions
```

Outcome: current RTH open to 10:00 ET close.

```text
Reversion30 = -sign(ON_return) × RTH_open_to_10:00_return × 10,000
```

Hypothesis: an unusually large overnight move tends to correct during the first 30 RTH minutes.

Gate:
- N >= 200
- mean >= +1.0 bps
- 95% CI > 0
- >= 4/6 years positive
- BH q < 0.05

## R020 / H029 — Overnight High/Low Breakout

Compute Overnight High and Overnight Low before RTH.

Between 09:31 and 11:30 ET:
- first close > ON High => UP breakout
- first close < ON Low => DOWN breakout

Outcome:
```text
Continuation30 = breakout_direction × exact_forward_return_30m × 10,000
```

Gate:
- N >= 500
- mean >= +1.0 bps
- 95% CI > 0
- >= 4/6 years positive
- BH q < 0.05

## R021 / H030 — Overnight Compression → Opening Expansion

Overnight range:
```text
ON_range_bps = (ON_high - ON_low) / ON_close × 10,000
```

Compression:
```text
ON_range_bps <= q20 of prior 60 eligible sessions
```

Opening range = High-Low of 09:31–10:00 ET.

Primary outcome:
```text
OpeningExpansionPct =
(opening_range_bps / prior60_mean_opening_range_bps - 1) × 100
```

Gate:
- N >= 200
- mean expansion >= +10%
- 95% CI > 0
- >= 4/6 years positive
- BH q < 0.05

## R022 / H031 — Opening Location Reversion

Opening location within overnight range:

```text
OpenLocation = (RTH_open - ON_low) / (ON_high - ON_low)
```

Extreme opening:
- >= 0.80 => upper extreme; expected DOWN
- <= 0.20 => lower extreme; expected UP

Signal is evaluated using the RTH open, but outcome begins after the first RTH bar closes at 09:31 ET.

```text
Reversion30 = expected_direction × exact_forward_return_30m_from_09:31 × 10,000
```

Gate:
- N >= 400
- mean >= +1.0 bps
- 95% CI > 0
- >= 4/6 years positive
- BH q < 0.05

## R023 / H032 — Efficient Overnight Trend Continuation

Overnight efficiency:

```text
ON_efficiency =
|log(ON_close / ON_open)|
/
sum absolute exact 1m log movement through the overnight session
```

Signal:
- |ON_return| >= q70 of prior 60 eligible sessions
- ON_efficiency >= 0.60

Outcome: RTH open to 10:00 ET close in overnight direction.

Gate:
- N >= 150
- mean >= +1.0 bps
- 95% CI > 0
- >= 4/6 years positive
- BH q < 0.05

## Multiple-testing rule

A hypothesis advances only if:
1. it passes its own frozen sample/economic/CI/year gate; and
2. BH q-value < 0.05 across H028–H032.

Descriptive side breakdowns cannot replace a failed primary hypothesis.

## Holdout

2026 is not used anywhere in B02.
