# ES POC + R072 transport — preregistered fixed rules

**2026-10-08. No ES 2025/2026 outcome data inspected.** Development transfer of MES-selected strategies is a **diagnostic**, not independent OOS confirmation.

**Source:** 20 individual ES quarterly Minute Last contracts MAR20–DEC24, DoNotMerge / non-back-adjusted, original SHA256 verified, UTC to New York timezone, exclude incomplete 390-bar RTH sessions and crossover rollovers. Preserve overnight bars for causal R072 H017. ES 2025 candidate validation and ES/MES 2026 final pseudo-forward SEALED.

**POC frozen import:** prior completed-session 0.25 HLC3 volume-weighted price-bin profile, same-contract previous POC, current RTH open higher than prior POC, first touch must close below, SHORT at next minute open, horizon 15min, ATR14(previous completed RTH) protective stop **0.45x**.

**R072 frozen import:** original causal dynamic HIGH state from 15min blocks and rolling past-60 same-block q20/q80, H017 LOW override, wick 0.50, first eligible setup/session, 11:00 ET cutoff, 30min exit; previous ATR14 protective stop **0.70x**. Direction upper-wick-reversal LONG, lower-wick-reversal SHORT, consistent with existing NinjaScript.

**Execution stress:** next-bar opening fill with 2 adverse ticks; catastrophe stop first on ambiguous candle and stop market slippage; timed market exit at next-bar open after H15/H30 signal clock; ES $4.68 RT, MES same ES-derived signals $1.90 RT. Stops rounded up to valid 0.25 tick increments. Neither sizing mode adds independent trade signals.

**Known nonparity:** archived USD medium/high economic news CSV isn't tracked; **no news blackouts or forced news exits**. Do not claim exact NinjaTrader parity. Minute OHLC lacks tick order book and stop-through-gap certainty.

**Before running commit:** report per-strategy and joint standalone signals, annual PnL 2020–24, counts, closed DD, PF, per-trade risk size median/p95/max, seven-day gaps, and note correlations and overlapping positions. Do not introduce post-hoc parameter changes, year selection or 2025/2026 outcomes. Every favorable result = RESEARCH ONLY.

**MFFU test criterion:** ES nominal stop >$500 is concerning when account loss cushion is $2,000. Contract maximum count and floating loss across S&P/Nasdaq must be enforced centrally. Current PDC ES transport failed MFFU activity and robustness.
