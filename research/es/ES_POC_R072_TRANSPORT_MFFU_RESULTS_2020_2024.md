# ES POC + R072 — 2020–2024 fixed-rule transfer: first completed result

**Run:** 2026-10-08 UTC, [GitHub Actions 37731781741](https://github.com/rgentil2/MES-Trading-Research/actions/runs/37731781741).  
**Prereq:** `ES_POC_R072_TRANSPORT_PREREG_MFFU.md` committed **before** results.  
**Status: DEVELOPMENT DIAGNOSTIC ONLY.** ES 2025 and all strategy 2026 outcomes **SEALED**.

## Source and methodological restrictions

- 20 individual ES quarterly Minute Last contracts, MAR20–DEC24, original SHA verified, DoNotMerge/non-back-adjusted; 1,748,293 stitched rows, 1,220 valid complete 390-bar RTH sessions.
- Frozen MES strategy parameters translated without search. POC: previous 1m HLC3-volume-profile POC, first close-through SHORT, H15, stop 0.45 ATR14. R072: past-60 15m-block dynamic HIGH, H017 override, wick .50, cutoff 11:00 NY, H30, stop 0.70 ATR14.
- Python uses next-minute market fills and conservatively assumes 2 ticks adverse slippage on both entry and market stop/time exit, stop-first on ambiguous minute OHLC.
- Fees used: 1 ES $4.68 RT, 1 MES $1.90 RT, with **same ES-derived signal set**, not two independent return streams.
- **IMPORTANT** USD medium/high economic-news entries/forced exits are not applied. This is **not a parity recreation of the NinjaTrader MES versions**, and trade P&L may change materially once original news control is applied. Tick order/limit queue fidelity unverified.
- Development transport of parameters originally researched on MES is **NOT an independent source of alpha**, and an ES result cannot justify opening 2025 on an unregistered final candidate.

## Trade results

| Metric | POC 1 ES | R072 1 ES | POC 1 MES same ES signals | R072 1 MES same ES signals |
|---|---:|---:|---:|---:|
| Signals/trades | 116 | 132 | 116 | 132 |
| Net 2020–24 | **-$1,930.38** | **+$6,932.24** | -$359.15 | +$504.20 |
| Net expectancy | -$16.64 | +$52.52 | -$3.10 | +$3.82 |
| PF | 0.907 | 1.197 | 0.834 | 1.140 |
| Closed trade DD | $6,171.50 | $6,179.38 | $688.75 | $676.65 |
| Median nominal stop risk | $1,260.93 | **$2,029.68** | $127.53 | $204.40 |
| 95th percentile stop risk | $2,167.18 | $3,390.93 | $218.15 | $340.52 |
| Max nominal stop risk | $3,204.68 | $3,804.68 | $321.90 | $381.90 |
| Stops >$2,000 | 11 | **74** | 0 | 0 |
| 7+ day signal gaps | 78 | 49 | same | same |
| Longest gap | 73d | 89d | same | same |

### Calendar years, 1 ES

| Year | POC net | R072 net |
|---|---:|---:|
| 2020 | -$2,701.42 | +$51.60 |
| 2021 | +$2,817.42 | -$3,109.12 |
| 2022 | +$1,442.36 | +$2,783.06 |
| 2023 | -$1,471.74 | +$3,097.10 |
| 2024 | -$2,017.00 | +$4,109.60 |

R072 positive 4/5 development calendar years but mediocre PF 1.197 and severe risk on an ES mini. POC has negative net in 3/5 years and cannot be approved.

## Standalone ES POC + R072 aggregate, before a shared router

248 trades, sum +$5,001.86, PF 1.089, closed-trade DD $6,643.66, signal-day gaps >7d 74, max 52d. These are summed signal profits, not an executable MFFU account portfolio; positions may overlap.

## All three ES signals (PDC + POC + R072) timing audit

Combining the *published 94 PDC ES trade entries* and these 248 ES POC/R072 signals (total 342) strictly as **dates and intervals**:
- **305 distinct trading days** in 2020–2024.
- **74 signal gaps >7 calendar days**; maximum gap 29 days.
- **8 simultaneous same-direction intervals**, maximum two contracts concurrently.
- No opposite ES-side overlap in this exploratory signal set; this is not a guarantee after new news rules or revised execution.
- Combined hypothetical performance is deliberately **not** summed: pre-frozen router, correlated drawdown, news and account rules need implementation, and ES/MES underlying risk is the same.

**Implication:** even all three historical transferred strategies do not satisfy the seven-day MFFU inactivity constraint; making PDC/POC/R072 larger does not solve signal timing.

## Research decision

- POC ES: **FAIL DEVELOPMENT TRANSPORT**, don't choose favorable ES calendar years retroactively.
- R072 ES: **RESEARCH WATCHLIST ONLY**; **one ES mini is NOT acceptable by default for MFFU 50K**. Median estimated stop risk >$2,000 and 74 trades need stop budget greater than the entire maximum EOD drawdown. Scaling to MES reduces risk but profitability becomes only +$504.20 over 5y and still fails inactivity.
- Focus next on **NQ/MNQ independent mechanism discovery and complementary timing**, not three S&P signal families relabeled as multiple independent assets.

## Data acquisition prepared

- NinjaTrader 8 C# `ninjatrader/NQMNQBulkMinuteExporter.cs`: official BarsRequest AddOn, sequential 20 NQ +20 MNQ contracts, minute Last 2020–24, DoNotMerge, provider-dependent; NOT yet compiled on user's local NinjaTrader.
- `ninjatrader/NQ_MNQ_BULK_EXPORT_GUIDE.md`: step-by-step installation.
- `research/nq/validate_ninja_bulk_exports.py`: source-only structural QC, rejects 2025/26 filenames and verifies OHLC/tick grid/volume/timestamps/hash; 4 passing local unit tests. Actual historical NQ/MNQ series cannot be acquired remotely from the user's local NT connection.

## Next gates

1. User installs/compiles AddOn on connected NT8 machine and runs it; share resulting NQ/MNQ 2020–24 folder with project. If historical provider retention insufficient, switch to a backfill vendor/API, not manual repeated retries.
2. Source-QC and data staging with per-quarter SHA, timezone/DST and rollover parity. Original ES 2025 remains sealed for candidate validation.
3. Run preregistered NQ-H01..H04 with causal features/blocked time CV and multiple-testing correction. Costed strategy selection and NinjaTrader parity only after a signal survives.
4. Validate synchronized multi-asset account, trailing EOD+float, 7-day inactivity, news, stops, correlations and Monte Carlo. Freeze. Then 2026 chronological pseudo-forward ONCE; real-time simulator before MFFU purchase.
