# NQ/MNQ NinjaTrader 8 bulk minute exporter (research-only)

**Designed, not compiled/run inside NT8 yet.** No local NinjaTrader desktop is available in the GitHub runner or assistant environment. This does NOT automatically obtain data from your personal brokerage connection until you install/run it in NinjaTrader on a connected Windows machine.

## Installation and use

1. In NinjaTrader Desktop 8, connect to your futures market-data provider. Confirm it actually has historical **NQ/MNQ 1-minute Last for 2020–2024**; retention depends on connection and vendor, NOT on the export script.
2. In Control Center select **New > NinjaScript Editor**, right-click AddOns, choose New AddOn, replace generated scaffold with the content of **`NQMNQBulkMinuteExporter.cs`**, save/compile (F5). You may need to create an AddOn named NQMNQBulkMinuteExporter; don't paste the code inside a Strategy or Indicator.
3. In Control Center choose **New > NQ/MNQ 2020-24 Research Export**. The exporter schedules **40 sequential jobs**, 20 NQ and 20 MNQ quarterly contracts (Mar/Jun/Sep/Dec 2020–24). `MergePolicy.DoNotMerge`, `BarsPeriodType.Minute` and ETH are fixed in code. Monitor **New > NinjaScript Output (Output 1)** and the provider status. Stop/retry if the provider rate-limits requests.
4. Export destination is `%USERPROFILE%\Documents\NinjaTrader 8\NQMNQ_Research_2020_2024\` with one file per individual quarterly contract plus `download_manifest.csv`. Exported timestamps use UTC; the raw semicolon format matches the project's existing files.
5. Any job with fewer than 20,000 bars is recorded `INCOMPLETE` and written as `.partial` rather than accepted. Failed jobs are logged; the program resumes files >1MB and a **separate QC must verify hashes, missing RTH sessions, and rollover**. A provider can return too short a range despite completing without error; don't assume EXPORTED means QC_PASS.
6. Send or sync the resulting NQ/MNQ folder into the private research environment. Never upload to a public repository; the repository stages only hashes, status, and small results. NQ **2025 and 2026 remain sealed**.

## Important limitation

`BarsRequest` from/to range uses **local midnight and full trading days**, so a contract request can have overlap with adjacent quarterly contracts. This is intentional for explicit rollover handling, NOT a reason to sum candles across both. Some providers cannot retrieve six years of minute data despite successful recent download. If the provider fails for early years, switch to a paid historical API only after comparing cost and retention; a C# script cannot create data a provider does not have.

## Research versus NinjaTrader Strategy Analyzer

Use Python for hypothesis generation, multiple-testing correction, clustered confidence intervals, walk-forward, multi-contract portfolio risk and Monte Carlo. Use NinjaTrader **Strategy Analyzer** for faithful implementation/backtests of a small fixed set of candidate rules, including stops, fills and commission settings, and finally 2026 reserved chronological pseudo-forward and live simulation after freeze. This is faster and more reproducible than programming every preliminary hypothesis as a NinjaScript strategy. Do not optimize thousands of Strategy Analyzer parameters on already-explored 2020–2024 and treat the best performance as proof of alpha.

## Official documentation

- BarsRequest: https://ninjatrader.com/support/helpguides/nt8/barsrequest.htm
- MergePolicy.DoNotMerge: https://docs.ninjatrader.com/ninjascript/barsrequest_mergepolicy
- Historical-data export/UTC: https://ninjatrader.com/support/helpguides/nt8/exporting.htm
- Per-provider historical availability: https://ninjatrader.com/support/helpguides/nt8/data_by_provider.htm