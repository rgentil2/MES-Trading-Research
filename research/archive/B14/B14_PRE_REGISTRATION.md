# B14 / R071–R072 — Exact Opposite-Sign Strategy Candidates

Frozen before execution: 2026-09-28.

## Status

This block is **post-hoc development**, not independent confirmation.

B13 revealed that H078 and H079 produced effects consistently opposite their pre-registered directions.

B14 changes **direction only**. Event definitions, thresholds, entry timing, one-trade/session rule, costs and primary 30-minute horizon remain unchanged.

2026 remains completely unopened.

## Common execution

- 2020–2025 development data only.
- R063 dynamic HIGH required.
- one MES.
- next exact 1m Open entry.
- maximum one trade/session; earliest valid event.
- new entry <=11:30 ET.
- 15m / 30m / 60m time exits recorded.
- primary = 30m.
- base RT cost = $4.38.
- stress RT cost = 1.5 × $4.38 = $6.57.
- no stops/targets.

## H080 / R071 — HIGH VWAP Displacement Reversion

Use the **exact H078 events**:

- HIGH block;
- cumulative RTH VWAP through block close;
- |VWAP displacement| >= same-block prior60 q60;
- block open→close direction aligned with VWAP displacement.

Only change:

```text
H078 direction = sign(VWAP displacement)
H080 direction = -sign(VWAP displacement)
```

Thus:
- positive displacement => SHORT;
- negative displacement => LONG.

Gate:
- >=150 trades/sessions;
- base-cost net expectancy >=+$2/trade;
- 95% CI entirely >0;
- raw p<0.05;
- BH q<0.05 across H080/H081;
- PF>=1.15;
- total net P&L>0;
- at least 4 positive calendar years among observed years;
- observed years >=5;
- 1.5×-cost expectancy >0;
- 2020–2022 aggregate expectancy >0;
- 2023–2025 aggregate expectancy >0.

## H081 / R072 — HIGH Rejection Signal Failure / Exact Inverse

Use exact H079 events:

Upper rejection:
- upper wick ratio >=0.50;
- Close<Open.

Lower rejection:
- lower wick ratio >=0.50;
- Close>Open.

Only change direction:

```text
H079 upper rejection => SHORT
H081 upper rejection => LONG

H079 lower rejection => LONG
H081 lower rejection => SHORT
```

Gate:
- >=100 trades/sessions;
- base-cost net expectancy >=+$2/trade;
- CI>0;
- raw p<0.05;
- BH q<0.05;
- PF>=1.15;
- net P&L>0;
- >=4/6 positive years;
- 1.5×-cost expectancy >0;
- 2020–2022 aggregate expectancy >0;
- 2023–2025 aggregate expectancy >0.

## Diagnostics

Report:
- 15/30/60m results;
- base and 1.5× cost;
- yearly P&L;
- early/late split;
- LONG/SHORT;
- MFE/MAE 30m.

Secondary horizons or subgroups cannot rescue a failed 30m primary.

## Interpretation rule

If a candidate passes, it may advance to execution/risk design, but its status is:
```text
PASS_DEV_POST_HOC_AWAITING_FINAL_FORWARD
```

It is not called independently validated.

## Holdout

2026 is not used anywhere in B14.
