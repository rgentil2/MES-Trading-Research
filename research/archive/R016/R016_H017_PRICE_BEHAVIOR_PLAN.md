# R016 — Price Behavior Inside Confirmed H017 Low-Volatility Regime

Frozen before execution: 2026-09-27.

## Purpose

H017/R012 established that extreme morning volatility compression tends to persist for at least the next 30 minutes.

R016 asks whether that confirmed regime contains a more directly tradable price behavior.

2026 remains completely unopened.

## H017 regime definition

The regime definition is inherited unchanged from R012:

- RTH minute bars, NinjaTrader end-of-bar timestamps.
- Signal window: 10:01–11:30 ET.
- RV30 = sqrt(sum of squared exact 1m log returns over trailing 30m) × 10,000.
- Compression threshold = same-minute 10th percentile of RV30 over the prior 60 sessions.
- Regime event = first qualifying compression event per session.
- No signal may occur after 11:30 ET.
- Outcomes may extend after 11:30 ET but must remain in the same RTH session and contract.

## H021 — Absolute-return persistence (confirmatory 2025)

R006 development data already suggested that absolute returns were lower after compression. H021 tests that specific observation on 2025 only.

At the H017 event:

```text
AbsReturnDiscount30 =
(1 - |forward_return_30m| / historical_same_minute_mean_|return30|) × 100
```

Historical baseline uses only the prior 60 sessions for the same minute.

Hypothesis:
The 30-minute absolute return after H017 is at least 20% below its historical same-minute baseline.

Individual gate:
- N >= 60
- sessions >= 60
- mean discount >= 20%
- 95% CI entirely > 0

## H022 — Short impulse mean reversion inside H017

Dataset: 2020–2025 strategy-development pool.

At the H017 event:
- compute exact trailing 5m log return;
- compute same-minute 70th percentile of |r5| over prior 60 sessions;
- require |r5| >= that threshold;
- require r5 != 0.

Outcome:

```text
Reversion15 = -sign(r5) × forward_return_15m × 10,000
```

Positive = the preceding 5m move reverted.

Hypothesis:
A relatively large 5m impulse observed at the H017 event tends to mean-revert over the next 15 minutes.

Individual gate:
- N >= 100
- sessions >= 100
- mean reversion >= 1.0 bps
- 95% CI entirely > 0
- at least 4 of 6 years positive

## H023 — Short-range breakout failure inside H017

Dataset: 2020–2025 strategy-development pool.

At the H017 event, freeze the high and low of the 15 bars ending at the regime signal.

From the next bar through 11:30 ET:
- find the first close above that fixed 15m range high or below its low;
- require an exact 15m forward outcome.

Outcome:

```text
Fade15 = -breakout_direction × forward_return_15m × 10,000
```

Positive = the breakout failed/reverted.

Hypothesis:
The first short-range breakout after an H017 compression event tends to fade rather than continue.

Individual gate:
- N >= 150
- sessions >= 150
- mean fade >= 1.0 bps
- 95% CI entirely > 0
- at least 4 of 6 years positive

## Multiple-testing gate

H021, H022 and H023 are primary hypotheses and are evaluated together using Benjamini-Hochberg FDR.

To pass R016, a hypothesis must:
1. pass its individual gate; and
2. have BH q-value < 0.05 across the three tests.

## Interpretation

Passing H021 alone strengthens the regime characterization but does not create a strategy.

Passing H022 or H023 would justify a separate strategy-construction experiment with:
- executable entry;
- stop;
- target/time stop;
- MES commission/slippage;
- P&L;
- expectancy;
- Profit Factor;
- drawdown.

## Holdout

2026 is not opened anywhere in R016.
