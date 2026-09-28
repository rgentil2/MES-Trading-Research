# B12 / R065–R067 — HIGH-Regime Strategy Architecture Discovery

Frozen before execution: 2026-09-28.

## Purpose

Convert the frozen R063 volatility-regime engine into candidate trading architectures without requiring a prior directional forecast.

R063 predicts movement magnitude. Price action supplies trade direction.

This block is architecture discovery only. Stops, targets, trailing exits and position sizing are **not optimized here**.

## Data / holdout

- Development pool: 2020-01-01 through 2025-12-31.
- 2026 remains completely unopened.
- R063 v1 is frozen and used without parameter changes.
- Only RTH full sessions.
- New positions must be opened no later than 11:30 ET.
- Positions may exit after 11:30 ET.
- Same contract/session required for entry and exit.

## Common 15-minute structure

Use non-overlapping R063 dynamic blocks ending:
09:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15 ET.

The 11:30 block cannot initiate a new breakout search because an entry after its close would violate the entry cutoff.

For each completed block:
- reference high = block High;
- reference low = block Low;
- R063 engine state at block close must be HIGH;
- H017 LOW override must not be active.

A breakout is confirmed by the first later 1-minute **close**:
- above reference high => LONG;
- below reference low => SHORT.

The breakout must occur before the next 15-minute block completes and must allow next-bar entry no later than 11:30 ET.

Entry:
- next exact 1-minute bar Open after the final signal.

Maximum:
- one executed trade per session per architecture;
- earliest valid trade wins.

## Costs

One MES contract:
- point value = $5.00;
- commission round trip = $1.88;
- slippage round trip = $2.50;
- total modeled cost = $4.38/trade.

No stop or profit target in B12.

## Frozen exit horizons

For every executed trade calculate:
- 15-minute time exit;
- 30-minute time exit;
- 60-minute time exit.

**Primary hypothesis metric is the 30-minute exit only.**

15m and 60m exits are secondary/descriptive and cannot rescue a failed 30m primary result.

All exits are exact time exits from next-bar entry timing and may occur after 11:30 ET.

## H074 / R065 — Direct HIGH-Regime Dynamic Breakout

Signal:
1. completed 15m R063 block is HIGH;
2. first close outside that block's High/Low during the immediately following 15-minute block;
3. H017 override is not active at breakout signal;
4. enter next exact 1m Open.

Direction follows breakout.

Primary outcome:
30-minute net P&L per trade.

Gate:
- >=200 trades/sessions;
- net expectancy >= +$1.00/trade;
- clustered 95% CI entirely > $0;
- raw p <0.05;
- BH q <0.05 across H074–H076;
- PF >=1.15;
- total net P&L >0;
- >=4/6 years positive expectancy.

## H075 / R066 — HIGH Breakout + Pullback Confirmation

Start with the same valid HIGH-regime breakout as H074.

After the breakout, wait a maximum of 10 exact 1-minute bars for the first retest:

LONG retest:
- bar Low <= broken reference High;
- bar Close >= broken reference High.

SHORT retest:
- bar High >= broken reference Low;
- bar Close <= broken reference Low.

Additional rules:
- if the opposite side of the original 15m block is closed through before retest, candidate is invalid;
- if a newly completed R063 dynamic block becomes non-HIGH before the retest signal, candidate is invalid;
- if H017 LOW override becomes active before the retest signal, candidate is invalid;
- entry is next exact 1m Open after retest and must be <=11:30 ET.

Primary outcome:
30-minute net P&L.

Gate:
- >=120 trades/sessions;
- expectancy >=+$1.00;
- CI >0;
- raw p<0.05;
- BH q<0.05;
- PF>=1.15;
- net P&L>0;
- >=4/6 positive years.

## H076 / R067 — NORMAL→HIGH Transition Breakout

Signal requires:
1. immediately previous completed 15m dynamic state = NORMAL;
2. current completed 15m R063 engine state = HIGH;
3. no H017 LOW override;
4. first close outside current block High/Low in the next 15m;
5. next-bar entry <=11:30.

Direction follows breakout.

Primary outcome:
30-minute net P&L.

Gate:
- >=120 trades/sessions;
- expectancy >=+$1.00;
- CI >0;
- raw p<0.05;
- BH q<0.05;
- PF>=1.15;
- net P&L>0;
- >=4/6 positive years.

## Descriptive diagnostics

For each architecture report:
- 15m / 30m / 60m gross and net expectancy;
- PF by horizon;
- win rate;
- max drawdown;
- yearly results;
- LONG / SHORT breakdown;
- entry-time distribution;
- MFE and MAE over the first 30 minutes after entry;
- breakout distance beyond reference level at signal;
- reference-block range.

MFE/MAE are descriptive only. They may inform a separately pre-registered B13 execution-design block but cannot alter B12 decisions.

## Multiple testing

The three 30-minute primary p-values are adjusted together using Benjamini-Hochberg FDR.

## Decision

A passing architecture may advance to B13 execution/risk design.

A failed architecture is not rescued by:
- 15m or 60m time exits;
- LONG/SHORT subgroup;
- time-of-day subgroup;
- MFE/MAE-derived stop/target;
- threshold changes.

## Holdout

2026 is not used anywhere in B12.
