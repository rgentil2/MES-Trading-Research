#!/usr/bin/env python3
"""Full all-13 D2 study, T sleeve: EIGHT models, 255 nonempty portfolio subsets.

The H sleeve (five alternative H09/H56 parent/router choices) is disjoint in
history and not added to T. Here all eight T are evaluated once on the same
seven existing DEV Last months, without optimizing signals, SL, TP or sessions.
Economic ranking is SHADOW with mixed inherited frictions; NO OOS/live signal.
"""
from __future__ import annotations
import argparse, json
from bisect import bisect_right
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import combinations, islice
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import (
    BASE,NEW,STRESS,frozen_t05,owner_policy,et_edge)
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade
from nq_t169_t188_monetary_month import new_signals,load_frozen
from nq_t133_t152_executable_d0_batch import load_registry as load_old_registry
from nq_t133_t152_executable_d0_features import classify_day as classify_old
from nq_t133_t168_d1_engine import prepare_context,stop_and_side,first_future_groups,model_one
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t209_t228_structural_d0 import (
    registry as load_new_registry,classify_day as classify_new,stats,bar_subset,
    regime_signal,month_guard,IDS as D0_IDS,CASE
)
from nq_t210_t224_five_economic_shadow import CASES,MODELED
from research.nq.nq_all13_subset_search import (
    T,subsets,choose_candidates,closed_metrics,T_SOURCE
)

FIVE=("T210","T212","T215","T217","T224")
PARENT={
    "T05-377":(115,5102.50),
    "T147":(20,642.25),
    "T186":(70,-970.),
    "T210":(17,-418.),
    "T212":(49,-1877.50),
    "T215":(14,835.75),
    "T217":(46,-1743.),
    "T224":(106,1256.),
}
EXPECTED_SOURCE=140
EXPECTED_READY=135
EXPECT_OLD_T147_CASE=21
MAX_DAILY=2
STOP_DAILY=-600
ORDER={name:i for i,name in enumerate(T)}


def atomic_bounds(groups, side, stop, target_r, model):
    """Reconstruct timestamp exposure under SAME stop-first rule as model_one."""
    if model["status"]!=MODELED:return None
    if model["entry_group_ambiguous"]:
        return "ENTRY_TIMESTAMP_ORDER_AMBIGUOUS"
    if not groups:return "MISSING_WHOLE_TIMESTAMP_GROUPS"
    first=groups[0]
    entry=F(first[2] if side>0 else first[1])+side*2
    risk=side*(entry-stop)
    target=entry+side*F(str(target_r))*risk
    for ts,low,high in groups[1:]:
        stop_hit=(low<=stop if side>0 else high>=stop)
        target_hit=(high>=target if side>0 else low<=target)
        if stop_hit:
            if model["exit_reason"] not in ("STOP","STOP_FIRST"):
                raise AssertionError("STOP_TIMESTAMP_REPLAY_PARITY")
            return (first[0],ts)
        if target_hit:
            if model["exit_reason"]!="TARGET":
                raise AssertionError("TARGET_TIMESTAMP_REPLAY_PARITY")
            return (first[0],ts)
    if model["exit_reason"]!="TIME_EXIT_ADVERSE_GROUP":
        raise AssertionError("TIME_EXIT_TIMESTAMP_REPLAY_PARITY")
    if groups[-1][0]<=first[0]:
        return "TIME_EXIT_NO_POST_ENTRY_GROUP"
    return (first[0],groups[-1][0])


def from_last_sim(day, events, times, bars, signal, key):
    ts,side=signal
    p=owner_policy(BASE if key=="T05-377" else NEW,bars,STRESS)
    r=simulate_single_trade(
        islice(events,bisect_right(times,ts),None),
        Signal(day,ts,side),p)
    if r["status"] in ("ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS","UNRESOLVED_END_OF_LAST_DATA"):
        return {"ID":key,"status":"UNRESOLVED_LAST_EXECUTION","decision":ts}
    if r["status"]!="SYNTHETIC_FILL_MODEL_ONLY":
        return {"ID":key,"status":"REJECTED_BY_ORIGINAL_EXECUTION","decision":ts}
    if r["entry_timestamp"]<=ts or r["exit_timestamp"]<r["entry_timestamp"]:
        raise AssertionError("NONCAUSAL_LEGACY_ORDER_TIMING")
    net=round(r["estimated_net_usd"],2)
    risk=float(p.stop_ticks)*5
    return {"ID":key,"status":"MODELLED",
            "decision":ts,"entry":r["entry_timestamp"],"exit":r["exit_timestamp"],
            "net":net,"stress_1p5":net,"extra10":round(net-10,2),
            "risk_usd":risk,"instrument":"NQ","ambiguous":False}


