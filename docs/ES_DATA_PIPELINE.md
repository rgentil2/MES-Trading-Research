# ES Data Pipeline Specification

Status: scaffolded; raw Tick schema awaits first NinjaTrader sample.

## Inputs

Per quarterly ES contract: Minute Last, Tick Last, Tick Bid and Tick Ask. Raw files are immutable after ingestion and receive SHA-256 hashes.

## Minute layer

Expected prior NinjaTrader minute pattern: timestamp;Open;High;Low;Close;Volume. For ES this must be re-verified on the first sample rather than assumed.

Checks: parse all rows, sorted timestamps, duplicates, finite OHLC, valid OHLC relationships, 0.25-point grid and positive volume.

## Tick layer

Exact Tick Last/Bid/Ask column schema is **not frozen yet**. It will be finalized after the first real ES exports.

Normalized logical fields: timestamp_utc, timestamp_et, contract, event_type, price and volume.

## Trade-to-BBO alignment

For every Last event, join latest Bid and Ask at or before trade time, within the same contract. Never use a future quote. Record bid/ask quote age. Report missing/stale distributions before choosing exclusions.

Primary aggressor classification is strict at-Bid/at-Ask. Inside-spread trades are unclassified.

## Minute-vs-tick reconciliation

Aggregate Tick Last to one-minute buckets after timestamp convention is established and compare open/high/low/close/volume with Minute Last. Resolve any systematic one-minute shift before research.

## Continuous ES

Keep old contract through its final exported timestamp; use new contract only after that cutoff; remove overlap from new contract; no back-adjustment; mark rollover; prohibit outcomes crossing a contract boundary.

## Planned outputs

- ES_CONTINUOUS_1M_2020_2024.parquet
- ES_TRADES_BBO_2020_2024.parquet
- ES_FLOW_5M_2020_2024.parquet
- results/es_data_quality/

Holdouts use separate paths and are not loaded by development scripts by default.

## First feature table

OHLCV, VWAP/context, trade count, buy/sell/unclassified volume, delta, normalized imbalance, session cumulative delta, spread, quote age, trade intensity, price displacement and price efficiency.

No Level-II feature may be synthesized from L1 data.
