# R072 Live NinjaScript Port Specification

Status: implementation specification. 2026 remains CLOSED.

## Why this is simpler than the full R063 stack

R072 does **not** require the pre-open/overnight R063 prediction layer.
Its signal uses only:

1. the dynamic 15-minute volatility state;
2. the H017 low-volatility override;
3. the 15-minute wick-rejection/failure rule;
4. first valid signal per session;
5. frozen news and execution rules.

Therefore a deployable R072 can be ported without reimplementing every R063 research output.

## A. Session/data convention

- MES 1-minute bars.
- Research RTH bars are EOB labeled 09:31 through 16:00 ET.
- Complete research session = exactly 390 consecutive RTH bars.
- 2020-2025 parity may use the Python eligible-session CSV to isolate data-vendor differences.
- Live implementation must not depend on a historical session whitelist.
- New contract sessions do not reset the dynamic percentile history unless explicitly stated by Python (they currently do not).

## B. Dynamic 15-minute volatility state

For each complete RTH session construct 15-minute blocks:

- block 0 = bars 09:31..09:45
- block 1 = 09:46..10:00
- block 2 = 10:01..10:15
- ...
- R072 only needs block ends through the 11:00 cutoff.

For each block:

range15_bps = (block_high - block_low) / block_close * 10000

For every block_id independently maintain the **last 60 prior observations** of range15_bps.

Before classifying today's block:
- q20 = 20th percentile of prior 60 values
- q80 = 80th percentile of prior 60 values
- current observation is excluded.

Pandas default linear quantile must be reproduced:
- sort n values;
- index = (n-1)*p;
- linearly interpolate between floor(index) and ceil(index).

Classification order:
1. if value <= q20 -> LOW
2. else if value >= q80 -> HIGH
3. else NORMAL

Warm-up:
- no state until 60 prior observations exist for that block_id.

## C. H017 override

H017 is causal and minute-of-day specific.

For each one-minute bar:
1. compute one-minute log return versus the prior consecutive bar;
2. compute RV30 over the 30 consecutive one-minute returns ending at the current bar:

rv30 = sqrt(sum(r1^2 over 30)) * 10000

For each minute-of-day independently maintain the prior 60 valid rv30 observations.

h017_threshold = prior-60 10th percentile of rv30 at that same minute.

Eligible H017 detection:
- minute >= 10:01 ET
- minute <= 11:30 ET
- rv30 and threshold available
- rv30 <= threshold

The first qualifying minute in a session becomes h017_time.

Dynamic engine state at a block close:
- raw state normally remains unchanged;
- if block_end >= h017_time and block_end <= h017_time + 30 minutes:
  engine_state = LOW
  engine_stage = H017_OVERRIDE
- otherwise engine_state = raw state.

## D. R072 signal

Only evaluate completed 15-minute blocks with engine_state == HIGH.

For each block:
- block_open = first bar open
- block_close = last bar close
- block_high = max high
- block_low = min low
- range = high-low

upper_wick_ratio = (high - max(open,close)) / range
lower_wick_ratio = (min(open,close) - low) / range

Frozen wick threshold = 0.50.

Inverse/failure direction:
- upper_wick_ratio >= 0.50 AND close < open -> LONG
- lower_wick_ratio >= 0.50 AND close > open -> SHORT

Cutoff:
- signal EOB timestamp <= 11:00 ET.

Session selection:
- take only the chronologically first valid R072 signal per session.

Entry:
- market entry at next one-minute open.

## E. Execution

Frozen center:
- quantity = 1 MES
- H30 timed exit
- USD High/Medium news policy:
  - no entry T-5 through T+5 inclusive
  - existing position flattened at T-5 open
- no fixed TP
- catastrophe stop candidate = 0.70 ATR14_prev
- catastrophe stop is a risk cap, not the alpha source.

ATR14_prev:
- causal Wilder ATR14 over complete prior RTH true ranges;
- same-contract prior close used in true range;
- on rollover session true range = session high-low;
- today's stop uses ATR known before today's open.

## F. Required parity ladder

### Level 1 — replay
Use R072SignalReplayParity.cs + frozen Python signals.
Target = 145 post-news trades.

This validates timing, fills, news exit and risk layer independently of signal generation.

### Level 2 — engine block parity
Full C# engine outputs, for each block:
- range15_bps
- q20/q80
- raw state
- h017_time
- engine state
- wick ratios
- candidate direction

Compare against R072_ENGINE_BLOCK_REFERENCE.csv.

Acceptance targets:
- >=99% block-state match after warm-up
- 100% direction match on common candidate blocks
- every systematic difference explained by source-data/session differences.

### Level 3 — generated signal parity
Without Python signal replay, C# must independently generate:
- the same pre-news first signals;
- after news blocking, approximately/exactly 145 trades.

Only after Level 3 can R072 be considered a deployable NinjaScript signal generator.

## G. No tuning during port

The port may fix implementation differences only.

Do not change:
- rolling window 60
- q20/q80
- H017 q10
- wick threshold 0.50
- cutoff 11:00
- H30
- 0.70 catastrophe stop
- news window.

Any parameter change is new research and cannot be justified with 2026.
