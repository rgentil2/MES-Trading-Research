# MES data pipeline

## Source

The repository stores the original NinjaTrader one-minute `Last` TXT exports in `data/raw/`.

Current source set:

- 28 quarterly MES contracts
- MAR20 through DEC26
- Raw files are preserved without modification
- Raw timestamps are interpreted as UTC and an America/New_York timestamp is added during processing

## Frozen rollover methodology

For this research project, the historical series follows the rollover already implied by the NinjaTrader exports.

For each adjacent pair of contracts:

1. Keep the old contract through its final exported timestamp.
2. Remove any overlapping timestamps from the new contract.
3. Start the new contract at its first timestamp strictly after the old contract ends.
4. Mark the first retained row of the new contract with `is_rollover=True`.
5. Do not back-adjust prices and do not create synthetic minute bars.

Forward/live trading must follow the same NinjaTrader rollover convention so that the operational methodology matches the backtest.

## Build

From the repository root:

```bash
python -m src.data_pipeline
```

Primary output:

```text
data/processed/MES_CONTINUOUS_1M_2020_2026.parquet
```

Audit outputs:

```text
results/data_quality/raw_manifest.csv
results/data_quality/rollover_transitions.csv
results/data_quality/qc_summary.json
```

## Critical downstream rule

A return, forward return, indicator window, or trade must not be calculated across a contract boundary without explicitly handling that boundary.

Rows where:

```text
is_rollover = True
```

identify the first retained bar of a new contract.

For intraday RTH research, session-based features such as VWAP should reset within each trading session, which naturally reduces rollover contamination.

## Baseline validation

The uploaded raw set was independently checked before freezing this pipeline:

- Contracts: 28
- Raw rows: 2,443,438
- Continuous rows after overlap removal: 2,365,496
- Overlapping rows removed: 77,942
- Contract transitions: 27
- Duplicate timestamps in continuous series: 0
- OHLC consistency errors: 0
- Non-positive volume rows: 0
- Prices off the 0.25 MES tick: 0
- Continuous range: 2020-01-01 23:01 UTC through 2026-09-25 21:00 UTC
- Observed transition gaps: 1 to 4 minutes

The pipeline does not fill those gaps with artificial bars.
