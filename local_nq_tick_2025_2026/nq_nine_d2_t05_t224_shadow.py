#!/usr/bin/env python3
"""Nine-ID D2 SHADOW exercise: eight old + T224, only valid shared pair T05/T224.

Immutable T05 Last legacy stress + T224 frozen D1 BASE; single-account chronology.
No H+T merge; H periods differ. No fill/trailing/OOS validation or D1 formal pass.
All trade/day paths remain PRIVATE inside GH runner and are deleted.
"""
from __future__ import annotations
import argparse
import json
from bisect import bisect_right
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import islice
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import (
    BASE,STRESS,frozen_t05,trace,owner_policy,et_edge
)
from nq_t08_risk_audit import Envelope
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade
from nq_t210_t224_five_economic_shadow import CASES,MODELED
from nq_t209_t228_structural_d0 import (
    registry,month_guard,classify_day,stats,bar_subset,regime_signal,IDS,CASE
)
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t133_t168_d1_engine import model_one,first_future_groups

NINE=("H09","H56","H69","H74","H77","T05-377","T147","T186","T224")
EXPECTED_T05_N=115
EXPECTED_T05_NET=5102.50
EXPECTED_T224_N=106
EXPECTED_T224_NET=1256.00
MAX_TRADES_DAY=2
STOP_DAY_USD=-600
PRE="research/nq/NQ_NINE_D2_T05_T224_SHARED_ACCOUNT_SHADOW_PREREG_2026_10_13.md"
T05_STATUS="SYNTHETIC_FILL_MODEL_ONLY"


def t224_plan(events,day,reg):
    """D0 frozen side/stop and D1 frozen model; no result-driven filters."""
    labels=classify_day(events,day,reg)
    if set(labels)!=set(IDS):raise AssertionError("WHOLE20_CAUSAL_LABELS_REQUIRED")
    if labels["T224"]!=CASE:return labels,None
    block=next(b for b in reg["blocks"] if b["block"]=="D")
    lo=et_edge(day,*map(int,block["window_et"][0].split(":")))
    hi=et_edge(day,*map(int,block["window_et"][1].split(":")))
    bars=completed_bars_by_print_count(events,day,(377,4181,10946))
    e377=bars[377]
    anchor=next((b for b in e377 if lo<=b.end_timestamp<hi),None)
    if anchor is None:raise AssertionError("T224_CASE_ANCHOR_MISSING")
    times=[e[0] for e in events]
    ix=e377.index(anchor)
    if ix<1:raise AssertionError("NO_PREVIOUS_E377")
    prev_macro=next((b for b in reversed(bars[4181])
                     if b.end_timestamp<anchor.end_timestamp),None)
    if prev_macro is None:raise AssertionError("T224_MACRO_NOT_READY")
    e=stats(bar_subset(events,times,anchor))
    d=stats(bar_subset(events,times,e377[ix-1]))
    m=stats(bar_subset(events,times,prev_macro))
    long=next((b for b in reversed(bars[10946])
               if b.end_timestamp<anchor.end_timestamp),None)
    lng=stats(bar_subset(events,times,long)) if long else None
    side=regime_signal("T224",e,d,m,lng)
    if side not in (-1,1):raise AssertionError("T224_FROZEN_SIDE_LOST")
    stop=F(e["profile"]["lo"]-2 if side>0 else e["profile"]["hi"]+2)
    risk=side*(e["end"]-stop)
    if not(8<=risk<=400 and risk*(5 if risk*5<=250 else F(1,2))<=250):
        raise AssertionError("T224_D0_FROZEN_RISK_PARITY_LOST")
    groups,covered=first_future_groups(events,anchor.end_timestamp,15)
    modeled=model_one(groups,side,stop,1.5,15,anchor.end_timestamp,covered)
    return labels,{"timestamp":anchor.end_timestamp,"side":side,
                   "stop":stop,"groups":groups,"model":modeled}


