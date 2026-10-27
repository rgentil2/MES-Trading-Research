#!/usr/bin/env python3
"""NQ V2 S0.4: two-track immutable structural batch preflight with NO market reads.

Broad track never removes 132 blocks; it records supported-vs-unimplemented
status for EVERY proposed AST. Compatible track uses available SYNTHETIC
scalar implementations to construct a separate, auditable engineering cohort.
NO candidate has been executed on actual market prices or passed G0/D0/D1/D2.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from research.nq import nq_m1_v2_generator as g
from research.nq import nq_m1_v2_m1_engine as base
from research.nq import nq_m1_v2_orders as engine

ID = "NQ_M1_V2_S0_4_TWO_TRACK_STRUCTURAL_BATCH"
LABEL_BROAD = "STRUCTURAL_FULL_132_BROAD_RESEARCH_ONLY"
LABEL_COMPATIBLE = "SYNTHETICALLY_COMPATIBLE_38_NOT_PARITY_CERTIFIED"
LABEL_PENDING = "PENDING_IMPLEMENTATION_OR_ANCHOR_PARITY"
SEALED = "H2025_H2026_T_SEALED"


def _stable_sha(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _reason(s: dict) -> str | None:
    try:
        engine.validate_supported(s)
    except (base.UnsupportedV2Feature, ValueError, KeyError, TypeError) as e:
        return type(e).__name__ + ": " + str(e)[:150]
    return None


def make_manifest(broad_count: int = 300, compatible_target: int = 100,
                  seed: int = 20261027) -> dict:
    if not (1 <= broad_count <= 100000 and 1 <= compatible_target <= 100000):
        raise ValueError("Requested batch sizes must be 1..100000; continue in new batches")
    g.permitted_years_for_generation((2020, 2021, 2022))
    all_registry = g.read_registry()
    broad = g.generate_batch(broad_count, seed=seed, registry=all_registry)
    reviewed = []
    excluded = Counter()
    used = set()
    for item in broad:
        for name in ("long", "short"):
            for leaf in base._leaves(item[name]):
                used.add(leaf["indicator"]["name"])
        why = _reason(item)
        if why:
            excluded[why] += 1
        reviewed.append({
            "strategy": item,
            "classification": LABEL_PENDING if why else LABEL_COMPATIBLE,
            "technical_reason": why
        })
    subset = dict(all_registry)
    subset["entries"] = [e for e in all_registry["entries"]
                         if e["name"] in base.SUPPORTED_INDICATORS]
    if len(subset["entries"]) != 38:
        raise RuntimeError("Expected S0.3 synthetic 38-scalar subset")
    compatible = []
    deep_rejections = Counter()
    seen = {g.fingerprint(v["strategy"]) for v in reviewed}
    attempts = 0
    for batch in range(25):
        if len(compatible) >= compatible_target:
            break
        take = min(100000, max(100, 2*(compatible_target-len(compatible))))
        proposed = g.generate_batch(take, seed=seed+1000+batch, registry=subset)
        for candidate in proposed:
            attempts += 1
            fp = g.fingerprint(candidate)
            if fp in seen:
                deep_rejections["DUPLICATE_FINGERPRINT"] += 1
                continue
            seen.add(fp)
            why = _reason(candidate)
            if why:
                deep_rejections[why] += 1
                continue
            compatible.append(candidate)
            if len(compatible) >= compatible_target:
                break
    if len(compatible) != compatible_target:
        raise RuntimeError("Insufficient engineering compatible strategies; no silent quota rescue")
    return {
        "schema": ID,
        "status": "S0_STRUCTURAL_ONLY_NO_MARKET_OUTCOMES",
        "seed": seed,
        "search_universe_blocks": 132,
        "available_scalar_implementations": 38,
        "blocks_certified_against_independent_reference": 0,
        "broad_review_status": LABEL_BROAD,
        "compatible_status": LABEL_COMPATIBLE,
        "stage": "IST_ONLY_2020_2022_NOT_YET_RUN",
        "holdouts": SEALED,
        "generation": {"broad_n": len(reviewed),
                       "distinct_broad_blocks_seen": len(used),
                       "broad_synthetically_compatible_n":
                           sum(v["technical_reason"] is None for v in reviewed),
                       "broad_pending_implementation_n":
                           sum(v["technical_reason"] is not None for v in reviewed),
                       "compatible_n": len(compatible),
                       "compatible_attempts": attempts,
                       "broad_reasons": dict(sorted(excluded.items())),
                       "compatible_rejections": dict(sorted(deep_rejections.items()))},
        "broad_manifest_sha256": _stable_sha(reviewed),
        "compatible_manifest_sha256": _stable_sha(compatible),
        "broad": reviewed,
        "compatible": compatible
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--broad-count", type=int, default=300)
    p.add_argument("--compatible-target", type=int, default=100)
    p.add_argument("--seed", type=int, default=20261027)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    m = make_manifest(args.broad_count, args.compatible_target, args.seed)
    # Only structural ASTs/metadata, no prices or performance observations.
    args.output.write_text(json.dumps(m, indent=2, ensure_ascii=False)+"\n", encoding="utf8")
    print(json.dumps({k:v for k,v in m.items()
                      if k not in ("broad", "compatible", "generation")},sort_keys=True))
    print(json.dumps(m["generation"],sort_keys=True))


if __name__ == "__main__":
    main()
