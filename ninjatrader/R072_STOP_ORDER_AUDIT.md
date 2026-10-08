# R072 — Protective Stop Order Audit (2026-10-07)

Scope: `R072LiveEngineParity`, 149 MES historical trades 2020–2025, catastrophe stop = 0.70 × previous-session ATR; no Python H017/session-universe dependency; 2 ticks slippage and $1.88 round-trip commission. 2026 remains sealed.

Evidence: User-exported `NinjaTrader Grid 2026-10-07 11-28 p. m..csv` (Orders, 447 rows) and `NinjaTrader Grid 2026-10-07 11-29 p. m..csv` (Trades, 149 rows), matched against frozen `r072_python_signals_et.csv` (145 events) from NinjaTrader R072 support bundle.

## Order-level checks

- 447 order rows = 149 full three-order groups: filled entry, stop-market protective order (cancelled on exit), filled market exit.
- All **149 of 149** entry groups have a stop-market order for one MES contract, recorded with the entry's timestamp.
- Stop direction is correct for all 149 (long stop = sell below entry, short stop = buy-to-cover above entry).
- Stop prices all lie on the MES 0.25-point tick grid, and no trade-level MAE exceeds its stop distance in USD.
- Every stop is **Cancelled**, never Filled. Existing 149 trades exit on H30 time (137) or news (12). Consequently, historic sample supports order installation and intended cancellation, not demonstrated triggered stop-fill behavior or fill under market gaps.
- Entry and exit order prices equal corresponding trade export prices in all 149 cases. NinjaTrader Trades timestamps are +1 minute from Orders timestamps owing to 1m label convention.

## ATR parity

For 145 sessions with frozen Python signal/ATR reference, compare stop ticks against `ceil(0.70 × atr14_prev / 0.25)`:

- 144/145 exact matches.
- One stop 1 tick farther than Python reference: 2020-10-29 10:15 ET LONG, Python ATR = 55.37218894593551; Python theoretical ceiling = 156 ticks; NinjaTrader = 157 ticks. This is conservative, 0.25 index points = $1.25 MES per contract. Investigate small ATR vendor/engine difference but do not optimize.
- Four additional sessions have no Python ATR reference and cannot be verified with this method: 2021-11-26, 2022-05-23, 2024-08-02, 2025-04-04.

## Decision

**Order-installation audit passed with one 1-tick ATR discrepancy and four additional sessions still lacking external ATR reference.** It is *not* a live-market stop-fill certification. Next: data/session completeness audit for the 4 additions, then portfolio-level timestamp/risk overlap for PDC+POC+R072 (ensuring matched execution assumptions), followed by go/no-go. Do not change R072 signal parameters based on historical outcomes. Do not use 2026 to optimize.

## Initial per-contract nominal stop risk

Given 1 MES = $5 per index point (before commission or stop slippage), the 149 stops imply: minimum **$110.00**, median **$208.75**, average **$233.79**, 75th percentile **$268.75**, 90th percentile **$332.75**, 95th percentile **$372.50**, maximum **$682.50**. 133/149 exceed $150, 48/149 exceed $250, and 5/149 exceed $500. The five >$500 are concentrated in April 2025. Historical no-stop-fill results do not remove these *potential* losses. Confirm compatibility with the specific $50k prop firm's trailing drawdown/daily risk, and simultaneous risk across strategies, before funding or scaling. This is a risk gate; never optimize the stop retrospectively to reduce sample losses.
