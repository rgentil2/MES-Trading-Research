# B07 / R038–R042 — Cross-Session Directional Consensus

Frozen before execution: 2026-09-28.

## Purpose

Test whether directional information becomes useful when independent session components agree or disagree:

1. previous RTH day;
2. overnight session;
3. current RTH gap.

This block deliberately avoids using the B05 volatility-regime engine so the directional signal is evaluated on its own first.

## Common policy

- Development pool: 2020-01-01 through 2025-12-31.
- 2026 remains completely unopened.
- Current RTH open = Open of the 09:31 ET end-bar.
- Current opening outcome = current RTH open through 10:00 ET close.
- Previous-day features require same contract.
- Overnight window = 18:01 ET end-bar through 09:30 ET end-bar before current RTH.
- Gap = log(Current RTH Open / Previous RTH Close).
- Thresholds use only information from prior eligible sessions.
- All hypotheses are frozen simultaneously.
- Primary p-values use Benjamini-Hochberg FDR across H049–H053.

## Magnitude filters

Each directional component is considered "meaningful" when its absolute return is at least the rolling 60-session 60th percentile of that component's historical absolute-return distribution.

No alternative percentile is tested in this block.

## H049 / R038 — Previous Day + Overnight Alignment

Signal:
- previous RTH return and overnight return have the same sign;
- both pass their q60 magnitude filters.

Outcome:
```text
Continuation30 =
sign(previous_day_return) × current_open_to_10:00_return × 10,000
```

Hypothesis:
when the previous RTH session and overnight agree directionally, the first 30 RTH minutes continue that direction.

Gate:
- N >= 150;
- mean >= +1.0 bps;
- 95% CI entirely > 0;
- >= 4/6 years positive;
- BH q < 0.05.

## H050 / R039 — Overnight + Gap Alignment

Signal:
- overnight return and current gap have the same sign;
- both pass q60 magnitude filters.

Outcome follows that aligned direction.

Same gate as H049.

## H051 / R040 — Previous Day + Gap Alignment

Signal:
- previous RTH return and current gap have the same sign;
- both pass q60 magnitude filters.

Outcome follows that aligned direction.

Same gate as H049.

## H052 / R041 — Triple Alignment

Signal:
- previous RTH return;
- overnight return;
- current gap;
all have the same sign and each passes its q60 magnitude filter.

Outcome follows the common direction.

Gate:
- N >= 75;
- mean >= +1.0 bps;
- 95% CI entirely > 0;
- >= 4/6 years positive;
- BH q < 0.05.

## H053 / R042 — Strong Previous-Day / Overnight Conflict

Signal:
- previous RTH and overnight returns have opposite signs;
- both pass q60 magnitude filters.

Hypothesis:
the more recent overnight direction dominates the first 30 RTH minutes.

Outcome:
```text
OvernightContinuation30 =
sign(overnight_return) × current_open_to_10:00_return × 10,000
```

Gate:
- N >= 150;
- mean >= +1.0 bps;
- 95% CI entirely > 0;
- >= 4/6 years positive;
- BH q < 0.05.

## Descriptive outputs

For each hypothesis:
- bullish/bearish counts;
- continuation rate;
- yearly stability;
- effect by B05 LOW/NORMAL/HIGH may be studied only later in a separately frozen experiment.

## Holdout

2026 is not used anywhere in B07.
