# ES Data Acquisition Plan

Frozen planning version: 2026-09-28.

## Instrument

E-mini S&P 500 futures (**ES**), quarterly MAR/JUN/SEP/DEC contracts.

Use individual contracts and **DoNotMerge** in NinjaTrader.

## Required exports

| Interval | Type | Required |
|---|---|---:|
| Minute | Last | Yes |
| Tick | Last | Yes |
| Tick | Bid | Yes |
| Tick | Ask | Yes |
| Minute | Bid | No |
| Minute | Ask | No |

Minute Bid/Ask are redundant if complete Tick Bid/Ask are available.

## Download order

Primary development set first: **2020–2024**.

Holdouts may be downloaded and stored but remain excluded from research:
- 2025 = validation.
- 2026 = final pseudo-forward.

## First-sample gate

Before bulk ingestion, one trading day from one ES contract must confirm:
- actual NinjaTrader file schema;
- timezone;
- end-of-bar convention for Minute;
- tick timestamp granularity;
- Tick Last volume field;
- Bid/Ask field structure;
- monotonicity and duplicate behavior;
- ability to align Last trades to the latest known Bid/Ask.

The tick parser remains intentionally unfrozen until that sample is inspected.

## Paid-data escalation

1. NinjaTrader Tick Last/Bid/Ask.
2. Databento Trades/TBBO only if NinjaTrader history has material gaps.
3. MBP-1 only if full BBO update information is necessary.
4. MBP-10 only around pre-defined event windows or after L1 evidence justifies L2.
