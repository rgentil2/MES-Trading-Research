# MES RTH Coverage Audit A2

Status: descriptive data-availability audit. No strategy outcomes permitted.

## Question

MES-MS1 labels a prior RTH session "full" only if the Last export contains
exactly 390 one-minute bars from 09:31 through 16:00 ET. The raw project rejects
non-positive-volume rows, so an absent one-minute Last bar can represent either
no trade or missing data. A1 found 169 V1 rows blocked by the prior-RTH rule and
zero cases where the same-contract raw file nevertheless had all 390 bars.

Before changing the rule, A2 measures how close those sessions were to full
coverage.

## Frozen descriptive cuts

For every active-contract RTH day and specifically for the prior sessions that
caused UNKNOWN_PREVIOUS_RTH, report:

- number of observed Last bars in 09:31-16:00 ET;
- whether 09:31 is present;
- whether 16:00 is present;
- observed coverage at thresholds 390, 385, 380, 370 and 350 bars;
- bar-count buckets: 390, 385-389, 380-384, 370-379, 350-369, 300-349, <300;
- annual counts.

These thresholds are diagnostics only. No threshold is promoted by this audit.
A subsequent V2 rule, if justified, must be frozen without reference to trading
returns.

## Boundaries

- Source: the same V1 2020-2024 active continuous series.
- No 2025 or 2026 features or outcomes.
- No forward return, P&L, strategy label, subgroup selection, CUSUM change,
  quantile change or hysteresis change.
- V1 remains immutable.
