#!/usr/bin/env python3
"""NQ M1 V2 semantic-parameter audit; fail-closed before ECONOMIC promotion.

The V2.0 broad registry deliberately includes parameters for future typed
comparison blocks. In the currently executable V2 AST leaf predicates
(RISING/FALLING/ABOVE_LAG/BELOW_LAG/CROSSES_OWN_LAG), numeric thresholds
like RSI lower_level and relative-volume ratio_threshold are NOT consumed.
Counting their variants as independent discoveries would be misleading.
Record them all but label semantic promotion as BLOCKED until moved into
a causal typed-predicate AST or removed from the active fingerprint.

No prices or market outcomes are read by this module.
"""
from __future__ import annotations
from collections import Counter
from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
from research.nq.nq_m1_v2_batch_preflight import make_manifest

BASE_PRICE_MA = frozenset(("SMA","EMA","WMA","RMA"))
MULTI = {"VWAP": {"anchor"},
         "OBV": set(),
         "True Range": set(),
         "Bollinger Bandwidth": {"period","std_multiplier"}}
# All remaining supported scalar calculations currently use period only.
USED = {name: ({"period","source"} if name in BASE_PRICE_MA
               else MULTI[name] if name in MULTI else {"period"})
        for name in SUPPORTED_INDICATORS}
OLD_PREDICATES = frozenset(("RISING","FALLING","ABOVE_LAG","BELOW_LAG","CROSSES_OWN_LAG"))
STATUS = "S0_SEMANTIC_AUDIT_ONLY_NOT_ECONOMIC_GATE"


def _leaves(x):
    if x["op"] in ("AND","OR"):
        yield from _leaves(x["left"])
        yield from _leaves(x["right"])
    else:
        yield x


def audit_strategy(s: dict) -> dict:
    counts = Counter()
    names = set()
    diagnostics = []
    for side in ("long","short"):
        for leaf in _leaves(s[side]):
            op=leaf["op"]
            if op not in OLD_PREDICATES:
                raise ValueError("Unversioned new predicate not eligible for V2.0 audit")
            block=leaf["indicator"]
            name=block["name"]
            if name not in USED:
                counts["not_implemented"] += 1
                continue
            active=USED[name]
            given=set(block["parameters"])
            unknown=given-active
            names.add(name)
            counts["leaves"] += 1
            if unknown:
                counts["leaves_with_inactive_parameters"] += 1
                counts["inactive_parameter_fields"] += len(unknown)
                diagnostics.append({"side":side,"indicator":name,
                                    "fields": sorted(unknown)})
    return {"id":s.get("id"), "indicator_names": sorted(names),
            "counts":dict(counts),
            "inactive": diagnostics,
            "economic_promotion":"BLOCKED_UNUSED_PARAMETERS" if diagnostics or
                counts["not_implemented"] else "SEMANTICALLY_CONSISTENT_NOT_VALIDATED"}


def audit_frozen_100() -> dict:
    m=make_manifest(300,100,20261027)
    reports=[audit_strategy(s) for s in m["compatible"]]
    blockers=[r for r in reports if r["economic_promotion"]=="BLOCKED_UNUSED_PARAMETERS"]
    totals=Counter()
    by_name=Counter()
    for r in reports:
        totals.update(r["counts"])
        for d in r["inactive"]:
            by_name[(d["indicator"], ",".join(d["fields"]))] += 1
    return {"status": STATUS,"no_market_data": True,
            "compatible_manifest_sha256":m["compatible_manifest_sha256"],
            "registered_blocks":132,
            "current_scalar_calculators":len(SUPPORTED_INDICATORS),
            "candidate_count":len(reports),
            "blocked_candidates":len(blockers),
            "unblocked_not_formally_validated":len(reports)-len(blockers),
            "total_fields":dict(totals),
            "inactive_by_indicator":{f"{k[0]}: {k[1]}":v for k,v in sorted(by_name.items())},
            "formal_gates_run":False}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_frozen_100(),indent=2,sort_keys=True))
