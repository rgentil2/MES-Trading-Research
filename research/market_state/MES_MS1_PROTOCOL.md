# MES Market State V1 — MES-MS1-20261003

Status: descriptive feature engineering, fixed before the first run. This is a
new, separate namespace. Frozen R063, its historical results, costs, multipliers
and labels are preserved. MS1 is not an implementation change to R063.

## Scope and authority

Only the twenty MES quarterly export files with contract years 2020–2024 may
be opened. Filter timestamps to ET calendar 2020–2024 before feature generation.
No ES files, 2025/2026 contracts, trade P&L, forward returns or outcome artifacts.
No inferential hypothesis, alpha allocation or strategy promotion in this phase.
Freeze fingerprints cover code, protocol, tests, workflow, dependencies and the
existing data loader. Source byte hashes are recorded in the resulting report.
Future phenotype/strategy research must register its entire family through the
existing search controls **before** any outcome calculation. MS1 states cannot
be used to reopen failed historical gates under a new subgroup label.

MES 2020–2025 has already been researched. The six proposed folds below are
internal chronological diagnostics on reused data, not pristine OOS. ES 2025
has a different policy. MES 2026 remains reserved for a complete frozen strategy;
no engine-only validation on 2026 is authorized by this protocol.

## Point-in-time inputs

UTC end-bar timestamps converted to America/New_York. Daily as-of is 09:30 ET,
including the completed minute ending 09:30. Computing/receiving the bar takes
time: no claim of a fill at exactly 09:30. No current RTH OHLC/volume participates.
The calendar is every weekday in the in-scope source coverage, including weekday
holidays: it is deliberately **not** represented as a certified CME calendar.
Unknown coverage on holidays is visible. Monday overnight starts Sunday 18:01.

Overnight interval: previous calendar day 18:01 through current day 09:30,
inclusive, one contract, both endpoints present, at least 800 of 930 possible
minute bars. Missing zero-volume bars versus missing records is not distinguishable
from these exports; this is a conservative coverage rule, not a liquidity test.
Previous observed RTH must have all 390 minute ends 09:31–16:00 in one contract.
Incomplete/shortened sessions are not fabricated or imputed.

ATR14 is the arithmetic mean of true range over the last 14 **full RTH sessions
of the currently active contract**, using its own preceding RTH close. The first
TR of a contract uses high-low, never the prior contract's close. Previous RTH
and overnight must share the contract; 14 full-session contract warm-up is required.
The inherited NinjaTrader implicit rollover follows original export endpoints,
not a newly validated live roll-selection algorithm. Source-contract transitions
are recorded and levels are never spliced across contracts. This restriction
reduces coverage; it does not establish a live data/roll audit as complete.

Volatility = ATR14 / previous RTH close. Trend10 = (last close - close ten full
sessions earlier) / ATR14. ER10 = absolute same displacement divided by sum of
absolute differences of the eleven closes. These are pre-open, multi-day
attributes; 'Directional' describes efficient past closes, not today's future
intraday direction. ER is not separately normalized by ATR.

Other attributes: overnight range/ATR14; overnight close minus first open / ATR14;
overnight volume / historical median; and pre-open close minus PDC / ATR14.
The last quantity is explicitly a **gap proxy**, not the actual RTH opening gap.
Direction: Bull > +1 ATR, Bear < -1 ATR, otherwise Neutral. Overnight direction
and gap proxy: Up > +0.1 ATR, Down < -0.1 ATR, otherwise Flat.
Value location: above PDH, below PDL or inside prior RTH range, with signed
distances to PDC/PDH/PDL. POC/VAH/VAL are deferred: Last OHLCV is insufficient
for exact volume-at-price; no exact auction-level claim is fabricated here.

## Lagged reference and hysteresis

Reference is the previous 252 weekday rows, strictly excluding today's row,
with at least 126 valid values per variable. The entire 252-row window must exist.
Missing values consume calendar positions. No 2019/pre-sample data is opened;
2020 contains genuine initialization, not retrospectively backfilled regimes.
All parameters are chosen before this run and are not optimized on results.

Volatility and ER use their separate past P33/P67 with linear interpolation.
Below P33 => LOW; above P67 => HIGH; inclusive middle band retains the last
known state. No initial state in the band => R0. Equal quantiles => unknown.
Input gaps and contract changes reset hysteresis and accumulated alerts.
Overnight range and volume use Compressed/Normal/Expanded or Low/Normal/High
attributes; these are not additional regime combinations.

