#!/usr/bin/env python3
"""T05+T215 and T05+T186+T215: MFFU Rapid EOD 50K Last risk shadow.

Reuses frozen eight-parent extraction and source signals, no parameter search.
Two studies: original decision PATH_FIXED and fee-aware -$600 router.
Keeps private individual days/events in runner, exports only safe aggregates.
Last prices are not executable Bid/Ask fills; worst timestamp group is an
ADVERSE ENVELOPE, never a certified intratrade broker drawdown or breach.
"""
from __future__ import annotations
import argparse
import json
from bisect import bisect_left,bisect_right
from collections import Counter,defaultdict
from datetime import date
from fractions import Fraction as F
from itertools import groupby,islice
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import BASE,NEW,STRESS,frozen_t05,owner_policy,et_edge
from nq_t169_t188_monetary_month import new_signals
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade
from nq_t133_t168_d1_engine import first_future_groups,model_one
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t209_t228_structural_d0 import registry as new_registry,stats,bar_subset,regime_signal,month_guard,CASE
from nq_all13_t8_shared_portfolios import extract_session,account_day,ORDER,T,MODELED as MODELLED
from nq_t133_t152_executable_d0_batch import load_registry as old_registry

MASKS={
    "A_T05_T215":("T05-377","T215"),
    "B_T05_T186_T215":("T05-377","T186","T215"),
}
FEES={"NQ":4.68,"MNQ":1.90}
FROZEN_FEES={"T05-377":7.5,"T186":7.5}
EXPECTED={
    "A_T05_T215":(123,6698.25,6996.67,121,2),
    "B_T05_T186_T215":(172,7615.75,8052.35,170,2),
}
SOURCE,READY=140,135
LIMIT=2000.
TARGET=3000.
MIN_TRADE_DAYS=4
CONSISTENCY=.30
STOP_DAY=-600.
MAX_DAILY=2
STAGE="PRIVATE_RAPID_EOD_50K_LAST_ENVELOPE_FIXED_AND_MFFU_ROUTER"


def fee_for(x):
    if x["instrument"] not in FEES:
        raise ValueError("UNKNOWN_CONTRACT")
    return FEES[x["instrument"]]


def old_fee(x):
    return FROZEN_FEES.get(x["ID"],4. if x["instrument"]=="NQ" else 1.50)


def cost_corrected(x):
    return round(x["net"]+old_fee(x)-fee_for(x),2)


