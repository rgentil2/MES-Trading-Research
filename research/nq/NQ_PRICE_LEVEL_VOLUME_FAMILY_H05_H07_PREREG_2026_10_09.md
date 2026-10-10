# NQ H05–H07 — Preregistered price-level and volume mechanism family

Status: **PREREGISTERED, NOT YET TESTED**. Logged 2026-10-09 BEFORE opening 2020–2024 outcomes for H05–H07. Single planned family with exactly 3 primary directional hypotheses; both long/short directions, 15m/30m horizons and all eligibility restrictions count as one declared family. Prior NQ H01–H04 attempts remain in the accumulated search ledger.

## Scientific objective and data

Study whether *price interaction with objectively known support/resistance levels* predicts a signed +30-minute NQ movement with positive net USD effect after Free-plan charges, without redefining thresholds based on results.

Source **NQ** individual quarterly 1-minute OHLCV contract files from uploaded NinjaTrader ZIP, with ZIP member paths containing **/development_2020_2024/** and matching strictly `NQ_(03|06|09|12)-(20|21|22|23|24|25)_20(20|21|22|23|24)_Minute_Last.txt`. ZIP member **2025 and 2026 file contents MUST NOT be opened**. No MNQ prices opened. These are **reused development years**, and results are therefore exploratory even if q is small.

Select precisely one non-back-adjusted quarterly contract per ET session using the existing fixed roll rule (Thursday eight calendar days before the quarterly third Friday), with strict contiguous 390 one-minute end-labelled 09:31–16:00 RTH. Reject incomplete sessions. Prior-day H/L is from the **last previous complete eligible RTH session**, provided its calendar distance is **<=5 days**. Warm-up for volume H06: **20 preceding complete eligible sessions**. Past-only overnight reference H07: ET **18:01 prior calendar day through 09:30 current day**, >=800 source minute bars for that same selected contract, high and low known by 09:30. Data source no-lookahead, NY DST aware.

## Primary hypothesis rules (ONE earliest event per hypothesis per session)

All signal bars are **09:46–11:00 ET**, known at the minute EOB close; a trade direction is defined causally, and entry is next-minute OPEN. Skip bars with both upward and downward conditions true rather than deciding retrospectively. There is **no news-event exclusion** in this diagnostic, to be added only to later executable-strategy validation.

- **NQ-H05 — Prior RTH high/low wick sweep rejection**: on an eligible scan bar, high >= prior-full-RTH high + **1 tick (0.25 NQ point)** and close strictly below the prior high -> SHORT; or low <= prior-full-RTH low - **1 tick** and close strictly above the prior low -> LONG. Exclude both-sided qualifying bars as ambiguous, without looking for a later eligible bar that day. First qualifying scan bar only. Mechanism: prior support/resistance liquidity sweep should reject and reverse.
- **NQ-H06 — Prior RTH high/low accepted break with volume**: two consecutive fully finished scan bars close strictly above previous RTH high (LONG) or below previous RTH low (SHORT). The second close must have minute volume >= **1.25 × median at the same minute clock** over the **previous 20 complete eligible RTH sessions**, regardless of contract; median computed strictly from past sessions. First qualifying bar only. Mechanism: volume-confirmed prior-day level acceptance should continue.
- **NQ-H07 — Overnight high/low first breakout rejection**: between 09:31 and 11:00 ET identify the **first** bar whose HIGH >= overnight high +1 tick OR whose LOW <= overnight low -1 tick. If both breach on that first bar, no trade for that session. If breach occurred before 09:46, no trade for that session. Once first breach occurs between 09:46 and 10:57, require a **close strictly back inside the same breached overnight boundary within the current bar or next 3 completed one-minute bars, at the latest 11:00**; signal at first reclaim, side opposite the breach (sweep above overnight high -> SHORT, below overnight low -> LONG). If the first breach has no reclaim within 3 bars, no later attempts that day. Mechanism: failure of initial overnight-level breakout predicts reversion.

All level values are observed before the signal; the first breakout condition consumes the day even when unprofitable. Thresholds above are not retrospectively optimized.

## Prespecified outcomes, fees and inference

Primary: directional next-open entry and exactly **+30 minutes** later open exit (signal-index i: entry bar i+1, exit bar i+31); secondary **+15 minutes** (exit i+16), with valid continuous RTH only. **NQ Free all-in fee = $2.87/side = $5.74 round trip**, plus **2 adverse 0.25-point ticks on entry and 2 on exit**, i.e. $20 adverse market-price slippage for a one-contract NQ at $20/point. **Total modeled friction = $25.74 RT**. Nominal mechanism USD = side × (exit_open - entry_open) × $20 - $25.74. If signal cannot complete full 30 minutes, exclude it as non-executable, with reasons. No stops, targets or actual market orders: *this is NOT a deployable backtest*. Sensitivity **+1 additional tick per side**, equivalent to -$10 per event.

Primary statistic: event mean net USD and effect direction. First one signal per day/hypothesis (days and hypotheses are correlated, don't pretend independence). For each hypothesis:
- N eligible signals (exploratory target **N > 150**, 151 minimum);
- mean signed net >0, and 90% CI of mean net strictly >0; also report 95% CI;
- one-sided calendar-week sign-flip p (10,000 replicates), *weekly block bootstrap* 90/95% CI of event mean (10,000 replicates), deterministic **seed 20261009**;
- BH q across **all three** preregistered H05–H07 primary p-values, exploratory q <=0.10; ALSO report BH adjustment across accumulated H01–H07 using the original four prior p-values for transparency (not independent confirmation);
- >= **3/5 development years** have positive annual net mean, with all five years included;
- no retrospective subgroup rescue. Also report PF, win rate, 15m stress and calendar gaps for descriptive strategy-screening only.

The **whole-family prospective Holm and nonrecyclable alpha control** of `research/RESEARCH_CONTROLS_POLICY.md` remains required for any formal confirmatory claim. This exploratory exercise is on repeatedly investigated 2020–2024 data: small p/q or 90% CI alone **cannot** establish independent discovery.

Decision tiers: only `PROMISING_EXPLORATORY`, `NOT_SUPPORTED_EXPLORATORY` or `INSUFFICIENT_EVIDENCE`. Any exploratory pass requires a wholly independent and properly preregistered 2025 confirmation after a candidate freeze, plus SL/TP, news and realistic fill before touching the final 2026 pseudo-forward. Do not automatically open 2025 or 2026.

## Reproducibility

Runner planned: `research/nq/nq_h05_h07_level_volume_screen.py`. Version + SHA must be retained. A source-only test suite must validate ZIP allowlisting, NY time convention, deterministic first-break/no-retry behavior, and cost calculation before outcomes are loaded.

Experiment has no directional empirical results in this preregistration; its parameters must not be edited after the first outcome run.
