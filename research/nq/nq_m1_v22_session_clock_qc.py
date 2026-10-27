#!/usr/bin/env python3
"""NQ RTH clock verifier: 390 1m END timestamps in New York timezone.

Independent of the research engine's minute arithmetic, using IANA ZoneInfo.
This is ONLY a synthetic clock integrity test; it does not establish which
holidays had shortened real trading sessions.
"""
from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
NY=ZoneInfo("America/New_York")
UTC=timezone.utc
EARLIEST=time(9,31)
LATEST=time(16,0)
EXIT_LAST=time(11,29)
TOTAL_RTH_BARS=390
PERMITTED={2020,2021,2022}


def verify_rth_end_labels(day: str, utc_ends: list[datetime])->dict:
    d=date.fromisoformat(day)
    if d.year not in PERMITTED:
        raise PermissionError("Only development IST sessions may be validated")
    if len(utc_ends)!=TOTAL_RTH_BARS:
        raise ValueError("Incomplete RTH minute session; do not invent bars")
    prev_utc=None
    local=[]
    for t in utc_ends:
        if not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset()!=timedelta(0):
            raise ValueError("Require timezone-aware UTC end timestamps")
        if prev_utc is not None and t<=prev_utc:
            raise ValueError("Out of order or duplicate UTC end labels")
        prev_utc=t
        l=t.astimezone(NY)
        if l.date()!=d:
            raise ValueError("ET calendar date mismatch")
        local.append(l)
    start=datetime.combine(d, EARLIEST, NY)
    expected=[start+timedelta(minutes=i) for i in range(TOTAL_RTH_BARS)]
    if any(a!=b for a,b in zip(local,expected)):
        raise ValueError("RTH end labels must be 09:31..16:00 ET by exact minute")
    if local[118].time()!=EXIT_LAST:
        raise ValueError("11:29 close index changed")
    return {"date":day,"utc_open_end":utc_ends[0].isoformat(),
            "utc_last_end":utc_ends[-1].isoformat(),
            "et_zone":str(NY),"bars":390,"entry_signal_after_end_only":True,
            "flat_after_index":118,"holdouts":"SEALED"}


def synthetic_utc_ends(day: str):
    d=date.fromisoformat(day)
    start=datetime.combine(d,EARLIEST,NY)
    return [(start+timedelta(minutes=i)).astimezone(UTC) for i in range(TOTAL_RTH_BARS)]
