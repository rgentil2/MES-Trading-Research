# Research Instrument Focus — ES

Effective: 2026-09-28.

## Primary instrument

All new research focuses on **E-mini S&P 500 futures (ES)**.

The MES program remains preserved as historical research and methodology. No MES effect, threshold, calibration, regime multiplier, or strategy result is assumed to transfer to ES.

## Temporal split

- **2020–2024:** development, hypothesis testing, feature construction and candidate discovery.
- **2025:** validation set; a candidate must be frozen before its 2025 outcome is inspected.
- **2026:** pseudo-forward reserved for the final fully frozen ES strategy.

Downloading or storing holdout files is allowed. Research code must exclude 2025/2026 by default until the appropriate gate.

## Research order

Hypothesis → statistical analysis → candidate → strategy → costed backtest → robustness/2025 validation → Monte Carlo → 2026 pseudo-forward → funding decision.

## Primary data plan

Preferred source before paid data:

- NinjaTrader individual ES quarterly contracts / DoNotMerge.
- Minute Last.
- Tick Last.
- Tick Bid.
- Tick Ask.

Paid Databento data is optional escalation. Full MBP-10 is not a default purchase; use it only if L1 evidence justifies L2 or for pre-frozen event windows.

## Entry-time constraint

No new position may be opened after **11:30 New York time**. Positions opened by the cutoff may close later under a frozen intraday exit rule.

## Holdout note

Metadata queries, downloads, checksums and storage do not open a holdout. Inspecting feature/outcome relationships, P&L or using 2025/2026 to choose parameters does.
