# Candidate C006 — Intraday Regime Persistence & Transition Dynamics

Origin: B09 / H059–H063.

## Core development result

A same-clock HIGH or LOW 15-minute range state predicts future movement magnitude for at least the next 60 minutes.

### HIGH
- next +15m expansion: +54.23%
- +30m: +53.75%
- +45m: +53.17%
- +60m: +52.34%
- HIGH->HIGH next-block probability: 53.93%

### LOW
- next +15m discount: +35.52%
- +30m: +35.27%
- +45m: +35.02%
- +60m: +34.08%
- LOW->LOW next-block probability: 52.63%

### Transition structure
- HIGH->LOW: 2.52%
- LOW->HIGH: 3.92%
- NORMAL is the dominant intermediate transition state.

## Interpretation

The regime behaves like a persistent latent state with slow decay over at least one hour, not like independent 15-minute volatility observations.

## Status

Development pass only. 2026 remains reserved for independent confirmation after the final regime specification is frozen.
