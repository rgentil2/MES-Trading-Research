# NQ-H04 — Overnight + opening-range compression: locked first mechanism test

**Preregistered:** 2026-10-09. **Experiment status:** specification frozen before computing H04 outcome. The primary source hypothesis NQ-H04 was already entered in `research/nq/NQ_2020_2024_RESEARCH_PREREG_MFFU.md`. **This is a volatility magnitude question, NOT a directional entry/exit strategy.**

## Universe and data isolation

- Use exclusively user-uploaded `NQMNQ_Research_2020_2026.zip` members with path segment **`development_2020_2024`** and basename **`NQ_*.txt`**; **never open/read any 2025 or 2026 data**. Do not load MNQ for the NQ-only mechanism screen.
- Single non-back-adjusted NQ quarterly contract chosen by fixed date: Thursday exactly 8 calendar days before the quarterly third-Friday expiration date, as previously preregistered for NQ-H01–H03. Do not combine overlapping contract prices.
- Full RTH session with strictly consecutive 390 UTC-derived NY time minute EOB labels `09:31..16:00`; verify no double count. Initial eligibility also requires at least **800 recorded overnight Last minute bars** between NY time `18:01` **on the preceding local calendar day** and `09:30` on the RTH session date. Overnight minutes from dates with weekend/holiday market closure naturally make a session ineligible. No interpolation.
- Current RTH session day is the date of first 09:31 bar. The futures evening session is assigned to the **next NY local calendar day**; Sunday evening belongs to Monday. At 09:45 no 09:46+ bar can be used for any feature.

## Mechanical signal: NQ-H04, defined at 09:45 NY

For session `t`, compute:
- `ON_range_bps[t]` = `10000*(max(overnight_high)-min(overnight_low))/close[09:45]` from up to 09:30 on date `t`. Denominator price observable by 09:45.
- `OR_range_bps[t]` = `10000*(max(RTH high 09:31..09:45)-min(RTH low 09:31..09:45))/close[09:45]`.
- Reference universe: the **prior 20 chronologically eligible completed sessions**, with valid overnight observations and complete RTH. Do not use current or future session in any rolling threshold.
- `compressed[t] = (ON_range_bps[t] <= median(ON_range_bps[t-20:t])) AND (OR_range_bps[t] <= median(OR_range_bps[t-20:t]))`. All eligible post-warmup sessions are scored, whether compressed or not.

The primary future volatility endpoint is the observed high-low range in the **next 30 RTH bars `09:46..10:15`** converted to bps using the causal 09:45 close. The past-only normalization benchmark is the median `09:46..10:15` 30m range bps of the previous 20 eligible sessions (only historical outcomes known at today's 09:45). Primary per-session outcome: `Z[t]=log(next30_range_bps[t] / past20median_next30_range_bps)`; require positive finite numerator and denominator.

**Primary contrast:** for each calendar week (Monday–Sunday in NY time) containing **>=1 compressed and >=1 noncompressed eligible day**, compute `W[k] = mean(Z of compressed days) - mean(Z of noncompressed days)`. The alternative was fixed as **H04 predicts W>0**, i.e. after joint compression the subsequent morning expansion is *stronger* than on noncompressed days in the same week, relative to prior-only volatility benchmarks. Equal-weight weeks. Do NOT switch to a calendar-year selected cohort if this fails.

## Statistical/reporting gate

- **H04 event count** = total days marked `compressed`, report number of paired weeks and counts by year. Updated prospective Gate1 N>150 is a screening target; if too few events, fail insufficient sample, do NOT loosen threshold after reading result.
- Mean `W` >0, 90% CI on mean `W` wholly above zero. Also report 95% CI. Method: week bootstrap, 10,000 resamples with fixed seed 20261009.
- One-sided paired-week sign-flip randomization p-value, **10,000 draws**, predeclared direction `W>0`.
- Apply Benjamini–Hochberg to **all four** NQ primary hypothesis screens H01-H04, documenting that H01-H03 have already been evaluated and therefore this is an **exploratory combined q, not a new independent confirmatory family**. For H01–H03 use the locked Free-account weekly sign-flip p values recorded in `research/costs/NINJATRADER_FREE_REPRICE_ES_NQ_2020_2024.json`.
- **Annual consistency** = at least **3/5 years** have positive mean weekly paired `W` (not the annual net P&L or an after-the-fact selected month).
- Report no-subset-rescue rules, unpaired weeks, total eligible RTH+overnight sessions, compressed frequency, data exclusions, and descriptive raw high-low ranges.
- Any positive H04 outcome is **a magnitude forecast only**. It cannot be called monetary edge without a separate preregistered *directional* entry plus realistic SL/TP and costs; do not create a trading strategy merely by post-hoc observing which side moved.

## Absolute restrictions

The experiment is **2020–2024 exploratory only**. H04 does not open 2025 for confirmation; no 2026 pseudo-forward inspection; no attempts to tune OR lengths, overnight clock boundaries, median quantile, 800-bar requirement, rollover date, conditional sign, lookback 20 or evaluation endpoint after seeing results. Existing MES/ES research family Holm controls remain authoritative for future confirmatory claims.

The prior H01-H03 mechanism results must not be retroactively relabelled as independent new discoveries because of the Gate1 amendment.
