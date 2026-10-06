# MES Strong-Hypothesis Temporal Review — OR15 R1 and Value Area R4

Date: 2026-10-06.
2026 remained closed.

## OR15 High-Vol + non-Chop (R1)

Historical implementation was successfully reconstructed with high fidelity:
- 2020-2024 event count: **106**, exactly matching the historical reference.
- reconstructed 60m directional mean: **+6.4788 bps**, matching the historical +6.48 bps.
- reconstructed 15m directional mean: +2.719 bps.

Tradable one-MES implementation:
- signal: first close above OR15 High by 11:30 ET;
- R1 known pre-open;
- entry: next 1m open;
- exit: fixed 60m close;
- cost: $4.38 RT;
- no stop/target.

2020-2024:
- N=106
- expectancy = +$9.48/trade
- PF = 1.267
- stress expectancy = +$7.29
- max DD = $1,111
- worst trade = -$304

2025:
- N=42
- expectancy = -$2.21/trade
- PF = 0.958
- stress expectancy = -$4.40
- max DD = $873
- worst trade = -$416

2020-2025:
- N=148 (~2.06/month)
- expectancy = +$6.16/trade
- PF = 1.152
- stress expectancy = +$3.97
- max DD = $1,111
- 5/8 observed semesters positive
- 4/5 observed years positive, but 2020 is one trade and 2023 has no R1 events.

Temporal concentration:
- 2022 contains 67/148 trades.
- 2022H1 is negative; 2022H2 is very strong.
- 2024H1 negative; 2024H2 very strong.
- 2025H1 negative; 2025H2 positive with only 8 trades.

Decision:
**Do not add OR15 R1 to the active MES candidate set.**
The underlying phenomenon is real and historically reproduced, but the fixed tradable implementation has weak PF, large drawdown, strong temporal concentration and deteriorates in 2025.
Retain only as a watchlist/research family; no stop optimization is justified before the stronger PDC/POC/R072 candidates are resolved.

## Value Area Re-entry -> POC in R4

Historical reference:
- R4 = Low Vol + Chop.
- Open outside prior 70% value area.
- Re-enter by a close inside value area before 10:30 ET.
- Prior POC still untouched.
- POC target.
- reference 2020-2024: N=37, 25 hits, 67.6%.

Recovered profile specification:
- prior RTH 1m HLC3;
- each minute volume assigned to nearest 0.25 price bin;
- 70% Value Area around POC.

Current reconstruction:
- N=29, 19 POC hits, 65.5%.

The hit rate is close, but the event count misses the historical reference by 8 trades. Therefore this is **not an exact reconstruction**.

Decision:
**Do not use the reconstructed P&L to accept or reject Value Area R4.**
Because the setup is low frequency and lower priority than PDC/POC/R072, park it unless the original value-area implementation can be recovered exactly.

## Current active MES research set

Treat each as one independent MES contract for now:
1. PDC small-gap + candidate SL 0.30 ATR + PDC target + news policy.
2. POC Breakdown + 15m exit + news policy.
3. R072 + 30m exit + news policy.

OR15 R1: watchlist only.
Value Area R4: parked pending exact reconstruction.

Portfolio risk sizing is deferred; each setup is currently analyzed as one independent MES contract.