def from_atomic_result(key, decision, groups, side, stop, target_r, model):
    if model["status"]!=MODELED:
        return {"ID":key,"status":model["status"],"decision":decision}
    bounds=atomic_bounds(groups,side,stop,target_r,model)
    if isinstance(bounds,str):
        return {"ID":key,"status":bounds,"decision":decision}
    if bounds is None or bounds[0]<=decision or bounds[1]<bounds[0]:
        raise AssertionError("NONCAUSAL_ATOMIC_EXECUTION")
    return {"ID":key,"status":"MODELLED","decision":decision,
            "entry":bounds[0],"exit":bounds[1],
            "net":round(model["net_usd"],2),
            "stress_1p5":round(model["stress_1_5x_usd"],2),
            "extra10":round(model["stress_plus_10_rt_usd"],2),
            "risk_usd":round(model["risk_nominal_usd"],6),
            "instrument":model["instrument"],"ambiguous":False}


def extract_session(events,day,bars,t05,old_reg,new_reg):
    """ALL eight parents, including losing members. Exactly one source-pass."""
    times=[x[0] for x in events]
    intents={k:[] for k in T}
    for ts,side,_ in t05:
        intents["T05-377"].append(from_last_sim(day,events,times,bars,(ts,side),"T05-377"))
    s186,_=new_signals(events,day)
    if s186["T186"] is not None:
        intents["T186"].append(from_last_sim(day,events,times,bars,s186["T186"],"T186"))
    old=classify_old(events,day,old_reg)
    if old["T147"]==CASE:
        ctx=prepare_context(events,day)
        m=next(x for x in old_reg["members"] if x["id"]=="T147")
        plan=stop_and_side(m,ctx)
        if plan is None:raise AssertionError("T147_D0_CASE_HAS_NO_PLAN")
        side,stop,r,horizon=plan
        future,covered=first_future_groups(events,ctx["anchor"],horizon)
        model=model_one(future,side,stop,r,horizon,ctx["anchor"],covered)
        intents["T147"].append(from_atomic_result(
            "T147",ctx["anchor"],future,side,stop,r,model))
    labels=classify_new(events,day,new_reg)
    if set(labels)!=set(D0_IDS):raise AssertionError("ORIGINAL_T209_T228_20_D0_CASES_MISSING")
    active=[x for x in FIVE if labels[x]==CASE]
    if active:
        bars_atomic=completed_bars_by_print_count(events,day,(377,4181,10946))
        lookup={}
        for block in new_reg["blocks"]:
            wanted=[x for x in block["ids"] if x in active]
            if not wanted:continue
            lo=et_edge(day,*map(int,block["window_et"][0].split(":")))
            hi=et_edge(day,*map(int,block["window_et"][1].split(":")))
            idx=next((i for i,b in enumerate(bars_atomic[377])
                      if lo<=b.end_timestamp<hi),None)
            if idx is None or idx<1:raise AssertionError("D0_CASE_WITHOUT_FIRST_E377")
            bar=bars_atomic[377][idx]
            e=stats(bar_subset(events,times,bar))
            d=stats(bar_subset(events,times,bars_atomic[377][idx-1]))
            ma=next((b for b in reversed(bars_atomic[4181])
                     if b.end_timestamp<bar.end_timestamp),None)
            lg=next((b for b in reversed(bars_atomic[10946])
                     if b.end_timestamp<bar.end_timestamp),None)
            macro=stats(bar_subset(events,times,ma)) if ma else None
            lng=stats(bar_subset(events,times,lg)) if lg else None
            future,covered=first_future_groups(events,bar.end_timestamp,15)
            for key in wanted:
                side=regime_signal(key,e,d,macro,lng)
                if side not in (-1,1):raise AssertionError("D0_CASE_FROZEN_SIDE_CHANGED")
                stop=F(e["profile"]["lo"]-2 if side>0 else e["profile"]["hi"]+2)
                model=model_one(future,side,stop,1.5,15,bar.end_timestamp,covered)
                intents[key].append(from_atomic_result(
                    key,bar.end_timestamp,future,side,stop,1.5,model))
    return intents,labels,int(old["T147"]==CASE)


