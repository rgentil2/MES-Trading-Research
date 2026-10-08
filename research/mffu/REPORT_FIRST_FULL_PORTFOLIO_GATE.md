# MFFU 50K — First reproducible 363-trade portfolio gate

**As of 2026-10-07 | Status: FAIL FOR CURRENT FUNDED-EVALUATION SPECIFICATION**

**Important:** this is **not** a verdict that none of these setups can ever work. It is a statement that the **unmodified 1-MES-per-signal basket** does not meet the new one-time-payment MFFU 50K evaluation requirements. This report is not an intraday/tick-level account pass certification. MES 2026 remains completely sealed.

## Canonical files already recovered (do not ask again)

- `research/mffu/inputs/PDC_NT_2tick_106trades.csv` — corrected NinjaTrader "Fill limit orders on touch" version.
- `research/mffu/inputs/POC_NT_2tick_108trades.csv` — POC H15, SL 0.45 ATR; short only.
- `research/mffu/inputs/R072_NT_2tick_149trades.csv` — autonomous R072, SL 0.70 ATR; four sessions outside original Python eligibility need QC.

All trades: 2020–2025, single MES per signal, NinjaTrader 2-tick slippage, commission 1.88 USD round trip included in `Profit`. For MFFU 1.90 USD round trip, subtract only **0.02 USD per trade**. No double deductions.

## First synchronized realized-P&L replay

| Metric | All historical signals | Deterministic account router scenario |
|---|---:|---:|
| Trades | 363 | 362 |
| Net with $1.90 RT | $1,897.80 | $1,947.20 |
| Trading days | 325 | 325 |
| Calendar-day gaps >7 between trades | **91** | **91** |
| Longest gap | **51 days** | **51 days** |
| Close-to-close daily realized running-peak DD | **$677.45** | **$677.45** |
| Highest closed-equity profit | **$2,504.45** | **$2,553.85** |
| Max concurrent positions (raw) | 2 MES | 2 MES |
| Opposite-direction historical overlap (raw) | 1 interval | 0 intervals |

Router rule for **diagnostic only**: process entry timestamps in order, order same-timestamp signals `PDC -> POC -> R072`, reject a new opposite direction while an MES position is still open. One historical POC short on 2021-02-09 was rejected because PDC was long; the skipped trade was a loser, explaining apparent +$49.40 improvement. **Do not select this policy based on the improvement or call it an additional proven edge.** Same-direction overlaps remain (max two MES).

## Historical 2020–2025 EOD account totals

| Year | PDC+POC+R072, MFFU fees |
|---|---:|
| 2020 | +$282.55 |
| 2021 | +$41.85 |
| 2022 | +$767.15 |
| 2023 | -$15.70 |
| 2024 | +$1,146.65 |
| 2025 | -$324.70 |
| **Total** | **+$1,897.80** |

2024 alone is about 60.4% of the six-year *net*; positive years 4/6. Best running profit never reached +$3,000. MFFU inactivity gate fails far sooner: under an idealized account beginning with the first logged trade on 2020-01-29, a first 7-consecutive-no-trade-days issue arises before the next trade (diagnostic; does not assert there was a real MFFU account in 2020). The full historical basket fails even when ignoring inactivity because it did not reach +$3,000. No simulated historical risk cap or position sizing changes have been adopted.

MFFU **evaluation** Rapid EOD: +$3,000 target, EOD maximum loss $2,000, 30% one-day profit consistency, >=4 trading days, 3 mini / 30 micro equivalent maximum, seven calendar days inactivity. The EOD trailing loss **locks at +$100 above starting balance**, not zero; the threshold only moves after EOD highs but open-equity losses can still breach it intraday. Our replay only tests EOD closed-trade values; it is **optimistic/incomplete** about floating-equity breaches and also does not rigorously simulate Builder's intraday soft pause.

## 10,000-path two-week block Monte Carlo (not a true success probability)

