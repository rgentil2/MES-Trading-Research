# OR15 R1 High-Vol + Non-Chop — Temporal Hierarchy Diagnostic

Status: locked before re-evaluating outcomes.

## Historical signal recovered

The reconstruction reproduces the historical 2020-2024 count of **106 OR15 R1 upper-breakout events**.

Signal:
- OR15 = first 15 RTH one-minute bars (NinjaTrader EOB labels 09:31-09:45 ET).
- first one-minute CLOSE above OR15 High, independently of any prior lower-side break.
- signal must occur by 11:30 ET.
- one upper-breakout signal maximum per session.

Regime R1, known before the RTH open:
- daily RTH ATR14 / prior close volatility state;
- High Vol = yesterday's ATR14/Close above causal rolling P67 of prior history;
- ER10 = abs(Close_t-Close_t-10) / sum(abs daily close changes, 10);
- Chop = ER10 at/below causal rolling P33;
- non-Chop = ER10 above P33;
- R1 = High Vol + non-Chop.
- rolling comparison window = 252 prior sessions; reconstruction warm-up = 126 observations.
- simple 14-session ATR is used because this reconstruction reproduces the historical event count exactly.
- today uses only information available through yesterday's completed RTH session.

## Outcomes

Phenomenon diagnostics:
- directional 15m, 30m, 60m return in bps from signal-bar close.

Tradable implementation diagnostic:
- long entry at next one-minute bar OPEN;
- exit at close exactly 60 minutes after signal bar;
- one MES contract;
- base cost $4.38 RT;
- stress cost $6.57 RT;
- no stop or target;
- no news filter in this first block.

## Evaluation hierarchy

- week/month: diagnostic only;
- quarter/semester: evaluation;
- year: robustness;
- R1 definition: explanation/context, not retuned.

## Historical fidelity checks

For 2020-2024:
- expected event count = 106;
- historical reference 60m directional effect ≈ +6.48 bps.

If the reconstruction materially misses these references, interpretation stops and the implementation is revisited.

## Statistical status

- 2020-2024 reproduces an already-known result and is not new validation.
- 2025 may be inspected because this OR15/R1 specification was frozen before the present re-evaluation.
- 2026 remains strictly closed.
