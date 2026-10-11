# NQ Tick Scalping — Oct 2025 through Jun 2026 (development QC)

This is a **separate** project track; its use of Q4-2025 does not open
2025 for the legacy H01–H78 research.

**Scope:** 2025-10 through 2026-04 development, 2026-05 through 2026-06
internal validation, 2026-07 through 2026-09 completely SEALED offline
pseudo-forward. The Oct-2026 data is archived but out of this study.

## Step 1 — Copy 2025-Q4 archives into the private DEV repository using your Windows PC

Already available locally in:

`C:\Users\rgent\NQTickResearch\github_releases_upload\Sealed\2025-10`,
`2025-11`, and `2025-12`. The uploader touches **only these folders**,
verifies their .sha256 sidecars and copies them to `rgentil2/NQ-Ticks-Dev-2026`.

Open PowerShell with GitHub CLI authenticated and run from a cloned checkout
of the **public** `MES-Trading-Research` repo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\local_nq_tick_2025_2026\copiar_q4_2025_a_dev.ps1
# After checking external-storage rights under your NinjaTrader/CME license:
.\local_nq_tick_2025_2026\copiar_q4_2025_a_dev.ps1 -Upload -LicenseConfirmed
```

The first command after changing the execution policy is PREVIEW-ONLY. The
second uploads 18 assets (3 months × 3 types × archive/checksum), skipping
already uploaded assets of the same filename/size. It never downloads or
modifies the original sealed July–September files, **never accesses**
`rgentil2/NQ-Ticks-Sealed` through GitHub and does not run GitHub Actions.

## Step 2 — Set one minimal read-only credential for public Actions

Create a **fine-grained personal access token** scoped to the single private
repository `rgentil2/NQ-Ticks-Dev-2026`, repository permissions
`Contents: Read-only` and no other repositories. Add as an Actions secret
named **`NQ_DEV_TICKS_READ_TOKEN`** on the public
`rgentil2/MES-Trading-Research` repo.

**Never give the token access to `NQ-Ticks-Sealed`.** Do not paste tokens in
chat, logs, documentation or commits.

## Step 3 — Manually run a single day QC in PUBLIC GitHub Actions

Open GitHub → public repo → Actions →
**NQ Tick QC Oct 2025-Jun 2026 (manual, public standard runner)** →
Run workflow. For the initial pilot, select:

- `day = 2025-10-15`
- `use_private_market_data = true`

Before running a real data pilot, you may run with
`use_private_market_data = false` to execute only synthetic safety tests.

The workflow uses standard `ubuntu-latest` hosted runners in the PUBLIC
repository (not private billable standard-runner minutes), `workflow_dispatch`
only (no push, PR, cron), downloads one month's 3 compressed archives from
Dev, verifies SHA256, extracts only the chosen day, performs streaming QC,
prints AGGREGATE counts but never raw tick prices, and deletes temporary data.
The code refuses any date outside Oct-2025 through Jun-2026.

## Scope of first-stage QC

Checks source files for required Last/Bid/Ask, nonempty rows, numeric
timestamps, actual UTC-to-ET 08:00–12:00 window with DST, subsecond events,
chronology, sizes and 0.25 NQ price grid. Does NOT yet certify BBO matching,
quote latency, contract rollover, spread/slippage execution, missing
intraminute activity or that historical records reconstruct official data
without discrepancies. QC PASS is NOT validation of any trading strategy.

Reference scope:
[NQ Q4-2025 to H1-2026 policy](../../NQ_TICK_SCALPING_Q4_2025_JUN_2026_SCOPE_2026_10_11.md).
