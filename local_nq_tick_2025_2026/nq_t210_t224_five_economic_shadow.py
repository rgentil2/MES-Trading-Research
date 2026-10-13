#!/usr/bin/env python3
"""POST-D0 selected-five standalone economic SHADOW, not formal D1/D2.

T210 T212 T215 T217 T224 from 20 fully preregistered T209..228.
Uses only preexisting Last DEV; freezes 20-family BH denominator.
All per-day results remain ephemeral PRIVATE on GH runner.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date
from fractions import Fraction as F
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS, month_days
from nq_b05h01_trade_expansion_month import et_edge, frozen_t05
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t209_t228_structural_d0 import (
    registry, month_guard, classify_day, regime_signal, stats, bar_subset,
    IDS, CASE, CONTROL, OTHER, MISSING, LABELS, SOURCE_DAYS, READY_DAYS
)
from nq_t133_t168_d1_engine import first_future_groups, model_one

FIVE=("T210","T212","T215","T217","T224")
FAMILY=20
CASES=({
"T209":0,"T210":18,"T211":12,"T212":50,"T213":5,
"T214":2,"T215":16,"T216":0,"T217":46,"T218":13,
"T219":1,"T220":0,"T221":1,"T222":1,"T223":0,
"T224":106,"T225":5,"T226":4,"T227":8,"T228":0})
PREREG="research/nq/NQ_13_H_T_EXPLORATORY_ECONOMIC_BRIDGE_PREREG_2026_10_13.md"
B=10_000
MODELED="MODELLED_EXECUTION_UNVERIFIED"
FIELDS=("net_usd","stress_1_5x_usd","stress_plus_10_rt_usd")


def month_study(root,month,reg):
    month_guard(month)  # BEFORE filesystem or source iteration
    source=0
    qc=Counter()
    labels_total={k:Counter() for k in IDS}
    daily=[]
    for d in sorted(month_days(root,month)):
        dev_day(d)  # validate scope, retain original ISO string for frozen engines
        day=d
        source+=1
        events=list(source_events(file_for(root,day,"Last")))
        ready,_,_=frozen_t05(events,day)
        qc[ready]+=1
        if ready!="READY":
            if ready not in ("SKIP_MISSING_OPENING_RANGE","SKIP_TINY_OPENING_RANGE"):
                raise AssertionError("SOURCE_QC_STATUS_UNEXPECTED")
            continue
        labels=classify_day(events,day,reg)
        if set(labels)!=set(IDS):raise AssertionError("NO_FULL_FAMILY_D0")
        for k,v in labels.items():labels_total[k][v]+=1
        data={k:{"group":labels[k],"status":"NO_CAUSAL_TRIGGER",
                 "net_usd":0.,"stress_1_5x_usd":0.,
                 "stress_plus_10_rt_usd":0.} for k in FIVE}
        if any(labels[k]==CASE for k in FIVE):
            complete=completed_bars_by_print_count(events,day,(377,4181,10946))
            bars=complete[377]
            times=[row[0] for row in events]
            for block in reg["blocks"]:
                wanted=[k for k in block["ids"] if k in FIVE and labels[k]==CASE]
                if not wanted:continue
                lo=et_edge(day,*map(int,block["window_et"][0].split(":")))
                hi=et_edge(day,*map(int,block["window_et"][1].split(":")))
                idx=next((i for i,z in enumerate(bars)
                          if lo<=z.end_timestamp<hi),None)
                if idx is None or idx<1:
                    raise AssertionError("CASE_HAS_NO_FROZEN_E377")
                x=bars[idx]
                e=stats(bar_subset(events,times,x))
                previous=stats(bar_subset(events,times,bars[idx-1]))
                macro=next((p for p in reversed(complete[4181])
                            if p.end_timestamp<x.end_timestamp),None)
                longbar=next((p for p in reversed(complete[10946])
                              if p.end_timestamp<x.end_timestamp),None)
                macrostats=stats(bar_subset(events,times,macro)) if macro else None
                longstats=stats(bar_subset(events,times,longbar)) if longbar else None
                future,covered=first_future_groups(events,x.end_timestamp,15)
                for k in wanted:
                    side=regime_signal(k,e,previous,macrostats,longstats)
                    if side not in (-1,1):
                        raise AssertionError("FROZEN_CASE_SIDE_PARITY_"+k)
                    stop=F(e["profile"]["lo"]-2 if side>0 else
                           e["profile"]["hi"]+2)
                    dist=side*(e["end"]-stop)
                    if not (8<=dist<=400 and
                            dist*(5 if dist*5<=250 else F(1,2))<=250):
                        raise AssertionError("FROZEN_D0_CASE_RISK_PARITY_"+k)
                    result=model_one(future,side,stop,1.5,15,x.end_timestamp,covered)
                    data[k]={"group":CASE,**result}
                    if result["status"]==MODELED:
                        if result["direction"]!=side:
                            raise AssertionError("DIRECTION_PARITY")
                        if not (8<=result["risk_ticks"]<=400 and
                                result["risk_nominal_usd"]<=250):
                            raise AssertionError("ENTRY_RISK_TOO_LARGE")
        daily.append({"date":d,"results":data})
        del events
    eligible=len(daily)
    if source!=sum(qc.values()) or eligible!=qc["READY"]:
        raise AssertionError("SOURCE_READY_INTEGRITY")
    if any(sum(labels_total[k].values())!=eligible for k in IDS):
        raise AssertionError("COUNT_ALL_20_INCOMPLETE")
    return {
        "stage":"PRIVATE_POST_D0_SELECTED_FIVE_ECONOMIC_UNVERIFIED",
        "month":month,"source":source,"eligible":eligible,
        "case_counts":{k:labels_total[k][CASE] for k in IDS},
        "daily":daily,"holdouts_opened":False,"new_data":False,
        "broker_fills_verified":False,"public_daily_records":False,
    }


def percentile(sorted_values,q):
    pos=(len(sorted_values)-1)*q
    lo=int(pos);hi=min(lo+1,len(sorted_values)-1)
    return sorted_values[lo]+(sorted_values[hi]-sorted_values[lo])*(pos-lo)


def bootstrap(y,identity,L):
    if len(y)!=READY_DAYS or L not in (3,5,10):
        raise ValueError("BOOTSTRAP_FULL_READY_SESSIONS_REQUIRED")
    n=len(y);starts=n-L+1
    rng=random.Random(20261013+int(identity[1:])*1009+L*37)
    observed=sum(y)/n
    distribution=[]
    for _ in range(B):
        sample=[]
        while len(sample)<n:
            i=rng.randrange(starts)
            sample.extend(y[i:i+L])
        distribution.append(sum(sample[:n])/n)
    distribution.sort()
    p=(1+sum((u-observed)>=observed for u in distribution))/(B+1)
    return {"L":L,"B":B,
            "CI90":[round(percentile(distribution,.05),5),
                    round(percentile(distribution,.95),5)],
            "p_one_sided_centered":round(p,8)}


def adjust_bh(p):
    if len(p)!=FAMILY or any(not 0<=x<=1 for x in p):
        raise ValueError("BH_FULL_TWENTY_DENOMINATOR_REQUIRED")
    order=sorted(range(FAMILY),key=lambda i:p[i])
    output=[1.]*FAMILY;running=1.
    for rank in range(FAMILY,0,-1):
        idx=order[rank-1]
        running=min(running,p[idx]*FAMILY/rank)
        output[idx]=round(running,8)
    return output


def adjust_holm(p):
    if len(p)!=FAMILY:
        raise ValueError("HOLM_FULL_TWENTY_REQUIRED")
    order=sorted(range(FAMILY),key=lambda i:p[i])
    out=[1.]*FAMILY;running=0.
    for rank,idx in enumerate(order):
        running=max(running,min(1.,p[idx]*(FAMILY-rank)))
        out[idx]=round(running,8)
    return out


def max_drawdown_closed(series):
    wealth=high=0.
    worst=0.
    for val in series:
        wealth+=val;high=max(high,wealth)
        worst=max(worst,high-wealth)
    return round(worst,2)


def aggregate(monthly,reg):
    if set(monthly)!=set(MONTHS):raise ValueError("EXACT_7_DEV_MONTHS_REQUIRED")
    rows=[]
    count=Counter();source=eligible=0
    for month in MONTHS:
        z=monthly[month]
        if (z["stage"]!="PRIVATE_POST_D0_SELECTED_FIVE_ECONOMIC_UNVERIFIED"
            or z["month"]!=month or z["eligible"]!=len(z["daily"])
            or set(z["case_counts"])!=set(IDS)
            or any(z[key] is not False for key in
                   ("holdouts_opened","new_data","broker_fills_verified",
                    "public_daily_records"))):
            raise ValueError("PRIVATE_RUN_SCHEMA_OR_SEALED_SCOPE_ERROR")
        source+=z["source"];eligible+=z["eligible"]
        rows.extend(z["daily"])
        count.update(z["case_counts"])
    if (source,eligible,len(rows))!=(SOURCE_DAYS,READY_DAYS,READY_DAYS):
        raise AssertionError("FROZEN_SOURCE_140_READY_135_REQUIRED")
    if any(count[k]!=CASES[k] for k in IDS):
        raise AssertionError("FROZEN_ORIGINAL_ALL_20_D0_CASE_PARITY_FAIL")
    if [z["date"] for z in rows]!=sorted(z["date"] for z in rows):
        raise AssertionError("DATE_ORDER_MUST_BE_CAUSAL")
    metrics={}
    pvalues={k:1. for k in IDS}
    for identity in FIVE:
        daily_base=[];daily_stress=[];daily_plus=[]
        trades=[];reject=Counter();instruments=Counter();exits=Counter()
        months=defaultdict(float);month_positive=Counter();active_weeks=set()
        ambiguous=0
        for day in rows:
            z=day["results"][identity]
            status=z["status"]
            reject[status]+=1
            if status==MODELED:
                val=z["net_usd"]
                daily_base.append(val)
                daily_stress.append(z["stress_1_5x_usd"])
                daily_plus.append(z["stress_plus_10_rt_usd"])
                trades.append(val)
                instruments[z["instrument"]]+=1
                exits[z["exit_reason"]]+=1
                ambiguous+=int(z["entry_group_ambiguous"])
                cal=date.fromisoformat(day["date"]).isocalendar()
                active_weeks.add((cal.year,cal.week))
                months[day["date"][:7]]+=val
            else:
                if z["group"]==CASE and status=="NO_CAUSAL_TRIGGER":
                    raise AssertionError("D0_CASE_SILENTLY_DISCARDED")
                daily_base.append(0.)
                daily_stress.append(0.)
                daily_plus.append(0.)
            if len(daily_base)!=len(daily_stress):raise AssertionError("CASE_ORDER")
        n=len(trades)
        base=round(sum(trades),2)
        stress=round(sum(daily_stress),2)
        plus=round(sum(daily_plus),2)
        if abs(plus-(base-10*n))>.015:
            raise AssertionError("PLUS10_COST_PARITY_FAIL")
        gross_wins=sum(t for t in trades if t>0)
        gross_losses=-sum(t for t in trades if t<0)
        pf=round(gross_wins/gross_losses,4) if gross_losses>0 else None
        boot={str(L):bootstrap(daily_base,identity,L) for L in (3,5,10)} if n>=15 else              {str(L):{"L":L,"B":B,"CI90":None,"p_one_sided_centered":None}
              for L in (3,5,10)}
        if n>=15:pvalues[identity]=boot["5"]["p_one_sided_centered"]
        month_nets={month:round(months.get(month,0.),2) for month in MONTHS}
        positive=[v for v in month_nets.values() if v>0]
        concentrate=max(positive)/sum(positive) if positive else None
        first=sum(months.get(m,0.) for m in MONTHS[:3])
        last=sum(months.get(m,0.) for m in MONTHS[3:])
        metrics[identity]={
            "N_CASE_D0":count[identity],
            "N_modelled_trades":n,
            "N_active_weeks":len(active_weeks),
            "N_sessions":READY_DAYS,
            "net_base_usd":base,
            "net_stress_1p5_usd":stress,
            "net_plus10_rt_usd":plus,
            "avg_net_per_trade_usd":round(base/n,4) if n else None,
            "PF_base":pf,"DD_closed_base_usd":max_drawdown_closed(daily_base),
            "DD_closed_stress15_usd":max_drawdown_closed(daily_stress),
            "DD_closed_plus10_usd":max_drawdown_closed(daily_plus),
            "win_rate":round(sum(t>0 for t in trades)/n,4) if n else None,
            "worst_modelled_trade_usd":round(min(trades),2) if trades else None,
            "assumed_instruments":dict(instruments),
            "exit_reasons":dict(exits),"statuses":dict(reject),
            "entry_group_ambiguous_trades":ambiguous,
            "oct_dec_2025_usd":round(first,2),
            "jan_apr_2026_usd":round(last,2),
            "monthly_net_usd":month_nets,
            "largest_positive_month_share":round(concentrate,4) if concentrate is not None else None,
            "bootstrap":boot,"q_BH20":None,"holm20_exploratory":None,
            "D1_formal":"BLOCKED_D0_FAMILY_BREADTH_5_OF_20",
            "D2_formal":"BLOCKED_NO_CONFIRMED_BROKER_FILLS",
            "N_trades_private":True,
        }
    ps=[pvalues[k] for k in IDS]
    q=adjust_bh(ps);h=adjust_holm(ps)
    for identity in FIVE:
        m=metrics[identity]
        i=IDS.index(identity);ci=m["bootstrap"]["5"]["CI90"]
        m["q_BH20"]=q[i] if m["N_modelled_trades"]>=15 else None
        m["holm20_exploratory"]=h[i] if m["N_modelled_trades"]>=15 else None
        if m["N_modelled_trades"]<15:
            status="LOW_POWER_BELOW_15_MODELLED_TRADES"
        elif m["entry_group_ambiguous_trades"]:
            status="BLOCKED_AMBIGUOUS_ENTRY_LAST_GROUP"
        elif m["net_base_usd"]<=0 or m["PF_base"] is None:
            status="FAILED_NET_OR_PF_NOT_ESTIMABLE"
        elif not (m["PF_base"]>=1.25 and
                  m["net_stress_1p5_usd"]>0 and m["net_plus10_rt_usd"]>0 and
                  m["DD_closed_base_usd"]<=1500 and
                  m["oct_dec_2025_usd"]>0 and m["jan_apr_2026_usd"]>0 and
                  m["largest_positive_month_share"] is not None and
                  m["largest_positive_month_share"]<.4 and ci and ci[0]>0 and
                  m["q_BH20"]<=.10):
            status="ECONOMIC_OR_STATISTICAL_GATE_FAILED"
        else:
            status="SHADOW_D1_ECONOMIC_SCREEN_FAVORABLE_NOT_FORMAL"
        m["D1_shadow"]=status
    return {
        "stage":"POST_SELECTION_FIVE_OF_TWENTY_EXPLORATORY_D1_SHADOW_ONLY",
        "source_days":source,"eligible_days":eligible,
        "D0_family_size":20,"selected_five":list(FIVE),
        "original_twenty_case_parity":True,
        "economics":metrics,
        "screen_favorable_ids":[k for k in FIVE if
            metrics[k]["D1_shadow"]=="SHADOW_D1_ECONOMIC_SCREEN_FAVORABLE_NOT_FORMAL"],
        "D1_formal_passed_ids":[],
        "D2_formal_authorized":False,
        "fee_NQ_assumed_usd_RT":4.0,"fee_MNQ_assumed_usd_RT":1.5,
        "slippage_entry_ticks":2,"slippage_exit_ticks":2,
        "all_last_only":True,"holdouts_opened":False,"new_data":False,
        "broker_fills_verified":False,"individual_trades_exported":False,
        "selection_after_D0":True,"Holm_confirmatory":None,
    }


def report(result):
    z=result["economics"]
    lines=[
        "# D1 sombra económica de cinco T seleccionadas post-D0 (13 H/T en tablero aparte)",
        "",
        "**EXPLORATORIA POST-SELECCIÓN, NO D1 formal**: D0 5/20, BH sobre k=20 original;",
        "Last no acredita fill; fees y slippage supuestos; H no se reejecuta.",
        f"Sesiones fuente {result['source_days']}, READY {result['eligible_days']}.",
        "",
        "| Hipótesis | CASE | Trades proxy | Neto base USD | Neto 1.5x | Neto +10RT | PF | DD cerrado USD | IC90 L5 media diaria USD | qBH20 | Estado sombra |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|"
    ]
    for k in FIVE:
        v=z[k];ci=v["bootstrap"]["5"]["CI90"]
        def fmt(n):return "N/D" if n is None else f"{n:,.2f}"
        lines.append(f"| {k} | {v['N_CASE_D0']} | {v['N_modelled_trades']} | "
         f"{fmt(v['net_base_usd'])} | {fmt(v['net_stress_1p5_usd'])} | "
         f"{fmt(v['net_plus10_rt_usd'])} | {fmt(v['PF_base'])} | "
         f"{fmt(v['DD_closed_base_usd'])} | {ci if ci else 'N/D'} | "
         f"{fmt(v['q_BH20'])} | {v['D1_shadow']} |")
    lines.extend([
        "",
        "**El DD reportado es CLOSED equity, NO Last intratrade ni trailing real de 50K.**",
        "IC90 bootstrap moving-block 10.000, L5 principal, L3/L10 sensibilidad.",
        "p/q es exploratoria, no compensa selección adaptativa de T01–T208.",
        "D1 formal mantiene BLOCKED_GATE_D0_5_OF_20; no D2 formal autorizada.",
        "No sumar H2020–24 minuto con T2025–26 Last como una cuenta.",
        "Ninguna variante optimizada después de observar este PnL.",
    ])
    return "\n".join(lines)+"\n"


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--month");parser.add_argument("--root",type=Path)
    parser.add_argument("--inputs",type=Path);parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    if args.month is not None:
        month_guard(args.month)
        if args.root is None:raise ValueError("SOURCE_ROOT_REQUIRED")
        result=month_study(args.root,args.month,registry())
        args.out.parent.mkdir(parents=True,exist_ok=True)
        if args.out.exists():raise ValueError("PRIVATE_FILE_ALREADY_EXISTS")
        args.out.write_text(json.dumps(result,separators=(",",":"))+"\n")
        print("EXPLORATORY_FIVE_MONTH_QC="+json.dumps({
            "month":args.month,"source":result["source"],
            "eligible":result["eligible"],
            "D0_case_counts":result["case_counts"],
            "broker_fills_verified":False,
        },sort_keys=True))
    else:
        if args.inputs is None or args.report is None:
            raise ValueError("SEVEN_MONTH_INPUTS_AND_REPORT_REQUIRED")
        source={
            m:json.loads((args.inputs/f"five_t_d1_{m}.json").read_text())
            for m in MONTHS
        }
        final=aggregate(source,registry())
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        args.report.write_text(report(final))
        print("EXPLORATORY_FIVE_SAFE_FINAL="+json.dumps({
            "source":final["source_days"],"eligible":final["eligible_days"],
            "ids":list(FIVE),"N_proxy_trades":{
                k:v["N_modelled_trades"] for k,v in final["economics"].items()},
            "net_usd":{k:v["net_base_usd"] for k,v in final["economics"].items()},
            "PF":{k:v["PF_base"] for k,v in final["economics"].items()},
            "DD_closed":{k:v["DD_closed_base_usd"] for k,v in final["economics"].items()},
            "qBH20":{k:v["q_BH20"] for k,v in final["economics"].items()},
            "screen_favorable":final["screen_favorable_ids"],
            "formal_D1_approved":False,
        },sort_keys=True))
