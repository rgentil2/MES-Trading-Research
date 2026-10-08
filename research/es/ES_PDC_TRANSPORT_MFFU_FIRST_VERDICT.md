# ES PDC fixed-rule transport — 2020–2024 research verdict for MFFU 50K

**Run:** 2026-10-07 Colombia (GitHub Actions #37730936766).  
**STATUS:** **RESEARCH DIAGNOSTIC ONLY — NOT APPROVED FOR FUNDED TRADING**  
**2025/2026 ES outcomes and 2026 MES remain sealed.**

## Scope and provenance

- Frozen MES PDC thresholds transported **without optimization** to ES, with separate preregistration `ES_PDC_TRANSPORT_PREREG_MFFU.md`.
- ES individual NinjaTrader 1-minute Last records for **20 development quarterly contracts MAR20–DEC24 only**; 20/20 SHA256/row-count checks passed; holdout LFS data not materialized.
- 1,748,293 stitched raw rows, 70,829 overlaps excluded, 491,057 RTH-filtered minute records; **1,220 complete 390-bar RTH sessions** included, 201 partial/non-session groups excluded (some Sunday spurious clock rows).
- MES-original PDC parameters: ATR14 Wilder prior full session, opening gap 0.10–0.20×ATR, first 5m untouched/heading toward PDC, entry at next open, stop 0.30 ATR, target previous close, no-new-entry after 11:30 ET.
- 2 ticks adverse on entry and market/stop exit; PDC limit target treated as touched/fill, conservative STOP-FIRST if OHLC ambiguous.
- Commission MFFU ES **$4.68 round trip**; MES **$1.90 round trip** for reference sizing at *ES-derived signals*. Source: https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list
- **Critical deviation:** the archived USD high/medium news blackout and forced flatten files are not committed; **NO NEWS FILTER** is applied. This is **not** complete frozen PDC parity and **not a deployable NinjaTrader fill simulation**. Both profit and trade frequency may differ after news rules.
- Contract MAR25 is an unopened validation file; using only 20 dev-contracts leaves a piece of late Dec 2024 unavailable. Do not characterize calendar 2024 as complete.

## Observed exploratory results

| Metric | ES one mini | MES one micro, same ES-derived signal timing |
|---|---:|---:|
| Research signals, 2020–2024 | 94 | 94 |
| Nominal net P&L | **+$4,710.08** | **+$336.40** |
| Net expectancy/trade | +$50.11 | +$3.58 |
| Profit factor | 1.367 | 1.256 |
| Closed-trade peak-to-trough DD | **$2,784.24** | $318.35 |
| Active months / 60 | 48 | 48 |
| Gaps >7 calendar days between signals | 61 | 61 |
| Max signal gap | 65 days | 65 days |

### ES P&L by development calendar year

| Year | ES trades | Net USD, 1 ES |
|---|---:|---:|
| 2020 | 25 | +$4,158.00 |
| 2021 | 18 | +$153.26 |
| 2022 | 19 | +$1,423.58 |
| 2023 | 17 | -$1,354.56 |
| 2024 (incomplete near year-end) | 15 | +$329.80 |
| **2020–2024** | **94** | **+$4,710.08** |

2020 contributes **88.3% of total net**. This is a major regime/time concentration problem and evidence against treating net positive as robust edge. Year 2023 negative.

### Stop size versus MFFU 50K EOD maximum loss of $2,000

Stop-dollar estimate includes ATR stop distance plus two ticks of worse stop execution and commission; **not** an absolute worst-case (gaps can exceed this).

| Metric, one ES | Result |
|---|---:|
| Median monetary stop | **$885.93** |
| 95th percentile stop | **$1,442.18** |
| Largest estimated stop | **$1,779.68** |
| Trades requiring more than $500 stop budget | **93/94** |
| Trades requiring more than $1,000 stop budget | **30/94** |
| Trades requiring more than $2,000 stop budget | 0/94 |

A position requiring ~$886 stop is already 44% of an entire $2k MFFU loss cushion, **before concurrent Nasdaq or other S&P signals**. Max stop ~=89% cushion. This is not a suitable default position size for a multi-strategy funded portfolio.

### Execution-cost sensitivity

| Assumption, one ES, 94 trades | Nominal net |
|---|---:|
| Base fills, 2 ticks entry and stop/time | +$4,710.08 |
| One additional adverse tick **per side** | +$2,360.08 |
| Two additional adverse ticks **per side** | **+$10.08** |

Sensitivity is accounting-only, not re-executed stop/target fills. The edge is very sensitive to fills.

### Rapid EOD evaluation chronology on 94 ES trade-day cashflows

Preregistered target +$3,000, EOD trailing floor -$2,000 locking at +$100, 30% daily best-profit consistency, minimum 4 trading days, 7 consecutive calendar-day inactivity. This chronology uses **closed EOD P&L only**, not full intraday unrealized equity.

- **Actual seven-day-inactivity-gate scenario:** FAIL on **2020-04-23**, after first 2020-04-16 ES PDC trade (net $495.32); no trade on Apr17–23.
- **Counterfactual with inactivity turned OFF:** closed-P&L and consistency simulation first reaches +$3,000 on **2020-07-17** after 10 trade days, balance +$3,240.70. **Not a valid MFFU pass** because the inactivity rule was knowingly removed, news ignored and intraday float untested.
- One MES same ES-derived signal set: also fails inactivity, and without that rule reaches **only +$336.40 net** across the development record (best +$592.95) — far below +$3,000.

## Critical decision

**Do not buy MFFU 50K on the strength of PDC transported to one ES.** It does not pass the actual activity rule, most stops use a large fraction of the loss allowance, 2020 drives a disproportionate share of profits and stress wipes out most nominal expectancy.

This result also does NOT validate or invalidate POC/R072 on ES: no independent ES POC/R072 execution tests have been run. The combined 363-trade MES study covers 2020–2025, a different period; do not naively sum the ES and MES results because instruments share market exposure and trade sets overlap.

## Next step

- Preserve holdouts. Investigate strict USD High/Medium news handling using frozen historical calendar (without resampling thresholds to rescue PDC).
- Review ES POC/R072 as separately preregistered fixed-rule *transfer* tests with their own stop-dollar risk. Prefer ES study for compatibility/size, not a way to artificially increase independent signal count.
- Acquire **NQ/MNQ 2020–2024 1-min Last** and run independently preregistered complementary directional hypotheses in `research/nq/NQ_2020_2024_RESEARCH_PREREG_MFFU.md`; no NQ backtest exists yet.
- Any future portfolio must have one MFFU-compliant risk allocator; 1 ES cannot be approved merely because simulated mean P&L is >0.
- Freeze new portfolio under exact news/order/risk policy, Monte Carlo with cross-index correlation and float, **then** release 2026 chronological pseudo-forward and real-time sim.

## Reproduction

- Script: `research/es/es_pdc_transport_gate.py`
- Account chronology: `research/es/es_pdc_mffu_gate.py`
- Workflow: `.github/workflows/es-pdc-transport-mffu.yml`
- [First ES PDC 2020-24 Action and complete 94-trade artifact](https://github.com/rgentil2/MES-Trading-Research/actions/runs/37730936766).
