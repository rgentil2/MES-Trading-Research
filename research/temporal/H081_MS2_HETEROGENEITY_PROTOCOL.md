# H081 x MES-MS2 Pre-open State Heterogeneity — preregistration

Status: post-hoc diagnostic of a frozen H081 signal against independently frozen,
outcome-free MES-MS2 pre-open features. Frozen before joining the two artifacts.

## Purpose

Calendar segmentation did not identify a clean recurring month/week edge for
H081. This block tests the next planned question: whether H081's 30-minute net
outcome differs systematically across market information known by 09:30 ET.

This is a heterogeneity diagnostic, not a strategy promotion block.

## Exact sources

1. H081 trades:
   - B14 run 36427711138
   - artifact b14-opposite-sign-candidates
   - artifact digest sha256:0017a78ebc25630b9a5b3f71417f1bc8f3a4ee186a2a96b72090744944e51047
   - exact frozen H081 event definition and 30-minute base/stress outcomes.

2. MES-MS2 features:
   - run 37391057933
   - artifact mes-market-state-v2-2020-2024
   - artifact digest sha256:cb6199c883652f4e2053b84651cc4a3629b36df6933a210e66b71248d083b3e5
   - features are causal as of 09:30 ET and were built without trading outcomes.

Scope is the intersection 2020-2024 only. 2025 H081 trades are excluded because
MES-MS2 was intentionally frozen on 2020-2024. 2026 is never opened.

## Join

Join H081 session_date to MES-MS2 date one-to-one.

For categorical state tests, require MES-MS2 input_status == READY and a
non-UNKNOWN category.

## Frozen categorical families

Test all seven variables; none may be selected in advance from outcome results:

1. volatility_state: LOW / MID / HIGH as emitted by MES-MS2;
2. efficiency_state: DIRECTIONAL / CHOP / UNKNOWN as emitted, with UNKNOWN not
   eligible for the omnibus test;
3. direction: BULL / NEUTRAL / BEAR;
4. overnight_state: COMPRESSED / NORMAL / EXPANDED;
5. volume_state: LOW / NORMAL / HIGH;
6. gap_state: UP_PROXY / FLAT_PROXY / DOWN_PROXY;
7. value_location: ABOVE_PDH / INSIDE_PREVIOUS_RANGE / BELOW_PDL.

MES-MS2 regime R0-R4 is reported descriptively only because V2 classified just
31.8% of all sessions and R0 is primarily a transition/reference state.

## Outcomes

Primary outcome: H081 net_pnl_30 under the original B14 base cost.

Secondary descriptive outcome: stress_net_pnl_30 under 1.5x B14 costs.

No entry, exit, stop, target, direction or cost is changed.

## Omnibus heterogeneity test

For each categorical family:

- keep categories with at least 15 H081 trades;
- require at least two eligible categories;
- statistic = weighted between-group sum of squared deviations of group mean
  net P&L from the eligible-sample overall mean;
- permutation null: shuffle net_pnl_30 labels across eligible rows 5,000 times;
- deterministic seed = 20261005 plus family index;
- p = (1 + permutations with statistic >= observed) / 5001.

Apply Benjamini-Hochberg FDR across the seven omnibus p-values.

Interpret q < 0.05 as evidence of outcome heterogeneity for that *family*, not as
permission to trade its best category. Any category-specific strategy would
require a separately frozen design.

## Required reporting

For every category of every family report:
- trades;
- net expectancy;
- stress expectancy;
- total net P&L;
- PF;
- win rate.

Also report:
- joined H081 trade count;
- READY feature count;
- p and BH q for each family;
- descriptive R0-R4 breakdown;
- count of 2026 rows opened (must equal zero).

## Anti-cherry-picking rule

No family cutoff, category merge, minimum count, permutation count, cost,
horizon or H081 rule may change after results.

## Holdout

MES 2026 remains completely unopened.
