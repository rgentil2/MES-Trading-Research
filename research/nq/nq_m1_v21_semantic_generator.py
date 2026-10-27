#!/usr/bin/env python3
"""NQ-only V2.1 semantic combinatorial generator, NO market price reads.

Preserves V2.0 registered 132-block universe and original frozen manifests.
Creates two disjoint audit trails:
  broad: all 132 blocks (uncertified blocks must remain pending)
  engineering: only the 38 mathematically implemented scalar blocks
For implemented blocks, indicator parameters are limited to fields USED by the
calculator. Threshold parameters are moved to explicit CAUSAL comparisons,
so they change the actual signal, rather than inflating fingerprint counts.

Research structure only. Genetic recombination is structural, NOT IST fitness
optimization. No ISV/holdout reads and no economic verdicts.
"""
from __future__ import annotations
from collections import Counter
import copy
import hashlib
import json
import math
import random

from research.nq import nq_m1_v2_generator as old
from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
from research.nq.nq_m1_v2_semantic_lint import USED
from research.nq import nq_m1_v2_orders as orders

AST_VERSION = "NQ_M1_V21_TYPED_THRESHOLDS_2026_10_27"
PREDICATES_LEVEL = frozenset(("ABOVE_LEVEL", "BELOW_LEVEL",
                              "CROSS_ABOVE_LEVEL", "CROSS_BELOW_LEVEL"))
PREDICATES_LAG = frozenset(("RISING", "FALLING", "ABOVE_LAG",
                            "BELOW_LAG", "CROSSES_OWN_LAG"))
THRESHOLDS = {
    "RSI": ("lower_level", "upper_level"),
    "MFI": ("threshold",),
    "CMO": ("threshold",),
    "CCI": ("threshold",),
    "Z-Score": ("z_threshold",),
    "Relative Volume": ("ratio_threshold",),
}
NO_MARKET_DATA = "AST_ONLY_NO_MARKET_NO_ECONOMIC_SCORE"
DEFAULT_SEED = 20261027


def _parameters(item: dict, rng: random.Random) -> dict:
    name = item["name"]
    if name not in USED:
        # Keep the entire proposed block in broad discovery; do NOT promote.
        return old.sample_parameters(rng, item["parameters"])
    permitted = USED[name]
    ranges = {k:v for k,v in item["parameters"].items() if k in permitted}
    sampled = old.sample_parameters(rng, ranges)
    if set(sampled) != permitted.intersection(item["parameters"]):
        raise ValueError("Missing active calculator parameter")
    return sampled


def _level(item: dict, rng: random.Random) -> float | None:
    fields = THRESHOLDS.get(item["name"], ())
    possible = [field for field in fields if field in item["parameters"]]
    if not possible:
        return None
    field = rng.choice(possible)
    sampled = old.sample_parameters(rng, {field: item["parameters"][field]})
    level = float(sampled[field])
    if not math.isfinite(level):
        raise ValueError("Nonfinite level")
    return level


def leaf(rng: random.Random, entries: list[dict]) -> dict:
    item = rng.choice(entries)
    result = {
        "indicator":{"registry_id":item["id"], "name":item["name"],
                     "parameters":_parameters(item, rng)}
    }
    level = _level(item, rng) if item["name"] in SUPPORTED_INDICATORS else None
    # Every threshold generated must be USED by the predicate.
    if level is not None and rng.random() < .75:
        result["op"] = rng.choice(sorted(PREDICATES_LEVEL))
        result["threshold"] = level
    else:
        result["op"] = rng.choice(sorted(PREDICATES_LAG))
        result["lag_completed_bars"] = rng.randint(1,20)
    return result


def expr(rng: random.Random, entries: list[dict], max_conditions: int = 8) -> dict:
    if not isinstance(max_conditions, int) or not 1 <= max_conditions <= 100:
        raise ValueError("Per-batch engineering maximum must be in 1..100")
    leaves = [leaf(rng, entries) for _ in range(rng.randint(1,max_conditions))]
    while len(leaves)>1:
        left=leaves.pop(rng.randrange(len(leaves)))
        right=leaves.pop(rng.randrange(len(leaves)))
        leaves.append({"op":rng.choice(("AND","OR")), "left":left,"right":right})
    return leaves[0]


def strategy(rng: random.Random, entries: list[dict], max_conditions: int = 8) -> dict:
    order = rng.choice(old.ENTRY_TYPES)
    return {
        "schema":old.STRATEGY_SCHEMA,
        "ast_version":AST_VERSION,
        "universe":"NQ_M1",
        "position_sizing":{"instrument":"NQ","contracts":1},
        "market_data_years_permitted_for_discovery":[2020,2021,2022],
        "signal_clock":"America/New_York",
        "bars_are_end_labeled":True,
        "signal_uses_completed_bars_only":True,
        "long":expr(rng, entries, max_conditions),
        "short":expr(rng, entries, max_conditions),
        "entry_order":{"kind":order,
                       "offset_ticks":rng.randint(0,32) if order!="MARKET" else 0,
                       "expiry_bars":rng.randint(1,30) if order!="MARKET" else 1},
        "exit":old.sample_exit(rng)
    }


