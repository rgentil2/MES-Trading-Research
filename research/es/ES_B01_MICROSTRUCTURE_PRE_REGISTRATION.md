# ES-B01 — Microstructure Pre-Registration

Status: **PRE-REGISTERED / NOT RUN**  
Frozen planning date: 2026-09-28.

## Research question

Does ES Level-I microstructure derived from Tick Last/Bid/Ask contain reliable information about short-horizon direction or volatility during the RTH morning beyond 1-minute OHLCV?

## Development sample

- ES, 2020–2024 only.
- New York time.
- Research window 09:30–11:30 ET.
- Non-overlapping 5-minute feature blocks.
- Event time <= 11:30 ET.
- Forward horizons may close after 11:30 if the event was opened by the cutoff.
- Same session and contract; no return across rollover.

## Trade/quote construction

For each Last trade attach the latest Bid and Ask at or before its timestamp using backward as-of joins within the same contract.

Aggressor:
- trade >= Ask → +1;
- trade <= Bid → -1;
- otherwise → 0/unclassified.

Primary variables:
- signed_volume = aggressor_side × trade_volume;
- delta = sum(signed_volume);
- volume_imbalance = delta / total_trade_volume;
- trade_intensity = trades / elapsed_seconds;
- price_efficiency = abs(close-open) / total_trade_volume.

No tick-rule fallback in the primary analysis. Report unclassified share and quote age.

## Thresholds

Extreme = past-only rolling q20/q80, using same feature clock where feasible. Future rows never enter thresholds.

## H-ES-001 — Aggressive-flow continuation

Extreme volume imbalance predicts same-direction +15 minute return. +5 and +30 are secondary descriptive horizons.

## H-ES-002 — Price/Delta divergence

Price makes a directional 5-minute extreme while normalized delta fails to confirm/opposes it. Hypothesis: +15 minute reversion.

The divergence formula must be mechanical from price-return rank and volume-imbalance rank; no discretionary chart labels.

## H-ES-003 — Absorption proxy

High absolute aggressive volume combined with low absolute price displacement per traded contract predicts +15 minute reversal against incoming aggression.

This is an L1 proxy, not an observation of hidden/passive depth.

## H-ES-004 — Price + Delta acceptance

Price direction and delta direction agree, both are in their directional tails, and close location confirms acceptance. Hypothesis: +15 minute continuation.

## H-ES-005 — Trade-intensity volatility

Trade intensity >= rolling q80 predicts higher subsequent movement magnitude over +15 minutes. This is a volatility hypothesis, not directional alpha.

## Statistical protocol

For primary tests report N, mean effect, median where useful, SE, 95% CI, raw p, BH q, session count and yearly effects 2020–2024. Account for within-session dependence. Do not rescue failed primaries with sides, subgroups or secondary horizons.

## Candidate gate

Apply ES_STAGE_GATES.md. A pass creates a candidate only; it does not authorize stop/target optimization.

2025 remains closed until a candidate is frozen. 2026 remains closed until the final complete strategy is frozen.