def original_engine_entry(events,day,oldbars,x,t05,times,selected_signals,newreg):
    """Return (side, modeled_entry_ticks); independent frozen signal parity."""
    key=x["ID"]
    if key in ("T05-377","T186"):
        ts_side=selected_signals.get((key,x["decision"]))
        if ts_side is None:
            raise AssertionError("MISSING_ORIGINAL_SIGNAL_SIDE_"+key)
        ts,side=ts_side
        if ts!=x["decision"]:
            raise AssertionError("FROZEN_SIGNAL_TIMESTAMP_CHANGED_"+key)
        policy=owner_policy(BASE if key=="T05-377" else NEW,oldbars,STRESS)
        result=simulate_single_trade(
            islice(events,bisect_right(times,ts),None),
            Signal(day,ts,side),policy)
        if (result["status"]!="SYNTHETIC_FILL_MODEL_ONLY"
            or result["entry_timestamp"]!=x["entry"]
            or result["exit_timestamp"]!=x["exit"]
            or round(result["estimated_net_usd"],2)!=x["net"]):
            raise AssertionError("LEGACY_PARENT_TRADE_PARITY_"+key)
        if result["entry_price_ticks"]<=0:
            raise AssertionError("INVALID_ENTRY_TICK")
        return side,F(result["entry_price_ticks"])
    if key!="T215":
        raise ValueError("UNAPPROVED_RISK_TRACE_OWNER")
    # T215 is from the frozen B-block first 377-print bar 10:00–10:15 ET.
    block=next(b for b in newreg["blocks"] if b["block"]=="B")
    lo=et_edge(day,*map(int,block["window_et"][0].split(":")))
    hi=et_edge(day,*map(int,block["window_et"][1].split(":")))
    complete=completed_bars_by_print_count(events,day,(377,4181,10946))
    cand=complete[377]
    ix=next((i for i,b in enumerate(cand) if lo<=b.end_timestamp<hi),None)
    if ix is None or ix<1:
        raise AssertionError("FROZEN_T215_ANCHOR_MISSING")
    bar=cand[ix]
    current=stats(bar_subset(events,times,bar))
    prev=stats(bar_subset(events,times,cand[ix-1]))
    macro_bar=next((b for b in reversed(complete[4181])
                    if b.end_timestamp<bar.end_timestamp),None)
    long_bar=next((b for b in reversed(complete[10946])
                   if b.end_timestamp<bar.end_timestamp),None)
    macro=stats(bar_subset(events,times,macro_bar)) if macro_bar else None
    longer=stats(bar_subset(events,times,long_bar)) if long_bar else None
    side=regime_signal("T215",current,prev,macro,longer)
    if side not in (-1,1) or bar.end_timestamp!=x["decision"]:
        raise AssertionError("T215_SIDE_OR_DECISION_PARITY")
    stop=F(current["profile"]["lo"]-2 if side>0 else
           current["profile"]["hi"]+2)
    groups,covered=first_future_groups(events,bar.end_timestamp,15)
    result=model_one(groups,side,stop,1.5,15,bar.end_timestamp,covered)
    if (result["status"]!=MODELLED or result["entry_group_ambiguous"]
        or result["instrument"]!=x["instrument"]
        or round(result["net_usd"],2)!=x["net"]
        or not groups or groups[0][0]!=x["entry"]):
        raise AssertionError("T215_PARENT_MODEL_PARITY")
    # Same adverse whole-timestamp entry price as parent model_one.
    worst=F(groups[0][2] if side>0 else groups[0][1])
    return side,worst+2*side


def last_adverse_envelope(events,times,x,side,entry_ticks):
    """Monotonic worst-possible Last envelope; NOT broker floating DD.

    Include whole entry and exit timestamp groups pessimistically.
    Best mark before worst mark per group for a conservative intra-group
    drawdown bound; Last timestamps cannot tell us actual order/fills.
    """
    lo=bisect_left(times,x["entry"])
    hi=bisect_right(times,x["exit"])
    rows=events[lo:hi]
    if not rows or rows[0][0]!=x["entry"] or rows[-1][0]!=x["exit"]:
        raise AssertionError("LAST_ENVELOPE_MISSING_ENTRY_OR_EXIT")
    value=5. if x["instrument"]=="NQ" else .5
    newfee=fee_for(x)
    exit_slip_usd=2*value
    min_relative=0.
    max_relative=0.
    intratrade_upper_dd=0.
    running_peak=0.
    for ts,it in groupby(rows,key=lambda y:y[0]):
        g=list(it)
        if not g:continue
        prices=[y[1] for y in g]
        extreme_min=min(prices)
        extreme_max=max(prices)
        worst=extreme_min if side>0 else extreme_max
        best=extreme_max if side>0 else extreme_min
        low=side*(float(F(worst)-entry_ticks))*value-newfee-exit_slip_usd
        high=side*(float(F(best)-entry_ticks))*value-newfee-exit_slip_usd
        if low>high+1e-6:
            raise AssertionError("REVERSED_SIDE_LAST_ENVELOPE")
        min_relative=min(min_relative,low)
        max_relative=max(max_relative,high)
        running_peak=max(running_peak,high)
        intratrade_upper_dd=max(intratrade_upper_dd,running_peak-low)
    return {
        "worst_rel_usd":round(min_relative,4),
        "best_rel_usd":round(max_relative,4),
        "local_upper_DD_usd":round(intratrade_upper_dd,4),
        "observed_whole_timestamp_bound":True,
    }


