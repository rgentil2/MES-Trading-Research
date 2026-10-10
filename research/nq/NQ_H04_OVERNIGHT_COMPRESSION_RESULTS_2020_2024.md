# NQ-H04 | Overnight + OR compression → next 30-minute volatility

**Experiment date:** 2026-10-09. **Decision: NOT_SUPPORTED_EXPLORATORY**. The mechanism test was preregistered on GitHub **before** the corresponding outcomes were computed: `research/nq/NQ_H04_OVERNIGHT_COMPRESSION_PREREG_2026_10_09.md` (commit `329feb180211579ef012fedfea6ed3ef9d9e07a6`).

## Data restrictions

Source: original user-provided NQ/MNQ ZIP. Only the **25 NQ development partitions 2020–2024** were opened. No 2025 or 2026 price bars, trades, or strategy outcomes were accessed. One active quarterly contract per session selected using the pre-existing fixed Thursday/eight-days-before-third-Friday rollover rule; 390-minute full RTH and >=800 overnight minutes required.

## The exact question

At 09:45 ET, check whether overnight range and 15-minute opening range are both below their rolling **past 20 eligible sessions' medians**. If jointly compressed, does the subsequent **09:46–10:15 ET** realized high-low range have greater **log relative** amplitude than on noncompressed days **in the same calendar week**, adjusted by the past-only median next-30-minute range?

H04 is **non-directional**: a magnitude forecast is not a trade with costs and stops. The test did not try to buy/sell or optimize the threshold after inspection.

## Results

| Measure | Value |
|---|---:|
| Full NQ RTH sessions before overnight eligibility | 1,221 |
| Full RTH + >=800 overnight minute observations | 1,214 |
| Scored sessions after 20-session causal warmup | 1,194 |
| Joint compression signals | **399** |
| Other eligible days | 795 |
| Paired calendar weeks with both conditions | 163 |
| Weeks without both groups, omitted from paired inference | 95 |
| Mean paired-week effect, log volatility ratio | **-0.169128** |
| Equivalent ratio of matched geometric means, `exp(-.169128)-1` | **-15.56%** |
| 90% weekly bootstrap confidence interval on log effect | **[-0.215348, -0.122514]** |
| 95% weekly bootstrap confidence interval on log effect | [-0.224288, -0.114279] |
| One-sided `greater than zero` sign-flip p | **1.000** |
| Descriptive BH-adjusted q within four NQ screens | **1.000** |
| Development years in the preregistered positive direction | **0/5** |

| Year | Compressed sessions | Paired weeks | Mean paired log-difference |
|---|---:|---:|---:|
| 2020 | 86 | 29 | -0.183234 |
| 2021 | 86 | 29 | -0.204714 |
| 2022 | 77 | 36 | -0.149960 |
| 2023 | 83 | 38 | -0.099671 |
| 2024 | 67 | 31 | -0.230040 |

**Why it fails:** sign is opposite to H04's preregistered claim, 90% CI entirely *below* zero, BH q=1 rather than <=0.1, and 0/5 years support the direction; only the N>150 gate is satisfied. The opposite descriptive pattern does **not** become a new validated hypothesis by changing direction after observing it; that requires a separately declared study and truly independent validation.

## Statistical caveats

Weekly sign-flips and nonparametric week bootstrap use week as the unit. A one-sided p=1 reflects the predeclared **positive** direction and finite Monte Carlo draws. The paired-week metric is not a percentage change in all raw future ranges; -15.56% is a ratio of *geometric* relative-volatility measures under specified matching and past-only normalization.

The descriptive four-family BH accounting reuses H01-H03 earlier exploratory p-values and is **not** independent Holm confirmation. Neither the relaxed Gate1 nor 2025/2026 holdouts may be used to salvage this failed version. Tests of alternative time windows, quantiles, directional filters, or stop/TP must be registered as separate adaptive experiments; no direct funded account deployment follows.

## Reproduce

After placing the original ZIP at a user-specified local path:

```bash
python research/nq/nq_h04_overnight_compression_2020_2024.py --zip "NQMNQ_Research_2020_2026.zip" --out "results/nq_h04_overnight_compression"
python -m unittest research/nq/test_nq_h04_overnight_compression.py -v
```

The file-loader explicitly restricts `ZipFile.open` to development partitions, and a regression test supplies intentionally unreadable held-out entries to verify that **neither held-out year is accessed**.