| Regime | Volatility memory state | Efficiency memory state |
|---|---|---|
| R1 | High | Directional (ER High) |
| R2 | High | Chop (ER Low) |
| R3 | Low | Directional (ER High) |
| R4 | Low | Chop (ER Low) |
| R0 | Missing/initially uncertain, or online alert | Reason recorded separately |

The retained middle-band value is a state memory, not an assertion that current
volatility lies above P67. Export current thresholds and raw attributes so this
is auditable. R0 does not authorize avoiding a trade; that requires a separate
registered outcome test, including its opportunity/frequency effects.

## Sequential change alerts

Three channels: log(ATR14/price), log(overnight range/ATR14), log(overnight volume).
For each, today's observation is standardized using only its past 252-row
reference (minimum 126 valid). Sample SD; z clipped to [-6,+6]. Two-sided CUSUM:
C+ = max(0,C+ + z - 0.5); C- = max(0,C- - z - 0.5). Any channel reaching 5
triggers an alert, resets all accumulators and starts a five-ready-session R0
window, including the alert day. New alerts restart it. Invalid inputs/rolls
reset it. Raw alerts, channel scores and the underlying component states remain
available for audit. Repeated observations and overlapping ATR windows are
dependent; false alarm rate and detection delay are **not calibrated**.

This is a heuristic sequential monitoring layer, not a statistically established
break test and not P(Change). No BOCPD posterior is implemented. Offline
Bai–Perron diagnostics, alternative detectors and HMM need separate specifications
and budgets if selected using strategy outcomes. Similar classifications from
two models on the same inputs do not constitute independent replication.

## Deliverables and validation boundaries

CAUSAL_FEATURES.csv: thresholds, past reference N, inputs, availability, R0 reason,
regime, attributes, episode ID and elapsed length. No future episode end/length.
Retrospective EPISODES.csv: start/end, observed duration and boundary censoring.
Transitions count adjacent weekday rows of the same contract, including R0;
rolls/missing business dates are not bridged. Empirical row proportions are
descriptive, not calibrated transition forecasts. Report annual coverage and
R0 reasons without choosing a year/state for better trading returns. Episodes
are contiguous runs and are **not assumed independent**.

Frozen internal fold scaffold (no strategies evaluated here):

| Fold | Development | Internal pseudo-OOS |
|---|---|---|
| 1 | 2020-01-01–2021-12-31 | 2022 H1 |
| 2 | 2020-07-01–2022-06-30 | 2022 H2 |
| 3 | 2021-01-01–2022-12-31 | 2023 H1 |
| 4 | 2021-07-01–2023-06-30 | 2023 H2 |
| 5 | 2022-01-01–2023-12-31 | 2024 H1 |
| 6 | 2022-07-01–2024-06-30 | 2024 H2 |

Freeze each candidate and all selection decisions before opening its next fold;
adaptation rules must also be frozen. Do not tune the regime engine by next-fold
PnL. Count episodes, calendar exposure and trades, with dependence-aware inference.
Walk-forward performance is pending. CPCV purge/embargo requires actual event
information intervals; none exist yet. PBO's original implementation is CSCV,
not interchangeable with CPCV. PBO needs comparable returns for all candidates;
DSR needs selection history and return distribution. Do not manufacture either
statistic from regime labels or treat incomplete historical trial counts as exact.

Next scientific step after this map: one bounded, preregistered phenomenon and
matched baseline inside a pre-specified state; then falsification, temporal
replication, execution/costs, internal walk-forward and an eligible locked test.

## Primary/official references and limitations

- NIST CUSUM: https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm
- Adams & MacKay (2007), BOCPD: https://arxiv.org/abs/0710.3742
- Bailey et al. (2015), PBO/CSCV: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
- Bailey & López de Prado (2014), DSR: https://doi.org/10.2139/ssrn.2460551

These references support concepts, not the profitability or validation of our
chosen thresholds. The unnamed 2026 MNQ study mentioned in the proposal is not
verified and is not relied on as evidence. This phase does not identify cycles,
prove statistical regimes, or complete execution-quality validation.