def allowed_intent(z):
    return z["status"]=="MODELLED" and not z.get("ambiguous",False)


def account_day(intents, mask):
    """Counterfactual single-account router; deterministic BEFORE seeing PNL."""
    selected=[x for k in mask for x in intents[k]]
    selected.sort(key=lambda x:(x["decision"],ORDER[x["ID"]]))
    closed=0.;last_exit=-1;executed=[];rej=Counter()
    for x in selected:
        if len(executed)>=MAX_DAILY or closed<=STOP_DAILY:
            rej["capacity"]+=1;continue
        if x["decision"]<=last_exit:
            rej["overlap"]+=1;continue
        if not allowed_intent(x):
            if x["status"] in ("UNRESOLVED_LAST_EXECUTION",
                               "ENTRY_TIMESTAMP_ORDER_AMBIGUOUS",
                               "MISSING_WHOLE_TIMESTAMP_GROUPS",
                               "TIME_EXIT_NO_POST_ENTRY_GROUP"):
                raise ValueError("CANNOT_ESTIMATE_UNRESOLVED_SELECTED_SOURCE")
            rej["not_modelled"]+=1
            continue
        if x["entry"]<=x["decision"] or x["exit"]<x["entry"]:
            raise ValueError("IMPOSSIBLE_CAUSAL_ORDER")
        executed.append(x)
        last_exit=x["exit"]
        closed=round(closed+x["net"],2)
    return executed,rej


def month_stage(root,month,old_reg,new_reg):
    month_guard(month)    # block OOS before any filesystem reads
    data=[];qc=Counter();cases=Counter();old_cases=0;source=0
    for day in sorted(month_days(root,month)):
        dev_day(day)
        source+=1
        events=list(source_events(file_for(root,dev_day(day),"Last")))
        status,bars,t05=frozen_t05(events,day)
        qc[status]+=1
        if status!="READY":
            if status not in ("SKIP_MISSING_OPENING_RANGE","SKIP_TINY_OPENING_RANGE"):
                raise AssertionError("UNEXPECTED_SESSION_QC")
            continue
        intents,labels,old=extract_session(events,day,bars,t05,old_reg,new_reg)
        for key in D0_IDS:cases[key]+=int(labels[key]==CASE)
        old_cases+=old
        data.append({"day":day,"intents":intents})
        del events
    if source!=sum(qc.values()) or len(data)!=qc["READY"]:
        raise AssertionError("SOURCE_MONTH_COVERAGE_FAIL")
    return {
        "stage":"PRIVATE_ALL13_T8_SUBSET_SOURCE_LEDGER",
        "month":month,"source":source,"eligible":len(data),
        "cases":dict(cases),"T147_cases":old_cases,
        "daily":data,"holdouts_opened":False,"new_data":False,
        "broker_fills_verified":False,"private_source_public":False
    }


def dd_daily(seq):
    high=equity=worst=0.
    for z in seq:
        equity+=z;high=max(high,equity);worst=max(worst,high-equity)
    return round(worst,2)


