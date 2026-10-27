#!/usr/bin/env python3
"""V2 S1 infrastructure: reproducible IST-only engineering PILOT, not economic selection.

Reads only whitelist-approved 2020-22 source archive members through frozen V1
reader; never opens 2023/24 nor sealed H2025/26. Regenerates S0.4 manifest
from fixed seed and checks frozen SHA. Only evaluates prefix of complete days
and prefix of predeclared compatible candidates. No strategy optimization,
no individual-day PnL, no trade list and no raw price exported. This pilot
MUST NOT be interpreted as a D1/D2 gate, ISV, or trading approval.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v2_batch_preflight import make_manifest
from research.nq.nq_m1_v2_orders import simulate_day
from research.nq.nq_m1_v2_generator import fingerprint

FROZEN_COMPATIBLE_SHA256 = "e05f93e8bd73f9c43a2ed48dbc5b6ac813b9d81400309a026fb4de81389b0bf2"
FROZEN_BROAD_SHA256 = "677efc7e5962558a6d237034f48a078f1b8b50e350bb253b99c1bebe2d2381e8"
FROZEN_SEED = 20261027
MODE = "IST_ENGINEERING_PILOT_ONLY"
HOLDOUTS = "H2025_H2026_T_SEALED"


def frozen_batch() -> dict:
    manifest = make_manifest(broad_count=300, compatible_target=100, seed=FROZEN_SEED)
    if (manifest["compatible_manifest_sha256"] != FROZEN_COMPATIBLE_SHA256
            or manifest["broad_manifest_sha256"] != FROZEN_BROAD_SHA256
            or manifest["search_universe_blocks"] != 132
            or manifest["available_scalar_implementations"] != 38):
        raise RuntimeError("V2 FROZEN S0.4 candidate manifest mismatch: NO IST READ")
    return manifest


def pilot(zip_path: Path, max_days: int = 3, max_strategies: int = 5) -> dict:
    """Pilot is 1-10 earliest chronological complete IST days, 1-10 ASTs."""
    if not (type(max_days) is int and 1 <= max_days <= 10
            and type(max_strategies) is int and 1 <= max_strategies <= 10):
        raise ValueError("Pilot subset must be 1..10 sessions and 1..10 frozen strategies")
    manifest = frozen_batch()  # verify BEFORE price IO
    ids, bars, source = load_years(zip_path, (2020, 2021, 2022))
    if (source["years_opened"] != [2020, 2021, 2022]
            or source["holdout_2025_opened"] is not False
            or source["holdout_2026_opened"] is not False
            or len(ids) < max_days):
        raise RuntimeError("Source whitelist audit failed")
    results = []
    for s in manifest["compatible"][:max_strategies]:
        count = Counter()
        for day, one_day_bars in zip(ids[:max_days], bars[:max_days]):
            out = simulate_day(one_day_bars, s, day)
            count["days_simulated"] += 1
            count["model_fills"] += out["filled"]
            for name, n in out["rejected"].items():
                count["rejected_"+name] += n
            for name, n in out["signal_diagnostics"].items():
                count["diagnostic_"+name] += n
            if out["holdouts"] != "SEALED":
                raise RuntimeError("Strategy simulator unexpected year state")
        results.append({"id": s["id"], "fingerprint_sha256": fingerprint(s),
                        "engineering_counts": dict(count),
                        "status": "NOT_ECONOMICALLY_EVALUATED"})
    return {
        "status": MODE,
        "manifest_seed": FROZEN_SEED,
        "compatible_manifest_sha256": FROZEN_COMPATIBLE_SHA256,
        "source": source,
        "ist_sessions_evaluated": max_days,
        "strategy_count": max_strategies,
        "window": "09:30_11:29_ET_DST",
        "broker_fills_verified": False,
        "formal_G0_D0_D1_D2_passed": False,
        "market_pnl_published": False,
        "holdouts": HOLDOUTS,
        "strategies": results,
    }


def main() -> None:
    a=argparse.ArgumentParser()
    a.add_argument("--zip", required=True, type=Path)
    a.add_argument("--out", required=True, type=Path)
    a.add_argument("--max-days", type=int, default=3)
    a.add_argument("--max-strategies", type=int, default=5)
    args=a.parse_args()
    r=pilot(args.zip, args.max_days, args.max_strategies)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(r, indent=2)+"\n", encoding="utf8")
    print(json.dumps({
        "status":r["status"], "source": r["source"], "ist_sessions_evaluated": r["ist_sessions_evaluated"],
        "strategy_count":r["strategy_count"], "model_fills_total":sum(x["engineering_counts"].get("model_fills",0) for x in r["strategies"]),
        "holdouts":r["holdouts"]}, sort_keys=True))

if __name__ == "__main__":
    main()
