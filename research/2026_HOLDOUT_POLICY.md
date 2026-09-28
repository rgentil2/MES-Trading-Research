# 2026 Holdout Policy — Strategy Forward Test Only

Frozen: 2026-09-28.

## Correction

The project will **not** spend 2026 validating the volatility-regime engine in isolation.

R063 remains a frozen development component, but its practical value must be evaluated as part of a complete trading strategy.

The previously pre-registered R064 engine-only validation protocol is superseded and must not be run.

## 2026 role

2026 is reserved exclusively for the final forward / pseudo-forward evaluation of a fully frozen strategy.

Before any 2026 row is inspected for strategy outcomes, the strategy must specify:

- regime engine version;
- tradable setup;
- directional trigger;
- entry timing and price convention;
- stop-loss;
- profit target and/or time exit;
- re-entry policy;
- maximum entries per session;
- position size;
- commission and slippage;
- session cutoff;
- risk limits;
- all strategy parameters;
- pass/fail gates.

## Development data

2020–2025 may be used for:
- strategy discovery;
- parameter development;
- walk-forward / rolling robustness;
- sensitivity analysis;
- Monte Carlo;
- cost stress;
- neighboring-parameter stability.

Because 2020–2025 has already been heavily researched, none of it is considered pristine independent holdout data.

## Forward test

Only after the strategy is frozen will 2026 be opened.

The forward evaluation must:
- replay 2026 chronologically;
- forbid parameter changes after seeing results;
- include modeled costs;
- report trades in sequence;
- report net expectancy, PF, win rate, max drawdown, losing streak, monthly stability and regime attribution;
- compare realized results with development/Monte Carlo expectations.

## No partial use

2026 must not be opened for:
- feature selection;
- regime-engine tuning;
- threshold adjustment;
- stop/target optimization;
- choosing among competing strategy variants;
- subgroup rescue.

Opening any 2026 strategy result spends the holdout for that frozen strategy version.
