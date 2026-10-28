#!/usr/bin/env python3
"""NQ V2.2 AST G0/D0 structural preflight: NO MARKET/ECONOMIC PASS.

Regulatory boundary: only registry-valid parameters and causal NQ-only V2.1
ASTs can be placed on the engineering shortlist. Unsupported indicators
remain in the 132-block broad research log as PENDING_IMPLEMENTATION.
This is NOT a legacy cohort-equivalent G0/D0 formal adapter (parity pending).
"""
from __future__ import annotations
import math
from collections import Counter

from research.nq import nq_m1_v2_generator as generator
from research.nq import nq_m1_v21_semantic_generator as v21
from research.nq import nq_m1_v22_semantic_fingerprint as canonical

STATUS="NQ_V22_STRUCTURAL_PRE_D0_NOT_LEGACY_G0_D0_NOT_ECONOMIC"


def validate_registry_parameters(strategy:dict)->dict:
    registry=generator.read_registry()
    lookup={entry["name"]:entry for entry in registry["entries"]}
    reasons=[]
    for side in ("long","short"):
        for leaf in v21._iter_leaves(strategy[side]):
            blk=leaf["indicator"]
            name=blk["name"]
            declared=lookup.get(name)
            if declared is None:
                reasons.append(f"UNREGISTERED_INDICATOR:{name}")
                continue
            params=blk["parameters"]
            for key,value in params.items():
                domain=declared["parameters"].get(key)
                if domain is None:
                    reasons.append(f"UNREGISTERED_PARAMETER:{name}:{key}")
                    continue
                if isinstance(domain,list) and len(domain)==2 and all(type(v) in (int,float) for v in domain):
                    if type(value) not in (int,float) or not math.isfinite(value) or not domain[0]<=value<=domain[1]:
                        reasons.append(f"OUT_OF_RANGE_PARAMETER:{name}:{key}")
                elif isinstance(domain,list) and value not in domain:
                    reasons.append(f"INVALID_ENUM_PARAMETER:{name}:{key}")
            op=leaf["op"]
            if op in v21.PREDICATES_LEVEL:
                if name not in v21.THRESHOLDS:
                    reasons.append(f"UNREGISTERED_LEVEL_DOMAIN:{name}")
                else:
                    # Threshold is an active PREDICATE parameter, not a
                    # calculator field; domains should reflect original
                    # candidate catalogue and sign conventions.
                    keys=[k for k in v21.THRESHOLDS[name]
                          if k in declared["parameters"]]
                    t=leaf.get("threshold")
                    if not keys or type(t) not in (float,int) or not math.isfinite(t):
                        reasons.append(f"INVALID_TYPED_LEVEL:{name}")
                    elif not any(
                        isinstance(declared["parameters"][k],list)
                        and len(declared["parameters"][k])==2
                        and all(type(z) in (int,float) for z in declared["parameters"][k])
                        and declared["parameters"][k][0]<=t<=declared["parameters"][k][1]
                        for k in keys
                    ):
                        reasons.append(f"OUTSIDE_DECLARED_TYPED_LEVEL:{name}")
    sem=v21.semantic_audit(strategy)
    if sem["semantic_status"]!="SEMANTICALLY_EXECUTABLE_UNCERTIFIED":
        reasons+=sem["reasons"]
    if reasons:
        return {"status":STATUS,"executable_mechanics":False,
                "reason_codes":sorted(set(reasons)),"semantic_hash":None,
                "economics_certified":False}
    return {"status":STATUS,"executable_mechanics":True,
            "reason_codes":[],"semantic_hash":canonical.semantic_fingerprint(strategy),
            "economics_certified":False}


def frozen_cohort_diagnostic():
    batch=v21.generate(100,seed=20261027,supported_only=True)
    rows=[validate_registry_parameters(x["strategy"]) for x in batch["rows"]]
    counts=Counter(reason for row in rows for reason in row["reason_codes"])
    return {"status":STATUS,"source_sha":batch["rows_sha256"],
            "nq_only":True,"rows":len(rows),
            "structurally_executable_count":sum(x["executable_mechanics"] for x in rows),
            "blocked":sum(not x["executable_mechanics"] for x in rows),
            "reason_counts":dict(sorted(counts.items())),
            "not_legacy_g0_d0_parity":True,"market_data_opened":False,
            "holdouts":"SEALED"}


if __name__=="__main__":
    import json
    print(json.dumps(frozen_cohort_diagnostic(),sort_keys=True,indent=2))
