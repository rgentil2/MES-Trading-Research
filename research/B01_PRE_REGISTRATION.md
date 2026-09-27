# B01 — Pre-registered hypothesis block R012–R015

Date frozen: 2026-09-27.

## Purpose

Four hypotheses are frozen together before any of their results are observed.

This prevents sequential idea selection from adapting to 2020–2024 as each prior experiment is seen.

## Common operating constraint

- New entries/signals must occur no later than 11:30 ET.
- Exits/outcomes may occur after 11:30 ET.
- No horizon crosses a contract boundary or RTH session.

## Hypotheses

### R012 / H017 — Low-volatility persistence (confirmatory OOS)
Follow-up to the opposite-sign result discovered in R006.

Dataset used for outcome: **2025 only**.
2024 may be read strictly as 60-session warm-up.

Hypothesis:
After the first 30-minute realized-volatility compression event between 10:01 and 11:30 ET, future 30-minute realized volatility remains below its same-minute 60-session historical baseline.

Primary metric:
`persistence_discount_pct = (1 - future_RV30 / baseline_future_RV30) * 100`.

Gate before multiplicity:
- N >= 60;
- sessions >= 60;
- mean discount >= 20%;
- 95% CI entirely > 0.

### R013 / H018 — Bullish efficient momentum (confirmatory OOS)
Follow-up to the descriptive UP-side result from R007.

Dataset used for outcome: **2025 only**.
2024 may be read strictly as warm-up.

Signal:
- trailing 15m return > 0;
- |r15| >= same-minute 90th percentile from prior 60 sessions;
- ER15 >= 0.70;
- first qualifying event/session;
- event <= 11:30 ET.

Outcome: directional forward return 15m.

Gate before multiplicity:
- N >= 30;
- sessions >= 30;
- mean >= +1.0 bps;
- 95% CI entirely > 0;
- continuation rate > 50%.

### R014 / H019 — Five-bar streak exhaustion
New family. Development dataset: **2020–2024**.

Signal:
- five consecutive non-zero 1m log returns with identical sign;
- absolute 5m return >= same-minute 80th percentile of the prior 60 sessions;
- first event/session;
- 09:36–11:30 ET.

Hypothesis:
The following 15-minute return reverts against the streak direction.

Primary metric:
`reversion_15m_bps = -sign(r5) * forward_return_15m * 10,000`.

Gate before multiplicity:
- N >= 300;
- sessions >= 300;
- mean >= +1.0 bps;
- 95% CI entirely > 0;
- >= 4/5 development years positive.

### R015 / H020 — Previous-session closing-strength continuation
New family. Development dataset: **2020–2024**.

Previous-session close location:
`CLV = (RTH_close - RTH_low) / (RTH_high - RTH_low)`.

Signal known before the next RTH open:
- LONG if previous CLV >= 0.80;
- SHORT if previous CLV <= 0.20;
- same contract required.

Outcome:
Directional return from current 09:30 open (Open of 09:31 end-bar) to the 10:00 ET close.

Gate before multiplicity:
- N >= 400;
- sessions >= 400;
- mean >= +1.0 bps;
- 95% CI entirely > 0;
- >= 4/5 development years positive.

## Multiple-testing rule

The four primary p-values are evaluated together using Benjamini-Hochberg FDR.

A hypothesis passes the block only if:
1. its individual pre-registered economic/sample/CI gate passes; and
2. BH q-value < 0.05 across H017–H020.

No subgroup or descriptive breakdown can replace a failed primary hypothesis.

## Holdout policy

- H017/H018 deliberately open 2025 because they are confirmatory follow-ups whose hypotheses were derived from prior 2020–2024 discoveries.
- H019/H020 use only 2020–2024. 2025 remains unopened for these hypotheses unless they pass B01.
- 2026 remains unopened for every B01 hypothesis.
