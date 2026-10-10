# Instrument focus: NQ-first joint strategy research (prospective 2026-10-10)

**User direction:** prioritize **NQ** instead of **MNQ** as the main instrument in the ongoing H79-H150 deductive multi-component strategy search, to evaluate whether the full system can exceed the user's 15% annual return target and matched VOO/QQQM benchmarks.

This is an **additive research priority**, NOT a retroactive edit of H01–H78, the original strategy rules, pre-registered testing families, the locked holdouts or the existing Gate 1 and family-wise Holm budgets. NQ is the **primary instrument to design and backtest**, not a mandate to trade 1 NQ despite funding risk. MNQ is retained as a **sizing/contingency instrument** and a useful cost/risk comparator.

## Why we changed the focus

- Dollar value: NQ US$20/index point vs MNQ US$2/index point, so 1 NQ has tenfold **gross directional exposure** compared with 1 MNQ, with commensurately larger adverse P&L.
- Controlled mechanical diagnostic, reusing **frozen** 2020–2024 one-MNQ theoretical NQ-minute-bar trade paths and applying NQ historical NinjaTrader Free assumed friction US$25.74/round trip (vs MNQ US$3.88):
  - **H69 1 NQ:** net +US$30,466.12, nominal 50k five-year equivalent CAGR **9.98%**, closed DD **US$8,214.22**.
  - **H74 1 NQ:** net +US$18,302.32, equivalent CAGR **6.44%**, closed DD **US$4,179.80**.
  - **H77 1 NQ:** net +US$25,681.40, equivalent CAGR **8.64%**, closed DD **US$5,414.42**.
- **None** exceeds the 15% net CAGR target, and **all seven** rescaled systems breach the illustrative US$2,000 closed-equity loss cushion for the studied funded 50k product. Floating-equity drawdown may be worse. The 50k nominal account size is not the amount of the user's own invested capital. ETF total-return series have not yet been loaded for a matched comparison.
- This is a **descriptive execution size change**, not an out-of-sample validation, new predictive mechanism, or evidence that a mini is inherently more profitable at equal risk. Historical 2020–2024 is extensively reused; 2025/2026 remain sealed.

## Binding rules for future *new* joint hypothesis families H79–H150

1. **Freeze NQ as the primary execution test instrument** and use point value US$20, with NQ-specific commission, adverse slippage, stop/TP and the actual chosen venue's fee model frozen before viewing a new outcome.
2. **First specify a joint mechanism that improves edge and/or risk at equal capital/risk** rather than assuming tenfold scaling is the improvement. State parent hypotheses, past defects, expected *incremental* effect, ablations, no-trade rules, causal router and conflicting-signal resolution.
3. Compute each candidate's actual **technical stop distance in NQ points** and gross/total dollar risk for a minimum 1 NQ. Compare to a **preregistered per-trade dollar risk cap** and the target account's **real current trailing-equity loss cushion**, contract restrictions and payout terms. When 1 NQ breaches the cap, mark **NQ_NOT_FEASIBLE_FOR_SELECTED_FUNDED_ACCOUNT**, do not override risk to force a higher CAGR. Compare scaled MNQ or a different appropriately capitalized account separately.
4. Include **closed and intratrade/floating equity** drawdown under an explicit first-hit fill/order assumption, stress 1.5x realistic transaction costs, gap/stop slippage and peak-to-trough equity. One-minute OHLCV and NQ hypothetical price paths **do not establish actual order execution**.
5. Apply the economic Gate to a **complete jointly executed strategy/portfolio**: net nominal equivalent CAGR strictly greater than max(15%, matched VOO/QQQM USD dividend-reinvested total-return CAGR), with equal dates, risk adjusted comparisons, non-duplicated positions and separate actual personal funded-account cashflow ROI.
6. Continue scientific search only through full family preregistration, source freeze and unaltered Gate 1/multiple-testing policy. H69/H74/H77 remain exploratory comparators with both favorable and unfavorable records; never select favorable years as a "new holdout".
7. **2025 sealed** until explicit authorization to validate a completely frozen candidate, and **2026 sealed** until the complete execution strategy and risk router are fixed. No purchase/live-trading approval follows from this research preference.

**Technical report:** `research/nq/NQ_VS_MNQ_EXECUTION_TRANSFER_DIAGNOSTIC_2020_2024.md`, with audited aggregation `results/nq_h73_h78/NQ_vs_MNQ_TRANSFER_2020_2024_AGGREGATE.json` and reproducible diagnostic script `research/nq/compare_execution_nq_mnq_2020_2024.py`. Raw per-trade ledgers remain private.

**H79 onward is NOT preregistered yet.** Formulate next family from the outcomes H69/H73-H78 under these NQ-first and risk-first principles, before any new development price outcome read.
