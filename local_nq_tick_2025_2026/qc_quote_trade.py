#!/usr/bin/env python3
"""Causal NQ Last/Bid/Ask microstructure diagnostics, Oct 2025-Jun 2026 only.

No market data/individual prices printed. Last(T) sees only Bid,Ask at t < T:
NinjaTrader separate export streams do not establish equal-timestamp ordering.
This does NOT validate executable fills or a trading strategy.
"""
from __future__ import annotations
from collections import Counter
from heapq import merge
from itertools import groupby
from pathlib import Path
import argparse
import json
import re
from qc_tick_day import check_day, file_for, parse_row, utc_bounds

KINDS = ("Last", "Bid", "Ask")
MAX_AGE_MS = (50, 100, 250, 500, 1000)
CONTRACT = re.compile(r"^NQ_(\d{2}-\d{2})_\d{4}_\d{8}_Tick_(?:Last|Bid|Ask)_ET0800_1200\.txt$")

def source_paths(root: Path, day: str) -> dict:
    d = check_day(day)  # check BEFORE searching any private file
    result = {k: file_for(root, d, k) for k in KINDS}
    contracts = []
    for p in result.values():
        match = CONTRACT.fullmatch(p.name)
        if match is None:
            raise ValueError("unexpected source name")
        contracts.append(match.group(1))
    if len(set(contracts)) != 1:
        raise ValueError("contract mismatch between Last/Bid/Ask")
    return result

def source_events(path: Path, kind: str, lo: int, hi: int, quality: Counter):
    previous = None
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            try:
                ts, px, vol = parse_row(line)
            except (ValueError, OverflowError):
                quality[kind+"_invalid"] += 1
                continue
            if previous is not None and ts < previous:
                raise ValueError(kind+" out-of-order timestamp")
            previous = ts
            quality[kind+"_rows"] += 1
            if not lo <= ts < hi:
                quality[kind+"_outside_ET_window"] += 1
                continue
            if abs(4*px - round(4*px)) > 1e-7:
                quality[kind+"_off_tick_grid"] += 1
            if kind == "Last" and vol <= 0:
                quality["Last_invalid_size"] += 1
            yield ts, kind, px

def analyze_streams(streams, *, day: str) -> dict:
    check_day(day)
    counts, age_bins, spreads, position = Counter(), Counter(), Counter(), Counter()
    bid = ask = None
    for ts, batch in groupby(merge(*streams, key=lambda x:x[0]), key=lambda x:x[0]):
        trades, bs, az = [], [], []
        for _, kind, px in batch:
            if kind == "Last":
                trades.append(px)
            elif kind == "Bid":
                bs.append(px)
            elif kind == "Ask":
                az.append(px)
            else:
                raise ValueError("unknown event kind")
        if trades and (bs or az):
            counts["last_sharing_timestamp_with_quote"] += len(trades)
        if len(set(bs)) > 1:
            counts["bid_timestamps_with_multiple_prices"] += 1
        if len(set(az)) > 1:
            counts["ask_timestamps_with_multiple_prices"] += 1
        for px in trades:
            counts["last_rows"] += 1
            if bid is None or ask is None:
                counts["last_without_prior_bbo"] += 1
                continue
            if not (bid[0] < ts and ask[0] < ts):
                raise ValueError("noncausal BBO state")
            counts["last_with_prior_bbo"] += 1
            age_ms = max(ts-bid[0], ts-ask[0]) / 10000
            for limit in MAX_AGE_MS:
                if age_ms <= limit:
                    counts[f"bbo_max_age_le_{limit}ms"] += 1
            label = ("le_50ms" if age_ms <= 50 else "50_to_250ms" if age_ms <= 250
                     else "250_to_1000ms" if age_ms <= 1000 else "gt_1000ms")
            age_bins[label] += 1
            if bid[1] > ask[1]:
                counts["last_crossed_bbo"] += 1
                continue
            if bid[1] == ask[1]:
                counts["last_locked_bbo"] += 1
                continue
            counts["last_positive_spread_bbo"] += 1
            if age_ms > 250:
                counts["last_positive_spread_stale_gt_250ms"] += 1
                continue
            counts["last_positive_spread_fresh_le_250ms"] += 1
            spread_ticks = round(4 * (ask[1]-bid[1]))
            spreads[str(spread_ticks) if spread_ticks <= 32 else "gt_32"] += 1
            if px < bid[1]:
                position["below_bid"] += 1
            elif px == bid[1]:
                position["at_bid"] += 1
            elif px > ask[1]:
                position["above_ask"] += 1
            elif px == ask[1]:
                position["at_ask"] += 1
            else:
                position["inside_spread"] += 1
        # Quotes at T become eligible for Last strictly later than T.
        # Same-time ordering inside each quote series is preserved by input order.
        if bs:
            bid = ts, bs[-1]
        if az:
            ask = ts, az[-1]
    return {
        "date_et":day, "status":"DIAGNOSTIC_ONLY" if counts["last_rows"] else "NO_TRADES",
        "causal_rule":"use only quotes strictly earlier than Last timestamp",
        "counts":dict(sorted(counts.items())),
        "max_quote_age_distribution":dict(sorted(age_bins.items())),
        "spread_ticks_for_positive_bbo_le_250ms":dict(sorted(spreads.items())),
        "last_location_for_positive_bbo_le_250ms":dict(sorted(position.items())),
        "classification_reconciles":sum(position.values())==counts["last_positive_spread_fresh_le_250ms"],
        "no_raw_prices_published":True,"no_trading_outcomes":True,
        "holdout_2026_jul_sep_opened":False,
        "limitations":["No global sequence for equal timestamps across NinjaTrader export streams",
                       "250ms is a predeclared diagnostic age threshold, not an optimized fill rule",
                       "BBO as-of does not establish latency, queue priority, or actual executable fills",
                       "Same-timestamp multiple Bid/Ask updates use the final side update only for later ticks"]
    }

def analyze_day(root: Path, day: str) -> dict:
    d = check_day(day)
    lo, hi = utc_bounds(d)
    paths = source_paths(root, day)
    qc = Counter()
    streams = (source_events(paths[k], k, lo, hi, qc) for k in KINDS)
    result = analyze_streams(streams, day=day)
    result["source_quality"] = dict(sorted(qc.items()))
    if any(qc[f"{k}_rows"] == 0 for k in KINDS):
        result["status"] = "MISSING_SOURCE"
    elif any(v for k,v in qc.items() if "invalid" in k or "outside_ET_window" in k or "off_tick_grid" in k):
        result["status"] = "SOURCE_REJECT"
    return result

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--day",required=True)
    parser.add_argument("--root",required=True,type=Path)
    args=parser.parse_args()
    report=analyze_day(args.root,args.day)
    print(json.dumps(report,indent=2))
    if report["status"]!="DIAGNOSTIC_ONLY":
        raise SystemExit(2)
