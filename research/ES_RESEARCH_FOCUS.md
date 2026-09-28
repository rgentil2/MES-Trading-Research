# Research Instrument Focus — ES

Effective: 2026-09-28.

## Primary instrument from this point forward

New research will focus on **E-mini S&P 500 futures (ES)**.

Existing MES research remains preserved as historical evidence and methodology development. No MES result is assumed to transfer automatically to ES.

## Temporal discipline for new ES research

- 2020–2024: development / hypothesis discovery
- 2025: validation OOS / validation set, opened only after a candidate is frozen
- 2026: pseudo-forward reserved for the final frozen strategy

## Research flow

Hypothesis
→ statistics
→ candidate
→ strategy
→ backtest with costs
→ robustness / OOS
→ Monte Carlo
→ forward / pseudo-forward
→ funding

## Data acquisition

Initial microstructure target:
- venue dataset: CME Globex / GLBX.MDP3
- instrument: ES
- continuous symbol for acquisition planning: ES.v.0
- schema: MBP-10 (Level II / top 10 aggregated price levels)

Metadata cost/size queries do not constitute opening 2025 or 2026 strategy outcomes.
