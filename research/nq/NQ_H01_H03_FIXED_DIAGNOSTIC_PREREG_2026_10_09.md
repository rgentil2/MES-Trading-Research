# NQ first diagnostic — H01/H02/H03 detailed preregistration

**Committed BEFORE inspecting NQ 2020–2024 hypothesis outcomes**, 2026-10-09. Original four NQ hypothesis families already established in `NQ_2020_2024_RESEARCH_PREREG_MFFU.md`. **This prereg does not assert any edge.** 2025/2026 holdout data inaccessible to the analysis.

## Data

Use NQ `Minute Last` RTH, original operator ZIP, only UTC-year DEV partitions (2020–2024). Fixed Thursday 8 days before the third Friday of quarterly expiration chooses the sole eligible contract per local ET day. Only complete consecutive 390 one-minute bars labelled 09:31..16:00 ET. No minute interpolation, no selecting dates for P&L, no lookahead. +15m supplementary and +30m primary horizon. The UTC-year ZIP folders labeled 2025/2026 **must not be opened**. Use 2020–2024 development for exploratory effects and yearly results, not independent OOS.

## Exact causal triggers; maximum first one per strategy per trading day

- **NQ-H01 ORB acceptance:** OR=RTH bars labelled 09:31..09:45; from 09:46 through 11:00 ET, first bar `close > OR_high` (LONG) or `close < OR_low` (SHORT) whose current one-minute volume >= **1.25 × median volume at same minute clock of prior 20 full eligible sessions**. Previous 20 full RTH sessions must exist. No subsequent-information acceptance filter.
- **NQ-H02 ORB failed break:** first close outside the same OR between 09:46..10:55. Within the following **five completed one-minute bars** (not beyond 11:00), a close strictly inside the OR bounds establishes a reversal: trade opposite direction of first breakout. If first breakout has no such rejection, do not seek a second breakout. No volume threshold.
- **NQ-H03 VWAP mean reversion with low efficiency:** between 10:00..11:00 ET, calculate causal cumulative session VWAP up through current minute from OHLC typical price × traded Last volume; absolute `close-VWAP` must exceed the **80th percentile of absolute same-clock displacement in prior 20 eligible sessions** (all past). Efficiency ratio for last 15 completed one-minute close movements `abs(close[t]-close[t-15]) / sum(abs(diff(close[t-15:t])))` <= **0.30**. First signal/day, trade against current signed deviation. If denominator 0, no signal.

Entry for all at next minute **OPEN**, two adverse ticks of NQ slippage on entry and two adverse ticks on exit. Primary descriptive exit is the OPEN exactly 30 minutes after entry; +15 minute equivalent secondary. Intraday futures NQ multiplier **$20 / point**, NQ fees $4.68 round-trip; net effect `side*(exit_open - entry_open)*20 - $24.68`. No protective stop/TP yet: **not a tradable strategy P&L**, merely a directional mechanism diagnosis and a lower-quality market-order fill model. Tick execution/news filter not modeled.

For no-signal or incomplete 30m path, do not synthesize trades. Report number of independent first signals, yearly count/net, expectancy, positive years, PF (on costed horizon P&L), predeclared week-block bootstrap 95% CI of average net effect, and joint BH q-values among H01/H02/H03. Include sensitivity +1 tick per side (subtract extra $10 / event) and note `H04` untested until overnight context is reconstructed; no data mining of thresholds.

No profitable in-sample result authorizes 2025 opening, portfolio inclusion, or purchase of MFFU. A candidate would next require meaningful economic edge, stop/TP specification, time-of-day, news and robustness under walk-forward. Pre-register later workflow separately.
