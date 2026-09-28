# B05 Decision — Staged Volatility-Regime Forecast

B05 is a development synthesis, not an independent validation.

## H043 — 09:30 pre-open forecast
PASS stage gate.

Predicted LOW:
- N: 475
- opening range: 29.557% below historical baseline
- LOW precision: 48.0%
- mean target ratio: 0.704

Predicted NORMAL:
- N: 478
- mean target ratio: 0.950

Predicted HIGH:
- N: 364
- opening range: 41.860% above baseline
- HIGH precision: 49.7%
- mean target ratio: 1.419

Ordered target ratios: LOW < NORMAL < HIGH.

## H044 — 09:45 updated forecast
PASS stage gate.

Predicted LOW:
- N: 540
- next-30m range: 30.729% below baseline
- LOW precision: 49.3%
- mean target ratio: 0.693

Predicted NORMAL:
- N: 358
- mean target ratio: 0.954

Predicted HIGH:
- N: 419
- next-30m range: 43.812% above baseline
- HIGH precision: 48.7%
- mean target ratio: 1.438

Ordered target ratios: LOW < NORMAL < HIGH.

## H045 — H017 dynamic LOW override
PASS stage gate.
- N: 512
- next-30m range discount: 38.893%
- median discount: 44.758%
- 95% CI: [36.097%, 41.689%]
- actual LOW precision: 55.9%

## Interpretation
A simple additive state model built from prior-day range, overnight range and first-15m range produces a useful separation of future range regimes. H017 provides an additional dynamic LOW override later in the morning.

This is a volatility/range forecasting engine, not a directional trading strategy.

2026 remains unopened.
