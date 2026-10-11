# NQ causal quote-trade as-of: seven-session development QC (2026-10-11)

**Status:** `DIAGNOSTIC_ONLY` in seven GitHub Actions runs; no strategy signal, backtest, performance evaluation, fill inference, or July–September 2026 pseudo-forward opening. **All data fetched exclusively from the private Dev repo**, SHA-256 verified, processed transiently on standard public `ubuntu-latest` runners, and removed after each job. No ticks or quoted prices are published in this repository.

Source: NinjaTrader exported NQ Last/Bid/Ask, ET sessions 08:00–12:00; one day each, not a complete time-series sample. The new scalping study permits 2025-10 through 2026-06 for source QC; May–Jun has an internal-validation role, not an unseen OOS. The initial 2025-Q4 change was recorded separately. July–September 2026 remains sealed.

## Source audit results

| ET day | Last rows | Both quotes ≤250 ms | Last tied to same-time quote update | Trades outside reconstructed prior BBO, of fresh subset | Spread 1–3 ticks, of fresh subset |
|---|---:|---:|---:|---:|---:|
| 2025-10-15 | 243,805 | 97.49% | 99.19% | 29.22% | 92.42% |
| 2025-11-03 (after DST) | 214,142 | 97.66% | 99.48% | 27.42% | 95.85% |
| 2025-12-16 (NQ 03-26) | 234,682 | 98.69% | 99.36% | 35.44% | 64.16% |
| 2026-01-15 | 242,080 | 97.31% | 99.28% | 31.19% | 95.74% |
| 2026-03-09 (after DST) | 215,845 | 98.66% | 99.50% | 34.73% | 42.84% |
| 2026-03-17 (NQ 06-26) | 160,066 | 97.54% | 99.51% | 26.84% | 92.48% |
| 2026-06-16 (NQ 09-26) | 208,804 | 98.86% | 99.56% | 32.82% | 45.87% |

Each run reports aggregated distributions and tests. All seven checks returned `DIAGNOSTIC_ONLY`; not `execution-validated`.

- [Initial Oct 15 strict BBO test](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38145073362): eight synthetic tests, Dev SHA-256, real Last/Bid/Ask diagnostic.
- [Six additional development-day checks](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38145229430): six successful matrix jobs, including rollover and DST-adjacent dates.

## Interpretation and limitations

1. **Strict temporal safeguard:** At timestamp T, each Last event is compared only with the latest Bid and Ask strictly **earlier** than T. Quotes at T are deferred. Same-timestamp cross-stream order is unknowable from independent exports. Importantly, >99% of trades coincide with at least one same-time quote update; this causes substantial microstructure uncertainty.
2. **Source availability is not executable price:** 97–99% of Last rows have both sides fresher than a descriptive 250 ms threshold. This does not certify exchange ordering, latency, matching engine sequence, available liquidity, queue priority, transaction costs, or actual fills.
3. **Outside reconstructed BBO:** 27–35% of fresh-book trades print above the preceding Ask or below the preceding Bid; the reason is not identified. This could reflect asynchronous quote capture or high-frequency movement; it cannot alone establish a bad export or aggressive-side classification.
4. **Spread dispersion is material:** 1–3 tick spreads range from ~43% to ~96% across dates. We must check time-of-day, volatility, session, rollover, and quote timestamp artifacts before selecting a scalping model.
5. **Study firewall:** these dates are authorized for the *new* tick-scalping study only. Do not open the sealed Jul–Sep 2026 dataset, do not use this period to retrofit the legacy H01–H78 research holdouts, and do not claim more than an offline historical source audit.

## Next engineering gate (not executed here)

Pre-register a separate **09:30–11:30 ET** source diagnostic by segments (09:30–10:00, 10:00–10:30, 10:30–11:30) with alternative quote-age thresholds reported side-by-side, not optimized. Reconcile NinjaTrader Last/Bid/Ask streams with a venue-sequenced feed or platform event ordering, if available, before using prior BBO as an actual executable price. Then study combined market-state + price/volume + execution/risk hypotheses on development data only, cost-stress and NQ sizing included.

No market P&L, simulated fills, CAGR, VOO/QQQM comparison, or funding-account risk outcome was measured.