def router_mffu(intents,mask):
    """Same frozen router as account_day, just apply actual NQ/MNQ RT fees.

    Original MAX_DAILY, STOP_DAY, and priority are immutable. If $-600 daily
    barrier changes a selected order, this is a new counterfactual path.
    """
    selected=[q for k in mask for q in intents[k]]
    selected.sort(key=lambda q:(q["decision"],ORDER[q["ID"]]))
    pnl=0.;last_exit=-1;out=[];rej=Counter()
    for x in selected:
        if len(out)>=MAX_DAILY or pnl<=STOP_DAY:
            rej["capacity"]+=1;continue
        if x["decision"]<=last_exit:
            rej["overlap"]+=1;continue
        if x["status"]!="MODELLED":
            if x["status"] in (
                "UNRESOLVED_LAST_EXECUTION",
                "ENTRY_TIMESTAMP_ORDER_AMBIGUOUS",
                "MISSING_WHOLE_TIMESTAMP_GROUPS",
                "TIME_EXIT_NO_POST_ENTRY_GROUP"):
                raise ValueError("CANNOT_ESTIMATE_UNRESOLVED_ORDER")
            rej["unmodeled"]+=1;continue
        if x["entry"]<=x["decision"] or x["exit"]<x["entry"]:
            raise AssertionError("NONCAUSAL_NEXT_TIMESTAMP")
        out.append(x)
        last_exit=x["exit"]
        pnl=round(pnl+cost_corrected(x),2)
    return out,rej


def month_stage(root,month,newreg,oldreg):
    month_guard(month)  # before licensed Last filesystem access
    source=0;ready=0
    private=[]
    for d in sorted(month_days(root,month)):
        dev_day(d)
        events=list(source_events(file_for(root,dev_day(d),"Last")))
        source+=1
        status,oldbars,t05=frozen_t05(events,d)
        if status!="READY":
            if status not in ("SKIP_MISSING_OPENING_RANGE",
                              "SKIP_TINY_OPENING_RANGE"):
                raise AssertionError("QC_FROZEN_STATUS_CHANGED")
            continue
        ready+=1
        intents,labels,oldcase=extract_session(events,d,oldbars,t05,oldreg,newreg)
        times=[t for t,_,_ in events]
        sigs={}
        sigs.update({("T05-377",ts):(ts,side) for ts,side,_ in t05})
        old186,_=new_signals(events,d)
        if old186.get("T186") is not None:
            sigs[("T186",old186["T186"][0])]=old186["T186"]
        cache={}
        for mask in MASKS.values():
            fixed,_=account_day(intents,mask)
            dynamic,_=router_mffu(intents,mask)
            for x in fixed+dynamic:
                key=(x["ID"],x["decision"],x["entry"],x["exit"])
                if key not in cache:
                    side,entry=original_engine_entry(
                        events,d,oldbars,x,t05,times,sigs,newreg)
                    envelope=last_adverse_envelope(
                        events,times,x,side,entry)
                    cache[key]={"ID":x["ID"],"instrument":x["instrument"],
                                "net_original":x["net"],"net_mffu":cost_corrected(x),
                                "envelope":envelope}
        def attach(trades):
            return [
                cache[(x["ID"],x["decision"],x["entry"],x["exit"])]
                for x in trades]
        private.append({
            "day":d,"fixed":{
                k:attach(account_day(intents,v)[0]) for k,v in MASKS.items()},
            "fee_router":{
                k:attach(router_mffu(intents,v)[0]) for k,v in MASKS.items()},
            "T215_frozen_CASE":int(labels["T215"]==CASE),
        })
        del events
    if ready>source:
        raise AssertionError("SOURCE_READY_IMPOSSIBLE")
    return {"stage":STAGE,"month":month,"source":source,"ready":ready,
            "days":private,"holdouts_opened":False,"new_data":False,
            "broker_fills_verified":False,"public_trade_details":False}


def dd_from_days(days):
    eq=peak=dd=0.
    for v in days:
        eq+=v;peak=max(peak,eq);dd=max(dd,peak-eq)
    return round(dd,2)


