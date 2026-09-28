# ES Holdout Policy

Frozen: 2026-09-28.

This policy applies to the **new ES program**.

## 2020–2024 — development

Allowed: data cleaning/QC, feature construction, hypothesis testing, statistical specification, candidate discovery and development sensitivity analysis.

## 2025 — validation

2025 may be downloaded and stored but must not be used to choose a feature, threshold, horizon, subgroup or strategy parameter.

A candidate must have a frozen specification before its 2025 outcome is inspected. Opening 2025 for a candidate spends validation for that version.

## 2026 — final pseudo-forward

2026 may be downloaded and stored, but strategy outcomes remain closed until a complete ES strategy is frozen.

Before opening 2026 specify setup/regime, directional trigger, entry convention, no-new-entry cutoff at 11:30 ET, stop, target/time exit, re-entry, max entries/session, size, costs, risk limits and pass/fail gates.

## Operational actions that do not spend a holdout

Downloading, checksums, file-size checks, schema checks, malformed-row counts, timestamp coverage, trade/quote presence and metadata cost queries are allowed.

Do not compute feature/outcome relationships, P&L, directional hit rate, expectancy or parameter comparisons on closed holdout years.
