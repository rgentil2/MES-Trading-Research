# MFFU MES 50K — First 1-minute floating-equity risk audit

**Date:** 2026-10-07 (Colombia)  
**Status:** 1-minute floating-equity replay PASSED DATA ALIGNMENT, **NOT APPROVED FOR FUNDED TRADING**  
**Holdout:** 2026 SEALED. No prices or strategy outcomes for 2026 inspected.

## Provenance

- 363 NinjaTrader MES trades: PDC 106, POC 108, R072 149.
- Canonical NinjaTrader CSV exports are tracked in `research/mffu/inputs/`.
- 2020–2025 historical MES source prices from quarterly `data/raw/MES *.Last.txt`; the MAR26 quarter is streamed only up to a strict **2026-01-01 00:00 UTC** cutoff so late December 2025 data can be included, with no 2026 price rows read.
- Frozen NinjaTrader fills modeled with **2 ticks of slippage**, fee amended from **$1.88 RT to MFFU $1.90 RT** by deducting only **$0.02 extra per fill**.
- Data preparation preserves the project's documented non-back-adjusted implicit-contract rollover; **no artificial bars**.
- Evidence: [GitHub Actions run 37730289884](https://github.com/rgentil2/MES-Trading-Research/actions/runs/37730289884), artifact `mffu-mes-floating-2020-2025`.
- Reproducible script: `research/mffu/mes_intraday_floating_audit.py`; five green unit tests in `research/mffu/test_mes_intraday_floating_audit.py`.

## Critical timestamp reconciliation

A first-pass entry-to-price comparison erroneously chose the raw candle labelled `NT_entry+1 minute`: median absolute deviation **1.75 index points**, with 82 trades deviating over three points. The time-alignment audit compared nearby open/close labels without changing any signal or trading parameter.

**Correct** entry-price reference is the **OPEN of the raw candle with the SAME end-of-bar timestamp as the NinjaTrader exported entry**. With that convention:
- 363/363 corresponding entry candles found;
- median and 95th-percentile absolute difference: **0.50 index points**;
- **0** entries deviate by more than three points, consistent with the configured two-tick slippage;
- full 325/325 active trading days have usable minute-by-minute bar paths during holding intervals.

Minute-path exposure uses candle labels `entry <= t < exit`. This avoids mistakenly treating the minute **after** historical exit fills as part of an open position.

## Portfolio results — original 363 signals (1 MES per signal)

| Measure | Modeled historical result |
|---|---:|
| Backtest signals | 363 |
| Trading dates | 325 |
| Net historical realized P&L, MFFU fee adjusted | **+$1,897.80** |
| Worst peak-to-candle-adverse floating-equity snapshot | **$744.35** |
| Minimum modeled floating-equity **buffer above existing MFFU EOD trailing floor** | **$1,311.90** |
| Date of minimum threshold buffer | 2022-01-27 10:16 ET |
| Modeled minute-bar adverse equity threshold touches | **0** |
| Missing 1-minute paths inside positions | **0** |
| Inactivity gaps > seven calendar days | **91** |
| Maximum closed-equity profit in 2020–2025 | **+$2,504.45** |

The hypothetical router rejecting opposite MES exposures (PDC→POC→R072 priority, **diagnostic only**) retains 362 trades, **+$1,947.20** realized net, identical worst buffer and floating adverse excursion, and zero modeled threshold touches. The improved P&L is merely the consequence of rejecting an in-sample losing POC short, not an independently validated rule.

### What this means

In this historical **minute OHLC** diagnostic, the one-MES basket does not appear constrained by the **$2,000 EOD trailing maximum-loss floor**: its minimum observed risk buffer remains positive. But the **seven-day inactivity gate fails** and the **+$3,000 evaluation goal is not reached** even across the entire 2020–2025 realized sequence. It is therefore **not a viable MFFU-funded configuration**.

The risk buffer is **not** a guarantee of live funded-account compliance. It does not simulate tick sequencing of a stop trigger, stop-market slippage during a gap, rejected orders, outages, evaluation resets, variation margin, or alternative correlation/execution conditions. The computed `$744.35` is a peak-to-adverse **snapshot model** and not a definitive executable account drawdown.

## Four new R072 sessions: raw RTH availability

| Date | Entry→Exit, ET | RTH bar count | Missing relative to full 390 | Interpretation |
|---|---|---:|---|---|
| 2021-11-26 | 09:46→10:16 LONG | 225 | 165 after 13:15 | Shortened Thanksgiving-week session; confirm official market-close schedule |
| 2022-05-23 | 10:01→10:31 LONG | 389 | 12:58 | Missing is **after** exit |
| 2024-08-02 | 09:46→10:16 SHORT | 382 | 11:55–12:02 | Missing block is **after** exit |
| 2025-04-04 | 10:32→11:02 LONG | 389 | 10:00 | Missing is **before entry**, potentially affects computed signals/features |

These sessions are missing from the original 390-bar Python-eligible universe. Missing minutes do **not** coincide with the four recorded position holding windows, but eligibility/indicator completeness and shortened-session rules remain unresolved. This audit **does not reinstate** the four trades as externally validated events.

## Decisions and next gates

**Stage A 1m accounting:** complete, **descriptive-only**.  
**Funding gate:** FAIL for current 1-MES basket due to economic goal and activity constraints.

1. Preserve 2026 untouched. Do not retroactively change signal parameters, stop ATR multiples, or trade priority to rescue performance.
2. Investigate 2025-04-04 missing 10:00 input and shortened holiday rules. Compare R072 signal-feature prerequisites, not just whether gaps overlap trades.
3. Additional tick/stop order and correlated intraday exposure shock testing are still required; backtests do not prove live fills.
4. Expand independent alpha discovery with ES/MES and NQ/MNQ. ES/MES and NQ/MNQ are **size families**, not separate sources of uncorrelated alpha. New strategies must first pass unbiased within-development holdouts, cost stress and plausible signal frequency.
5. Once a full portfolio and deterministic risk router are specified, run block Monte Carlo with stress, freeze all rules, **then** open 2026 chronological pseudo-forward **once**; subsequently live simulator and only then purchase a funding evaluation.

## Links

- Existing combined historical replay: `research/mffu/MFFU_363_TRADE_FIRST_REPLAY.json`
- Existing 10,000-path bootstrap: `research/mffu/MFFU_363_MONTE_CARLO_BLOCKBOOTSTRAP_10000.json`
- Cost sensitivity: `research/mffu/MFFU_PORTFOLIO_COST_SENSITIVITY.json`
- Risk audit GitHub Action workflow: `.github/workflows/mffu-mes-floating-audit.yml`
