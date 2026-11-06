# NQ S0.75 — V15 Chronological Risk + Train-Only Walk-Forward
Date: 2026-11-06 | Research implementation, not authorized for live/funded trading

## Mandatory user workflow

**ONE final NinjaTrader 8 validation only, once the complete StrategyQuant-equivalent system is integrated.** No interim NT8 compilation, screenshots, exports or 20-candidate runs are requested. All interim QA runs in GitHub Actions using controlled synthetic M1 data.

## What V15 actually implements

### 1) `NQNativeWalkForwardV15.cs` — temporal segregation

- 2020–2022 is **development** only. Native year lock forbids any 2023+ observation in the generator. 2023–24 external validation and 2025–26 final holdout remain completely untouched and cannot be claimed tested without those data.
- Four chronological rolling folds with default **12 months training / next 6 months validation / move 6 months**:
  1. Train 2020-01 to 2020-12; test 2021-01 to 2021-06.
  2. Train 2020-07 to 2021-06; test 2021-07 to 2021-12.
  3. Train 2021-01 to 2021-12; test 2022-01 to 2022-06.
  4. Train 2021-07 to 2022-06; test 2022-07 to 2022-12.
- Genetic evaluation callback sees **only trainCache**. Winner's 20 genes and canonical ID are fixed **before** next validation period is opened.
- Segment-local ranking computes each fold's own net PnL, PF, closed DD and months below five trades; does **NOT** interpret a 12-month training sample as meeting the **full 36-month V7 G0 rule**. PeriodPass is a preliminary local screen, not a funded-account acceptance decision.
- Source quality: sorted year-locked data, **all 120 contiguous 09:30–11:29 Eastern-time M1 bars per observed session**, and at least 15 such sessions per calendar month by default. Not yet exact exchange-day, rollover, time-zone or contract consistency validation.
- CI injects a large adverse trend in the **final Jul–Dec 2022 validation period** and verifies all four training selections and scores stay **bit-for-bit unchanged**. This is an explicit no-lookahead test.
- Repeated external validation 2023–24 must eventually use **frozen** model selection logic. The true final 2025–26 holdout must not be queried for optimization/tuning.

### 2) `NQNativeHistoricalEvaluatorV12.cs` — executed fill receipts

- For each closed simulated V12 trade, export a detailed **immutable `NQExecutionFillV12` row** (entry/exit timestamps, side, quantity, fill prices and the same fees used in the original cash PnL).
- Original V12 objective, trading guards, protective stop/target, slippage, chronological 11:28/11:29 flat and V9 fitness remain untouched.
- 2020–22 source restriction remains; this is still conservative M1 **OFFLINE** fill estimation, not the proprietary NT8 engine.

### 3) `NQNativeChronologicalRiskV15.cs` — actual account chronology *at M1 resolution*

- Merge all strategies' detailed execution receipts into chronological positions on the original M1 OHLCV source. Each source bar provides a realized-equity point, a **close-marked floating equity**, and a conservative **same-minute favorable-before-adverse high/low envelope** for open positions.
- Calculate chronological max closed DD, max close-marked open-equity DD, adversarial peak-to-trough proxy DD, worst session loss, number of overlapping NQ contracts, worst concurrent adverse PnL exposure, and whether proxy **$1,000 daily pause** / **$2,000 account stress loss** caps are breached.
- Any missing minute while a position was open, missing fill timestamp, impossible side/quantity, cross-session position, 2023+ data or unclosed position fails closed.
- Important: this **is not** true chronological sequencing *inside* each minute, not a tick or order-book reconstruction, not a certified MFFU account trailing drawdown engine, not a true intrabar replay. When both bar high and low might be reached, the model assumes the unfavorable sequence for stress and labels the output as a **proxy**.

### 4) `NQNativeIntegratedPortfolioRiskV15.cs` — do not approve a portfolio on closed metrics alone

- Requires V13's 3–5 distinct candidates to meet historical cost stress, bootstrap, 36-month frequency/Profit Factor and diversification/closed-DD gates **first**.
- Candidate's per-trade V13 net/timestamp must reconcile with detailed V12 fill receipt to within 3¢; duplicate IDs or inconsistent prices fail closed.
- For candidates selected by V13, join actual 2020–22 execution receipts; require V15 chronological risk to pass the **same combined** portfolio and reconcile portfolio net with actual summed fills.
- The combined result is **PROVISIONAL**. It does not certify any NinjaTrader fill, live-safe account rules or real historical profitability.

## C# CI tests

Workflow: `.github/workflows/nq-v15-risk-walkforward-qa.yml`.

1. **Chronology**: two overlapping positions and 120 bar-by-bar account marks; a synthetic minute low shock produces a $2,936 adverse DD and breaches both provisional thresholds. A V12 simulated strategy with two complete fills reconciles **exact dollar realized net** with the V15 ledger; null/unknown direction/OOS 2023+ and a missing minute while position open are rejected.
2. **Train-only genetics**: 36 months of deterministic synthetic morning bars; four 12m/6m folds, 88 unique training evaluations, deterministic replay, unchanged training winners when *only* Jul–Dec 2022 is altered, invalid day/Month/OOS guards. The synthetic outcome of four positive folds is NOT market profitability.
3. **Integrated portfolio**: three 360-trade synthetic V13 candidates, each with detailed 1-contract receipts; base synthetic prices permit the combined 3-strategy provisional risk gate to pass. Replacing only a concurrently observed bar low with a large adverse shock must cause **V15 rejection while V13 closed metrics remain unchanged**. Tests corrupt fill price and correlated clone rejections.

## Important limitations before final NinjaTrader validation

- No full real 2020–22 NQ M1 bars or 2023–26 held-out data in GitHub. **No empirical NQ WF PnL or real portfolio quality has been established.**
- No native NT8 Windows simulator parity. Existing source-strategy import remains unverified against the actual vendor libraries.
- Native NT8 `RunIteration()` does not expose a supported synchronous numeric return. The custom GA's actual live NT8 optimizer feedback bridge remains unimplemented. Current V15 WF uses the independently implemented V14 offline M1 scoring engine.
- Real 100k candidate throughput on millions of contract-adjusted bars, tick-level fills, MFFU trailing-drawdown mechanics, data consistency, market-regime robustness and final production import/strategy deployment checks are still pending.
- **132 directional conditions ≠ 132 independent indicator formulas**.

## Project status

V10–V15 source is saved in **stacked draft pull requests** with tested CI. Never merge to deployment or run in funded/live mode without completing the missing gaps and a single final end-to-end NinjaTrader 8 validation.
