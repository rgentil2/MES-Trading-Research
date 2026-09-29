#!/usr/bin/env python3
"""QC NinjaTrader ES Tick Last / Minute Last exports without opening holdout outcomes."""

from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import hashlib


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tick-last", required=True, type=Path)
    ap.add_argument("--minute-last", required=True, type=Path)
    args = ap.parse_args()

    tick = args.tick_last
    minute = args.minute_last

    rows = bid_gt_ask = nonpos = offgrid = 0
    sides = Counter()
    first_ts = last_ts = None

    with tick.open("r", encoding="utf-8", newline="") as f:
        for line in f:
            if not line.strip():
                continue
            ts, last_s, bid_s, ask_s, vol_s = line.rstrip("\r\n").split(";")
            last = float(last_s)
            bid = float(bid_s)
            ask = float(ask_s)
            vol = int(vol_s)
            rows += 1
            first_ts = first_ts or ts
            last_ts = ts
            bid_gt_ask += bid > ask
            nonpos += vol <= 0
            offgrid += abs(last * 4 - round(last * 4)) > 1e-9
            if last >= ask:
                sides["ask"] += 1
            elif last <= bid:
                sides["bid"] += 1
            elif bid < last < ask:
                sides["inside"] += 1
            else:
                sides["other"] += 1

    minute_rows = sum(1 for line in minute.open("r", encoding="utf-8") if line.strip())

    print(f"tick_rows={rows}")
    print(f"tick_first={first_ts}")
    print(f"tick_last={last_ts}")
    print(f"minute_rows={minute_rows}")
    print(f"bid_gt_ask={bid_gt_ask}")
    print(f"volume_nonpositive={nonpos}")
    print(f"last_off_025_grid={offgrid}")
    print(f"trade_classification={dict(sides)}")
    print(f"tick_sha256={sha256(tick)}")
    print(f"minute_sha256={sha256(minute)}")


if __name__ == "__main__":
    main()
