#!/usr/bin/env python3
"""T209-T228: causal atomic Last G0/D0 for twenty frozen structural mechanisms.

Never measures future outcomes, PnL, PF, drawdown or broker fills.
Uses ONLY existing seven 2025-10..2026-04 DEV months, sealed dates fail closed.
Signal windows and exact rules frozen in the preregistered JSON.
"""
from __future__ import annotations
import argparse
import json
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import combinations, groupby
from pathlib import Path
from statistics import median

from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS, month_days
from nq_b05h01_trade_expansion_month import et_edge, frozen_t05
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events

ROOT=Path(__file__).resolve().parents[1]
REGISTER=ROOT/"research/nq/NQ_T209_T228_20_STRUCTURAL_D0_PREREG_2026_10_13.json"
IDS=tuple(f"T{k}" for k in range(209,229))
BLOCKS=("A","B","C","D")
SOURCE_DAYS,READY_DAYS=140,135
CASE,CONTROL,OTHER,MISSING="CASE","CONTROL","OTHER","NOT_EVALUABLE"
LABELS=(CASE,CONTROL,OTHER,MISSING)
MIN_CASE=MIN_CONTROL=15
DUPLICATE_CUTOFF=0.85


def registry(path=REGISTER):
    r=json.loads(Path(path).read_text())
    if (r.get("prereg_id")!="NQ-T209-T228-20-DIVERSE-STRUCTURAL-G0-D0-V1"
        or r.get("version")!=2
        or r.get("months")!=list(MONTHS)
        or (r.get("source_sessions"),r.get("eligible_sessions"))!=(SOURCE_DAYS,READY_DAYS)
        or [x["block"] for x in r["blocks"]]!=list(BLOCKS)
        or tuple(x["id"] for x in r["members"])!=IDS
        or set(r.get("trigger_definitions",{}))!=set(IDS)
        or any(x["take_profit_R"]!=1.5 or x["timeout_minutes"]!=15
               or x["nominal_risk_cap_usd"]!=250
               or x["future_outcomes_in_D0"] is not False
               for x in r["members"])
        or r["D0"]["case_min"]!=15
        or r["D0"]["control_min"]!=15
        or r["D0"]["min_diverse_testable_for_D1"]!=20
        or r["D0"]["jaccard_near_duplicate"]!=0.85
        or r["D0"]["no_future_outcome_reads"] is not True
        or r["no_new_data"] is not True or r["no_OOS"] is not True
        or r["blocked_new_five_second_signals"] is not True):
        raise ValueError("FROZEN_COHORT_REGISTER_PARITY_FAIL")
    for b in r["blocks"]:
        if b["block"] not in BLOCKS or len(b["ids"])!=5:
            raise ValueError("BLOCK_FIVE_IDS_REQUIRED")
        for k in b["ids"]:
            if k not in IDS:raise ValueError("BLOCK_ID_INVALID")
    return r


def month_guard(month):
    if month not in MONTHS:
        raise ValueError("SEALED_OR_OUT_OF_SCOPE_BEFORE_ANY_IO")
    return month


def sign(x):
    return (x>0)-(x<0)


def groups(rows):
    """Atomic time groups with order-invariant VWAP; do not use arbitrary last tick."""
    result=[]
    for ts,it in groupby(rows,key=lambda row:row[0]):
        a=list(it);qty=sum(z[2] for z in a)
        if qty<=0:raise ValueError("BAD_QTY")
        result.append({"time":ts, "price":F(sum(z[1]*z[2] for z in a),qty),
                       "qty":qty, "prints":len(a)})
    return result


def profile(rows):
    levels=Counter()
    for _,p,q in rows:levels[p]+=q
    if not levels:return None
    top=max(levels.values())
    poc=F(sum(p for p,v in levels.items() if v==top),sum(v==top for v in levels.values()))
    qty=sum(levels.values())
    return {"levels":levels,"poc":poc,"qty":qty,
            "hi":max(levels),"lo":min(levels),
            "vwap":F(sum(p*q for p,q in levels.items()),qty)}


