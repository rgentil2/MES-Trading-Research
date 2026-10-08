# ES PDC transport — preregistration, 2020–2024 development only

Frozen: 2026-10-07 (America/Bogota); **TRANSPORT / DIAGNOSTIC ONLY**.

## Question
If the previously frozen MES PDC small-gap strategy is *ported without changing its numerical thresholds* to ES Minute Last development data, does its observed dollar stop size and activity plausibly fit MFFU Rapid EOD 50K?

**No independence claim:** MES and ES track the same S&P 500 index. MES's previously selected parameters cannot become ES holdout validation; this is a development-transfer diagnostic.

## Allowed source
ES 20 quarterly `Minute Last` LFS exports MAR20–DEC24 only. Verify each contract file against `data_es_staging/manifests/ES_MINUTE_LAST_MANIFEST.csv` and require the manifest stage `DEVELOPMENT`. Do not LFS-smudge 2025 or 2026. Use UTC raw timestamps, NY conversion, EOB minute convention 09:31–16:00 (390 bars) and non-back-adjusted implicit contract rollover. Only sessions with exactly 390 consecutive bars and expected first/last label are eligible. Use past-only complete-session Wilder ATR14; use previous close only when prior contract matches. Historical holidays and incomplete RTH days are omitted.

## Imported PDC specification (NO SEARCH)
- Gap = |RTH opening price - previous eligible complete session close| / ATR14(previous complete sessions); 0.10 <= gap < 0.20.
- First five 1-min RTH bars must not touch previous close; 5th-minute close must move toward it.
- Enter next bar at its **open**, actual entry assumed 2 ticks adverse from entry-bar open; skip if fill already crossed target.
- 1 contract ES reference; stop distance rounded up to an integer tick count for 0.30 * ATR14. Protective stop relative to adverse entry fill. Target previous close.
- Until 11:30 ET signal exit or target/stop. EOB 11:30 time order fills at 11:31 next bar open.
- If stop and target are within the same OHLC bar, assume STOP FIRST (conservative).
- Market/stop/time-exit price 2 ticks worse than bar/stop price. Target limit price uses *touch fill*, optimistic; tick data not available across all development years.
- ES MFFU costs **$4.68 round trip**; separate parallel 1 MES economic scenario **$1.90 round trip**, same hypothetical ES-based signals and fills, strictly a scaling diagnostic.
- No news filter in this first pass, because exact frozen 2020–2024 news windows are not committed. This is **NOT exact MES PDC parity** and **NOT a tradable ES signal validation**. News flat/entry windows could change the results either direction. Never present this as a funding-ready backtest.
- Refuse to score a trade whose exit interval lacks consecutive one-minute bars.

## Outputs / decision rules
- Report trade count, active years/quarters/months, 7-calendar-day signal inactivity, net, PF, per-year, EOD closed-balance max DD, stop risk median/95th/max, and ES stop vs 2k MFFU loss budget (also $200, $500, $1000 bins).
- Stress accounting +1 and +2 adverse tick **per side** relative to the baseline (no resimulated fills; descriptive friction stress).
- A mechanical **RISK SIZING FAIL** if even one planned 1 ES loss estimate exceeds $2,000; flag >$500 for attention (25% of account drawdown). This threshold is an initial veto/diagnostic, not calibrated on the sample.
- Do not use results for tuning gap, ATR stop, time exit, trade side or news rule. Any new candidate requires independent hypothesis validation and re-registered protocol.
- No 2025 candidate/ES outcome P&L, no 2026 data inspected.
