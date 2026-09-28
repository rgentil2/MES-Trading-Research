# R063 Final Regime Engine v1 — Freeze Manifest

## Frozen specification
- Specification commit: `0db366ea9324a568372ebfcdeea5e09b8207f8a6`
- Date: 2026-09-28
- 2026 data had not been opened.

## Implementation
- Initial implementation commit: `643fb8c619ed56f40d487d5bf75037e7ce90a9de`
- Formatting-only audit fix: `277591c8d6b3e62098f6182a071d1d06b38b1649`
- The formatting fix replaced a missing optional Markdown dependency and did not change engine rules, thresholds, calibration constants or validation gates.

## Successful development audit
- GitHub Actions run: `36420365626`
- Conclusion: SUCCESS
- Artifact: `r063-final-regime-engine-audit`
- Artifact ID: `10969571214`
- Artifact SHA256: `43bae07f0ebc70890d7e2f7865ab47f622737c4461af3630d32203c840de71ea`

## Reproduced development calibration

PREOPEN:
- LOW: n=475, observed mean ratio=0.704426, frozen=0.704
- NORMAL: n=478, observed mean ratio=0.949661, frozen=0.950
- HIGH: n=364, observed mean ratio=1.418596, frozen=1.419

OPEN15:
- LOW: n=540, observed mean ratio=0.692707, frozen=0.693
- NORMAL: n=358, observed mean ratio=0.953601, frozen=0.954
- HIGH: n=419, observed mean ratio=1.438115, frozen=1.438

Dynamic multiplier table and H017 override were also reproduced from the frozen specification.

## Isolation
The successful workflow explicitly verified:
```text
R063 audit verified: 2026 unopened.
```

## Validation protocol
R064 is pre-registered in:
`research/R064_2026_VALIDATION_PROTOCOL.md`

R064 is **not executed** by the R063 audit workflow.

Any later 2026 validation must use the frozen R063 v1 specification and the already-registered R064 gates without modification.
