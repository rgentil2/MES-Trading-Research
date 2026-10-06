# MES Stage 2 — NinjaTrader Strategy Analyzer Parity Specification

Date: 2026-10-06.

2026 remains CLOSED.

## Objective

Before using NinjaTrader for optimization, verify that NinjaTrader reproduces the Python research engine closely enough that both are testing the same strategies.

The order of work is:

1. signal parity;
2. entry-time and side parity;
3. exit-rule parity;
4. commission / slippage parity;
5. only then performance comparison.

Do not judge a NinjaTrader PF until signal parity is established.

## Strategies and current centers

### PDC
- one MES
- gap 0.10-0.20 causal ATR
- prior close untouched first five RTH minutes
- first five minutes move toward PDC
- entry at next one-minute open
- TP = PDC
- SL = 0.30 ATR
- time exit = 11:30 ET
- USD High/Medium news policy T-5/T+5
- Python expected trades 2020-2025: 106

Local reference:
- 0.25 ATR / 0.30 ATR / 0.35 ATR all remain profitable.
- Keep 0.30 as center.

### POC Breakdown
- one MES
- open above prior RTH POC
- first POC contact closes below POC
- short next one-minute open
- fixed 15-minute exit for parity
- USD High/Medium news policy T-5/T+5
- Python expected trades 2020-2025: 109

Local references:
- H10 and H20 are robustness references only.
- Do NOT switch the parity build from H15 to H20 based on the already-seen development result.

### R072
- one MES
- wick threshold = 0.50
- cutoff = 11:00 ET
- one signal/session
- frozen R072/H081 direction
- next one-minute open
- fixed 30-minute exit
- USD High/Medium news policy T-5/T+5
- Python expected trades 2020-2025: 145

Status:
- provisional because the 20/30/40-minute neighborhood did not pass the local plateau gate.
- implement for parity/comparison, but do not final-freeze yet.

## Data

Use the same MES 1-minute historical source and rollover/merge convention as the Python repository.

The Python timestamp convention is NinjaTrader end-of-bar labeling:
- first RTH 1-minute bar is labeled 09:31 ET;
- a market entry generated from a signal bar is modeled at the next bar OPEN.

All clocks must be America/New_York / Eastern Time with DST respected.

## NinjaTrader configuration for parity

Use Strategy Analyzer with:
- MES
- 1-minute primary data series
- one contract
- Calculate = OnBarClose for bar-defined signals
- no unrestricted optimization
- use local historical data corresponding to the research source

Signal logic should run in OnBarUpdate and, if additional series are later added, BarsInProgress must explicitly gate the logic.

NinjaTrader documents that OnBarUpdate frequency is governed by Calculate and multi-series scripts must filter BarsInProgress. It also provides configurable historical fill processing and slippage in Strategy Analyzer.

## Historical fills

Parity and realism are two distinct passes.

### Pass A — signal parity
Compare signal/entry timestamps and directions. Ignore small P&L differences.

Required:
- same setup dates;
- same side;
- same intended next-bar entry;
- no 2026.

Target:
- >=99% date/side match;
- investigate every mismatch.

### Pass B — execution parity
Then compare:
- entry price;
- stop/target fill;
- news forced-flat price;
- timed exit;
- commissions.

NinjaTrader has its own historical fill algorithm and optionally a higher-resolution secondary series. Historical P&L differences caused by intrabar order sequencing must be documented rather than hidden.

For PDC, Python uses the conservative rule:
- target only touched -> PDC;
- stop only touched -> stop;
- stop and target in same 1m bar -> STOP FIRST;
- stop gap-through -> worse of bar open and stop;
- target gap improvement is not credited.

A NinjaTrader high-resolution/tick pass may later replace that conservative ambiguity with more realistic sequencing, but it must be labeled as an execution refinement rather than signal optimization.

## News policy

USD High/Medium scheduled events:
- flatten at T-5;
- Python models this as OPEN of the one-minute bar beginning at T-5;
- block new entry T-5 through T+5 inclusive;
- news-flat takes precedence over that minute's stop/target path.

The same frozen 2020-2025 Forex Factory calendar must be used for parity.

## Costs

Python:
- base RT cost = $4.38
- stress RT cost = $6.57

For NinjaTrader, configure commissions as closely as possible to $4.38 round trip for the parity run.
Then separately test slippage using Strategy Analyzer's slippage setting.

## Expected Python center metrics

Stage-1 center results including frozen news policy:

PDC SL 0.30 ATR:
- trades 106
- PF 1.5355
- expectancy +$5.888/trade
- stress expectancy +$3.698
- max DD ~$211.95
- 9/12 positive semesters

POC H15:
- trades 109
- PF 1.3026
- expectancy +$4.278/trade
- stress expectancy +$2.088
- max DD ~$332.57
- 5/12 positive semesters

R072 H30:
- trades 145
- PF 1.3018
- expectancy +$7.525/trade
- stress expectancy +$5.335
- max DD ~$497.55
- 7/11 positive observed semesters

These are reference values, not NinjaTrader targets to optimize toward.

## Stage-2 acceptance

A strategy passes implementation parity when:
1. signal date/side match >=99%;
2. trade-count difference <=1%;
3. all systematic timestamp discrepancies are explained;
4. no unexplained rollover/timezone mismatch remains;
5. P&L differences can be attributed to documented fill/commission/slippage rules.

Only after this may NinjaTrader be used for Stage 3 robustness tests.

## Current advancement

- PDC: eligible for Stage 2.
- POC: eligible for Stage 2.
- R072: eligible for parity only, not final freeze.
- 2026: CLOSED.