def model_summary(rows,mask):
    daily_b=[];daily_plus=[];daily_stress=[]
    trades=[];status=Counter();owners=Counter()
    per_month=defaultdict(lambda:{"base":0.,"plus":0.,"stress":0.})
    for day in rows:
        try:
            executed,reject=account_day(day["intents"],mask)
        except ValueError as e:
            return {"members":list(mask),"status":str(e)}
        status.update(reject)
        for k in mask:
            for q in day["intents"][k]:
                if q["status"]=="MODELLED":continue
                status[f"source_{k}_{q['status']}"]+=1
        b=round(sum(x["net"] for x in executed),2)
        plus=round(sum(x["extra10"] for x in executed),2)
        stress=round(sum(x["stress_1p5"] for x in executed),2)
        daily_b.append(b);daily_plus.append(plus);daily_stress.append(stress)
        mon=day["day"][:7]
        per_month[mon]["base"]+=b
        per_month[mon]["plus"]+=plus
        per_month[mon]["stress"]+=stress
        owners.update(x["ID"] for x in executed)
        trades.extend(executed)
    N=len(trades)
    sums=lambda key:round(sum(x[key] for x in trades),2)
    def pf(key):
        w=sum(x[key] for x in trades if x[key]>0)
        l=sum(-x[key] for x in trades if x[key]<0)
        return round(w/l,4) if l>0 else None
    E_R=sum(x["net"]/x["risk_usd"] for x in trades)/N if N else None
    return {
        "members":list(mask),"status":"ESTIMABLE",
        "sample":T_SOURCE,"reconciled_parent_count":8,
        "broker_fills_verified":False,"holdouts_opened":False,
        "N":N,"N_by_parent":dict(owners),
        "net_base":sums("net"),"net_plus10":sums("extra10"),
        "net_1p5":sums("stress_1p5"),
        "PF_base":pf("net"),"PF_plus10":pf("extra10"),
        "PF_1p5":pf("stress_1p5"),
        "DD_base_closed":dd_daily(daily_b),
        "DD_plus10_closed":dd_daily(daily_plus),
        "DD_1p5_closed":dd_daily(daily_stress),
        "expectancy_R":round(E_R,6) if E_R is not None else None,
        "positive_months_base":sum(v["base"]>0 for v in per_month.values()),
        "positive_months_plus10":sum(v["plus"]>0 for v in per_month.values()),
        "reject_counts":dict(status),
        "floating_DD":None,"last_intratrade_DD":None,
    }


def aggregate(months):
    if set(months)!=set(MONTHS):raise ValueError("ALL_SEVEN_DEV_MONTHS_REQUIRED")
    rows=[];source=eligible=0;cases=Counter();oldcases=0
    for month in MONTHS:
        m=months[month]
        if (m["month"]!=month or m["stage"]!="PRIVATE_ALL13_T8_SUBSET_SOURCE_LEDGER"
            or m["eligible"]!=len(m["daily"])
            or any(m[k] is not False for k in ("holdouts_opened","new_data",
                "broker_fills_verified","private_source_public"))):
            raise ValueError("PRIVATE_MONTH_FAIL_CLOSED")
        source+=m["source"];eligible+=m["eligible"]
        cases.update(m["cases"]);oldcases+=m["T147_cases"]
        rows.extend(m["daily"])
    if (source,eligible,len(rows))!=(EXPECTED_SOURCE,EXPECTED_READY,EXPECTED_READY):
        raise AssertionError("SEVEN_MONTH_COVERAGE_NOT_140_135")
    if any(cases[k]!=CASES[k] for k in D0_IDS) or oldcases!=EXPECT_OLD_T147_CASE:
        raise AssertionError("T20_OR_T147_D0_CASE_PARITY")
    if [r["day"] for r in rows]!=sorted(r["day"] for r in rows):
        raise AssertionError("DATE_SORTED_DEV_ONLY")
    parents={}
    for k in T:
        z=model_summary(rows,(k,))
        if z["status"]!="ESTIMABLE" or (z["N"],z["net_base"])!=PARENT[k]:
            raise AssertionError(f"FROZEN_PARENT_N_PNL_MISMATCH_{k}:{z.get('N')}:{z.get('net_base')}")
        parents[k]={"N":z["N"],"net_usd":z["net_base"],"DD_daily_closed":z["DD_base_closed"]}
    all_models=[model_summary(rows,mask) for mask in subsets(T)]
    ranked=choose_candidates(all_models)
    count=Counter(z["status"] for z in all_models)
    strongest=sorted(
        [z for z in all_models if z["status"]=="ESTIMABLE" and
         z["DD_plus10_closed"]>0],
        key=lambda z:(-(z["net_plus10"]/z["DD_plus10_closed"]),
                      -(z["expectancy_R"] or -999),
                      len(z["members"])))[:12]
    shortlist=[{"members":z["members"],"N":z["N"],"net_plus10":z["net_plus10"],
                "DD_plus10_closed":z["DD_plus10_closed"],
                "PF_plus10":z["PF_plus10"],
                "expectancy_R":z["expectancy_R"]} for z in strongest]
    # no raw session/price/trade rows in public results
    return {
        "stage":"ALL13_T8_EXHAUSTIVE_255_SUBSETS_SHADOW_DEV_ONLY",
        "source_sessions":source,"eligible_sessions":eligible,
        "parent_parity":parents,"T147_CASE_days":oldcases,
        "T20_case_parity":True,
        "T_subsets_total":len(all_models),
        "T_subsets_status_counts":dict(count),
        "T_all_subsets":all_models,
        "T_ranked_by_base_cost_adjusted_DD_descriptive_only":shortlist,
        "T_pareto_with_exploratory_cost_gates":ranked,
        "H_five_alternatives_not_rescored":list(("H09","H56","H69","H74","H77")),
        "H_T_joint_equity":None,"best_validated_portfolio":None,
        "D1_D2_formal":"BLOCKED",
        "floating_DD":None,"mixed_original_cost_assumptions":True,
        "sample_selection_bias":True,
        "holdouts_opened":False,"new_data":False,
        "broker_fills_verified":False,"individual_market_data_public":False,
    }