def portfolio_metrics(rows,mask,kind):
    daily=[];detailed=[];contract=Counter();owner=Counter()
    min_mark=0.;global_peak=0.;max_adverse_dd=0.
    worst_daily_open_rel=0.
    for d in rows:
        day_trades=d[kind][mask]
        start=sum(daily)
        net=0.;worst_day_open=0.
        for t in day_trades:
            eq_prior=start+net
            env=t["envelope"]
            low=eq_prior+env["worst_rel_usd"]
            high=eq_prior+env["best_rel_usd"]
            # pessimistic upper bound where timestamp group order is unknown
            global_peak=max(global_peak,high,eq_prior)
            max_adverse_dd=max(max_adverse_dd,global_peak-low,
                               env["local_upper_DD_usd"])
            worst_day_open=min(worst_day_open,net+env["worst_rel_usd"])
            min_mark=min(min_mark,low)
            contract[t["instrument"]]+=1
            owner[t["ID"]]+=1
            net+=t["net_mffu"]
        daily.append(round(net,2))
        detailed.append({"day":d["day"],"trades":day_trades,
                         "net":round(net,2),"worst_day_open":round(worst_day_open,4)})
        worst_daily_open_rel=min(worst_daily_open_rel,worst_day_open)
        global_peak=max(global_peak,start+net)
    return {
        "N":sum(contract.values()),"NQ":contract["NQ"],"MNQ":contract["MNQ"],
        "owner_N":dict(owner),
        "net_mffu":round(sum(daily),2),
        "DD_closed_eod":dd_from_days(daily),
        "DD_last_adverse_upper_bound":round(max_adverse_dd,2),
        "worst_intraday_vs_day_open":round(worst_daily_open_rel,2),
        "private":detailed,
    }


def stage_replay(private_days,funded=False,strict_eval_lock=False):
    """ONE mock evaluation account then separate sim-funded stage next session.

    EOD trailing floor fixed throughout intraday, updated at end of session.
    Source Last intra-group marks are upper-bound failures, NOT broker breaches.
    """
    balance=0.;eod_high=0.;days_traded=0;max_positive_day=0.
    first_barrier=None;first_target=None;first_buffer=None
    max_gap=0;gap_count=0;prev_trade_date=None
    worst_room=float("inf");seen_trades=0;peak_before=0.
    active=True;failed=False
    for i,row in enumerate(private_days):
        # Based on CLOSED results of previous sessions, trailing never falls.
        if funded:
            floor=min(100.,max(-LIMIT,eod_high-LIMIT))
        elif strict_eval_lock:
            floor=min(100.,max(-LIMIT,eod_high-LIMIT))
        else:
            floor=max(-LIMIT,eod_high-LIMIT)
        in_day=0.
        if row["trades"]:
            days_traded+=1
            day=date.fromisoformat(row["day"])
            if prev_trade_date is not None:
                gap=(day-prev_trade_date).days
                max_gap=max(max_gap,gap)
                gap_count+=int(gap>7)
            prev_trade_date=day
        for t in row["trades"]:
            worst=balance+in_day+t["envelope"]["worst_rel_usd"]
            worst_room=min(worst_room,worst-floor)
            if first_barrier is None and worst<=floor:
                first_barrier=i+1
                failed=True
                # DO NOT interpret hypothetical succeeding path as a valid
                # surviving evaluation; stop at first bound breach.
                break
            in_day+=t["net_mffu"];seen_trades+=1
        if failed:break
        balance=round(balance+in_day,2)
        if balance<=floor:
            first_barrier=i+1;failed=True;break
        eod_high=max(eod_high,balance)
        max_positive_day=max(max_positive_day,in_day)
        if funded:
            if first_buffer is None and balance>=2100.:
                first_buffer=i+1
        elif (first_target is None and balance>=TARGET
              and days_traded>=MIN_TRADE_DAYS
              and max_positive_day<=CONSISTENCY*balance+1e-8):
            first_target=i+1
            break
    return {
        "phase":"SIM_FUNDED_FROM_ZERO" if funded else "EVALUATION_50K_FROM_ZERO",
        "trades_processed_before_stop":seen_trades,
        "trading_days_processed":days_traded,
        "first_adverse_envelope_floor_touch_session_index":first_barrier,
        "first_eval_target_and_consistency_session_index":first_target,
        "first_funded_2100_buffer_session_index":first_buffer,
        "current_balance_if_no_bound_failure":round(balance,2) if not failed else None,
        "min_open_equity_distance_from_floor_bound_usd":
            round(worst_room,2) if worst_room<float("inf") else None,
        "largest_positive_closed_day_usd":round(max_positive_day,2),
        "max_gap_calendar_days_between_traded_days":max_gap,
        "gaps_over_7_calendar_days_between_trade_days":gap_count,
        "conditioned_on_last_bound_not_broker_fills":True,
        "news_calendar_verified":False,
        "inactivity_rule_resolved":False,
    }


