# MES — Forex Factory News Filter Re-test — Decision

Status: **FAIL AS RESCUE / KEEP RULE FOR FUTURE TESTS**

Run date: 2026-10-05.

Rule was frozen before outcomes:
- USD only.
- High + Medium Forex Factory events.
- Flat at T-5 minutes.
- No new entry T-5 through T+5.
- Existing bars retained.
- Scheduled events only.

Calendar:
- 2,856 event rows.
- 1,911 unique event timestamps.
- 935 event rows between 09:30-11:30 ET, representing 770 unique timestamps.
- 5 All-Day events excluded because they have no causal clock time.

Results:

| Strategy | Base PF | News PF | Base net pts/trade | News net pts/trade | Base years + | News years + |
|---|---:|---:|---:|---:|---:|---:|
| OR15 first breakout 30m | 0.840 | 0.809 | -0.752 | -0.769 | 1/5 | 1/5 |
| Academic overnight reversal | 0.879 | 0.891 | -0.606 | -0.520 | 0/5 | 1/5 |
| Academic intraday momentum | 0.735 | 0.754 | -1.328 | -1.205 | 0/5 | 0/5 |
| Public ORB15 1.5R | 1.004 | 0.945 | +0.042 | -0.491 | 3/5 | 1/5 |
| Market Profile return-to-value | 1.883 | 1.883 | +3.013 | +3.013 | 3/5 | 3/5 |

The Market Profile result is unchanged because none of its 27 trades intersected the blackout rule.

Decision:
- The user's historical news rule is operationally valid and should remain available for future strategy tests.
- It does **not** explain the previous MES failures and does not create a promotable strategy.
- Do not tune High-only/Medium-only or ±3/±10 minute variants after seeing these results.
- Proceed to the agreed externally sourced NinjaTrader-forum strategy challenge.
