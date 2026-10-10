# NinjaTrader brokerage Free: all-in fees, 2026-10-09

**Source:** Operator-supplied NinjaTrader itemized price table, **ALL-IN RATES → FREE** column, which shows the price **per contract per side**. A complete trade is **TWO sides: entry + exit**. User explicitly requested this account-plan assumption. This policy is for **NinjaTrader's own brokerage Free account**, NOT an assertion about commissions in MyFundedFutures, Interactive Brokers, or other funding plans. Verify rates again before trading because schedules can change.

## Core instruments — charge per one contract

| Contract | Free all-in per side | Free all-in round trip | Original research MFFU fee assumption (RT) |
|---|---:|---:|---:|
| ES E-mini S&P 500 | $2.87 | **$5.74** | $4.68 |
| NQ E-mini Nasdaq 100 | $2.87 | **$5.74** | $4.68 |
| MES Micro S&P 500 | $0.94 | **$1.88** | $1.90 |
| MNQ Micro Nasdaq 100 | $0.94 | **$1.88** | $1.90 |

**Compute separately:** gross directional trade P&L, fill slippage, commissions/fees. The all-in Free fee includes the operator table's exchange + NFA + clearing + Free brokerage commission, so **do not add those itemized columns a second time**. For multi-contract trades, multiply RT fee by contract count, and for partial exits ensure the correct filled contract-side count.

For one historical MES NinjaTrader export that **already** subtracts $1.88 round-trip commission, the Native Free scenario should simply use its original exported Profit column. Do not subtract $1.88 again. The previously used $1.90 MFFU scenario was a separate accounting model, adding an incremental **$0.02 per trade**.

Full 124-symbol Free rate table: `research/costs/NINJATRADER_FREE_ALL_IN_124_SYMBOLS_2026_10_09.json`.
Exact historical trade-event repricing: `research/costs/NINJATRADER_FREE_REPRICE_ES_NQ_2020_2024.json`.

## Free commission accounting reprice, unchanged signal fills, historical ES/NQ 2020–2024 development only

| Experiment | Trades/events | Former accounting net USD | Free accounting net USD | Free PF | Free realized DD USD |
|---|---:|---:|---:|---:|---:|
| PDC→ES | 94 | +4,710.08 | **+4,610.44** | 1.358 | 2,803.32 |
| POC→ES | 116 | -1,930.38 | **-2,053.34** | 0.901 | 6,224.50 |
| R072→ES | 132 | +6,932.24 | **+6,792.32** | 1.193 | 6,222.84 |
| POC+R072 ES raw, un-routed | 248 | +5,001.86 | **+4,738.98** | 1.085 | 6,656.38 |

The 3 ES portfolios/strategies are **not simultaneous diversified alpha** (they share the same S&P underlying), and the POC+R072 combination is **not a routed executable portfolio**. ES cost stress, inactivity and absence of fundamental-news restrictions from earlier audits remain material.

Free estimated nominal stop medians for 1 ES: PDC **$886.99**, POC **$1,261.99**, R072 **$2,030.74**. Note **74 / 132 R072 ES stop scenarios exceed $2,000 nominal risk**; stop fills can be worse after price gaps. A 50K prop account with a 2K max-loss allowance cannot use the same nominal single-ES strategy automatically.

## Free NQ H01–H03 event-study repricing (NO SL/TP yet!)

Each NQ event's previously modeled price slippage was **two 0.25-point ticks on entry and two on exit**, or **$20 total slippage** for 1 NQ at $20/index point. Old NQ fee $4.68 -> Free fee $5.74. Thus total estimated round-trip friction **$25.74/event**. Same 2020–2024 NQ OHLC and event outcomes; no modification to hypothesis/entry/exit features.

| Diagnostic | Events | Prior mean USD | Free mean USD | Free aggregate USD | Free PF | Weekly sign-flip p | BH q |
|---|---:|---:|---:|---:|---:|---:|---:|
| NQ-H01 ORB volume | 1,117 | +3.58 | **+2.52** | +2,813.42 | 1.006 | .44831 | .67247 |
| NQ-H02 failed ORB | 636 | +38.72 | **+37.66** | +23,954.36 | 1.096 | .20016 | .60048 |
| NQ-H03 VWAP mean reversion | 675 | -78.00 | **-79.06** | -53,364.50 | .819 | .97640 | .97640 |

H02 95% weekly bootstrap interval for mean USD/event: **[-47.44, +123.63]**, not statistically resolved; in-sample gains are concentrated in 2022. H01 barely above zero with PF~1; H03 remains negative. **This is not evidence sufficient to trade or fund**.

## Scope and research integrity

- These are **accounting re-pricings** of frozen realized paths, not fresh historical searches, stop redesigns, tick-level re-executions, or extra hypothesis trials.
- The prior preregistrations and MFFU-cost results are preserved; Free is a **new brokerage scenario**, not silently substituted for the funding firm's account fee structure. ES code now computes both; NQ script's commission assumption changes from $4.68 to $5.74 per user's Free directive.
- **ES 2025, NQ/MNQ 2025 and all 2026 strategy outcomes remain sealed**. Recalculation reads 2020–2024 trade-event artifacts only.
- If testing an actual funded MFFU account, use **MFFU's specific charged rates**, not NinjaTrader brokerage Free, regardless of NinjaTrader being the frontend platform.
