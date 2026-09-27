# B01 Decision — R012–R015

## Multiple-testing result

All four hypotheses were frozen before execution and evaluated together with Benjamini-Hochberg FDR.

| Hypothesis | Stage | N | Mean effect | p-value | BH q-value | Block result |
|---|---|---:|---:|---:|---:|---|
| H017 / R012 | OOS 2025 | 84 | +47.813% RV discount | 9.34e-170 | 3.74e-169 | PASS |
| H018 / R013 | OOS 2025 | 63 | +7.602 bps | 0.1724 | 0.3448 | FAIL |
| H019 / R014 | DEV 2020–2024 | 958 | -0.331 bps reversion | 0.6201 | 0.6201 | FAIL |
| H020 / R015 | DEV 2020–2024 | 582 | +1.040 bps | 0.4833 | 0.6201 | FAIL |

## H017 — confirmed low-volatility persistence

R006 originally hypothesized volatility expansion after compression and found the opposite pattern in development data. H017 froze that opposite pattern and tested it independently on 2025.

2025 result:
- 84 events;
- mean future-RV discount: 47.813%;
- median discount: 48.181%;
- 95% CI: [44.439%, 51.187%];
- BH q-value: 3.74e-169.

H017 passes the pre-registered individual and block gates.

This is the first phenomenon in the project to survive a genuinely independent confirmatory test after being discovered in earlier data.

## Other hypotheses

H018 had positive economic magnitude but insufficient statistical evidence.
H019 showed no streak-exhaustion effect.
H020 met the 1 bps magnitude and 4/5 positive-year descriptive conditions, but its confidence interval crossed zero and it failed the statistical gate.

## Holdout status

2026 remains completely unopened for H017 and for the entire B01 block.

R012 remains active. R013–R015 are archived.

No 2026 pseudo-forward test may be run until a separate R012 2026 protocol is frozen.
