# MES Stage 1 — Local Robustness Refinement

Status: locked before the local-neighborhood results are inspected.

2026 remains strictly closed.

## Objective

Refine the three active MES strategy candidates without unrestricted optimization.
Each strategy is treated independently as one MES contract.

The purpose is to test whether the current central parameter sits on a local performance plateau.
The objective is NOT to choose whichever value maximizes historical P&L.

## Common assumptions

- MES point value: $5.
- Base round-trip cost: $4.38.
- Stress round-trip cost: $6.57.
- Forex Factory USD High/Medium rule remains fixed:
  - flatten at T-5 at the OPEN of the T-5 minute;
  - block new entries T-5 through T+5 inclusive.
- 2020-2025 may be used only as development/robustness characterization.
- 2026 forbidden.

## PDC neighborhood

Everything remains fixed except the stop distance:
- 0.25 ATR
- 0.30 ATR — current center
- 0.35 ATR

Fixed:
- gap 0.10-0.20 ATR
- first five minutes toward untouched PDC
- next-minute-open entry
- TP=PDC
- exit no later than 11:30 ET
- news rule fixed

Local robustness interpretation:
- all three values should have PF >=1.25;
- all three should have positive stress expectancy;
- at least two of three should have >=7 positive semesters;
- 0.30 ATR should not be an isolated spike: at least one neighbor must have expectancy >=80% of 0.30 expectancy and PF no more than 0.15 below 0.30.

If satisfied, retain 0.30 as the neutral center rather than switching to the historical best neighbor.

## POC neighborhood

Everything remains fixed except the time exit:
- 10 minutes
- 15 minutes — current center
- 20 minutes

Fixed:
- prior POC breakdown signal
- short at next-minute open
- news rule fixed
- no stop/target introduced

Local robustness interpretation:
- both neighboring horizons must have positive stress expectancy;
- both neighbors PF >=1.10;
- at least one neighbor expectancy >=70% of the 15-minute center or exceeds it without materially worse DD.

If satisfied, retain 15 minutes as the central specification.

## R072 neighborhood

Everything remains fixed except the time exit:
- 20 minutes
- 30 minutes — current center
- 40 minutes

Fixed:
- wick threshold 0.50
- cutoff 11:00 ET
- one signal/session
- next-minute-open entry
- direction frozen by R072/H081
- news rule fixed
- no stop/target added

Local robustness interpretation:
- both neighboring horizons must have positive stress expectancy;
- both neighbors PF >=1.10;
- at least one neighbor expectancy >=70% of the 30-minute center or exceeds it without materially worse DD.

If satisfied, retain 30 minutes as the central specification.

## Prohibited

- no additional parameter values after results;
- no combinations of stop + entry + target + timing sweeps;
- no changing the news window;
- no selecting months/years to improve metrics;
- no 2026.
