# Candidate C004 — Staged Volatility Regime Engine

## Operating logic

### 09:30
Previous-day range state + overnight range state.

### 09:45
Add first-15m range state.

### Dynamic
If H017 appears, override to LOW for the next 30 minutes.

## Development performance
The engine produced ordered LOW/NORMAL/HIGH future range states in 2020–2025.

09:30:
- LOW target ratio ~0.704
- NORMAL ~0.950
- HIGH ~1.419

09:45:
- LOW ~0.693
- NORMAL ~0.954
- HIGH ~1.438

H017:
- next30 range ~38.9% below baseline on average.

## Status
Development-passed synthesis only.

2026 is reserved for future independent validation after strategy-development decisions are frozen.