def stats(rows):
    if not rows:return None
    g=groups(rows)
    if len(g)<4:return None
    pr=profile(rows)
    if pr is None:return None
    changes=[g[i]["price"]-g[i-1]["price"] for i in range(1,len(g))]
    net=g[-1]["price"]-g[0]["price"]
    total=sum((abs(d) for d in changes),F(0))
    return {"rows":rows,"groups":g,"profile":pr, "changes":changes,
            "net":net,"path":total,
            "efficiency":abs(net)/total if total else F(0),
            "end":g[-1]["price"],"start":g[0]["price"],
            "range":pr["hi"]-pr["lo"]}


def weighted_prints(rows, predicate):
    a=[(p,q) for _,p,q in rows if predicate(q)]
    if not a:return (None,0)
    total=sum(q for p,q in a)
    return (F(sum(p*q for p,q in a),total),len(a))


def group_time_share(g,reference,above=True):
    intervals=[b["time"]-a["time"] for a,b in zip(g,g[1:])]
    total=sum(intervals)
    if total<=0:return F(0)
    sel=sum(dt for a,dt in zip(g,intervals)
            if (a["price"]>reference if above else a["price"]<reference))
    return F(sel,total)


def segments_qty(g):
    i=len(g)//2
    first=sum(x["qty"] for x in g[:i])
    last=sum(x["qty"] for x in g[i:])
    return first,last,i


def regime_signal(hypothesis,current,previous,macro,long_context):
    """Return side or None; rules frozen in registry.trigger_definitions.

    All inputs end strictly at or before current E377 end. No future prints.
    """
    e=current;d=previous;g=e["groups"];levels=e["profile"]["levels"]
    q=e["profile"]["qty"];vw=e["profile"]["vwap"]
    lo,hi=e["profile"]["lo"],e["profile"]["hi"]
    mid=F(lo+hi,2);last=e["end"];body=e["net"]
    widths=e["range"]
    code=hypothesis

    if code=="T209":
        return sign(body) if abs(body)>=8 and 5*abs(body)>=3*e["path"] else None
    if code=="T210":
        x=last-vw
        return -sign(x) if widths>0 and e["path"]>=3*widths and abs(body)<=F(widths,4) and abs(x)>=4 else None
    if code=="T211":
        if len(g)<8:return None
        k=len(g)//2;a=g[k]["price"]-g[0]["price"];b=last-g[k]["price"]
        return sign(b) if abs(a)<=3 and abs(b)>=8 else None
    if code=="T212":
        sig=[sign(x) for x in e["changes"] if x]
        reversals=sum(a!=b for a,b in zip(sig,sig[1:]))
        x=last-vw
        return -sign(x) if reversals>=6 and abs(x)>=5 else None
    if code=="T213":
        if not e["changes"]:return None
        maxjump=max(abs(x) for x in e["changes"])
        k=next(i for i,x in enumerate(e["changes"]) if abs(x)==maxjump)
        delta=last-g[k+1]["price"]
        s=sign(e["changes"][k])
        return -s if maxjump>=12 and s*delta<=-6 else None

    if code in ("T214","T217"):
        upper=sum(vol for p,vol in levels.items() if 3*(p-lo)>=2*widths)
        lower=sum(vol for p,vol in levels.items() if 3*(p-lo)<=widths)
        if code=="T214":
            up=100*upper>=65*q and last>=mid+2
            down=100*lower>=65*q and last<=mid-2
        else:
            up=100*lower>=35*q and last>mid+4
            down=100*upper>=35*q and last<mid-4
        return (1 if up else -1) if up!=down else None
    if code=="T215":
        delta=e["profile"]["poc"]-d["profile"]["poc"]
        return sign(delta) if abs(delta)>=6 and abs(body)>=4 and sign(delta)!=sign(body) else None
    if code=="T216":
        top3=sum(sorted(levels.values(),reverse=True)[:3])
        x=e["profile"]["poc"]-last
        return sign(x) if top3*2>=q and abs(x)>=8 else None
    if code=="T218":
        level=min(levels,key=lambda p:(abs(F(p)-last),p))
        x=last-d["profile"]["poc"]
        return sign(x) if levels[level]*4*len(levels)<=q and abs(x)>=8 else None

    if code=="T219":
        big,nb=weighted_prints(e["rows"],lambda qty:qty>=4)
        small,ns=weighted_prints(e["rows"],lambda qty:qty<=2)
        return sign(big-small) if nb>=10 and ns>=10 and abs(big-small)>=5 else None
    if code=="T220":
        ep=F(q,len(e["rows"]))
        dp=F(d["profile"]["qty"],len(d["rows"]))
        return sign(body) if 2*ep>=3*dp and abs(body)>=6 else None
    if code=="T221":
        big,nb=weighted_prints(e["rows"],lambda qty:qty>=4)
        x=big-last if nb>=10 else F(0)
        return sign(x) if nb>=10 and abs(body)>=6 and abs(x)>=6 and sign(x)==-sign(body) else None
    if code=="T222":
        first_qty,last_qty,k=segments_qty(g)
        late=last-g[k]["price"]
        return -sign(late) if first_qty>=2*last_qty and abs(late)>=6 else None
    if code=="T223":
        x=last-vw
        dense=sum(row["prints"]>=3 for row in g)
        return -sign(x) if 2*dense>=len(g) and widths<=18 and abs(x)>=4 else None

    if code in ("T224","T225","T227") and macro is None and code!="T227":
        return None
    if code=="T224":
        ref=macro["profile"]["vwap"]
        above=group_time_share(g,ref,True)
        below=group_time_share(g,ref,False)
        up=above>=F(7,10) and last>=ref+4
        down=below>=F(7,10) and last<=ref-4
        return (1 if up else -1) if up!=down else None
    if code=="T225":
        ref=macro["profile"]["vwap"]
        x=last-ref
        sides=[sign(row["price"]-ref) for row in g]
        nonzero=[s for s in sides if s!=0]
        crosses=sum(a!=b for a,b in zip(nonzero,nonzero[1:]))
        return -sign(x) if crosses>=4 and abs(x)>=6 else None
    if code=="T226":
        if long_context is None:return None
        ref=long_context["profile"]["poc"]
        before=e["start"]-ref;after=last-ref
        return sign(after) if abs(before)>=4 and abs(after)>=6 and sign(before)!=sign(after) else None
    if code=="T227":
        eg=[b["time"]-a["time"] for a,b in zip(g,g[1:])]
        dg=[b["time"]-a["time"] for a,b in zip(d["groups"],d["groups"][1:])]
        x=last-vw
        return -sign(x) if eg and dg and 2*median(eg)>=3*median(dg) and e["path"]>=2*widths and abs(x)>=4 else None
    if code=="T228":
        past=d["net"]
        delta=last-d["end"]
        return -sign(past) if d["efficiency"]>=F(65,100) and e["efficiency"]<=F(1,4) and abs(past)>=8 and -sign(past)*delta>=3 else None
    raise AssertionError("UNKNOWN_HYPOTHESIS_"+code)


