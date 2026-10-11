# NQ Last/Bid/Ask strict as-of QC

This new development-only source audit matches trade timestamps to the most recent Bid and Ask whose timestamps are strictly earlier than the trade timestamp. It does not infer same-timestamp exchange sequencing or real executable fills. Scope: 2025-10 through 2026-06; the Jul-Sep 2026 pseudo-forward remains sealed. Source-level and aggregate statistics only. Runs in standard public GitHub Actions, using the Dev-only read token; no raw ticks are committed.
