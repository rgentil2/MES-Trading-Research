# ES Data Staging

Purpose: isolated landing area for ES market data while the research pipeline is being built.

This folder is intentionally separated from `research/`, `src/`, and the historical MES data so that raw-data handling does not affect the rest of the project.

## What belongs here

- `raw/`: original NinjaTrader/Databento files on the local machine only.
- `processed/`: temporary Parquet/derived datasets on the local machine only.
- `holdout/`: 2025/2026 physical files, stored but not analyzed until their gates are reached.
- `manifests/`: tracked inventories, hashes, date coverage and source metadata.
- `qc/`: tracked small QC reports and summaries.
- `samples/`: small representative samples safe to commit for parser/testing work.

## Git policy

Large raw/processed/holdout files are ignored by Git. Do not force-add them.

The repository should track only:
- manifests;
- checksums;
- schemas;
- QC summaries;
- small samples;
- documentation.

## Current ES source priority

1. NinjaTrader Minute Last.
2. NinjaTrader Tick Last.
3. Tick Bid/Ask only if needed after checking whether Tick Last already contains BBO fields.
4. Databento only for gaps, validation or deeper market-depth research.

## Holdout discipline

- 2020–2024: development.
- 2025: validation only after candidate freeze.
- 2026: final pseudo-forward only after full strategy freeze.

Downloading/storage does not open a holdout. Outcome analysis does.
