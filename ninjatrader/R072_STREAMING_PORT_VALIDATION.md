# R072 Streaming Engine Port Validation

Date: 2026-10-07.
2026 remains CLOSED.

## Purpose

Validate that the R072 engine can be expressed causally, sequentially and bar-by-bar before relying on the NinjaScript port.

The streaming Python emulation independently rebuilt:
- minute-by-minute H017 RV30 and prior-60 same-minute q10;
- complete-session 15-minute block ranges;
- prior-60 same-block q20/q80;
- HIGH/LOW/NORMAL state;
- H017 LOW override;
- wick ratios;
- first candidate/session;
- R072 inverse direction;
- next-bar entry.

It was compared against the existing vectorized Python research implementation.

## Result

- vectorized signals: 166
- streaming signals: 166
- common sessions: 166
- vector-only: 0
- streaming-only: 0
- block match rate: 100%
- signal-time match rate: 100%
- direction match rate: 100%
- entry-price match rate: 100%

Decision:

**EXACT ENGINE SIGNAL PARITY = PASS**

This establishes that the R072 research logic is fully expressible as a causal streaming engine.

## Implication for NinjaScript

The remaining R072 port risk is implementation/data parity in NinjaTrader, not ambiguity in the research algorithm.

Validation ladder remains:
1. frozen-signal replay -> target 145 post-news trades;
2. live-engine with Python H017 reference -> target same signals;
3. live-engine with fully computed H017 -> block-level audit vs Python reference;
4. 0.70 ATR catastrophe stop;
5. 1-tick and 2-tick execution stress.

Passing the Python streaming validation does not by itself freeze R072; the existing 20/30/40 horizon-robustness limitation still applies.