def trace_t224_end(plan):
    """Reconstruct exit timestamp without changing frozen model_one economics.

    Never infer intra-timestamp ordering of Last. Ambiguous entry group => block.
    """
    z=plan["model"]
    if z["status"]!=MODELED:
        return None
    if z["entry_group_ambiguous"]:
        raise ValueError("T224_ENTRY_SAME_TIMESTAMP_STOP_ORDER_UNRESOLVED")
    g=plan["groups"]
    if not g:return None
    side,stop=plan["side"],plan["stop"]
    first=g[0]
    worst=F(first[2]) if side>0 else F(first[1])
    entry=worst+side*2
    risk=side*(entry-stop)
    target=entry+side*F(3,2)*risk
    for ts,low,high in g[1:]:
        touches_stop=low<=stop if side>0 else high>=stop
        touches_target=high>=target if side>0 else low<=target
        if touches_stop:
            if z["exit_reason"] not in ("STOP","STOP_FIRST"):
                raise AssertionError("T224_STOP_CHRONOLOGY_DISAGREES_WITH_MODEL")
            return (first[0],ts)
        if touches_target:
            if z["exit_reason"]!="TARGET":
                raise AssertionError("T224_TARGET_CHRONOLOGY_DISAGREES_WITH_MODEL")
            return (first[0],ts)
    if z["exit_reason"]!="TIME_EXIT_ADVERSE_GROUP":
        raise AssertionError("T224_TIMEOUT_CHRONOLOGY_DISAGREES_WITH_MODEL")
    if g[-1][0]<=first[0]:
        raise ValueError("T224_TIMEOUT_WITHOUT_POST_ENTRY_OBSERVATION")
    return (first[0],g[-1][0])


def replay_account(events,day,bars,t05,t224=None):
    """Single shared account; prices use original parent engines, not a new alpha."""
    times=[r[0] for r in events]
    tagged=[(ts,0,side,BASE) for ts,side,_ in t05]
    if t224 is not None:
        tagged.append((t224["timestamp"],1,t224["side"],"T224"))
    tagged.sort(key=lambda x:(x[0],x[1]))
    last_exit=-1;closed=0.
    rt=Counter()
    trades=[]
    for ts,_,side,owner in tagged:
        if rt["executed"]>=MAX_TRADES_DAY or closed<=STOP_DAY_USD:
            rt["capacity"]+=1
            continue
        if ts<=last_exit:
            rt["overlap"]+=1
            rt[f"overlap_{owner}"]+=1
            continue
        if owner==BASE:
            policy=owner_policy(BASE,bars,STRESS)
            r=simulate_single_trade(
                islice(events,bisect_right(times,ts),None),
                Signal(day,ts,side),policy)
            if r["status"]!=T05_STATUS:
                if r["status"] in ("ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS",
                                   "UNRESOLVED_END_OF_LAST_DATA"):
                    raise ValueError("T05_UNRESOLVED_PAPER_EXPOSURE")
                rt["rejected_t05"]+=1
                continue
            val=round(r["estimated_net_usd"],2)
            end=r["exit_timestamp"]
            if end<=ts:raise AssertionError("T05_INVALID_EXIT_TIME")
            st15=val
        elif owner=="T224":
            r=t224["model"]
            if r["status"]!=MODELED:
                rt["rejected_t224"]+=1
                continue
            bounds=trace_t224_end(t224)
            if bounds is None:raise AssertionError("T224_NO_REPLAY_BOUNDS")
            if bounds[0]<=ts or bounds[1]<bounds[0]:
                raise AssertionError("T224_REPLAY_INCORRECT_ENTRY_AFTER_DECISION")
            val=round(r["net_usd"],2)
            st15=round(r["stress_1_5x_usd"],2)
            end=bounds[1]
        else:
            raise AssertionError("INVALID_OWNER")
        closed=round(closed+val,2)
        last_exit=end
        rt["executed"]+=1
        rt[f"executed_{owner}"]+=1
        trades.append({"owner":owner,"net":val,"net_plus10":round(val-10,2),
                       "net_t224_stress":st15})
    return {"counter":dict(rt),"trades":trades,
            "net":round(sum(t["net"] for t in trades),2),
            "net_plus10":round(sum(t["net_plus10"] for t in trades),2),
            "net_t224_stress":round(sum(t["net_t224_stress"] for t in trades),2)}


