# MES Stage 4 — Final Freeze Protocol

Status: PRE-REGISTERED BEFORE 2026.

A strategy can be frozen only after its allowed Stage-2/3 work is complete.

## Required frozen fields

For each strategy:
- version ID
- signal definition
- data/session convention
- side
- entry condition
- entry order type/timing
- quantity = 1 MES
- stop
- target
- timed exit
- news rule
- rollover rule
- commission assumption
- slippage assumption
- behavior on ambiguous intrabar fills
- behavior when data is missing
- behavior at session boundaries

## Current intended candidates

### PDC
Expected freeze center unless Stage 2 exposes an implementation error:
- gap 0.10 <= abs(open-PDC)/ATR14 < 0.20
- causal prior-session Wilder ATR14
- PDC untouched first 5 RTH minutes
- fifth-minute close progresses toward PDC
- next-minute-open entry
- TP=PDC
- SL=0.30 ATR
- time exit 11:30 ET
- USD High/Medium T-5/T+5
- 1 MES

### POC
Expected parity center:
- previous RTH POC
- open above POC
- first contact closes below
- short next-minute open
- H15 time exit
- news rule
- 1 MES

H15 may only be changed before freeze if a separately preregistered decision rule authorizes it. Historical superiority of H20 alone is insufficient.

### R072
Not currently eligible to freeze because Stage-1 plateau failed.
It may be dropped, kept as provisional research, or subjected to a separately preregistered robustness study before freeze.

## Freeze rule

Once a strategy is marked FROZEN:
- no parameter changes;
- no adding filters;
- no changing news handling;
- no selecting a better horizon;
- no changing stop/target;
- no use of 2026 to refine it.

Only frozen strategies may enter Stage 5.
