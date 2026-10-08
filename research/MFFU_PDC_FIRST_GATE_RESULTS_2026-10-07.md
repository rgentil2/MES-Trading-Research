# MFFU 50K — First funded-account gate: PDC only

**Run date:** 2026-10-07 (Colombia)  
**Status:** PDC-ONLY HISTORICAL GATE — FAIL, NOT A FULL PORTFOLIO TEST  
**Holdouts:** 2026 remained sealed.

## Source and execution assumptions

- Frozen NinjaTrader `PDCSmallGapParity` v1.0.
- User's corrected NinjaTrader Trades CSV: `NinjaTrader Grid 2026-10-07 11-44 p. m..csv`, 106 entries, 2020–2025.
- NinjaTrader reference: 2-tick slippage and 1.88 USD round-trip commissions **already deducted** in the Trades `Profit` column.
- MFFU scenario: 1.90 USD round trip for MES. Adjustment **-0.02 USD per trade**; do not subtract the full commission again.
- Historical total 591.97 USD; cost-adjusted 589.85 USD for 106 trades.
- No 2026 strategy outcome data touched.
- Comparison target: Rapid EOD 50K and Builder 50K Default; target +3,000 USD, max EOD trailing loss 2,000 USD; Rapid EOD 30% evaluation consistency, 4 minimum days; Builder one day, no evaluation consistency, daily soft pause 1,000 USD.
- MFFU one-time-payment accounts: potential closure after 7 consecutive calendar days without trades.
- **MFFU EOD max loss also checks unrealized losses intraday**; closed-trade/equity EOD is necessary but insufficient proof of compliance.

## PDC-only historical diagnostic, 2020–2025

| Measurement | Observed |
|---|---:|
| PDC trades | 106 |
| Net, original NT fees | +591.97 USD |
| Net, adjusted from 1.88 to 1.90 USD RT | +589.85 USD |
| Distinct days trading | 106 |
| Inter-trade gaps **over 7 calendar days** | 71 |
| Largest gap between trading dates | 87 days |
| Longest consecutive no-trade days between trades | 86 days |
| Maximum concurrent PDC positions | 1 |
| First modeled inactivity breach if evaluation begins with first recorded trade | 2020-04-24 |
| EOD evaluation outcome if inactivity is enforced | FAIL — inactivity |
| EOD evaluation outcome if inactivity is disabled, using entire sequence | NOT PASSED — +589.85 USD vs +3,000 USD goal |

The evaluation account opening date was not recorded; the first-trade assumption is a **diagnostic**, not a literal 2020 MFFU account history. Avoid counting overlapping positions incorrectly when NinjaTrader's minute labels produce `entry_time == exit_time`; zero-duration intervals are excluded from positive-time overlaps.

## Monte Carlo diagnostic

- **10,000 replications** per plan/scenario.
- Calendar-week bootstrap using adjacent two-week blocks drawn from 2020–2025.
- 12-month simulated horizon; fixed seed 20261007.
- Plans: Builder 50K Default and Rapid EOD 50K.
- All scenarios start at first simulated recorded trade; additional delays before the first trade are unknown.
- With seven-day inactivity enforced: 10,000 / 10,000 replications **failed inactivity**; 0 passed, for EACH plan.
- With inactivity disabled to isolate the economic objective: 10,000 / 10,000 replications **not passed**; 0 passed, for EACH plan.

**Inference:** PDC alone has insufficient trading frequency and profitability for the chosen MFFU evaluation. This is a *model diagnostic*, not an established true 0% pass probability; the historical sample was used for discovery, the MC block length is a modeling choice, and fills/correlation/intraday stop paths remain uncertain.

## Required portfolio work — not yet claimed complete

1. Need same-run access to **all three canonical, 2-tick NinjaTrader Trades rows** (PDC 106, POC 108, autonomous R072 149) for an exact synchronized 363-trade account replay. POC/R072 summaries are in GitHub, but their original Trades CSV files are not committed; don't silently synthesize entries/exits from annual aggregates. Do not re-request previously uploaded files simply to re-quote their reports.
2. Merge trades by exact entry/exit event timestamp; quantify simultaneous and opposing signals across PDC, POC and R072. Implement deterministic account-level conflict resolution; compare baseline and permitted portfolios.
3. Include portfolio-level clock-time floating equity paths from minute/tick historical series and order fills. MAE of distinct trades cannot be indiscriminately summed to claim an observed simultaneous floating-equity breach.
4. Implement MFFU evaluation drawdown threshold at EOD and monitor **floating equity against the current EOD threshold intraday**, account inactivity, Rapid 30% consistency and Builder daily soft pause.
5. Apply portfolio-level block Monte Carlo preserving correlated trading days/weeks, gaps, and skip/fill scenarios; preregister acceptance gates before opening 2026.
6. POC and R072 are **watchlist**, not funding approved. R072 four extra historical dates require RTH completeness check; 149 stop order placements audited but triggered stop execution not tested.
7. New ES/NQ research is an **independent alpha search**, not merely an increase in contract size; ES and MES share underlying exposure, as do NQ and MNQ.
8. Once full execution/risk/portfolio rules are frozen, evaluate unseen 2026 chronologically (pseudo-forward), then current market simulated execution, then funding purchase decision.

## MFFU source-of-truth links

- Rapid EOD rules: https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look
- Builder rules: https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide
- Seven-day inactivity: https://help.myfundedfutures.com/en/articles/16596524-inactivity-rule-one-time-payment-model
- Open-equity drawdown: https://help.myfundedfutures.com/en/articles/8348565-end-of-day-eod-drawdown-explained
- Commission: https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list

**Gate:** PDC alone = **FAIL for MFFU 50K**, not a conclusion about the complete three-strategy or future multi-instrument portfolio.