def bar_subset(events, times, b):
    i,j=bisect_left(times,b.start_timestamp),bisect_right(times,b.end_timestamp)
    a=events[i:j]
    if len(a)!=b.prints or not a:
        raise AssertionError("NON_ATOMIC_BAR_SPAN")
    if sum(p*q for _,p,q in a)!=b.price_times_qty_ticks:
        raise AssertionError("ATOMIC_BAR_VWAP_MISMATCH")
    return a


def classify_day(events,day,reg):
    """Exactly 20 labels for eligible DEV day. D0 NEVER reads price after signal."""
    dev_day(day)
    complete=completed_bars_by_print_count(events,day,(377,4181,10946))
    bars=complete[377]
    times=[row[0] for row in events]
    cache={}
    labels={}
    for b in reg["blocks"]:
        ident=b["block"]
        # Time windows from registry, never based on observed PnL.
        edge0=et_edge(day,*tuple(map(int,b["window_et"][0].split(":"))))
        edge1=et_edge(day,*tuple(map(int,b["window_et"][1].split(":"))))
        idx=next((i for i,x in enumerate(bars)
                  if edge0<=x.end_timestamp<edge1),None)
        if idx is None or idx<1:
            for k in b["ids"]: labels[k]=MISSING
            continue
        current=bars[idx]
        prev=bars[idx-1]
        e=stats(bar_subset(events,times,current))
        d=stats(bar_subset(events,times,prev))
        if e is None or d is None:
            for k in b["ids"]:labels[k]=MISSING
            continue
        prevmacro=next((x for x in reversed(complete[4181])
                        if x.end_timestamp<current.end_timestamp),None)
        prevlong=next((x for x in reversed(complete[10946])
                       if x.end_timestamp<current.end_timestamp),None)
        ma=stats(bar_subset(events,times,prevmacro)) if prevmacro else None
        lng=stats(bar_subset(events,times,prevlong)) if prevlong else None
        for k in b["ids"]:
            side=regime_signal(k,e,d,ma,lng)
            if side is None:
                labels[k]=CONTROL
                continue
            if side not in (-1,1):raise AssertionError("BAD_CAUSAL_SIDE")
            # D0 reference: Last ATOMIC GROUP VWAP, not executable price.
            stop=F(e["profile"]["lo"]-2) if side>0 else F(e["profile"]["hi"]+2)
            risk=side*(e["end"]-stop)
            if risk<8 or risk>400:
                labels[k]=OTHER
                continue
            instrument="NQ" if risk*5<=250 else "MNQ"
            if risk*(5 if instrument=="NQ" else F(1,2))>250:
                labels[k]=OTHER
                continue
            # Actual next-group entry/stop/risk MUST be recalculated in D1.
            labels[k]=CASE
    if set(labels)!=set(IDS):raise AssertionError("COHORT_20_INCOMPLETE")
    if any(s not in LABELS for s in labels.values()):
        raise AssertionError("COHORT_LABEL_INVALID")
    return labels


