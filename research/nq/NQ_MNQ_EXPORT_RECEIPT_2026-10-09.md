# NQ and MNQ minute export receipt — 2026-10-09

Status: OPERATOR-REPORTED EXPORTED, NOT YET DATA-QC VERIFIED.

The operator provided NinjaTrader output confirming 56 completed historical Minute Last export requests: 28 NQ quarterly contracts and 28 MNQ quarterly contracts, MAR/JUN/SEP/DEC 2020–2026. All output lines are EXPORTED, with no visible EMPTY, FAILED or INCOMPLETE results.

Cross-year splitting is reported: 50 expected 2020–2024 development files (25 per symbol), 10 expected 2025 validation-holdout files (5 per symbol), 8 expected 2026 pseudo-forward-holdout files (4 per symbol). File counts are predictions from the log and exporter design, not independently observed on disk.

The active DEC26 contracts returned 33,350 NQ bars and 37,201 MNQ bars at the time of export. This is only partial-year 2026 history; completion is scheduled for later. 2025 and 2026 price values must NOT be used for research until pre-registered freeze gates.

NEXT:
1. Run research/nq/validate_ninja_bulk_exports.py against the user's NQMNQ_Research_2020_2026 folder, optionally with --holdout-metadata. This validator opens only development_2020_2024 and scans only names and sizes of holdout files.
2. Share nq_mnq_structural_qc.json and the 2020–2024 development data for actual quality verification, per-contract hashes, session completeness, rollover and signal research.
3. Keep holdout 2025/2026 price files sealed until documented validation/final pseudo-forward approvals.
4. EXPORTED is a write-success indication, not proof of gap-free source history.

Exporter: ninjatrader/NQMNQBulkMinuteExporter.cs.
Validator: research/nq/validate_ninja_bulk_exports.py.
Research preregistration: research/nq/NQ_2020_2024_RESEARCH_PREREG_MFFU.md.
