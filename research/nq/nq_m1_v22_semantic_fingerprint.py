#!/usr/bin/env python3
"""NQ V2.2 AST semantic canonicalisation for multiplicity audits ONLY.

Boolean AND/OR are commutative and associative; duplicate identical leaves
are idempotent. Existing V2.1 generator fingerprint/manifest stays FROZEN.
Legacy predicates RISING/ABOVE_LAG and FALLING/BELOW_LAG are aliases in
the CURRENT IMPLEMENTATION. Never use this for execution by itself.
"""
from __future__ import annotations
import copy
from collections import Counter
import hashlib
import json
import math
from research.nq import nq_m1_v21_semantic_generator as source

ALIASES={"RISING":"ABOVE_LAG","FALLING":"BELOW_LAG"}
OPS={"AND","OR"}
OLD=frozenset(("RISING","FALLING","ABOVE_LAG","BELOW_LAG","CROSSES_OWN_LAG"))
LEVEL=source.PREDICATES_LEVEL


def _json(x):
    return json.dumps(x,sort_keys=True,separators=(",", ":"),ensure_ascii=True)


def _canon(tree:dict):
    op=tree["op"]
    if op in OPS:
        leaves=[]
        def collect(node):
            if node["op"]==op:
                collect(node["left"])
                collect(node["right"])
            else:
                leaves.append(_canon(node))
        collect(tree)
        distinct={_json(x):x for x in leaves}
        return {"op":op,"children":[distinct[k] for k in sorted(distinct)]}
    if op not in OLD|LEVEL:
        raise ValueError("Unrecognized AST node; no semantic hash")
    b=tree["indicator"]
    name=b["name"]
    if name not in source.USED:
        raise ValueError("Unimplemented indicator cannot receive a semantic fingerprint")
    params=copy.deepcopy(b["parameters"])
    if set(params)-source.USED[name]:
        raise ValueError("Inactive parameters cannot be semantically fingerprinted")
    r={"op":ALIASES.get(op,op),
       "indicator":{"name":name,"parameters":params}}
    if op in OLD:
        if "threshold" in tree:
            raise ValueError("Inactive threshold")
        lag=tree["lag_completed_bars"]
        if type(lag) is not int or not 1<=lag<=20:
            raise ValueError("Invalid causal lag")
        r["lag_completed_bars"]=lag
    else:
        if "lag_completed_bars" in tree:
            raise ValueError("Inactive causal lag")
        level=tree.get("threshold")
        if type(level) not in (int,float) or not math.isfinite(level):
            raise ValueError("Invalid active threshold")
        r["threshold"]=float(level)
    return r


def semantic_spec(strategy:dict)->dict:
    audit=source.semantic_audit(strategy)
    if audit["semantic_status"]!="SEMANTICALLY_EXECUTABLE_UNCERTIFIED":
        raise ValueError("Only executable typed ASTs can be compared semantically")
    if strategy["position_sizing"]!={"instrument":"NQ","contracts":1}:
        raise PermissionError("Only 1 NQ")
    return {"ast_version":strategy["ast_version"],
            "universe":"NQ_M1","position_sizing":{"instrument":"NQ","contracts":1},
            "long":_canon(strategy["long"]),
            "short":_canon(strategy["short"]),
            "entry_order":copy.deepcopy(strategy["entry_order"]),
            "exit":copy.deepcopy(strategy["exit"]),
            "signal_clock":strategy["signal_clock"],
            "signal_uses_completed_bars_only":strategy["signal_uses_completed_bars_only"],
            "flat_at_et":strategy["exit"]["flat_at_et"]}


def semantic_fingerprint(strategy:dict)->str:
    return hashlib.sha256(_json(semantic_spec(strategy)).encode("utf8")).hexdigest()


def audit_frozen_100()->dict:
    m=source.generate(100,seed=20261027,supported_only=True)
    seen={}
    group_sizes=Counter()
    eligible=0
    duplicates=[]
    pending=Counter()
    for row in m["rows"]:
        s=row["strategy"]
        try:
            key=semantic_fingerprint(s)
        except (ValueError,PermissionError) as e:
            pending[str(e)[:128]]+=1
            continue
        eligible+=1
        group_sizes[key]+=1
        if key in seen:
            duplicates.append({"candidate_id":s["id"],"same_semantics_as":seen[key]})
        else:
            seen[key]=s["id"]
    return {"status":"SEMANTIC_MULTIPLICITY_AUDIT_ONLY_NO_MARKET",
            "frozen_original_rows_sha256":m["rows_sha256"],
            "nq_only":True, "registered_blocks":132,
            "cohort_n":100,"executably_semantic_n":eligible,
            "canonical_groups":len(seen),
            "duplicate_groups":sum(v>1 for v in group_sizes.values()),
            "duplicate_candidates":len(duplicates),
            "duplicate_links":duplicates,
            "not_yet_executable":dict(sorted(pending.items())),
            "economic_metrics":None,
            "holdouts":"SEALED"}