def eval_then_funded(trades_by_day):
    eval_stage=stage_replay(trades_by_day)
    strict=stage_replay(trades_by_day,strict_eval_lock=True)
    if eval_stage["first_eval_target_and_consistency_session_index"] is not None:
        # The first evaluation pass is a cutoff of DEV, NOT an OOS interval.
        funded_start=eval_stage["first_eval_target_and_consistency_session_index"]
        funded=stage_replay(trades_by_day[funded_start:],funded=True)
    else:
        funded=None
    return {"evaluation":eval_stage,"evaluation_floor_lock_sensitivity":strict,
            "post_eval_funded_fresh_zero":funded}


def aggregate(months):
    if set(months)!=set(MONTHS):
        raise AssertionError("EXACT_SEVEN_DEV_MONTHS")
    rows=[];source=ready=0
    for month in MONTHS:
        r=months[month]
        if (r["stage"]!=STAGE or r["month"]!=month
            or any(r[k] is not False for k in (
                "holdouts_opened","new_data","broker_fills_verified","public_trade_details"))
            or r["ready"]!=len(r["days"])):
            raise AssertionError("PRIVATE_RUN_SCHEMA_OR_SOURCE_FAIL")
        rows+=r["days"];source+=r["source"];ready+=r["ready"]
    if (source,ready,len(rows))!=(SOURCE,READY,READY):
        raise AssertionError("140_SOURCE_135_READY_REQUIRED")
    if [r["day"] for r in rows]!=sorted(r["day"] for r in rows):
        raise AssertionError("NONCHRONOLOGICAL_SESSIONS")
    outputs={}
    for mask in MASKS:
        fixed=portfolio_metrics(rows,mask,"fixed")
        expected_n,old_net,new_net,eq_nq,eq_mnq=EXPECTED[mask]
        old=round(sum(
            t["net_original"] for r in rows for t in r["fixed"][mask]),2)
        if (fixed["N"],old,fixed["net_mffu"],fixed["NQ"],fixed["MNQ"])!=(
            expected_n,old_net,new_net,eq_nq,eq_mnq):
            raise AssertionError("FROZEN_TWO_PARENT_ROUTES_AND_FEE_SWAP_NOT_REPRODUCED_"+mask+
                                 "_"+str((fixed["N"],old,fixed["net_mffu"],fixed["NQ"],fixed["MNQ"])))
        rerouted=portfolio_metrics(rows,mask,"fee_router")
        fixed_private=fixed.pop("private")
        reroute_private=rerouted.pop("private")
        outputs[mask]={
            "fixed_original_decision_path":fixed,
            "mffu_fee_aware_daily_stop_rerouter":rerouted,
            "replay_mffu_fee_router":eval_then_funded(reroute_private),
            "fixed_path_fee_swap_reconciled":True,
            "rerouter_changes_N":rerouted["N"]-fixed["N"],
            "source_last_only":True,
        }
    return {
        "stage":"MFFU_RAPID_EOD_50K_TOP2_LAST_ADVERSE_ENVELOPE_SHADOW",
        "official_50k_target":3000,"official_50k_eod_max_loss":2000,
        "official_eval_consistency":.30,"official_eval_min_trading_days":4,
        "official_funded_lock_floor_relative":100,
        "source_sessions":source,"eligible_sessions":ready,
        "results":outputs,
        "max_concurrent_positions":1,"max_new_entries_per_day":2,
        "net_fee_NQ_roundtrip_usd":4.68,"net_fee_MNQ_roundtrip_usd":1.90,
        "adverse_exit_slip_ticks":2,
        "hypothetical_last_path":True,"broker_fills_verified":False,
        "real_breaches_determined":False,
        "news_rule_verified":False,"inactivity_rule_certified":False,
        "holdouts_opened":False,"new_data":False,"individual_trade_paths_exported":False,
        "eval_to_funded_out_of_sample":False,
    }