Uses resampled adjacent 14-day **calendar blocks** from the already-searched 2020–2025 period; paths aggregate all three setups by original trading day, so same-day trading correlation and inactivity weeks are at least partly retained. Trading begins at first synthetic signal. Includes modeled EOD loss threshold and evaluation consistency; excludes intraday mark-to-market path and unexpected execution losses. Deterministic seed and data provenance in JSON artifact.

| Portfolio / horizon | Enforce MFFU seven-day inactivity? | Outcome |
|---|---|---|
| Raw basket, 12 months | Yes | 0 / 10,000 pass, **10,000 inactivity failures** |
| Raw basket, 12 months | No (counterfactual) | 0 / 10,000 pass |
| Raw basket, 72 months | Yes | 0 / 10,000 pass, **10,000 inactivity failures** |
| Raw basket, 72 months | No (counterfactual) | 2,405 / 10,000 pass; 165 EOD closed-balance loss failures; 7,430 no pass |
| Router basket, 12 months | Yes | 0 / 10,000 pass, **10,000 inactivity failures** |
| Router basket, 72 months | No (counterfactual) | 2,527 / 10,000 pass; 144 EOD loss failures; 7,329 no pass |

The 24.05% six-year counterfactual pass frequency is **not** the real pass chance. It discards the rule that causes failure in 100% of these sampled paths and omits unobserved intraday drawdown. A six-year evaluation without this activity requirement is not a viable representation of the purchased MFFU product.

## Follow-up gates (do not open 2026 yet)

1. **Minute/tick-path portfolio equity:** synchronize the raw 1-minute price data to entry/exit order events; reconstruct actual floating P&L and compare to EOD floor each minute. Tick-resolution fills should be used for stop/news collision cases. Do not add different per-trade MAEs and call that an observed drawdown.
2. **R072 source control:** verify 1-minute RTH completeness, holiday/early-close calendar and rollover on the four extra R072 dates; confirm protective orders on gap-through-stop scenarios.
3. **Account-level portfolio risk:** preregister a single position/hedging router and monetary risk budget, including joint S&P-Nasdaq correlated drawdowns before introducing NQ.
4. **Broader *independent* edge search:** PDC/POC/R072 frequency and economics fail MFFU 50K as currently designed. ES may validate the same S&P signal at larger multiplier but **ES is not new independent alpha**. Introduce NQ/MNQ hypotheses and additional complementary setups, with all newly selected parameters developed only on allowed data.
5. **Additional statistical gate:** compare 2-week vs 4-week and alternate block Monte Carlo, extra fill/slippage +1 tick each side, commissions under stress, skipped trades, and a drawdown-conditioned kill switch **preregistered before selecting**.
6. **Freeze then out-of-sample:** freeze all entry/exit/risk/priority/size/cost parameters and the MFFU evaluation pass/fail thresholds with a version and SHA; only after that open **2026 chronological pseudo-forward**, then current-data real-time sim and funded evaluation.

## Primary artifacts

- Raw synchronized signal/Trades replay: `research/mffu/MFFU_363_TRADE_FIRST_REPLAY.json`
- 10k Monte Carlo full model results: `research/mffu/MFFU_363_MONTE_CARLO_BLOCKBOOTSTRAP_10000.json`
- Earlier PDC-only study: `research/MFFU_PDC_FIRST_GATE_RESULTS_2026-10-07.md`
- Existing account research architecture: `research/MFFU_MULTI_INSTRUMENT_PORTFOLIO_PLAN.md`

## Sources and caution

- MFFU Rapid EOD: https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look
- Inactivity: https://help.myfundedfutures.com/en/articles/16596524-inactivity-rule-one-time-payment-model
- EOD floating equity: https://help.myfundedfutures.com/en/articles/8348565-end-of-day-eod-drawdown-explained
- Cross-instrument limits: https://help.myfundedfutures.com/en/articles/10244682-cross-instrument-policy
