# MES Market State — Availability Audit A1

Status: descriptive data audit. No trading outcomes, forward returns, P&L, strategy
selection, threshold optimization or promotion are permitted.

## Purpose

MES-MS1 classified only 381 of 1,294 weekday rows as R1-R4. Before any
regime-conditioned strategy test, this audit determines how much of the R0
coverage is caused by data construction rather than genuine state uncertainty.

The audit addresses three fixed questions:

1. **Incoming-contract history:** did the raw incoming quarterly contract already
   contain at least 14 complete prior RTH sessions before the day on which the
   continuous series began using it? If yes, discarding overlap from the
   continuous price series must not imply that this causal history was
   unavailable.
2. **Previous-RTH failures:** for rows labeled UNKNOWN_PREVIOUS_RTH, was the same
   contract's prior RTH actually complete in its raw file, partial, or absent?
3. **Late 2024 coverage:** how many ET-calendar-2024 rows/days are added by
   allowing the MAR25 source file solely to complete 2024? No 2025 feature,
   return or P&L may be calculated.

## Fixed boundaries

- V1 remains immutable and its report is the comparison baseline.
- MES 2026 is not opened in any form.
- This audit may read MES MAR25 only as a source container. All observations are
  filtered to ET timestamps <= 2024-12-31 before any daily analysis.
- No ES files are opened.
- "Full RTH" keeps the existing project convention: 390 one-minute Last bars
  ending 09:31 through 16:00 ET. This audit does not yet reinterpret legitimate
  shortened sessions.
- No calendar rule, CUSUM parameter, quantile, ATR window, hysteresis rule or
  regime definition is changed here.
- Results may justify a separately frozen V2 for data-availability reasons only.
  They may not be used to select a profitable subgroup.

## Decision rule

A V2 data-construction change is justified if the audit demonstrates that a
material number of V1 R0 rows were caused by overlap removal even though the
same-contract raw history was already observable, or if late-2024 source
coverage is materially incomplete without MAR25.

Any V2 must be specified before rerunning the state map and must preserve the
2026 holdout policy.
