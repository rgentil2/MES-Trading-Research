# ES Research Program

Status: **DATA ACQUISITION / PRE-REGISTRATION**  
Effective: 2026-09-28.

This directory is the primary research track for ES.

## Current state

Waiting for NinjaTrader exports of Minute Last, Tick Last, Tick Bid and Tick Ask.

The first sample is used only for schema/QC validation. No hypothesis result is evaluated until the data contract is frozen.

## Separation from MES

The existing MES archive remains auditable. ES starts as a new instrument program. MES discoveries may motivate questions, but they do not count as ES evidence and their numerical thresholds are not inherited.

## Sequence

1. Data schema and QC.
2. Continuous-contract construction with explicit rollover boundaries.
3. ES-B01 microstructure hypotheses on 2020–2024 only.
4. Candidate freeze.
5. 2025 validation.
6. Strategy design only after a statistical candidate exists.
7. Costed backtest and robustness.
8. Monte Carlo.
9. Final strategy freeze.
10. 2026 chronological pseudo-forward.
