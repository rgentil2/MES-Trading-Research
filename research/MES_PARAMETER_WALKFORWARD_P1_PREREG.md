# MES Parameter Walk-Forward P1 — R072 family

Status: preregistered exploratory model-selection block on already-researched MES development data.

## Objective

Test whether the promising R072 exact-inverse rejection architecture can be made
more robust by controlled parameter selection rather than by inspecting the best
full-sample result.

This block implements the requested hierarchy:

- **Week -> diagnostic only**
- **Month -> diagnostic only**
- **Quarter / semester -> evaluation**
- **Year -> robustness**
- **Market regime -> explanation**

Week or month results may never be used to select or rescue parameters.

## Data authority

- MES 1-minute development data, ET calendar 2020-2025.
- This history has already been researched and is not pristine OOS.
- 2026 remains fully reserved for the final frozen strategy and is not used.
- Base round-trip cost: $4.38 per MES trade.
- Stress cost: 1.5x = $6.57.
- Maximum one trade per session, earliest qualifying signal.
- Entry is the next exact 1-minute Open after the completed signal bar.

## Base architecture

R072 / H081 exact inverse of the HIGH-regime rejection signal:

- R063 dynamic engine state must be HIGH.
- Upper rejection: upper wick ratio >= threshold and Close < Open -> LONG.
- Lower rejection: lower wick ratio >= threshold and Close > Open -> SHORT.
- No side optimization.
- No stop/target optimization in P1. P1 optimizes only signal selectivity,
  latest entry time and time exit. Stop/target design is a later block only if P1
  shows robust pseudo-OOS evidence.

## Frozen parameter grid

Wick threshold:
- 0.40
- 0.45
- 0.50
- 0.55
- 0.60

Latest signal time ET:
- 10:30
- 11:00
- 11:30

Time exit:
- 15 minutes
- 30 minutes
- 60 minutes

Total: 45 variants.

The original R072 point (0.50, 11:30, 30m) is included.

## Walk-forward selection

Eight non-overlapping semester tests:

| Fold | Training window | Test |
|---|---|---|
| 1 | 2020-01-01..2021-12-31 | 2022 H1 |
| 2 | 2020-07-01..2022-06-30 | 2022 H2 |
| 3 | 2021-01-01..2022-12-31 | 2023 H1 |
| 4 | 2021-07-01..2023-06-30 | 2023 H2 |
| 5 | 2022-01-01..2023-12-31 | 2024 H1 |
| 6 | 2022-07-01..2024-06-30 | 2024 H2 |
| 7 | 2023-01-01..2024-12-31 | 2025 H1 |
| 8 | 2023-07-01..2025-06-30 | 2025 H2 |

Within each training window a variant is eligible only if:

- >=25 training trades;
- base net expectancy > 0;
- PF > 1.00;
- 1.5x-cost expectancy > 0;
- at least half of observed training semesters have positive net P&L.

Eligible variants are ranked by:
1. highest median semester expectancy;
2. highest training PF;
3. highest training expectancy;
4. more trades;
5. deterministic parameter order as final tie-break.

If no variant is eligible, that fold selects **NO TRADE**. We do not force a
parameter choice.

## Evaluation hierarchy

### Week — diagnostic
Report trades, net P&L, expectancy, PF and win rate. Never a gate.

### Month — diagnostic
Same metrics plus share of total positive/negative P&L. Never a gate.

### Quarter / semester — evaluation
Report the same metrics. Primary temporal evidence is the sequence of eight
pseudo-OOS semesters and their constituent quarters.

### Year — robustness
Report annual P&L, expectancy, PF, trade count and positive-year count on
concatenated pseudo-OOS trades.

### Market regime — explanation
Using only causal context available by the signal:
- pre-open R063 prediction;
- first-15 updated prediction;
- previous-day range state;
- overnight range state;
- five-day range state;
- pre-open support and open15 support.

These are explanatory breakdowns only. No regime subgroup can rescue a failed
overall walk-forward result in P1.

## P1 interpretation

P1 is promising, not final, if concatenated pseudo-OOS results satisfy all:

- net expectancy > 0;
- PF >= 1.15;
- stress-cost expectancy > 0;
- >=5 of 8 semesters positive;
- >=3 of 4 pseudo-OOS years positive;
- no single positive year contributes >50% of positive annual P&L;
- parameter selections are not obviously unstable (report selection counts).

No minimum trades/month gate is imposed in P1. Frequency is reported rather
than used to discard a potentially useful sparse edge.

A P1 pass authorizes a separate preregistered P2 for stop/target/risk design.
It does not authorize trading and does not open 2026.
