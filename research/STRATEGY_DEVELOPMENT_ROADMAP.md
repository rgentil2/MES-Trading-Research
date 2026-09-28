# Strategy Development Roadmap Before 2026

## Current state

The project has a frozen volatility-regime engine (R063) that forecasts movement magnitude but does not predict direction or create trades.

Therefore the next objective is not additional engine validation. It is to build a complete executable strategy around independently motivated price triggers.

## Phase S1 — Strategy architecture

Develop candidate trading architectures on 2020–2025.

Priority family:

### Dynamic-range breakout conditioned by regime

Use the most recently completed 15-minute block as the tradable structure.

Candidate logic:
- trade only when R063 state is HIGH;
- place a directional trigger beyond the completed 15-minute block high/low;
- enter only after price confirms which side breaks;
- no directional prediction is made before the breakout;
- LOW/NORMAL are no-trade unless separately pre-registered.

This directly uses what R063 predicts well: **large future movement**, while price action itself supplies direction.

Alternative candidates may include:
- HIGH-regime pullback continuation after a confirmed break;
- NORMAL→HIGH state transition breakout;
- volatility-conditioned trailing exit.

Candidates must be frozen in blocks before testing to reduce adaptive selection.

## Phase S2 — Execution design

For any candidate that shows positive gross behavior, freeze and test:
- next-bar vs stop-entry execution;
- stop location;
- target / trailing / time exit;
- one trade per session or limited re-entry;
- 11:30 ET maximum new-entry rule;
- positions may close after 11:30 ET;
- MES $5/point;
- commission $1.88 RT;
- slippage baseline $2.50 RT.

No 2026 data.

## Phase S3 — Strategy gate

A strategy may advance only if development/robustness is credible, targeting:

- >=200 total trades where feasible;
- net expectancy >0;
- PF >=1.20 in broad development;
- stable neighboring parameters;
- majority of walk-forward windows profitable;
- positive under 1.5x modeled costs;
- drawdown compatible with intended prop-firm limits;
- no single year/month dominating total P&L.

## Phase S4 — Robustness

Before 2026:
- walk-forward;
- parameter sensitivity;
- execution/cost stress;
- Monte Carlo >=10,000 equity paths;
- drawdown and losing-streak percentiles;
- prop-firm loss-limit risk.

## Phase S5 — Freeze strategy

Create a versioned final strategy specification and SHA/commit manifest.

Only then may 2026 be opened.

## Phase S6 — 2026 forward / pseudo-forward

Replay 2026 chronologically using the frozen strategy with no tuning.

Decision is PASS / FAIL / INSUFFICIENT SAMPLE exactly as pre-registered.
