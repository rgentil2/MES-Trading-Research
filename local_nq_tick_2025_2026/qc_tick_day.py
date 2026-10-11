#!/usr/bin/env python3
"""Read-only NQ Last/Bid/Ask quality checks, 2025-Q4 through 2026-H1 ONLY.
Never loads 2026-07/08/09, never writes tick prices or raw events to logs.
Input is a single day's NinjaTrader export (UTC; prices on NQ 0.25 grid).
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import date, datetime, time, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

FIRST, LAST = date(2025, 10, 1), date(2026, 6, 30)
STAMP_RE = re.compile(r"^(\d{8}) (\d{6})(?: (\d{1,7}))?$")
TYPES = ("Last", "Bid", "Ask")


def check_day(text: str) -> date:
    d = date.fromisoformat(text)
    if not FIRST <= d <= LAST:
        raise ValueError("SEALED_OR_OUT_OF_SCOPE: allowed 2025-10-01..2026-06-30 only")
    return d


@lru_cache(maxsize=8192)
def utc_minute_100ns(yymmddhhmm: str) -> int:
    dt = datetime.strptime(yymmddhhmm, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * 10_000_000


def parse_row(row: str) -> tuple[int, float, float]:
    cells = row.rstrip("\r\n").split(";")
    if len(cells) != 3:
        raise ValueError("bad column count")
    m = STAMP_RE.fullmatch(cells[0])
    if m is None or int(m[2][-2:]) >= 60:
        raise ValueError("bad timestamp")
    ns100 = utc_minute_100ns(m[1] + m[2][:4]) + int(m[2][-2:]) * 10_000_000
    ns100 += int((m[3] or "0").ljust(7, "0"))
    price, volume = float(cells[1]), float(cells[2])
    if not math.isfinite(price) or not math.isfinite(volume) or price <= 0 or volume < 0:
        raise ValueError("bad price/volume")
    return ns100, price, volume


def utc_bounds(d: date) -> tuple[int, int]:
    ny = ZoneInfo("America/New_York")
    a = datetime.combine(d, time(8, 0), tzinfo=ny).astimezone(timezone.utc)
    b = datetime.combine(d, time(12, 0), tzinfo=ny).astimezone(timezone.utc)
    return int(a.timestamp()) * 10_000_000, int(b.timestamp()) * 10_000_000


def file_for(root: Path, day: date, kind: str) -> Path:
    if kind not in TYPES:
        raise ValueError("invalid data kind")
    sub = root / ("Tick_" + kind)
    name = f"NQ_*_{day:%Y%m%d}_Tick_{kind}_ET0800_1200.txt"
    matches = list(sub.glob(name))
    if len(matches) != 1:
        raise FileNotFoundError(f"{kind} for {day}: expected exactly one file, found {len(matches)}")
    return matches[0]


def check_file(path: Path, kind: str, lo: int, hi: int) -> dict:
    c = Counter()
    prev = None
    with path.open("r", encoding="utf-8-sig") as f:
        for raw in f:
            try:
                t, price, size = parse_row(raw)
            except (ValueError, OverflowError):
                c["invalid"] += 1
                continue
            c["rows"] += 1
            if prev is not None and t < prev:
                c["out_of_order"] += 1
            if prev == t:
                c["same_timestamp"] += 1
            prev = t
            if not lo <= t < hi:
                c["out_of_window"] += 1
            if abs(price * 4 - round(price * 4)) > 1e-7:
                c["off_tick_grid"] += 1
            if kind == "Last" and size <= 0:
                c["invalid_last_size"] += 1
            if t % 10_000_000:
                c["subsecond_rows"] += 1
    return {k: int(c[k]) for k in ("rows", "invalid", "out_of_order", "same_timestamp",
            "out_of_window", "off_tick_grid", "invalid_last_size", "subsecond_rows")}


def audit(root: Path, day: str) -> dict:
    # This gate runs BEFORE file glob/open; no holdout data can be read here.
    d = check_day(day)
    lo, hi = utc_bounds(d)
    files = {k: file_for(root, d, k) for k in TYPES}
    summary = {k: check_file(files[k], k, lo, hi) for k in TYPES}
    valid = all(summary[k]["rows"] > 0 and all(summary[k][x] == 0 for x in
        ("invalid", "out_of_order", "out_of_window", "off_tick_grid")) for k in TYPES)
    valid = valid and summary["Last"]["invalid_last_size"] == 0
    return {
        "scope": "2025-10..2026-06 only",
        "date_et": day,
        "status": "PRELIMINARY_PASS" if valid else "REJECT_OR_REVIEW",
        "tick_prices_emitted": False,
        "holdout_2026_jul_sep_opened": False,
        "source_types": summary,
        "note": "Preliminary file QC. Requires later Bid/Ask as-of matching, spread, missing minutes, rollover and minute-bar reconciliation. No real fill claims.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--day", type=str, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.root, a.day), indent=2))


if __name__ == "__main__":
    main()