def semantic_audit(s: dict) -> dict:
    reasons=[]
    if s.get("ast_version") != AST_VERSION:
        reasons.append("INVALID_V21_AST_VERSION")
    if s.get("position_sizing") != {"instrument":"NQ","contracts":1}:
        reasons.append("NQ_ONE_CONTRACT_REQUIRED")
    if s.get("market_data_years_permitted_for_discovery") != [2020,2021,2022]:
        reasons.append("IST_ONLY_REQUIRED")
    for direction in ("long", "short"):
        for node in _iter_leaves(s[direction]):
            name = node["indicator"]["name"]
            params = node["indicator"]["parameters"]
            if name not in SUPPORTED_INDICATORS:
                reasons.append("PENDING_INDICATOR_IMPLEMENTATION:"+name)
                continue
            if set(params) != USED[name].intersection(params.keys()):
                reasons.append("INACTIVE_CALCULATOR_PARAMETERS:"+name)
            op=node["op"]
            if op in PREDICATES_LEVEL:
                if "lag_completed_bars" in node:
                    reasons.append("INERT_LAG_ON_LEVEL_PREDICATE:"+name)
                if name not in THRESHOLDS:
                    reasons.append("LEVEL_WITHOUT_REGISTERED_DOMAIN:"+name)
                if "threshold" not in node or not isinstance(node["threshold"], (float,int)):
                    reasons.append("MISSING_NUMERIC_THRESHOLD:"+name)
            elif op in PREDICATES_LAG:
                if "threshold" in node:
                    reasons.append("INERT_THRESHOLD_ON_LAG_PREDICATE:"+name)
                if type(node.get("lag_completed_bars")) is not int or not 1<=node["lag_completed_bars"]<=20:
                    reasons.append("MISSING_OR_INVALID_LAG:"+name)
            else:
                reasons.append("UNKNOWN_PREDICATE:"+name)
    if not reasons:
        try:
            orders.validate_supported(s)
        except (ValueError,TypeError,KeyError) as exc:
            reasons.append("TECHNICAL_ORDER_OR_ANCHOR:"+str(exc)[:120])
    return {"semantic_status":"SEMANTICALLY_EXECUTABLE_UNCERTIFIED" if not reasons
            else "PENDING_TECHNICAL_IMPLEMENTATION",
            "reasons":reasons}


def _iter_leaves(tree):
    if tree["op"] in ("AND","OR"):
        yield from _iter_leaves(tree["left"])
        yield from _iter_leaves(tree["right"])
    else:
        yield tree


def _strip_identity(s):
    return {k:copy.deepcopy(v) for k,v in s.items() if k not in ("id","lineage")}


def _mutation(rng: random.Random, s: dict, entries: list[dict], max_conditions: int):
    c=_strip_identity(s)
    part=rng.choice(("long","short","exit","entry_order"))
    if part in ("long","short"):
        c[part]=expr(rng,entries,max_conditions)
    elif part=="exit":
        c["exit"]=old.sample_exit(rng)
    else:
        typ=rng.choice(old.ENTRY_TYPES)
        c["entry_order"]={"kind":typ,
                          "offset_ticks":rng.randint(0,32) if typ!="MARKET" else 0,
                          "expiry_bars":rng.randint(1,30) if typ!="MARKET" else 1}
    return c


def generate(count: int, seed: int = DEFAULT_SEED, supported_only: bool = False,
             max_conditions: int = 8, random_fraction: float = .60) -> dict:
    old.permitted_years_for_generation(old.IST)
    if not 1 <= count <= 100_000 or not 0 <= random_fraction <= 1:
        raise ValueError("Invalid bounded batch size or structural random fraction")
    r=old.read_registry()
    entries=[e for e in r["entries"] if not supported_only
             or e["name"] in SUPPORTED_INDICATORS]
    if supported_only and len(entries)!=38:
        raise RuntimeError("38 mathematical implementations expected")
    rng=random.Random(seed)
    pool, seen, rows=[],set(),[]
    rejects=Counter()
    tries=0
    while len(rows)<count:
        tries+=1
        if tries>500*count:
            raise RuntimeError("Not enough distinct specifications")
        if not pool or rng.random()<random_fraction:
            s=strategy(rng,entries,max_conditions)
            kind="RANDOM"
        elif len(pool)>1 and rng.random()<.7:
            a,b=rng.sample(pool,2)
            s=_strip_identity(a)
            for key in rng.sample(("long","short","exit","entry_order"),
                                  rng.randint(1,3)):
                s[key]=copy.deepcopy(b[key])
            kind="STRUCTURAL_CROSSOVER"
        else:
            s=_mutation(rng,rng.choice(pool),entries,max_conditions)
            kind="STRUCTURAL_MUTATION"
        key=old.fingerprint(s)
        if key in seen:
            rejects["DUPLICATE_AST_FINGERPRINT"]+=1
            continue
        seen.add(key)
        audit=semantic_audit(s)
        s["id"]=f"NQ-M1-V21-{seed}-{len(rows)+1:06d}"
        s["lineage"]={"method":kind,"fingerprint_sha256":key}
        rows.append({"strategy":s,"audit":audit})
        pool.append(s)
        rejects.update(audit["reasons"])
    material=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    return {
        "schema":AST_VERSION,
        "status":NO_MARKET_DATA,
        "search_scope":"ENGINEERING_38" if supported_only else "BROAD_132",
        "registered_blocks_total":132,
        "implemented_scalar_blocks":38,
        "nq_only_one_contract":True,
        "holdouts":"2023_2024_NO_FIT__2025_2026_SEALED",
        "count":len(rows),
        "attempts":tries,
        "seed":seed,
        "random_fraction":random_fraction,
        "rows_sha256":hashlib.sha256(material).hexdigest(),
        "semantic_executable_count":sum(x["audit"]["semantic_status"]==
                                        "SEMANTICALLY_EXECUTABLE_UNCERTIFIED" for x in rows),
        "technical_reasons":dict(sorted(rejects.items())),
        "rows":rows
    }


def main():
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser()
    p.add_argument("--count",type=int,default=300)
    p.add_argument("--seed",type=int,default=20261027)
    p.add_argument("--scope",choices=("broad","engineering"),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    manifest=generate(a.count,a.seed,a.scope=="engineering")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in manifest.items() if k!="rows"},sort_keys=True))

if __name__=="__main__":
    main()
