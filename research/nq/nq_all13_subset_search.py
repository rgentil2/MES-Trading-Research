#!/usr/bin/env python3
"""All-13 hypothesis topology, honest sample compatibility and Pareto candidate selection.

The nine/13-member investigation cannot be legitimately collapsed into one
equity curve while H(2020-24 minute) and T(2025-26 Last) have disjoint samples.
This executable enumerates *all* raw 8191 subsets, classifies admissibility,
and can rank 255 T subsets ONLY when an exact 8-parent per-session exposure
ledger has been independently reconciled. No synthetic return imputation.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

H=("H09","H56","H69","H74","H77")
T=("T05-377","T147","T186","T210","T212","T215","T217","T224")
IDS=H+T
T_SOURCE="NQ_LAST_2025_10_TO_2026_04"
MIN_T_N=35
MIN_POSITIVE_MONTHS=4
STOP_DAILY=-600
MAX_POS=1
MAX_ENTRIES=2
PREF=Path(__file__).with_name("NQ_ALL13_PORTFOLIO_SEARCH_PREREG_2026_10_13.json")

def load_frozen(path=PREF):
    x=json.loads(Path(path).read_text())
    if (x["design_id"]!="NQ-ALL13-SUBSET-D2-SHADOW-V1"
        or x["source_boundary"]["H"]["models"]!=list(H)
        or x["source_boundary"]["T"]["models"]!=list(T)
        or x["enumeration"]["number_raw_nonempty_subsets"]!=8191
        or x["enumeration"]["T_any_nonempty_subset_count"]!=255
        or x["source_boundary"]["same_day_H_T_cross_group_exposure"] is not False
        or x["source_boundary"]["no_holdout_reads"] is not True
        or x["selection_policy"]["PF_cost_stressed_min"]!=1.25
        or x["shared_execution"]["max_concurrent_positions"]!=MAX_POS
        or x["shared_execution"]["max_new_entries_per_day"]!=MAX_ENTRIES
        or x["shared_execution"]["closed_day_stop_usd"]!=STOP_DAILY):
        raise ValueError("ALL13_FROZEN_SOURCE_OR_SELECTION_POLICY_CHANGED")
    return x

def subsets(names):
    return (s for n in range(1,len(names)+1) for s in combinations(names,n))

def classify_subset(s):
    a=set(s)
    if not a or not a.issubset(set(IDS)):
        raise ValueError("INVALID_13_SUBSET")
    h=a.intersection(H);t=a.intersection(T)
    if h and t:
        return "CROSS_SAMPLE_NO_JOINT_EQUITY"
    if h:
        if len(h)==1:
            return "H_EXCLUSIVE_PARENT_OR_ROUTER_ALTERNATIVE"
        # H09+H56 already represented by H69 under one trade/day;
        # all other multi-choices share these same two parents.
        return "H_PARENT_ROUTER_DUPLICATION_OR_EQUIVALENT"
    return "T_SAME_CALENDAR_NEEDS_EIGHT_PARENT_EXPOSURE_LEDGER"

def topology():
    by=Counter(classify_subset(s) for s in subsets(IDS))
    expected={
        "CROSS_SAMPLE_NO_JOINT_EQUITY":7905,
        "H_EXCLUSIVE_PARENT_OR_ROUTER_ALTERNATIVE":5,
        "H_PARENT_ROUTER_DUPLICATION_OR_EQUIVALENT":26,
        "T_SAME_CALENDAR_NEEDS_EIGHT_PARENT_EXPOSURE_LEDGER":255,
    }
    if dict(by)!=expected or sum(by.values())!=8191:
        raise AssertionError("ALL13_ENUMERATION_PARITY")
    return {
        "stage":"ALL13_TOPOLOGY_VERIFIED_NO_NEW_MARKET_OUTCOMES",
        "universe":list(IDS),"raw_nonempty_subsets":8191,
        "coverage":dict(by),
        "H_alternative_choices":list(H),
        "T_member_set":list(T),
        "T_subsets_pending_single_account_replay":255,
        "cross_H_T_joint_net_and_DD":None,
        "T_best_subset":None,
        "D1_D2_formal":"BLOCKED",
        "samples_H":"2020-2024 NQ 1m DEV",
        "samples_T":"2025-10..2026-04 NQ Last DEV",
        "holdouts_opened":False,"new_market_data":False,
        "no_broker_fills_verified":True,
    }

def closed_metrics(trades,months):
    """Comparable only *within* one account/calendar and cost scenario."""
    net=0.;peak=0.;worst=0.;wins=losses=0.
    for p in trades:
        net+=p
        peak=max(peak,net)
        worst=max(worst,peak-net)
        if p>0:wins+=p
        elif p<0:losses+=-p
    return {
        "N":len(trades),"net_usd":round(net,2),
        "DD_closed_usd":round(worst,2),
        "PF":round(wins/losses,5) if losses else None,
        "net_DD":round(net/worst,5) if worst>0 else None,
        "expectancy_usd_trade":round(net/len(trades),3) if trades else None,
        "positive_months":sum(v>0 for v in months.values()),
    }

def pareto(ranked):
    """Ex-ante axes: +net, -closed DD, +per-trade expectancy.
    No artificial score gives bonus for an unobserved/small drawdown.
    """
    arr=list(ranked)
    selected=[]
    for x in arr:
        dom=False
        for y in arr:
            if x is y:continue
            if (y["net_plus10"]>=x["net_plus10"]
                and y["DD_plus10_closed"]<=x["DD_plus10_closed"]
                and y["expectancy_R"]>=x["expectancy_R"]
                and (y["net_plus10"]>x["net_plus10"]
                     or y["DD_plus10_closed"]<x["DD_plus10_closed"]
                     or y["expectancy_R"]>x["expectancy_R"])):
                dom=True;break
        if not dom:selected.append(x)
    return sorted(selected,key=lambda z:(-z["net_DD_plus10"],-z["expectancy_R"],z["ID"]))

def choose_candidates(summaries):
    """Fail closed: inputs MUST come from a reconciled 8-parent T ledger.
    No result, no synthetic portfolios or guessed 'best'.
    """
    if len(summaries)!=255 or len({tuple(x["members"]) for x in summaries})!=255:
        raise AssertionError("ALL_255_T_SUBSETS_REQUIRED")
    if set(tuple(x["members"]) for x in summaries)!=set(subsets(T)):
        raise AssertionError("T255_EXHAUSTIVE_NO_SELECTIVE_SUBSETTING")
    shortlisted=[]
    for r in summaries:
        if (r["sample"]!=T_SOURCE or r["reconciled_parent_count"]!=8
            or r["broker_fills_verified"] is not False
            or r["holdouts_opened"] is not False):
            raise ValueError("SOURCE_OR_PARENT_PARITY_NOT_PROVEN")
        if r["status"]!="ESTIMABLE":continue
        if (r["N"]>=MIN_T_N
            and r["positive_months_base"]>=MIN_POSITIVE_MONTHS
            and r["net_plus10"]>0
            and r["net_1p5"]>0
            and r["PF_plus10"] is not None and r["PF_plus10"]>=1.25
            and r["PF_1p5"] is not None and r["PF_1p5"]>=1.25
            and 0<r["DD_plus10_closed"]<=1500
            and r["expectancy_R"] is not None):
            z=dict(r)
            z["net_DD_plus10"]=round(r["net_plus10"]/r["DD_plus10_closed"],5)
            shortlisted.append(z)
    return {
        "stage":"POST_SELECTION_RETROSPECTIVE_T255_DEV_PARETO_ONLY",
        "evaluated_candidates":255,
        "passing_economic_filter_count":len(shortlisted),
        "pareto_candidates":pareto(shortlisted),
        "best_confirmed_portfolio":None,
        "look_elsewhere_bias":True,"holdouts_opened":False,
        "D2_formal":"BLOCKED",
    }

def markdown(z):
    s=z["coverage"]
    lines=[
        "# Universo completo de trece: auditoría de combinaciones",
        "",
        "**8191 subconjuntos enumerados; ningún resultado global artificial.**",
        "",
        "| Clase de subconjunto | Cantidad | Estado |",
        "|---|---:|---|",
        f"| H+T juntos | {s['CROSS_SAMPLE_NO_JOINT_EQUITY']} | No estimable: calendarios disjuntos |",
        f"| Solo H: alternativas únicas | {s['H_EXCLUSIVE_PARENT_OR_ROUTER_ALTERNATIVE']} | Comparar solo 2020–2024 minuto |",
        f"| Solo H: padres/routers duplicados | {s['H_PARENT_ROUTER_DUPLICATION_OR_EQUIVALENT']} | No contar alpha doble |",
        f"| Solo T | {s['T_SAME_CALENDAR_NEEDS_EIGHT_PARENT_EXPOSURE_LEDGER']} | Requiere motor de ocho padres |",
        "",
        "La búsqueda estructural incluye las 13, sin acreditar aún una cartera rentable.",
        "H+T no dispone de equity compartida. Ningún OOS abierto.",
        "255 alternativas T crean sesgo por búsqueda retrospectiva.",
    ]
    return "\n".join(lines)+"\n"

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    load_frozen()
    z=topology()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
    args.report.write_text(markdown(z))
    print("NQ_ALL13_TOPOLOGY_SAFE="+json.dumps({
        "models":len(z["universe"]),"raw_subsets":z["raw_nonempty_subsets"],
        "coverage":z["coverage"],"T_best_subset":None,
        "no_OOS":not z["holdouts_opened"]},sort_keys=True))
