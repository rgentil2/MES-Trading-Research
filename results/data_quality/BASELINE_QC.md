# Baseline QC — MES raw dataset

## Dataset

- 28 quarterly MES contracts
- MAR20 through DEC26
- 1-minute Last exports from NinjaTrader
- 2,443,438 raw rows

## Continuous-series result

Using the frozen NinjaTrader-implied rollover rule:

- 2,365,496 retained rows
- 77,942 overlapping rows removed
- 27 contract transitions
- 0 duplicate timestamps
- Timestamps sorted ascending
- 0 OHLC relationship errors
- 0 non-positive-volume rows
- 0 prices outside the 0.25 MES tick grid

UTC coverage:

```text
2020-01-01 23:01:00
to
2026-09-25 21:00:00
```

Observed first-bar gaps after rollover are between 1 and 4 minutes. No synthetic bars are inserted.

## Frozen decision

**Backtest:** follow the rollover implicit in the NinjaTrader historical exports.

**Forward/live:** follow the same rollover convention configured in NinjaTrader.

The project does not use the previously considered 09:00 ET volume-comparison rule.

## Research constraint

Never calculate a return across a contract change without explicitly excluding or handling the rollover boundary. The processing pipeline marks the first retained row of each new contract with `is_rollover=True`.