def report(z):
    lines=["# Trece hipótesis: rama ocho T, barrido completo de 255 subconjuntos",
      "",
      "**ESTUDIO EXPLORATORIO sobre datos ya vistos: NO es validación OOS ni cartera 13 H+T.**",
      f"Sesiones fuente {z['source_sessions']}; READY {z['eligible_sessions']}.",
      "Paridad parentales EXIGIDA antes de ordenar: "+str(z["parent_parity"]),
      "Estados 255: "+str(z["T_subsets_status_counts"]),
      f"Frontera que cumple filtros económicos exploratorios: "
      f"{z['T_pareto_with_exploratory_cost_gates']['passing_economic_filter_count']} modelos.",
      "",
      "| Subconjunto (T) | N | Neto +$10RT | DD cerrado +$10RT | PF +$10RT | Exp R/trade |",
      "|---|---:|---:|---:|---:|---:|",
    ]
    for row in z["T_ranked_by_base_cost_adjusted_DD_descriptive_only"]:
        lines.append(f"| {','.join(row['members'])} | {row['N']} | "
            f"{row['net_plus10']:,.2f} | {row['DD_plus10_closed']:,.2f} | "
            f"{row['PF_plus10']} | {row['expectancy_R']} |")
    lines+=["","**Ninguna de las anteriores puede declararse ganadora: el mejor"
        " de 255 subconjuntos sobre las mismas 135 sesiones presenta sesgo"
        " de selección retrospectiva.** La rentabilidad/DD mostrada es"
        " CLOSE-DAY equity, NO intraday float/trailing en cuenta real.",
        "Las H son 5 opciones alternativas 2020–24 minuto; nunca sumar curvas"
        " con T 2025–26 Last sin historial emparejado autorizado.",
        "Costos por padre: T05/T186 original estrés, T147/T210/T212/T215/T217/T224"
        " modelo base. +$10RT y 1,5× coste se evalúan sobre decisiones fijas.",
        "Drawdown flotante N/D, Bid/Ask real y reglas de fondeo no verificadas.",
        ""]
    return "\n".join(lines)+"\n"


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--month")
    p.add_argument("--root",type=Path)
    p.add_argument("--inputs",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    from research.nq.nq_all13_subset_search import load_frozen
    load_frozen()
    if a.month is not None:
        month_guard(a.month)
        if a.root is None:raise ValueError("DATA_ROOT_REQUIRED")
        load_frozen();old_reg=load_old_registry();new_reg=load_new_registry()
        load_frozen()
        z=month_stage(a.root,a.month,old_reg,new_reg)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        if a.out.exists():raise ValueError("NO_REWRITE_PRIVATE_MONTH")
        a.out.write_text(json.dumps(z,sort_keys=True,separators=(",",":"))+"\n")
        print("ALL13_T8_PRIVATE_MONTH_QC="+json.dumps({
            "month":a.month,"source":z["source"],"ready":z["eligible"],
            "T147_CASE_days":z["T147_cases"],"no_trade_data_exposed":True},sort_keys=True))
    else:
        if not a.inputs or not a.report:raise ValueError("SEVEN_MONTHS_AND_REPORT_REQUIRED")
        months={x:json.loads((a.inputs/f"t8_{x}.json").read_text()) for x in MONTHS}
        summary=aggregate(months)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
        a.report.write_text(report(summary))
        print("ALL13_T8_SAFE_FINAL="+json.dumps({
            "source":summary["source_sessions"],"ready":summary["eligible_sessions"],
            "parent_parity":summary["parent_parity"],
            "status_counts":summary["T_subsets_status_counts"],
            "pareto_count":summary["T_pareto_with_exploratory_cost_gates"]["passing_economic_filter_count"],
            "best_validated_portfolio":None,
            "holdouts_opened":False},sort_keys=True))
