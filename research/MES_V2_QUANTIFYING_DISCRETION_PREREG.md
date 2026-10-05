# MES V2 — Quantifying Discretion — Pre-registration

Locked before outcome analysis.

## Goal

Test whether measurable features that a discretionary trader could visually perceive can distinguish strong from weak MES OR15 breakouts without human trade selection.

## Data policy

- Development/discovery: 2020-01-01 through 2022-12-31.
- Temporal validation: 2023-01-01 through 2024-12-31.
- 2025 is not read.
- 2026 is not read.
- MES is the execution instrument.
- ES Minute Last is used only as contemporaneous contextual information.
- No Tick Last data are used in this first V2 layer.

## Event

- RTH uses the NinjaTrader EOB convention already established in the project.
- Opening range = first 15 RTH one-minute bars.
- Event = first MES one-minute close outside OR15 after the opening range and no later than the bar labeled 11:24 ET.
- Direction = +1 above OR high, -1 below OR low.
- Only full RTH sessions with at least 390 bars are eligible.
- One event maximum per session.

## Observation / execution timing

This experiment explicitly allows a five-minute confirmation window to quantify acceptance/rejection.

- Signal bar = first OR15 breakout close.
- Confirmation window = the next five complete 1-minute bars.
- Hypothetical entry = open of the following bar, strictly after all confirmation features are known.
- Primary outcome = direction-aligned 30-minute return from that entry, net of the fixed MES round-trip cost.
- Secondary outcome = 60-minute return.
- Fixed round-trip cost = $4.38 = 0.876 MES index points.

This is a signal-quality experiment, not a final SL/TP strategy.

## Feature families

All features are causal at hypothetical entry.

### MES signal-bar structure
1. OR width / prior ATR14.
2. Breakout displacement beyond OR edge / ATR14.
3. Signal candle body efficiency = abs(C-O)/(H-L).
4. Aligned close location within signal candle.
5. Same-minute MES RVOL using prior 20 sessions only.
6. Cumulative MES RVOL using prior 20 sessions only.
7. Aligned 3-minute speed / ATR14.
8. Aligned five-bar path efficiency.
9. Aligned distance from session VWAP / ATR14.

### ES contemporaneous confirmation
10. ES same-minute RVOL, prior-20-session normalization.
11. ES cumulative RVOL.
12. ES signal-candle aligned efficiency.
13. ES already outside its OR15 in the MES breakout direction.
14. ES broke its OR15 first in the same direction.
15. ES minus MES aligned three-minute relative move.
16. ES aligned three-minute move / ES ATR14.

### Five-minute acceptance / rejection
17. Fraction of MES confirmation closes remaining outside OR.
18. Fraction of MES confirmation volume whose bar close remains outside OR.
19. Maximum re-entry depth into OR / ATR14.
20. Five-minute net continuation / ATR14.
21. Five-minute MFE / ATR14.
22. Five-minute MAE / ATR14.
23. Mean MES RVOL over confirmation window.
24. Fraction of ES confirmation closes outside ES OR in same direction.
25. ES five-minute continuation / ES ATR14.

No other features may be added after results are observed in this block.

## Models

Two fixed diagnostics:

### Logistic diagnostic
- Median imputation learned on 2020-2022 only.
- StandardScaler learned on 2020-2022 only.
- LogisticRegression with default L2 penalty, C=1.0, max_iter=5000.
- Binary target: primary 30-minute trade is net profitable after $4.38 cost.
- Main validation diagnostic: ROC AUC on 2023-2024.
- AUC < 0.55 is considered weak discrimination.

### Interpretable tree
- DecisionTreeClassifier.
- max_depth = 2.
- min_samples_leaf = 180.
- random_state = 42.
- Same binary target.
- No hyperparameter tuning.
- After fitting on 2020-2022, select the terminal leaf with the highest discovery profitable fraction.
- The exact path to that leaf is frozen automatically and applied unchanged to 2023-2024.

## Promotion gate for the selected tree leaf

To justify any execution research, the frozen leaf must satisfy on 2023-2024:

1. >= 120 validation events (>= 5/month over 24 months).
2. Net mean 30-minute return > 0.
3. Net time-exit profit factor >= 1.15.
4. Positive net total in both 2023 and 2024.
5. Mean gross 30-minute lift versus the full validation OR15 event set >= 3 bps.
6. Logistic validation AUC >= 0.55 as independent evidence that the feature set contains out-of-sample information.

If the gate fails, Layer 1 OHLCV “quantified discretion” is rejected. Tick/BidAsk microstructure is considered only as a separate Layer 2 decision.

## No post-result rescue

No changing:
- confirmation window,
- model depth,
- min leaf size,
- feature thresholds,
- OR duration,
- event time window,
- target horizon,
- cost assumption,

within this block after outcomes are observed.
