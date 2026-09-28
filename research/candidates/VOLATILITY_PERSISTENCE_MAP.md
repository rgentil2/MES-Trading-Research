# Volatility Persistence Map

Current research repeatedly finds stronger and more stable information in **volatility/range persistence** than in directional prediction.

## Confirmed / development-passed components

### H017 / R012
Extreme RTH RV30 compression was independently confirmed in 2025 to persist over the next 30 minutes.

### C001 — Overnight compression
B02 discovered that compressed overnight range was followed by an opening range roughly 32% below baseline. Opposite-sign discovery only; not independently confirmed.

### C002 — Previous-day range
B03 development:
- narrow previous RTH day → next opening ~29% below baseline;
- wide previous RTH day → next opening ~41% above baseline.

### C003 — First-15m range
B04 development:
- wide first 15m → next 30m range ~55% above baseline;
- narrow first 15m → next 30m range ~35% below baseline.

## Working interpretation
MES volatility appears strongly state-dependent and persistent across several horizons:
previous day → overnight/open → first 15m → next 30m.

This should currently be treated as a **regime-forecasting capability**, not as proof of a profitable directional trading strategy.

2026 remains unopened.

### C005 — Five-day range regime
B08 development:
- high prior five-day average range → next opening range ~42% above baseline;
- low prior five-day average range → next opening range ~26% below baseline.

## Extended working interpretation
The same broad state-persistence effect is now visible at:
- multi-day (5-session regime);
- previous day;
- overnight;
- first 15 minutes;
- rolling intraday RV30.

This strengthens the case for treating volatility/range as a persistent latent state rather than a sequence of independent observations.