def month_stage(root,month,reg):
    month_guard(month)
    src=0;ready=0;cases=Counter();qc=Counter();days=[]
    for d in sorted(month_days(root,month)):
        dev_day(d)
        events=list(source_events(file_for(root,dev_day(d),"Last")))
        src+=1
        status,bars,t05=frozen_t05(events,d)
        qc[status]+=1
        if status!="READY":
            if status not in ("SKIP_MISSING_OPENING_RANGE","SKIP_TINY_OPENING_RANGE"):
                raise AssertionError("UNKNOWN_SOURCE_QC")
            continue
        ready+=1
        original=Envelope()
        extra=Envelope()
        attrs,extra_attrs,rejects=trace(d,events,bars,t05,STRESS,original,extra)
        cnt=attrs[BASE]
        classic_n=cnt["trades"];classic_net=round(cnt["net_cents"]/100,2)
        raw_labels,t224=t224_plan(events,d,reg)
        for k in IDS:cases[k]+=int(raw_labels[k]==CASE)
        t224model=t224["model"] if t224 else None
        if t224model is not None and t224model["status"]==MODELED:
            if t224model["entry_group_ambiguous"]:
                raise ValueError("T224_ENTRY_SAME_TIMESTAMP_STOP_ORDER_UNRESOLVED")
            trace_t224_end(t224)
        only=replay_account(events,d,bars,t05)
        if only["counter"].get("executed_"+BASE,0)!=classic_n or abs(only["net"]-classic_net)>.01:
            raise AssertionError("T05_CLASSIC_PARENT_NOT_REPRODUCED")
        combined=replay_account(events,d,bars,t05,t224)
        days.append({"date":d,"t05_classic_n":classic_n,"t05_classic_net":classic_net,
                     "t224_model":t224model,"only":only,"combined":combined,
                     "t224_case":t224 is not None})
        del events
    if src!=sum(qc.values()) or ready!=qc["READY"]:
        raise AssertionError("SOURCE_QC_FAILED")
    return {
        "stage":"PRIVATE_NINE_D2_T05_T224_CHRONOLOGICAL_SHADOW",
        "month":month,"source":src,"eligible":ready,
        "cases":{k:cases[k] for k in IDS},"days":days,
        "holdouts_opened":False,"new_history":False,
        "fills_verified":False,"raw_ticks_public":False
    }


def dd_closed(v):
    peak=equity=worst=0.
    for x in v:
        equity+=x;peak=max(peak,equity);worst=max(worst,peak-equity)
    return round(worst,2)


def stats_trade(v):
    positive=sum(t for t in v if t>0)
    negative=sum(t for t in v if t<0)
    return {"N":len(v),"net_usd":round(sum(v),2),
            "PF":round(positive/-negative,4) if negative<0 else None,
            "DD_closed_usd":dd_closed(v),
            "expectancy_usd_per_trade":round(sum(v)/len(v),3) if v else None}


