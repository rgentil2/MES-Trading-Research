# ES DEC26 — NinjaTrader QC

Source: user-provided NinjaTrader `DoNotMerge` export in `DATA ES.zip`.

Status: **QC ONLY — 2026 HOLDOUT NOT OPENED**

## Files used

| File | Rows | Size | SHA-256 |
|---|---:|---:|---|
| ES DEC26 Tick Last | 10,113,428 | 485,253,104 bytes | `07faf27144bf26bc87fc6be893385f7214367bd06cfb6f4f95224435423c5d68` |
| ES DEC26 Minute Last | 36,507 | 1,732,086 bytes | `16dc66c648aaa181252f5d5aadf50324d5444e13bc3b20804b951baed900eb87` |

Tick Last coverage: `2026-06-12 19:59:00` through `2026-09-25 20:59:59`.

Minute Last coverage: `2026-06-12 20:00:00` through `2026-09-25 21:00:00`.

## Confirmed Tick Last schema

```
timestamp ; last ; bid ; ask ; volume
```

Therefore Tick Last already contains the contemporaneous BBO fields needed for the first L1 microstructure research block. Separate full Tick Bid/Ask files are not required for the initial ES-B01 pipeline unless later research specifically needs quote updates that occur without a trade.

## Tick QC

- Bid > Ask: **0**
- Non-positive trade volume: **0**
- Last prices off the ES 0.25-point grid: **0**
- Consecutive rows sharing the same timestamp: **8,212,248**. This is expected when multiple trades share the same exchange timestamp; it is not treated as duplicate-row removal.
- Trades at/through Ask: **5,056,348**
- Trades at/through Bid: **5,057,079**
- Trades strictly inside the spread: **1**
- One-tick spread: **9,641,048 / 10,113,428 = 95.3292%**

Primary aggressor classification can therefore use:
- `last >= ask` → buy initiated;
- `last <= bid` → sell initiated;
- inside spread → unclassified.

## Minute-vs-Tick reconciliation

Observed NinjaTrader minute-label convention is normally the right edge of the minute: ticks in a raw clock minute aggregate to the following minute label.

All **36,507** Minute Last bars had a corresponding Tick Last aggregate.

Exact full OHLCV reconciliation:
- **36,489 / 36,507 = 99.9507%**
- mismatches: **18 bars (0.0493%)**

The mismatches are sparse and mostly around session-boundary/low-liquidity timestamps. A small number of individual historical ticks are allocated differently by NinjaTrader's minute-bar construction than by a naive timestamp-only aggregation.

Research implication: use **Tick Last as the microstructure source of truth**. Minute Last remains a cross-check/context source. Do not force Tick data to match Minute bars by deleting or moving trades.

## Methodological decision

This dataset is from **2026**, the final pseudo-forward holdout.

Allowed now:
- schema discovery;
- parser development;
- integrity/QC checks;
- hashes and manifests;
- timestamp/bar-convention validation.

Not allowed now:
- testing ES-B01 hypotheses;
- evaluating directional effects;
- P&L/backtests;
- choosing thresholds from 2026 outcomes.

Next research data required: active ES contracts covering **2020–2024**, prioritizing `Minute Last + Tick Last`.
