# MES Stage 5 — 2026 Untouched Holdout Protocol

Status: LOCKED BEFORE 2026 IS OPENED.

**Do not execute until Stage 4 freeze is complete.**

## Purpose

Use 2026 as a one-time pseudo-forward / historical forward test of fully frozen MES strategies.

2026 must not be used for:
- signal discovery
- parameter tuning
- stop/target selection
- news-rule selection
- regime-filter selection
- choosing which months to include

## Per-strategy test

Run each frozen strategy independently with exactly one MES contract.

Report:
- trade count
- trades/month
- net P&L
- expectancy/trade
- PF
- win rate
- max DD
- worst trade
- monthly diagnostics
- quarterly/semester evaluation where sample size allows

## Interpretation

A frozen strategy is not required to:
- profit every month;
- profit every quarter;
- reproduce its historical PF exactly.

Primary questions:
1. Is net expectancy positive after costs?
2. Is PF >1.0 and broadly compatible with historical uncertainty?
3. Is DD within a plausible historical/stress range?
4. Is failure explainable by known regime variation rather than a rule change?
5. Does execution remain mechanically reproducible?

## Combined descriptive basket

After individual results are read, combine frozen strategies descriptively as one MES per independent setup.

No portfolio weighting optimization is allowed in Stage 5.

Report:
- combined trades/month
- combined P&L
- PF
- DD
- simultaneous positions
- correlation of strategy daily P&L

## Decision after 2026

Possible outcomes:
- GO TO FUNDED-ACCOUNT DESIGN
- CONTINUE PAPER/SIM VALIDATION
- DROP STRATEGY
- RETURN TO RESEARCH WITH 2026 PERMANENTLY OUT-OF-SAMPLE / NO RETUNING ON IT

Once 2026 is opened, it can never again be treated as untouched validation.
