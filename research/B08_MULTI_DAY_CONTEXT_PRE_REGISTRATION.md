# B08 / R043–R047 — Multi-Day Context

Frozen before execution: 2026-09-28.

## Common policy

- Development pool: 2020–2025.
- 2026 remains completely unopened.
- Full RTH sessions only.
- Multi-day windows require the current contract and every session in the relevant lookback to be the same contract.
- Rolling thresholds use only prior eligible observations.
- H054–H058 are frozen simultaneously.
- Primary p-values use BH/FDR.

## H054 / R043 — Three-Day Streak Exhaustion

Signal:
- previous 3 RTH sessions all have the same non-zero open-to-close return sign;
- absolute sum of those 3 returns >= q60 of prior 60 eligible 3-day streak magnitudes.

Hypothesis:
the next session's first 30 minutes revert against the streak.

Outcome:
```text
Reversion30 =
-sign(3day_streak) × current_open_to_10:00_return × 10,000
```

Gate:
- N >= 150;
- mean >= +1 bps;
- CI > 0;
- >=4/6 positive years;
- BH q <0.05.

## H055 / R044 — Five-Day Range Breakout at the Open

Prior five-session range:
- high = max RTH High over prior 5 same-contract sessions;
- low = min RTH Low over prior 5 same-contract sessions.

Signal:
- current RTH Open > prior5 High => bullish breakout;
- current RTH Open < prior5 Low => bearish breakout.

Hypothesis:
the first 30 minutes continue in breakout direction.

Gate:
- N >= 150;
- mean >= +1 bps;
- CI >0;
- >=4/6 positive years;
- BH q <0.05.

## H056 / R045 — Five-Day Overextension Reversion

Five-day total return:
```text
R5D = log(previous_session_close / open_5_sessions_ago)
```

Signal:
- |R5D| >= q80 of prior 60 eligible five-day returns.

Hypothesis:
the next opening 30 minutes revert against the five-day move.

Gate:
- N >= 200;
- mean >= +1 bps;
- CI >0;
- >=4/6 positive years;
- BH q <0.05.

## H057 / R046 — High Five-Day Range Persistence

Five-day range regime feature:
```text
AvgRange5 = mean RTH range_bps over prior 5 sessions
```

Signal:
- AvgRange5 >= q80 of prior 60 eligible AvgRange5 observations.

Outcome:
```text
OpeningExpansionPct =
(current opening30 range / prior60 opening30 mean - 1) × 100
```

Gate:
- N >= 200;
- mean expansion >= +10%;
- CI >0;
- >=4/6 positive years;
- BH q <0.05.

## H058 / R047 — Low Five-Day Range Persistence

Signal:
- AvgRange5 <= q20.

Outcome:
```text
OpeningDiscountPct =
(1 - current opening30 range / prior60 opening30 mean) × 100
```

Same gate as H057.

## Holdout

2026 is not used anywhere in B08.
