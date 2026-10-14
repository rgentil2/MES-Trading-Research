# ES 1min -> MES 50k research transport, 2026-10-14

This is **not** an ES-trained strategy builder. It transports **exactly the existing frozen 144 NQ v1/v2 rule combinations** onto the 20 pre-existing ES Minute Last LFS quarterly DEVELOPMENT contracts dated 2020--2024. **No threshold search, no new hypotheses, no 2025/2026 access**. A result on ES is exploratory (reused ES historical and reused NQ idea catalog), not independent evidence of alpha.

Execution must happen in GitHub Actions or an environment with real ES LFS files. The public Git tree only contains 132-byte LFS pointers; if LFS is not available the job must fail. Data reading reuses `research.es.es_pdc_transport_gate` audited 20-manifest loader, checksum SHA-256, UTC->NY DST, completed 390-bar 09:31--16:00 sessions; excludes rollover-day mixed contracts.

**MECHANICAL CHANGE ONLY, no selection:** Signal price source ES 1m instead of NQ 1m. Risk sizing P&L uses **MES at $5/point** and modeled fee **$1.90 RT** rather than MNQ $2/point, with 2 adverse ticks each side, one-to-five MES, $250 reference risk per trade, 8--60 point ATR-based SL bound, 1.5R/2R TP, stop-first intrabar ambiguity, time exit 20--30 minutes. MES executions are **NOT** verified, prices come from ES candles; ES native $50/point would be 10x more exposure, not used for $50k account ranking. No dynamic optimization or parameter adjustment on ES outcomes permitted.

Data split: 2020--2022 retrospective train, 2023--24 reused internal, 2025 HOLDOUT (sealed), 2026 excluded. Correction BH for all 144 registry entries, excluding older H/T tests (so only exploratory). 2025 may only be opened later after frozen portfolio and independent review.

One shared strategy account router exists in `v2_router.py` but is **not run on a selected top-k here**: selecting priority by the same ES outcomes would be portfolio overfitting. A frozen candidate ranking and priority must be defined on train before checking internal and routing.

Actual method via GH Actions ".github/workflows/es-builder-50k-transport.yml": checkout without LFS, LFS pull **only 2020--2024 ES 1m**, scan holdout pointers, `python research/strategy_builder_50k/run_es_builder_transport.py --output /tmp/es_builder_50k_result --allow-existing-dev-reuse --bootstrap 1000`, upload only CSV/JSON summary as artifact (no OHLC, no raw trades).

The separate NQ T05/T186/T215 transfer to NinjaTrader is NOT modified; branch only. If LFS fetch fails, diagnose LFS access without using any 2025/2026 data or switching the hypothesis rules.