# S0.60 — V5 ATR mode 1, real NT8 709-trade CSV audit (2026-11-02)

Source: user-provided Strategy Analyzer screenshot and exported trades CSV; raw CSV remains user-provided, not uploaded to GitHub. SHA256 original CSV: `5e8f17cd3de979d5ffc5e69005362fe39d716b0854056e96370501ccc84f4a62`.

## Historical experiment

`NQNativeGeneticLabV5` ExitMode=1; ATR period=14, ATR stop x10=15 (1.5 ATR), target=32 fixed ticks, StopTicks=20 unused in mode1. Same Count2 A0n12 B7n14 AND; Reverse0, maxDaily2; NQ Last M1 IST 2020–22, native Standard fill and 2 slippage ticks.

## Cross-checked against all 709 exported trades

- 709 trades; 519 longs / 190 shorts, 415 winners / 294 losers, win 58.53%.
- Net **-US$11,373.84**, PF **0.85**, max closed DD **US$14,856.72**, commission **US$4,083.84** (= 709 × US$5.76), gross profit US$63,014.60, gross loss -US$74,388.44, average trade -US$16.04. CSV sum net, commissions and last cumulative profit all match screenshot.
- Exit names: **406 Profit target**, all **exactly +32 ticks** and net +US$62,621.44; **283 Stop loss**, all unfavorable, **35 different stop distances from -9 to -57 ticks**, total net -US$73,330.08; **20 timed exits EXIT_1129_L 15 / EXIT_1129_S 5**, combined net -US$665.20.
- **121 stop-market fills worse than 55 ticks from realized entry price**, with largest -57 ticks. **This is consistent with up to 55-tick intended stop + 2-tick NT8 historical slippage** (NT8 official help: historical slippage applies to stop-market). At 57 NQ ticks × $5 plus $5.76 commission, largest observed loss **-US$290.76**, below provisional $300 per trade. DO NOT claim exact ATR stop submitted for every trade: exported CSV lacks ATR values and intended stop offsets; need logging/intended stop vs realized to prove per-trade math.
- No simultaneous open trades found, no calendar date more than 2 entries; 29 trading dates with one entry and 340 dates with two. Earliest entry **09:50**, latest entry **11:28** (consistent with 11:27 signal + next-bar fill), latest exit **11:29**; zero exits after 11:29. Zero negative trade durations.
- Annual net / entries: 2020 **321 / -$4,288.96**; 2021 **327 / -$6,668.52**; 2022 **61 / -$416.36**. **9 of 36 months have fewer than five entries**; 2020 March, 2022 March, April and October have zero. Investigate later whether source is vol/ATR risk cap, indicator effects or data issues; no unsupported causal claims.
- **G0 FAIL:** net negative, PF0.85 <1.25, max DD $14,856.72 >$2,000, some months below frequency target. Trades>=150 pass but no finalist; floating DD/MFFU rule not yet modeled. Holdouts 2023+ remain sealed.

## Conclusion and next native check

Mode1 demonstrates a working historical fixed TP and variable stop family with time flattening, plausible slippage and consistent commission accounting. It is **not** an edge, not proven exact ATR per trade, not a funded-account compliant risk model, and not proof against live fills. Do not change guardrails just to improve backtest.

Next: Backtest **ExitMode=2** with same signal genes, ATRPeriod=14, ATRStopX10=15, ATRTargetX10=25, same fees/data/session, then send Summary and exported Trades. In mode2 both favorable target tick distances and stop distances should vary. Then test mode3 (ATR stop, no TP) and confirm no Profit target exits. Keep 2023–26 unopened.
