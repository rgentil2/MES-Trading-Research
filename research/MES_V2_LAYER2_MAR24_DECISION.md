# MES V2 — Layer 2 MAR24 Microstructure Pilot — Decision

Status: **FAIL / DO NOT IMPORT REST OF 2024 TICK**

Run date: 2026-10-05.

The pilot was pre-registered in `research/MES_V2_LAYER2_MAR24_PREREG.md` before outcome inspection.

## Data integrity

- ES MAR24 Tick Last materialized successfully: 2,106,586,960 bytes.
- Tick records scanned: 42,807,254.
- Parse failures: 0.
- First parsed line confirmed expected NinjaTrader structure:
  `20240101 230000 0440000;4818;4818;4818;94`
- 2025/2026 Tick objects were explicitly verified to remain unmaterialized.
- JUN24/SEP24/DEC24 Tick were not used.

## Sample

- Eligible MES OR15 breakout events with matching ES Tick coverage: 46.
- Date range: 2024-01-02 through 2024-03-08.
- All 46 events contained signal-window Tick data.
- Base event itself was weak in this period:
  - profitable after cost: 43.48%
  - gross mean: -1.446 MES points/trade
  - net mean: -2.322 MES points/trade
  - gross mean: -2.927 bps

## Pre-registered incremental-information test

Chronological TimeSeriesSplit, 5 folds.

Pooled OOF ROC AUC:
- Minute baseline: **0.5374**
- Tick microstructure only: **0.4490**
- Minute + Tick combined: **0.4728**
- Incremental AUC vs baseline: **-0.0646**

Combined fold AUCs where defined:
- fold 2: 0.5833
- fold 3: 0.5000
- fold 4: 0.1667
- fold 5: 0.2500
Only 1 of 5 folds exceeded 0.50; fold 1 was undefined because the test slice had one class.

OOF ranking check:
- top predicted tercile N=12
- bottom predicted tercile N=11
- top minus bottom gross 30m outcome: **-2.03 bps**

The model ranked nominally better setups worse, not better.

## Gate

- N >= 40: PASS
- Combined AUC >= 0.58: FAIL
- AUC lift vs minute baseline >= 0.04: FAIL
- >=4/5 folds AUC >0.50: FAIL
- Top-vs-bottom gross outcome lift >=3 bps: FAIL

Overall: **FAIL**.

## Microstructure descriptive findings

No feature showed strong standalone relationship with the 30m outcome.

Largest absolute Spearman relationships:
- p95 spread ticks: +0.284
- aligned ES price change during signal minute: +0.154
- average trade size: -0.147
- volume-rate ratio: +0.141
- trade-rate ratio: +0.139
- aligned delta ratio: +0.127

These are descriptive only and are not promoted or thresholded.

Median spread was exactly 1 tick across all events.
Classified aggressive-volume fraction was 1.0 across all events, consistent with the NinjaTrader Tick Last records carrying Last at Bid/Ask for these observations.

Winner vs loser means were directionally modest:
- aligned delta ratio: 0.139 winners vs 0.135 losers
- trades/sec: 80.9 winners vs 71.1 losers
- volume/sec: 122.6 winners vs 112.5 losers
- aligned ES signal-minute move: 11.2 ticks winners vs 8.65 losers
- price impact /1000: 10.36 winners vs 12.64 losers

These differences were insufficient to generalize under the fixed multivariate test.

## Decision

Per the pre-registration, do **not** spend resources importing the remaining JUN24, SEP24, or DEC24 Tick files solely to continue this OR15 microstructure hypothesis.

This pilot does not prove that all order-flow research is useless. It shows that, for the current event definition and the fixed set of causal signal-minute microstructure measures, MAR24 provides no evidence of incremental predictive value over minute-level information.

MES remains paused. Further MES work would require a genuinely new hypothesis/data design rather than expanding this failed pilot.