def month_stage(root,month,reg):
    month_guard(month)    # check BEFORE touching ANY licensed data
    count={k:Counter() for k in IDS}
    pair=Counter()
    source=eligible=0
    qc=Counter()
    for day in sorted(month_days(root,month)):
        d=dev_day(day)
        source+=1
        events=list(source_events(file_for(root,d,"Last")))
        # Frozen READY calendar matching original 135 sessions; legacy T05
        # ONLY for eligibility parity/QC, NEVER as new T-C signal/feature.
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!="READY":
            if status not in ("SKIP_MISSING_OPENING_RANGE","SKIP_TINY_OPENING_RANGE"):
                raise AssertionError("UNKNOWN_QC")
            continue
        labels=classify_day(events,day,reg)
        cases=[k for k in IDS if labels[k]==CASE]
        for k,v in labels.items():count[k][v]+=1
        for a,b in combinations(cases,2):pair[f"{a}__{b}"]+=1
        eligible+=1
        del events
    if sum(qc.values())!=source or qc["READY"]!=eligible:
        raise AssertionError("SOURCE_QC_INCONSISTENCY")
    if any(sum(count[k].values())!=eligible for k in IDS):
        raise AssertionError("MISSING_MEMBER_DAY")
    return {
        "month":month,"source_sessions":source,"eligible_sessions":eligible,
        "counts":{k:{z:count[k][z] for z in LABELS} for k in IDS},
        "case_joint_counts":dict(pair),
        "future_outcomes_read":False,"PNL":None,"PF":None,"DD":None,
        "bid_ask_execution_verified":False,"holdouts_opened":False,
        "new_data":False,"private_rows_or_event_dates_emitted":False
    }


def aggregate(rows,reg):
    if set(rows)!=set(MONTHS):
        raise AssertionError("NEEDS_ALL_SEVEN_DEV_MONTHS")
    totals={k:Counter() for k in IDS}
    co=Counter()
    source=eligible=0
    for m in MONTHS:
        r=rows[m]
        if (r["month"]!=m
            or r["future_outcomes_read"] is not False
            or r["PNL"] is not None or r["PF"] is not None or r["DD"] is not None
            or any(r[k] is not False for k in (
                "holdouts_opened","new_data","private_rows_or_event_dates_emitted",
                "bid_ask_execution_verified"))
            or set(r["counts"])!=set(IDS)):
            raise AssertionError("UNSAFE_MONTH_AGGREGATE")
        source+=r["source_sessions"]
        eligible+=r["eligible_sessions"]
        for k in IDS:totals[k].update(r["counts"][k])
        co.update(r["case_joint_counts"])
    if (source,eligible)!=(SOURCE_DAYS,READY_DAYS):
        raise AssertionError("SESSION_PARITY_140_135")
    if any(sum(totals[k].values())!=eligible for k in IDS):
        raise AssertionError("INCOMPLETE_D0_MEMBER")
    testable=[k for k in IDS if totals[k][CASE]>=MIN_CASE and
              totals[k][CONTROL]>=MIN_CONTROL]
    pairs=[]
    near=set()
    for a,b in combinations(testable,2):
        common=co[f"{a}__{b}"]
        union=totals[a][CASE]+totals[b][CASE]-common
        jac=common/union if union else 0.
        if jac>=DUPLICATE_CUTOFF:
            near.add(b)
            pairs.append({"members":[a,b],"jaccard":round(jac,4)})
    distinct=[k for k in testable if k not in near]
    state=("D0_PASS_TO_FULL_COHORT_D1_PREREG_REQUIRED"
           if len(distinct)>=20 else
           "D0_COHORT_INSUFFICIENT_DISTINCT_TESTABLE_NO_D1")
    all_rows=[]
    for member in reg["members"]:
        k=member["id"]
        all_rows.append({
            "id":k,"block":member["block"],
            "CASE":totals[k][CASE],"CONTROL":totals[k][CONTROL],
            "OTHER":totals[k][OTHER],"NOT_EVALUABLE":totals[k][MISSING],
            "status":"TESTABLE" if k in testable else "LOW_POWER_OR_UNDERCONTROL",
            "distinct":k in distinct})
    return {
        "stage":"T209_T228_G0_D0_ONLY_NO_ECONOMIC_OUTCOMES",
        "source_sessions":source,"eligible_sessions":eligible,
        "members":all_rows,"N_registered":20,
        "N_testable":len(testable),"N_distinct_testable":len(distinct),
        "near_duplicate_pairs":pairs,"D0":state,
        "N_D1_passes":None,"D1_authorized":False,"D2_authorized":False,
        "future_outcomes_read":False,"PNL":None,"PF":None,"DD":None,
        "broker_fills_verified":False,
        "holdouts_opened":False,"new_data":False
    }


