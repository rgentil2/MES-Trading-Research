# NQ S0.76 — V16 historical data adapter, frozen external validation, research runner
Date: 2026-11-06 | Status: C# source and CI research QA; NO real NQ backtest or NT8 compile

## Fixed user requirement: exactly ONE final NinjaTrader validation

The user is NOT doing interim NinjaTrader compilations or backtests. Continue implementing all modules in GitHub, testing deterministic C# source with synthetic M1 data and source shims. Only once the entire system is finished, conduct the ONE final integrated NT8 compile, Strategy Analyzer backtest, receipts parity, 2023–24 external and 2025–26 frozen holdout review. Do not suggest more interim NinjaTrader runs.

## Official source contract — NT8 Export / Historical Data

Verified in NinjaTrader's official documentation (2026-11-06):

- Minute Last TXT format: `yyyyMMdd HHmmss;open;high;low;close;volume`; **one-minute**, semicolon-separated. `https://static.ninjatrader.com/support/helpGuides/nt8/importing.htm`
- NinjaTrader historical export timestamps are **UTC END OF BAR**. `https://static.ninjatrader.com/support/helpGuides/nt8/exporting.htm`
- NinjaScript custom `RunIteration()` returns **void**, so there is NO documented synchronous numerical fitness return. `https://docs.ninjatrader.com/ninjascript/runiteration`. Do not invent or rely on undocumented NT8 optimizer feedback callbacks.

## V16 files

1. `NQNativeDataLoaderV16.cs` — pure C#, supports read-only seekable stream from official NT8 1-minute Last export. SHA256 exact raw source digest; strict date/order/duplicate/6-column/invariant numeric/OHLC/NQ 0.25-tick-volume guards; converts UTC *end* timestamp to `America/New_York` / Windows `Eastern Standard Time` with proper DST, then **subtracts one minute** to obtain completed bar **start**. Trims to **08:00–11:29 Eastern**, retaining 90 pre-RTH minutes for the 7–28 period ATR calculation and the full 09:30–11:29 research/flat exit window. Avoids ambiguous overnight fall-back repeat hours. Discards other hours only by deliberate research contract, not as a claim of full-market historical parity. Enforces 3 explicit **nonoverlapping** year partitions and records a 36/24-month complete-session histogram. Contract handling policy is **declared metadata, not independently verified** by the loader.
2. `NQNativeHistoricalEvaluatorV12.cs` and `NQNativeChronologicalRiskV15.cs` — add isolated, range-guarded **external** evaluation method for ONLY 2023–24 or 2025–26, reusing the same conservative M1 fills and open-equity calculations. The original 2020–22 V9/V7 training fitness and older regression tests are not changed. External results are **NOT passed to the train-only GA** and do not call the V9 2020–22 fitness function.
3. `NQNativeFrozenCampaignV16.cs` — accepts 3–5 distinct canonical 20-gene strategies that match an already provisionally passing **development V13/V15 portfolio**. Freezes ids/genes/contract policy/development export checksum and final cutoff into SHA256 identity. Permits one **2023–24 external evaluation**, requires ALL individual local economic gates and combined chronological risk to pass, then unlocks a single **2025–26 final holdout evaluation** on exactly the same genomes. Strict source/contract/provenance/day-month/OOS boundaries. Locks prevent repeated evaluation **within the same C# campaign instance** only, NOT deliberate bypass by instantiating a new campaign. These are research-process controls, not tamper-proof security.
4. `NQNativeResearchRunnerV16.cs` — **actual end-to-end headless pipeline**:
   `loaded 2020–22 M1 -> V14 cached V12 real GA/V9 score -> top reviewed genes -> V13 unchanged G0 robustness -> V13 diversified 3–5 portfolio + V15 chronological combined open-equity -> V15 nested rolling train-only walk-forward -> freeze V16 campaign for external results`. If insufficient profitable/robust candidates or the WF account gates fail, the runner stops with an explicit rejection and **NO frozen campaigns**. No live order calls.
5. Tests:
   - `tests/NQNativeDataLoaderV16Test.cs`: verified equivalent synthetic official NT8 TXT export, March/Nov DST, one-minute timestamp semantics, 36-month coverage, strict price/instrument/volume/duplicate/OOS failure.
   - `tests/NQNativeFrozenCampaignV16Test.cs`: mock development-proof provenance (NOT real economic proof), 3 distinct frozen V11 genes, synthetic complete external 2023–24 and final **Jan 2025–Oct 2026** windows, combined V15 account risk, loss-of-edge / wrong policy / repetition / early cutoff rejections.
   - `tests/NQNativeResearchRunnerV16Test.cs`: synthetic 36 months × 15 120-minute sessions; actual V14 genetic evaluation and original V13 economic quality audit; no evidence of real edge or fake portfolio; fails closed if even one month misses a complete session or OOS years are supplied.
   - Workflow `.github/workflows/nq-v16-native-data-frozen-qa.yml` with three .NET8 CI jobs.

## Critical 2026-11-06 calendar detail

**2026-11 and 2026-12 are not complete in the real market on 2026-11-06.** The explicit frozen final cutoff `2026-11-01T00:00` means the available **Jan 2025–Oct 2026** portion is evaluable without inventing future data. If later shifting the cutoff, it must be set **before viewing the final holdout** and recorded in the freeze digest. The complete 2025–26 calendar cannot be backtested as of the current date.

## What this does NOT prove

- **No** actual 2020–22, 2023–24, or 2025–Oct2026 NQ historical market trade results calculated. Repository lacks complete historical M1 payload.
- **No** Windows NinjaTrader 8 compile or proprietary native historical fill parity; no tick-level high-low sequencing or exact MFFU trailing drawdown accounting.
- **No** certified continuous futures contract backadjustment or rollover mechanics, exchange-calendar quality check or realistic market-specific bid/ask spread proof.
- **No** NinjaTrader **native optimizer feedback**; documented `RunIteration()` is void. This headless C# GA produces candidates and a separate native NT8 V11 Strategy will require final import/replay. Until that final integration, this is NOT a finished in-platform StrategyQuant equivalent.
- **132 conditions** are 12 feature families × 11 directional predicates, NOT 132 independent indicators. Search 100k capacity hasn't been benchmarked with millions of real bars.
- **No** real funded/prop trading readiness.

## Next engineering priority

Productionize the Windows NT8 read-only capture/import and one-run Strategy Analyzer parity harness, audit contract roll adjustment and UTC/Eastern bar alignment on source samples, provide a deterministic versioned frozen strategy portfolio deployment artifact, and run a full 100k-candidate CI synthetic scalability test without leaking data. Keep all draft PRs stacked and unmerged until final integrated check.
