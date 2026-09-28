# B13 / R068–R070 — HIGH-Regime Directional Trigger Discovery

Frozen before execution: 2026-09-28.

## Purpose

B12 showed that HIGH-regime range breakout alone does not provide directional alpha.

B13 tests three different directional triggers derived from the completed HIGH 15-minute block itself.

R063 remains frozen. No stop/target optimization is allowed in this block.

## Common policy

- Development data: 2020–2025 only.
- 2026 remains completely unopened.
- R063 dynamic state must be HIGH at completed block close.
- H017 LOW override must not be active.
- Eligible dynamic blocks end 09:45 through 11:15 ET.
- Signal is known at completed block close.
- Entry = next exact 1-minute bar Open.
- Entry clock must be <=11:30 ET.
- One trade maximum per session per architecture; earliest valid signal wins.
- One MES contract.
- Costs: $1.88 commission RT + $2.50 slippage RT = $4.38/trade.
- No stop or target.
- 15m / 30m / 60m time exits are recorded.
- 30m is the only primary horizon.

## H077 / R068 — HIGH Block Directional Close Continuation

For a completed HIGH block calculate:

```text
BodyRatio = |Close - Open| / (High - Low)
CLV = (Close - Low) / (High - Low)
```

Bullish signal:
- Close > Open;
- BodyRatio >= 0.60;
- CLV >= 0.80.

Bearish signal:
- Close < Open;
- BodyRatio >= 0.60;
- CLV <= 0.20.

Trade in the block direction at next exact 1m Open.

Primary hypothesis:
the strong directional HIGH block continues over the next 30 minutes.

Gate:
- >=150 trades/sessions;
- net expectancy >=+$1/trade;
- 95% CI entirely >0;
- raw p<0.05;
- BH q<0.05 across H077–H079;
- PF>=1.15;
- total net P&L>0;
- >=4/6 years positive expectancy.

## H078 / R069 — HIGH VWAP Displacement Continuation

At each completed HIGH block compute cumulative RTH VWAP through block close:

```text
TypicalPrice = (High + Low + Close) / 3
VWAP = sum(TypicalPrice × Volume) / sum(Volume)
VWAPDisplacementBps = log(BlockClose / VWAP) × 10,000
```

Magnitude filter:
- |VWAPDisplacementBps| >= same-block-clock q60 of the prior 60 eligible sessions.

Alignment:
- block open-to-close return must have the same sign as VWAP displacement.

Direction:
- positive displacement => LONG;
- negative displacement => SHORT.

Entry next exact 1m Open.

Primary hypothesis:
a HIGH block that moves directionally away from intraday VWAP continues over the next 30 minutes.

Same gate as H077, with >=150 trades/sessions.

## H079 / R070 — HIGH Block Rejection Reversal

For a completed HIGH block:

```text
UpperWickRatio = (High - max(Open,Close)) / (High-Low)
LowerWickRatio = (min(Open,Close) - Low) / (High-Low)
```

Upper rejection:
- UpperWickRatio >=0.50;
- Close < Open;
- expected direction SHORT.

Lower rejection:
- LowerWickRatio >=0.50;
- Close > Open;
- expected direction LONG.

Entry next exact 1m Open.

Primary hypothesis:
a large HIGH-regime block with strong rejection reverses over the next 30 minutes.

Gate:
- >=100 trades/sessions;
- net expectancy >=+$1/trade;
- CI>0;
- raw p<0.05;
- BH q<0.05;
- PF>=1.15;
- total net P&L>0;
- >=4/6 years positive expectancy.

## Descriptive diagnostics

For each architecture:
- gross/net expectancy at 15/30/60m;
- PF, win rate, max DD;
- yearly results;
- LONG vs SHORT;
- entry time;
- MFE/MAE first 30m;
- BodyRatio / CLV / wick ratios / VWAP displacement as applicable.

Secondary horizons and subgroups cannot rescue a failed primary hypothesis.

## Multiple testing

BH/FDR across H077, H078, H079 primary 30m p-values.

## Holdout

2026 is not used anywhere in B13.