def aggregate(allmonths):
    if set(allmonths)!=set(MONTHS):
        raise ValueError("NEED_EXACT_SEVEN_MONTHS")
    daily=[];source=eligible=0;cases=Counter()
    for m in MONTHS:
        x=allmonths[m]
        if x["month"]!=m or x["stage"]!="PRIVATE_NINE_D2_T05_T224_CHRONOLOGICAL_SHADOW" \
           or x["eligible"]!=len(x["days"]) \
           or set(x["cases"])!=set(IDS) \
           or any(x[k] is not False for k in ("holdouts_opened","new_history","fills_verified","raw_ticks_public")):
            raise ValueError("INVALID_MONTH_OR_PRIVACY")
        source+=x["source"];eligible+=x["eligible"]
        cases.update(x["cases"]);daily.extend(x["days"])
    if (source,eligible,len(daily))!=(140,135,135):
        raise AssertionError("COVERAGE_140_135_REQUIRED")
    if any(cases[k]!=CASES[k] for k in IDS):
        raise AssertionError("D0_WHOLE_TWENTY_FROZEN_CASE_PARITY_FAILED")
    if [x["date"] for x in daily]!=sorted(x["date"] for x in daily):
        raise AssertionError("NONCHRONOLOGICAL_SESSIONS")
    t05n=sum(x["t05_classic_n"] for x in daily)
    t05net=round(sum(x["t05_classic_net"] for x in daily),2)
    t224=[x["t224_model"] for x in daily if x["t224_model"] and x["t224_model"]["status"]==MODELED]
    if (t05n,t05net)!=(EXPECTED_T05_N,EXPECTED_T05_NET):
        raise AssertionError("T05_115_5102P50_PARENT_PARITY")
    if len(t224)!=EXPECTED_T224_N or abs(sum(x["net_usd"] for x in t224)-EXPECTED_T224_NET)>.01:
        raise AssertionError("T224_106_1256_PARENT_PARITY")
    for x in t224:
        if x["entry_group_ambiguous"]:
            raise ValueError("T224_UNKNOWN_ENTRY_SEQUENCE")
    base=[];combo=[];extra=[];stress=[];per_month=defaultdict(lambda:{"A":0.,"B":0.,"Bplus":0.,"Bstress":0.})
    total=Counter(); owners=Counter()
    for row in daily:
        A=row["only"];B=row["combined"]
        base.append(A["net"]);combo.append(B["net"])
        extra.append(B["net_plus10"]);stress.append(B["net_t224_stress"])
        m=row["date"][:7]
        for key,val in (("A",A["net"]),("B",B["net"]),("Bplus",B["net_plus10"]),("Bstress",B["net_t224_stress"])):
            per_month[m][key]+=val
        total.update(B["counter"])
        for t in B["trades"]:owners[t["owner"]]+=1
    a_trades=[t["net"] for row in daily for t in row["only"]["trades"]]
    b_trades=[t["net"] for row in daily for t in row["combined"]["trades"]]
    b_extra=[t["net_plus10"] for row in daily for t in row["combined"]["trades"]]
    b_stress=[t["net_t224_stress"] for row in daily for t in row["combined"]["trades"]]
    a=stats_trade(a_trades);a["DD_closed_usd"]=dd_closed(base)
    b=stats_trade(b_trades);b["DD_closed_usd"]=dd_closed(combo)
    ex=stats_trade(b_extra);ex["DD_closed_usd"]=dd_closed(extra)
    st=stats_trade(b_stress);st["DD_closed_usd"]=dd_closed(stress)
    if a["N"]!=t05n or abs(a["net_usd"]-t05net)>.01:
        raise AssertionError("T05_STANDALONE_ROUTER_PARITY")
    if abs(b["net_usd"]-sum(owners[o]*0 for o in [] )-round(sum(combo),2))>.01:
        raise AssertionError("SHARED_ACCOUNT_NOT_BALANCED")
    return {
        "stage":"NINE_D2_SHADOW_T05_T224_MIXED_PARENT_COST_NOT_FORMAL",
        "nine_members":list(NINE),
        "source":source,"eligible":eligible,
        "parent_checks":{"T05_trades":t05n,"T05_stress_net_usd":t05net,
                         "T224_trades":len(t224),
                         "T224_base_net_usd":round(sum(z["net_usd"] for z in t224),2),
                         "all20_D0_case_parity":True},
        "account_A_T05_stress":a,"account_B_T05_stress_plus_T224_base":b,
        "account_B_extra10_fixed_path":ex,
        "account_B_T224_1p5x_cost_T05_stress_unchanged":st,
        "delta_B_minus_A_usd":round(b["net_usd"]-a["net_usd"],2),
        "delta_Bextra_minus_Aextra_usd":round(ex["net_usd"]-(a["net_usd"]-a["N"]*10),2),
        "account_B_counts":dict(total),
        "account_B_parent_executions":dict(owners),
        "monthly_net_usd":{m:{k:round(z[k],2) for k in ("A","B","Bplus","Bstress")}
                           for m,z in per_month.items()},
        "other_seven_members":{
            "T147":"NO_COMMON_EXECUTION_TIMESTAMPS_REPLAYED",
            "T186":"PREVIOUS_D2_SHADOW_ROUTER_T05_T186_FAILED",
            "H09":"DIFFERENT_2020_2024_MINUTE_WINDOW",
            "H56":"DIFFERENT_2020_2024_MINUTE_WINDOW",
            "H69":"H09_H56_DERIVED_ROUTER_DIFFERENT_WINDOW",
            "H74":"H09_H56_DERIVED_ROUTER_DIFFERENT_WINDOW",
            "H77":"H09_H56_DERIVED_ROUTER_DIFFERENT_WINDOW"},
        "D2_formal":"BLOCKED_NO_TWO_D1_PASSED_NO_EXECUTABLE_FILLS",
        "combined_floating_DD_usd":None,"funded_trailing_tested":False,
        "all_simulations_unverified":True,"holdouts_opened":False,
        "new_history":False,"individual_trades_public":False
    }


