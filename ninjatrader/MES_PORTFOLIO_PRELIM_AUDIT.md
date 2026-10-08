# MES — Portfolio, stop and data-quality audit (preliminary)

Analysis: 2026-10-07. **2026 remains sealed. No parameter optimization conducted.**

## Portfolio input versions
- **PDC**: 106-trade Stage 2 zero-friction parity trade export for ENTRY/EXIT TIMING; separate historical Stage 3 2-tick NinjaTrader summary **NET +$591.97** with $1.88 RT commission included. The individual 2-tick PDC trades are NOT yet available.
- **POC**: 108-trade 2-tick, $1.88 RT net trade export (NET +$314.46).
- **R072 autonomous**: 149-trade 2-tick, $1.88 RT net trade export (NET +$998.63). Python H017 and eligible-session CSVs OFF, news/rollover ON.
- Total across separate Strategy Analyzer runs: **363 trades; +$1,905.06 net** over 72 months (about $26.46/month). This is **NOT** a synchronized portfolio backtest; joint trailing intraday DD cannot be inferred.
- Previous PDC notes had subtracted NinjaTrader commissions a second time; corrected PDC document in `ninjatrader/PDC_V1_FREEZE.md`. Do not use the old $392.69 number as PDC stressed net.

## Frequency and exposure from ENTRY/EXIT timestamps
- 363 operations = **5.04/month on average**. Median calendar month 5; **40/72 months** had >=5 trades, 1/72 months zero.
- 325 distinct trading dates with signals; 36 dates with >=2 strategies active, 2 dates with all 3 generating trades.
- Date-matched pairs / interval overlaps: PDC-POC 18 / 7; PDC-R072 10 / 1; POC-R072 12 / 2.
- Across the 363 historical records, **maximum 2 concurrent positions**, during 10 dates; no 3-way simultaneous overlap seen.
- Overlap involving PDC uses its **zero-friction** Stage 2 exit timestamps, so exact 2-tick portfolio overlap must be rechecked when the 2-tick PDC Trades CSV is supplied.

## Synchronized subportfolio with fully comparable 2-tick Trades CSVs: POC + R072
- 257 trades, **+$1,313.09 net**, close-to-close realized running-peak drawdown **$581.43**; this DD ignores adverse excursions on open trades and is NOT an intraday risk metric.
- Annual net: 2020 -$165.12, 2021 +$64.70, 2022 +$699.14, 2023 -$33.32, 2024 +$1,054.78, 2025 -$307.09.
- **2024 accounted for 80.33% of their combined net**. Without 2024, combined POC+R072 net was **+$258.31** for the other five years.
- 257 trades = **3.57/month** average, median 3; 3/72 months zero and 24/72 months >=5.
- Same-day POC/R072 overlap 12 days; actual simultaneous 2 days.

## R072 catastrophe stop, code-level and historical excursion audit
- NinjaScript uses `SetStopLoss(signal, CalculationMode.Ticks, ceil((0.70 * atr14_prev) / TickSize), false)` **before** the corresponding `EnterLong/EnterShort`.
- If the ATR is missing or <=0, signal entry is skipped (when stop feature ON).
- Matched 145/149 R072 autonomous trades against frozen Python 145-signal ATR records. Four new NinjaTrader-only dates do not have a matched reference ATR.
- For 1 MES ($5/point, tick size .25): **computed nominal SL distance** for 145 original trades: min **$110.00**, median **$207.50**, mean **$232.37**, max **$682.50**; **22/145 >=$300**, **5/145 >=$400**.
- **0/145 MAE values** in exported 2-tick trade data reached their individual calculated distance to the nominal stop; maximum ratio MAE/theoretical stop distance ~0.91.
- Exit names for 149 trades: **137 time / 12 news / 0 stops**.
- This is consistent with the lack of stop fills. It does **NOT** prove that historical stops were working orders: NinjaTrader Strategy Analyzer **Orders export/order-state audit** is required. It also does not prove ATR parity between the NinjaTrader-computed ATR and Python ATR for all 145 dates.
- A 0.70 ATR stop can be wide relative to a funded-account trailing DD and may suffer slippage beyond its nominal threshold.

## R072 extra sessions without historical Python completeness eligibility
- 2021-11-26: LONG (US Thanksgiving week / altered holiday schedule), net 2 ticks -$100.63.
- 2022-05-23: LONG, +$84.37.
- 2024-08-02: SHORT, +$311.87.
- 2025-04-04: LONG, -$61.88.
- These four collectively +$233.73 net; date list absent in 1457 eligible-session Python CSV.
- **Data-quality not yet resolved:** must audit source 1-minute RTH bar completeness and CME holiday schedule before treating these as portable trading opportunities; the first date is notably a modified US Thanksgiving session.

## Decision
- **No strategy is newly approved for live funding.**
- Preserve frozen PDC v1.0 parameters, do not optimize POC or R072 on 2020–2025 results.
- The three-strategy collection just meets the aggregate monthly-trade count but still needs risk gating; positive net is financially modest versus research effort and uncertain intra-trade DD.
- 2026 remains SEALED pending a preregistered frozen production candidate.

## Exact next actions (no new parameter optimization)
1. Export **PDC 2-tick Trades CSV** from Strategy Analyzer so total three-strategy realized net equity, overlap and closed-trade DD can be computed without approximating PDC fills.
2. Export **R072LiveEngineParity historical Orders** in stop-enabled 2-tick run; verify presence, price, quantity, status/cancellation of protective `Stop market` order for all entry fills. If not available, add instrumented OnOrderUpdate/OnExecutionUpdate logging solely in a separate diagnostic build.
3. Audit 1-minute bars for four extra sessions (09:31–16:00 ET / CME abbreviated trading days, missing-minute checks).
4. Establish maximum **initial nominal stop risk per strategy** and combined concurrent risk for the exact funded-account rules (trailing DD, daily maximum loss), with stop slippage stress.
5. Only then decide freeze/hold/retire R072 and if an ES/NQ research lab should take priority.

## Reproducibility
- PDC reference zero-cost: `NinjaTrader Grid 2026-10-06 09-49 p. m..csv`
- POC 2-tick net: `NinjaTrader Grid 2026-10-07 09-04 p. m..csv`
- R072 autonomous 2-tick net: `NinjaTrader Grid 2026-10-07 10-44 p. m.(1).csv`
- ATR reference: `r072_python_signals_et.csv` from existing R072 parity support bundle.
