#!/usr/bin/env python3
"""NQ S0.31 — FIRST REAL IST 2020–22 EXPLORATORY market search, NOT 10K certification.

The 120-rule legacy control catalog is explicitly separate from the frozen
10,000 AST cohort and the 13-gate production candidate ranking. The user has
requested beginning research; this pilot only generates provisional research
metrics on the already-inspected IST 2020-22 M1 archive. Never represent it as
successful economic quality-gate release, finalist selection, ISV or MFFU proof.

No market data is opened until (1) the scope and 13-gate state are verified,
(2) ZIP SHA256 matches original frozen source, (3) archive member whitelist
agrees with prior technical audit. Unopened 2023–26 stay reserved or sealed.

Signals: pre-registered chrono catalogue, 09:35–11:27 decision end labels,
next bar 09:36–11:28 open (market), flat 11:29. Real NQ M1 OHLC proxies,
stop-first if ambiguous, conservative 1-tick TP limit trade-through and
adverse stop/time slippage. DOES NOT reconstruct intrabar path or fills.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import math
import numpy as np
from research.nq.nq_m1_chrono_discovery import (
    read_config,catalog,manifest_sha,signal,stop_distance,load_years
)
from research.nq.nq_m1_v29_ohlc_conservative_protocol import (
    Bar,entry as conservative_entry,exit_bar,POINT_USD,TICK,
    COMMISSION_RT_USD,DEFAULT_SLIP_TICKS_SIDE
)
from research.nq.nq_m1_v32_real_ist_source_readonly_qa import (
    _gate,EXPECTED_SHA256,EXPECTED,sha_file,_validate_source
)
from research.nq.nq_m1_v23_source_contract_qa import inspect_archive_manifest
from research.nq.nq_m1_v22_contract_provenance import metadata_for_sessions

STATUS="S0_31_IST_2020_2022_REAL_120_EXPLORATORY_CONTROL_NOT_10K_NOT_RELEASED"
FIRST_SIGNAL=4
LAST_SIGNAL=116
FLAT_INDEX=118
MAX_ORDERS=2
STOP_RISK_CAP_USD=300.0
DAILY_CLOSED_PAUSE_USD=-600.0
MAX_SUGGESTED=120

def guard():
    q=_gate()
    if (q["checks_total"]!=13 or q["passed_verified"]!=0 or
        q["decision"]!="EXECUTION_BLOCKED" or q["ready_for_economic_execution"]):
        raise PermissionError("This is exploratory only; 13-gate state was changed")
    cfg=read_config()
    e=cfg["execution"]
    if (len(catalog(cfg))!=120 or
        cfg["all_positions_flat_et"]!="11:29" or
        e["contract"]!="NQ" or e["contract_count"]!=1 or
        e["point_value_usd"]!=20 or e["tick_size"]!=TICK or
        e["round_trip_commission_usd"]!=COMMISSION_RT_USD or
        e["slippage_ticks_each_side"]!=DEFAULT_SLIP_TICKS_SIDE or
        e["max_open_positions"]!=1 or
        e["max_filled_entries_per_day"]!=MAX_ORDERS or
        e["closed_pnl_daily_pause_usd"]!=DAILY_CLOSED_PAUSE_USD or
        e["max_initial_stop_risk_usd"]!=STOP_RISK_CAP_USD):
        raise RuntimeError("Reference research catalog/cost assumptions changed")
    return cfg,q

def choose_rules(cfg,n:int=120):
    if type(n) is not int or not 1<=n<=120:raise ValueError("Max candidates 1..120")
    rows=catalog(cfg)
    # An evenly spaced subcohort for smoke tests (if n<120) cannot be called
    # a complete run. The full 120 uses original preregistered ordering.
    if n==120:return rows
    indexes=[math.floor(k*120/n) for k in range(n)]
    return [rows[i] for i in indexes]

def _bar(b):
    return Bar(*map(float,b[:4]))

def _model_trade(g:np.ndarray,index:int,side:int,rule:dict,cfg:dict):
    if not FIRST_SIGNAL<=index<=LAST_SIGNAL or side not in (-1,1):
        raise ValueError("Out of scope model entry")
    # A signal uses g[:index+1] only, and the next-minute market open is a
    # separately observed future fill proxy, never input to the signal.
    ref=conservative_entry(_bar(g[index+1]),side,"MARKET")
    px=ref["fill_price"]
    risk=stop_distance(g[:index+1],index,side,px,rule)
    # Risk amount includes adverse protective slippage and round-trip fee.
    modeled_stop_risk=risk*POINT_USD+DEFAULT_SLIP_TICKS_SIDE*TICK*POINT_USD+COMMISSION_RT_USD
    if modeled_stop_risk>STOP_RISK_CAP_USD:
        return None,"PROVISIONAL_MODEL_RISK_UNEXECUTABLE"
    stop=px-side*risk
    if stop<=0 or abs(stop/TICK-round(stop/TICK))>1e-7:
        raise ValueError("Stop outside price tick grid")
    target=(None if rule["target_r"] is None else px+side*risk*float(rule["target_r"]))
    if target is not None and (target<=0 or abs(target/TICK-round(target/TICK))>1e-7):
        raise ValueError("Target outside price tick grid")
    for j in range(index+1,FLAT_INDEX+1):
        b=_bar(g[j])
        stop_hit=b.low<=stop if side==1 else b.high>=stop
        target_touched=(target is not None and
                        (b.high>=target if side==1 else b.low<=target))
        target_marketable=(target is not None and
                           (b.open>=target if side==1 else b.open<=target))
        target_through=(target is not None and
                        (b.high>=target+TICK if side==1 else b.low<=target-TICK))
        # When a bar hits BOTH barriers we must still give precedence to SL.
        # Otherwise, for TP as limit, reject exact touch queue assumptions.
        tp_candidate=(target if (stop_hit or target_marketable or target_through)
                      else None)
        event=exit_bar(b,side,stop,tp_candidate,
                       pending_entry_same_bar=False,
                       forced_time_exit=(j==FLAT_INDEX))
        if event["exited_proxy"]:
            exit_px=event["exit_price"]
            net=round(side*(exit_px-px)*POINT_USD-COMMISSION_RT_USD,2)
            return {
                "signal_idx":index,"entry_idx":index+1,
                "exit_idx":j,"side":side,
                "entry_price":round(px,5),"exit_price":round(exit_px,5),
                "reason":event["reason"],
                "ambiguous_stop_first":bool(event["ambiguous_bar"]),
                "target_exact_touch_unconfirmed":bool(target_touched and not (
                    stop_hit or target_marketable or target_through)),
                "model_initial_risk_usd":round(modeled_stop_risk,2),
                "model_net_usd":net
            },None
    raise RuntimeError("Forced flat missing at 11:29")

def run_day(g:np.ndarray,rule:dict,cfg:dict):
    if g.shape!=(390,5) or not np.isfinite(g).all():
        raise ValueError("Require full valid NQ 390 M1 RTH session")
    # Previous data not needed: rules are one-session completed-bar only.
    results=[]
    counts=Counter()
    closed=0.
    index=max(FIRST_SIGNAL,rule["lookback"],20)
    while index<=LAST_SIGNAL and len(results)<MAX_ORDERS:
        if closed<=DAILY_CLOSED_PAUSE_USD:
            counts["closed_daily_pause"]+=1
            break
        side=signal(g[:index+1],index,rule)
        if side==0:
            index+=1;continue
        counts["signals"]+=1
        trade,reason=_model_trade(g,index,side,rule,cfg)
        if reason:
            counts[reason]+=1
            index+=1
            continue
        results.append(trade)
        closed+=trade["model_net_usd"]
        index=trade["exit_idx"]+1
    return results,counts

def stats_by_rule(trades,dates,rule,counts):
    nets=[x["model_net_usd"] for x in trades]
    gross_profit=sum(z for z in nets if z>0)
    gross_loss=-sum(z for z in nets if z<0)
    balance=peak=dd=0.
    for amount in nets:
        balance+=amount
        peak=max(peak,balance)
        dd=max(dd,peak-balance)
    years=sorted(set(d[:4] for d in dates))
    annual={y:round(sum(t["model_net_usd"] for t in trades
                        if t["session"].startswith(y)),2) for y in years}
    months=sorted(set(d[:7] for d in dates))
    trades_per_month=Counter(t["session"][:7] for t in trades)
    # Avoid divide-by-zero and infinite PF falsely reading as "excellent".
    pf=(round(gross_profit/gross_loss,5) if gross_loss>0 else None)
    no_trade_gap=longest=0
    for m in months:
        if trades_per_month[m]==0:
            no_trade_gap+=1;longest=max(longest,no_trade_gap)
        else:no_trade_gap=0
    return {**rule,"signals":counts["signals"],
            "model_risk_rejections":counts.get("PROVISIONAL_MODEL_RISK_UNEXECUTABLE",0),
            "closed_daily_pauses":counts.get("closed_daily_pause",0),
            "trades":len(nets),"net_usd":round(sum(nets),2),
            "gross_profit_usd":round(gross_profit,2),
            "gross_loss_usd":round(gross_loss,2),"pf":pf,
            "closed_trade_max_dd_usd":round(dd,2),
            "net_per_trade_usd":round(sum(nets)/len(nets),2) if nets else None,
            "months_with_trades":sum(trades_per_month[m]>0 for m in months),
            "months_in_IST":len(months),
            "months_with_5plus":sum(trades_per_month[m]>=5 for m in months),
            "longest_consecutive_calendar_months_without_trade":longest,
            "positive_years":sum(z>0 for z in annual.values()),
            "annual_pnl_usd":annual,
            "ambiguous_stop_first_count":sum(t["ambiguous_stop_first"] for t in trades),
            "unconfirmed_tp_exact_touch_count":sum(
                t["target_exact_touch_unconfirmed"] for t in trades)}

def run_exploratory(dates,bars,source,max_candidates=120):
    cfg,q=guard()
    _validate_source(dates,bars,source,expected_counts=False)
    n=len(dates)
    if n>735:raise ValueError("Unexpected extra sessions")
    rules=choose_rules(cfg,max_candidates)
    rows=[]
    totals=Counter()
    for rule in rules:
        trades=[];counts=Counter()
        for date,g in zip(dates,bars):
            today,c=run_day(g,rule,cfg)
            trades.extend({"session":date,**t} for t in today)
            counts.update(c)
        rows.append(stats_by_rule(trades,dates,rule,counts))
        totals["model_trades_across_alternative_rules"]+=len(trades)
        totals["signals_across_alternative_rules"]+=counts["signals"]
    # Sort for convenience only; do not freeze winners or export per-trade
    # ledger outside the private market research runner.
    rows.sort(key=lambda x:(-x["net_usd"],x["id"]))
    return {"schema":"NQ_S031_REAL_IST_120_LEGACY_CONTROL_EXPLORATORY_V1",
            "status":STATUS,
            "purpose":"INITIAL_SEARCH_SANITY_CHECK_NOT_10K_AST_SCREEN",
            "source_zip_sha256":EXPECTED_SHA256,
            "days":n,"years_opened":[2020,2021,2022],
            "partial_sessions_excluded":source["partial_sessions_excluded"],
            "catalog_count":120,"rules_exploratory_evaluated":len(rules),
            "catalog_sha256":manifest_sha(catalog(cfg)),
            "signal_minute_end_et":"09:35",
            "last_signal_minute_end_et":"11:27",
            "last_entry_minute_end_et":"11:28",
            "forced_flat_minute_end_et":"11:29",
            "slippage_ticks_per_market_side":DEFAULT_SLIP_TICKS_SIDE,
            "commission_roundtrip_usd":COMMISSION_RT_USD,
            "reference_initial_stop_risk_cap_usd":STOP_RISK_CAP_USD,
            "shared_account_portfolio_simulated":False,
            "funded_plan_exact_rules_verified":False,
            "intrabar_execution_or_slippage_verified":False,
            "original_10000_132_ast_evaluated":0,
            "source_IST_2020_2022_only":True,
            "isv1_2023_opened":False,"isv2_2024_opened":False,
            "2025_2026_opened":False,
            "frozen_cohort_changed":False,
            "first_control_search_ran":True,
            "formal_G0_D0_D1_D2_approved":False,
            "economic_13_quality_gates_passed_verified":0,
            "top_ranked_only_exploratory_no_winners":True,
            "sum_across_alternatives_not_a_real_portfolio":True,
            "aggregate_counts":dict(totals),"rules":rows}

def audit_real_archive(path:Path,max_candidates:int=120):
    cfg,q=guard()
    if sha_file(path)!=EXPECTED_SHA256:
        raise PermissionError("Real IST archive SHA changed BEFORE reading any member")
    manifest=inspect_archive_manifest(path)
    if (manifest["source_members"]!=15 or
        manifest["allowed_years"]!=[2020,2021,2022] or
        manifest["market_member_contents_opened"]):
        raise ValueError("Source member whitelist changed")
    dates,bars,source=load_years(path,(2020,2021,2022))
    _validate_source(dates,bars,source,expected_counts=True)
    report=run_exploratory(dates,bars,source,max_candidates)
    if report["days"]!=EXPECTED["sessions"]:
        raise RuntimeError("IST complete-session count changed")
    return report

def main():
    p=argparse.ArgumentParser(description="Exploratory 120 NQ M1 control rules, IST only")
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--max-candidates",type=int,default=120)
    a=p.parse_args()
    r=audit_real_archive(a.zip,a.max_candidates)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({k:r[k] for k in ("status","days",
           "rules_exploratory_evaluated","aggregate_counts",
           "original_10000_132_ast_evaluated","economic_13_quality_gates_passed_verified")},sort_keys=True))

if __name__=="__main__":main()