def report(z):
    def fmt(x):
        return "N/D" if x is None else str(x)
    lines=[
        "# Replay riesgo Last: dos carteras vs MFFU Rapid EOD 50K",
        "",
        "**Conservador y NO verificable como fill de broker ni OOS.**",
        f"{z['source_sessions']} sesiones de origen, {z['eligible_sessions']} READY.",
        "Comparación fee NQ $4,68 RT / MNQ $1,90 RT (sin duplicar fees).",
        "",
        "| Cuenta simulada | Trades | Neto MFFU USD | DD diario cerrado | Límite superior DD Last adverso | Peor caída intra día desde inicio |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for k,v in z["results"].items():
        for tag,model in (("Original decisions / corrected fees",v["fixed_original_decision_path"]),
                          ("Rerouted by corrected fees",v["mffu_fee_aware_daily_stop_rerouter"])):
            lines.append(f"| {k} {tag} | {model['N']} | {fmt(model['net_mffu'])} | "+
                f"{fmt(model['DD_closed_eod'])} | {fmt(model['DD_last_adverse_upper_bound'])} | "+
                f"{fmt(model['worst_intraday_vs_day_open'])} |")
    lines.append("")
    for k,v in z["results"].items():
        lines.extend([f"## {k} — eval y funded separados",
                      f"- Eval replay: {v['replay_mffu_fee_router']['evaluation']}",
                      f"- Eval con piso hipotético lock+$100: {v['replay_mffu_fee_router']['evaluation_floor_lock_sensitivity']}",
                      f"- Funded solo si eval pasó antes de terminar DEV: {v['replay_mffu_fee_router']['post_eval_funded_fresh_zero']}",
                      ""])
    lines.extend([
      "Las excursiones Last son un **límite superior conservador** al tomar los",
      "grupos de timestamps completos y el peor orden interno; crossing de $2.000",
      "puede ser un falso positivo del envelope. NO reportar un breach de broker.",
      "La evaluación de noticias Tier1 e inactividad de cuenta REAL siguen pendientes.",
      "La fase posterior a evaluación usa la misma DEV del estudio, NO OOS.",
      "La regla propia stop diario cerrado−$600 permanece aunque Rapid EOD carezca de DLL.",
      "**No abrir OOS, no comprar cuenta y no retocar señales para pasar el reto.**",
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
        if a.root is None:raise ValueError("ROOT_REQUIRED")
        z=month_stage(a.root,a.month,new_registry(),old_registry())
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,separators=(",",":"),sort_keys=True)+"\n")
        print("MFFU_TOP2_MONTH_PRIVATE_QC="+json.dumps({
            "month":a.month,"source":z["source"],"ready":z["ready"]},sort_keys=True))
    else:
        if a.inputs is None or a.report is None:raise ValueError("SEVEN_MONTH_INPUTS_REQUIRED")
        months={m:json.loads((a.inputs/f"mffu_top2_{m}.json").read_text())
                for m in MONTHS}
        result=aggregate(months)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        a.report.write_text(report(result))
        print("MFFU_TOP2_SAFE_FINAL="+json.dumps({
            "source":result["source_sessions"],"eligible":result["eligible_sessions"],
            "by_portfolio":{name:{
                "fixed":v["fixed_original_decision_path"],
                "rerouted":v["mffu_fee_aware_daily_stop_rerouter"],
                "eval":v["replay_mffu_fee_router"]["evaluation"],
                "funded":v["replay_mffu_fee_router"]["post_eval_funded_fresh_zero"]}
                for name,v in result["results"].items()}},sort_keys=True))