def report(z):
    lines=[
        "# T209–T228 — G0/D0 veinte hipótesis estructurales (solo LAST DEV)",
        "",
        "**Sin observar PnL, PF ni drawdown; 0 operaciones de broker verificadas.**",
        f"Fuente {z['source_sessions']} sesiones, elegibles {z['eligible_sessions']}.",
        f"Registradas {z['N_registered']}, testables {z['N_testable']}, "
        f"distintas testables {z['N_distinct_testable']}.",
        f"**Resultado D0: {z['D0']}**. D1 NO AUTORIZADA sin prerregistro posterior.",
        "",
        "| ID | Bloque | CASE | CONTROL | OTHER | N/D | Testable | Distinta |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for m in z["members"]:
        lines.append(
            f"| {m['id']} | {m['block']} | {m['CASE']} | {m['CONTROL']} | "
            f"{m['OTHER']} | {m['NOT_EVALUABLE']} | {m['status']} | "
            f"{'Sí' if m['distinct'] else 'No'} |"
        )
    lines.extend([
        "",f"Colisiones Jaccard>=0,85: {len(z['near_duplicate_pairs'])}.",
        "La tabla clasifica activaciones/controles, NO ganancias ni entradas reales.",
        "T205...T208 ya pertenecían a la cohorte anterior; aquí son NUEVOS T209–T228.",
        "Riesgo de señal preliminar D0 al precio atómico no es riesgo de fill.",
        "No cambiar ventanas, umbrales o signos para aumentar conteo de CASE;",
        "registrar fallos de potencia, pasar a otro bloque si faltan 20 distintas.",
        "","Holdouts T mayo–sept2026 y H 2025–26 siguen cerrados.",
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
    reg=registry()
    if a.month is not None:
        month_guard(a.month)
        if a.root is None:raise ValueError("ROOT_REQUIRED")
        z=month_stage(a.root,a.month,reg)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,sort_keys=True)+"\n")
        print("T209_T228_D0_SAFE_MONTH="+json.dumps({
            "month":a.month,"source":z["source_sessions"],
            "eligible":z["eligible_sessions"],
            "cases_by_id":{k:v[CASE] for k,v in z["counts"].items()}},sort_keys=True))
    else:
        if a.inputs is None or a.report is None:
            raise ValueError("REQUIRES_INPUTS_AND_REPORT")
        monthly={m:json.loads((a.inputs/f"t209_t228_d0_{m}.json").read_text()) for m in MONTHS}
        z=aggregate(monthly,reg)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
        a.report.write_text(report(z))
        print("T209_T228_G0_D0_SAFE_FINAL="+json.dumps({
            "source":z["source_sessions"],"eligible":z["eligible_sessions"],
            "N_testable":z["N_testable"],
            "N_distinct_testable":z["N_distinct_testable"],
            "stage":z["D0"]},sort_keys=True))
