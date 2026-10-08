#!/usr/bin/env python3
"""Development-only NinjaTrader NQ/MNQ minute-bar QC.

Only files inside development_2020_2024 are opened. The 2025 and 2026
directories are never opened, even when --holdout-metadata is provided.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

# Example: NQ_03-25_2024_Minute_Last.txt (MAR25's December 2024 bars).
PATTERN = re.compile(
    r"^(NQ|MNQ)_(03|06|09|12)-(20|21|22|23|24|25)_20(20|21|22|23|24)_Minute_Last[.]txt$"
)
TICK_SIZE = 0.25


def file_qc(path: Path) -> dict:
    match = PATTERN.fullmatch(path.name)
    if match is None:
        raise ValueError("Not a development-year bar partition: " + path.name)
    symbol, month, expiry_yy, bar_yy = match.groups()
    expected_year = 2000 + int(bar_yy)
    rows = bad_rows = outoforder = duplicates = 0
    first_ts = last_ts = None
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for raw in stream:
            sha.update(raw)
            line = raw.decode("utf-8-sig").strip()
            if not line:
                continue
            rows += 1
            try:
                cells = line.split(";")
                if len(cells) != 6:
                    raise ValueError("Expected timestamp + 5 OHLCV fields")
                timestamp = datetime.strptime(cells[0], "%Y%m%d %H%M%S")
                # Reject any accidental post-2024 content before price evaluation.
                if timestamp.year != expected_year:
                    raise ValueError("Timestamp outside permitted development partition")
                op, hi, lo, cl, volume = [float(v) for v in cells[1:]]
                prices = (op, hi, lo, cl)
                if not all(math.isfinite(value) for value in (*prices, volume)):
                    raise ValueError("Nonfinite value")
                if volume <= 0 or lo > min(op, cl) or hi < max(op, cl) or lo > hi:
                    raise ValueError("Invalid OHLC or volume")
                if any(abs(value / TICK_SIZE - round(value / TICK_SIZE)) > 1e-7
                       for value in prices):
                    raise ValueError("Price not on 0.25-point grid")
                if last_ts is not None:
                    if timestamp < last_ts:
                        outoforder += 1
                    elif timestamp == last_ts:
                        duplicates += 1
                if first_ts is None:
                    first_ts = timestamp
                last_ts = timestamp
            except (ValueError, OverflowError):
                bad_rows += 1
                if bad_rows > 100:
                    break
    status = ("QC_PASS_CANDIDATE"
              if rows >= 20000 and bad_rows == 0 and outoforder == 0 and duplicates == 0
              else "QC_REVIEW_REQUIRED")
    return {
        "symbol": symbol,
        "quarter": month + "-" + expiry_yy,
        "bar_year": expected_year,
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha.hexdigest(),
        "rows": rows,
        "first_utc": first_ts.isoformat() if first_ts else None,
        "last_utc": last_ts.isoformat() if last_ts else None,
        "bad_rows": bad_rows,
        "outoforder": outoforder,
        "duplicates": duplicates,
        "status": status,
        "reason": "Structural QC only; full session/rollover validation still required",
    }


def audit(root: Path) -> dict:
    # No access to held-out folders, even if they exist under root.
    development = root / "development_2020_2024"
    if not development.is_dir():
        development = root  # folder supplied directly by caller
    found = []
    for file in sorted(development.glob("*.txt")):
        if PATTERN.fullmatch(file.name) is None:
            raise ValueError("Nondevelopment filename in development: " + file.name)
        found.append(file_qc(file))
    expected = set()
    for sym in ("NQ", "MNQ"):
        for yy in range(20, 25):
            for month in ("03", "06", "09", "12"):
                expected.add(f"{sym}_{month}-{yy:02d}_20{yy:02d}_Minute_Last.txt")
            # The following year's MAR contract contains late December bars.
            expected.add(f"{sym}_03-{yy + 1:02d}_20{yy:02d}_Minute_Last.txt")
    observed = {item["file"] for item in found}
    missing = sorted(expected - observed)
    return {
        "scope": "2020-2024 development ONLY; 2025/2026 outcome files never opened",
        "expected_contract_partitions": len(expected),
        "received": len(found),
        "missing": missing,
        "files": found,
        "status": (
            "ALL_FILES_QC_PASS_CANDIDATE"
            if not missing and all(item["status"] == "QC_PASS_CANDIDATE" for item in found)
            else "SOURCE_INCOMPLETE"
        ),
    }


def holdout_inventory_metadata_only(root: Path) -> dict:
    # Path existence, filename, byte size only. No opening files or reading bars.
    result = {}
    for stage in ("validation_holdout_2025", "pseudo_forward_holdout_2026"):
        folder = root / stage
        result[stage] = [
            {"file": file.name, "bytes": file.stat().st_size}
            for file in sorted(folder.glob("*.txt"))
        ] if folder.is_dir() else []
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--holdout-metadata", action="store_true",
                        help="Names and byte sizes only; never open holdout files")
    args = parser.parse_args()
    report = audit(args.folder)
    if args.holdout_metadata:
        report["sealed_holdout_metadata_only"] = holdout_inventory_metadata_only(args.folder)
    output = args.output or args.folder / "nq_mnq_structural_qc.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "expected": report["expected_contract_partitions"],
        "received": report["received"],
        "missing_count": len(report["missing"]),
        "bad": [(item["file"], item["status"]) for item in report["files"]
                if item["status"] != "QC_PASS_CANDIDATE"],
    }, indent=2))


if __name__ == "__main__":
    main()