def report(r):
    fmt=lambda x:"N/D" if x is None else f"{x:,.2f}"
    lines=["# D2 SOMBRA DE NUEVE — T05 + T224, un solo calendario y una sola cuenta",
           "","**No es aprobación de D1 ni D2 formal; Last no son fills verificados.**",
           "La familia H 2020–24 no se une a los Last 2025–26. T147/T186 presentes",
           "en los nueve, pero NO se suman; se documentan sus gates y bloqueos.",
           f"Fuente {r['source']} / READY {r['eligible']}, padres {r['parent_checks']}.","",
           "| Simulación | Trades | Neto USD | PF | DD cerrado USD |",
           "|---|---:|---:|---:|---:|"]
    for label,key in (
        ("A T05 estrés congelado","account_A_T05_stress"),
        ("B T05 estrés + T224 base (costo MIXTO)","account_B_T05_stress_plus_T224_base"),
        ("B +$10 RT fijo sobre ambas","account_B_extra10_fixed_path"),
        ("B T224 costo1,5x, T05 estrés","account_B_T224_1p5x_cost_T05_stress_unchanged")):
        z=r[key]
        lines.append(f"| {label} | {z['N']} | {fmt(z['net_usd'])} | {fmt(z['PF'])} | {fmt(z['DD_closed_usd'])} |")
    lines.extend(["",
        f"Delta B−A costo MIXTO: {fmt(r['delta_B_minus_A_usd'])} USD; no es alfa robusta.",
        f"Delta Bextra−Aextra: {fmt(r['delta_Bextra_minus_Aextra_usd'])} USD.",
        f"Rechazos/capacidad: {r['account_B_counts']}.",
        f"Operaciones ejecutadas en B por sistema: {r['account_B_parent_executions']}.",
        "","## Nueve entradas de evaluación D2",
        "| ID | Participación en D2 ejercicio | Dictamen |",
        "|---|---|---|",
        "| T05-377 | Padre benchmark en A y B | No D1 formal; coste +$10 falla PF individual |",
        "| **T224** | Nuevo padre de señal T05+T224 B | No D1 formal; PF base 1,17 y qBH20=1 |",
        "| T147 | Comparador T del mismo universo | G0 paridad sí; pendiente replay de exposición |",
        "| T186 | Referencia T negativa | D2 anterior T05+T186 falla PF/DD |",
        "| H09 | Padre H | Periodo 2020–24 minuto distinto de T |",
        "| H56 | Padre H | Periodo 2020–24 minuto distinto de T |",
        "| H69 | Router H09/H56 | No fuente independiente, datos H distinto periodo |",
        "| H74 | Router H09/H56 | No fuente independiente, datos H distinto periodo |",
        "| H77 | Router H09/H56 | No fuente independiente, datos H distinto periodo |",
        "",
        "**Drawdown B arriba es SOLO equity cerrada por día**, no intratrade, trailing ni evaluación de fondeo US$50K.",
        "El escenario principal mezcla dos modelos originales de costo para no cambiar reglas retrospectivamente;",
        "por ello su PF y neto NO son comparación contractual homogénea y no se usa para PASS.",
        "No retocar parámetros según el resultado, no nueva prueba OOS y sin modificar prioridades.",
        f"**Estado D2: {r['D2_formal']}**.",
        ])
    return "\n".join(lines)+"\n"


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--month")
    p.add_argument("--root",type=Path)
    p.add_argument("--inputs",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    if a.month is not None:
        month_guard(a.month)
        if a.root is None:raise ValueError("SOURCE_REQUIRED")
        z=month_stage(a.root,a.month,registry())
        a.out.parent.mkdir(parents=True,exist_ok=True)
        if a.out.exists():raise ValueError("NEVER_OVERWRITE_PRIVATE_MONTH")
        a.out.write_text(json.dumps(z,separators=(",",":"),default=float)+"\n")
        print("D2_NINE_PRIVATE_MONTH_SAFE_QC="+json.dumps({
            "month":a.month,"source":z["source"],"eligible":z["eligible"],
            "t224_cases":z["cases"]["T224"],
            "private_data_not_exported":True}))
    else:
        if a.inputs is None or a.report is None:raise ValueError("7_INPUTS_REQUIRED")
        m={x:json.loads((a.inputs/f"d2_nine_{x}.json").read_text()) for x in MONTHS}
        z=aggregate(m)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
        a.report.write_text(report(z))
        print("D2_NINE_SAFE_FINAL="+json.dumps({
            "source":z["source"],"eligible":z["eligible"],
            "T05_parent_n":z["parent_checks"]["T05_trades"],
            "T224_parent_n":z["parent_checks"]["T224_trades"],
            "A":z["account_A_T05_stress"],
            "B":z["account_B_T05_stress_plus_T224_base"],
            "B_extra10":z["account_B_extra10_fixed_path"],
            "delta":z["delta_B_minus_A_usd"],
            "execution_by_owner":z["account_B_parent_executions"],
            "formal_D2":z["D2_formal"]},sort_keys=True))
