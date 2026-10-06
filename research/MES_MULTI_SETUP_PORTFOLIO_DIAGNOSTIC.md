# MES Multi-Setup Portfolio Diagnostic — PDC + POC + R072

Status: **DESCRIPTIVE / NOT INDEPENDENT VALIDATION**

Date: 2026-10-06.

2026 remained closed.

## Uniform manual-news-policy basket

Components:
1. PDC small-gap + SL 0.30 ATR + TP PDC + 11:30 time exit + USD High/Medium T-5/T+5.
2. POC Breakdown + fixed 15m exit + USD High/Medium T-5/T+5.
3. R072 W0.50 / cutoff 11:00 / H30 + USD High/Medium T-5/T+5.

All components use one MES per signal and $4.38 RT base cost.

### 2020-2025 aggregate

- Trades: **360**
- Average frequency: **5.00 trades/month**
- Net P&L: **+$2,181.61**
- Net expectancy: **+$6.06/trade**
- Net PF: **1.345**
- Stress expectancy at $6.57 RT: **+$3.87/trade**
- Max chronological/daily drawdown: **$581.20**
- Worst single trade: **-$285.63**
- Positive semesters: **9/12**
- Positive years: **5/6**

### Annual P&L

- 2020: +$286.63
- 2021: +$260.89
- 2022: +$794.00
- 2023: +$63.05
- 2024: +$947.21
- 2025: **-$170.18**

The basket solves the previous 2023 weakness but does not solve the 2025 deterioration.

## Diversification

Daily P&L correlations are approximately zero:
- PDC vs POC: -0.018
- PDC vs R072: +0.022
- POC vs R072: -0.011

This is a strong descriptive diversification property.

## Concurrent exposure

Across 2020-2025:
- 11 actual overlapping-position intervals.
- Maximum simultaneous open setups: **2**, never 3.
- Pair overlaps:
  - PDC + POC: 8
  - POC + R072: 2
  - PDC + R072: 1

Thus the 5-trade/month basket does not generally imply three simultaneous MES positions.

## Strategy-specific news observations

PDC:
- news policy improves PF and semester stability but made 2025 slightly negative because two 2025 winners were force-exited before reaching PDC.

POC:
- news policy lowers expectancy/PF slightly and reduces positive semesters; it mainly reduces drawdown.

R072:
- news policy materially improves aggregate PF and expectancy but 2025 remains negative.

Because these strategy-specific choices are known only after inspecting outcomes, no post-hoc mixture of news/no-news variants is promoted.

## Statistical status

The basket is **not** an untouched validation:
- component signals and PDC stop architecture were developed using 2020-2025 information;
- the portfolio combination was inspected after component outcomes were known.

Therefore the basket is a research candidate only.

Do not open 2026 until:
1. final component rules are frozen;
2. NinjaTrader implementation reproduces the Python event/fill logic closely;
3. narrow local robustness tests are specified in advance;
4. account-level position sizing / concurrent exposure rules are frozen.

## NinjaTrader next-stage scope

Allowed:
- implementation parity checking;
- commission/slippage sensitivity;
- narrow stop-neighborhood check for PDC: 0.25 / 0.30 / 0.35 ATR;
- funded-account drawdown and sizing simulations;
- confirm same-day/concurrent-order behavior.

Not allowed:
- unrestricted optimizer sweeps over many parameters;
- selecting arbitrary times/thresholds solely because they maximize 2020-2025 performance;
- reading 2026 before the final rules are frozen.
