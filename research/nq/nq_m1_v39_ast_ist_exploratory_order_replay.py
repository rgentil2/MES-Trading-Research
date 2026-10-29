#!/usr/bin/env python3
"""S0.34: preliminary complete-order M1 replay of 12 frozen AST on 3 IST days.

This is a BOUNDED EXPLORATORY MODEL, not the certified 10K economic pipeline.
It reuses the reviewed S0.26 synthetic reference's PURE order mechanics, but
never calls simulate_synthetic_day (which remains fixture-only). It must NOT
be used as evidence of exchange queue fills, officially sanctioned G0/D0/D1,
actual MFFU intraday trailing drawdown, or a winning strategy.

The archive entry is restricted to SHA-pinned IST NQ Minute_Last 2020–2022.
The 3 sessions and 12 AST indices were selected BEFORE viewing PnL.
2023–26 remain unread. Only diagnostic counts and short per-strategy sample
metrics leave the private runner, with all results flagged INSUFFICIENT_SAMPLE.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from research.nq.nq_m1_v38_10k_real_ist_signal_smoke import frozen_sample
from research.nq.nq_m1_v30_132_signal_m1_bridge import (
    signals_at,_validate_candidate,_session_guard
)
from research.nq.nq_m1_v31_full_synthetic_lifecycle import (
    FIRST_SIGNAL,LAST_ENTRY_SIGNAL,CLOSE_IDX,ACCOUNT_INTERNAL,
    _history,_stop_distance,_target_distance,_protective_replay,
)
from research.nq.nq_m1_v29_ohlc_conservative_protocol import (
    Bar,entry as m1_entry,TICK,POINT_USD,COMMISSION_RT_USD,
    DEFAULT_SLIP_TICKS_SIDE
)
from research.nq.nq_m1_v32_real_ist_source_readonly_qa import (
    _gate,_validate_source,sha_file,EXPECTED_SHA256,EXPECTED,ALLOWED_YEARS
)
from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v23_source_contract_qa import inspect_archive_manifest
from research.nq.nq_m1_v22_contract_provenance import prior_same_contract

STATUS="S0_34_EXPLORATORY_FROZEN_AST_M1_ORDER_REPLAY_THREE_IST_DAYS_NOT_CERTIFIED"
FIXED_SESSION_SELECTION=("FIRST","MIDDLE","LAST")
MAX_STRATEGIES=12

def session_indices(n):
    if not isinstance(n,int) or n<3:raise ValueError("Need at least 3 sessions")
    return [0,n//2,n-1]

def replay_one_day(bars,day,strategy,session_context=None):
    """Caller-provided bars are ONLY test fixtures; real callers use ZIP SHA entry."""
    _gate()
    _session_guard(day)
    _validate_candidate(strategy)
    if (not isinstance(bars,np.ndarray) or bars.shape!=(390,5)
        or not np.isfinite(bars).all()):
        raise ValueError("Only 390 valid OHLCV M1 bars")
    # Require tick grid and OHLC consistency even in single-day synthetic tests.
    if ((bars[:,:4]<=0).any() or (bars[:,4]<0).any()
        or (bars[:,1]<np.maximum(bars[:,0],bars[:,3])).any()
        or (bars[:,2]>np.minimum(bars[:,0],bars[:,3])).any()
        or (np.abs(bars[:,:4]/TICK-np.round(bars[:,:4]/TICK))>1e-7).any()):
        raise ValueError("Non-conforming NQ M1 bar")
    prior=_history(day,session_context)
    spec=strategy["entry_order"]
    exits=strategy["exit"]
    trades=[];count=Counter();closed=0.;index=FIRST_SIGNAL
    while index<=LAST_ENTRY_SIGNAL and len(trades)<ACCOUNT_INTERNAL["max_entries_per_day"]:
        if closed<=ACCOUNT_INTERNAL["closed_daily_pause_usd"]:
            count["DAILY_PNL_CLOSED_PAUSE"]+=1;break
        decision=signals_at(bars,index,strategy,day,session_context)
        act=decision["action"];count[act]+=1
        count["UNAVAILABLE_LEAF_VALUES"]+=decision["unavailable_indicator_leaf_evaluations"]
        if act not in ("LONG","SHORT"):
            index+=1;continue
        side=1 if act=="LONG" else -1
        kind=spec["kind"]
        offset=int(spec["offset_ticks"])
        level=(None if kind=="MARKET" else
               float(bars[index,3])+side*TICK*offset if kind=="STOP"
               else float(bars[index,3])-side*TICK*offset)
        # ALL protective decisions below use ONLY the completed signal bar.
        # For MARKET the next open cannot be known; the signal-close plus
        # adverse entry slippage is a transparent provisional reference.
        # STOP/LIMIT quote the previously submitted exact requested price.
        # This avoids using next-bar fill price to "cancel" orders post-fill.
        quote=(float(bars[index,3])+side*DEFAULT_SLIP_TICKS_SIDE*TICK
               if kind=="MARKET" else level)
        anticipated_risk=_stop_distance(bars,index,side,quote,exits,prior)
        if anticipated_risk is None:
            count["PRE_ORDER_NO_PROTECTION"]+=1;index+=1;continue
        anticipated_cap=(anticipated_risk*POINT_USD+
                         DEFAULT_SLIP_TICKS_SIDE*TICK*POINT_USD+
                         COMMISSION_RT_USD)
        if anticipated_cap>ACCOUNT_INTERNAL["max_initial_risk_usd"]:
            count["PRE_ORDER_RISK_CAP"]+=1;index+=1;continue
        anticipated_target,anticipated_reason=_target_distance(
            bars,index,side,quote,anticipated_risk,exits,prior)
        if anticipated_reason not in ("VALID","NO_TARGET"):
            count["PRE_ORDER_TARGET_"+anticipated_reason]+=1
            index+=1;continue
        expiry=min(CLOSE_IDX-1,
                   index+(1 if kind=="MARKET" else int(spec["expiry_bars"])))
        fill_idx=None;price=None;fill_reason=None
        for j in range(index+1,expiry+1):
            bar=Bar(*map(float,bars[j,:4]))
            fill=m1_entry(bar,side,kind,level)
            if fill["filled_proxy"]:
                fill_idx=j;price=fill["fill_price"];fill_reason=fill["reason"]
                break
        if fill_idx is None:
            count["PENDING_EXPIRED"]+=1;index=expiry+1;continue
        risk=_stop_distance(bars,index,side,price,exits,prior)
        if risk is None:
            # A real pre-submitted order could not reject a fill after it
            # happened: report this as unmodelled exposure, never zero-risk.
            count["POST_FILL_PROTECTION_UNMODELLED"]+=1
            index=fill_idx+1;continue
        initial=risk*POINT_USD+DEFAULT_SLIP_TICKS_SIDE*TICK*POINT_USD+COMMISSION_RT_USD
        if initial>ACCOUNT_INTERNAL["max_initial_risk_usd"]:
            count["POST_FILL_RISK_CAP_UNMODELLED"]+=1
            index=fill_idx+1;continue
        target,reason=_target_distance(bars,index,side,price,risk,exits,prior)
        if reason not in ("VALID","NO_TARGET"):
            count["POST_FILL_TARGET_UNMODELLED_"+reason]+=1
            index=fill_idx+1;continue
        action=_protective_replay(bars,index,fill_idx,kind,side,price,
                                  risk,target,exits,prior)
        # Pure reference returns a key named synthetic_net_usd. This module
        # reports the same quantity as exploratory MODEL ONLY, never broker.
        result={
            "session":day,"candidate_id":strategy["id"],"side":side,
            "entry_idx":fill_idx,"signal_idx":index,
            "exit_idx":action["exit_idx"],
            "entry_kind":kind,"entry_reason":fill_reason,
            "entry_price":round(price,5),
            "exit_price":action["exit_price"],
            "exit_reason":action["exit_reason"],
            "initial_model_risk_usd":round(initial,2),
            "ambiguous_bars":action["ambiguous_bars"],
            "exploratory_net_usd":action["synthetic_net_usd"]
        }
        if not (FIRST_SIGNAL<result["entry_idx"]<=CLOSE_IDX-1
                and result["exit_idx"]<=CLOSE_IDX
                and result["signal_idx"]<result["entry_idx"]
                and result["exit_idx"]>=result["entry_idx"]):
            raise RuntimeError("Historical replay exceeded frozen intraday clock")
        trades.append(result)
        closed+=result["exploratory_net_usd"]
        index=result["exit_idx"]+1
    return {"trades":trades,"counts":dict(count),
            "net_usd":round(closed,2)}

def evaluate_fixed_sample(dates,bars,source,strategies,chosen=None):
    """No claims about 735-session fitness; three precommitted days only."""
    _gate()
    _validate_source(dates,bars,source,expected_counts=False)
    if (not isinstance(strategies,list) or not 1<=len(strategies)<=MAX_STRATEGIES
        or len({s["id"] for s in strategies})!=len(strategies)):
        raise ValueError("Require <=12 unique AST")
    indices=session_indices(len(dates)) if chosen is None else list(chosen)
    if len(indices)!=3 or indices!=sorted(set(indices)) or any(
        type(i) is not int or not 0<=i<len(dates) for i in indices):
        raise ValueError("Require 3 distinct ordered sessions")
    summary=[];total=Counter()
    for s in strategies:
        records=[];local=Counter()
        for ix in indices:
            ctx=prior_same_contract(dates,bars,ix)
            run=replay_one_day(bars[ix],dates[ix],s,ctx)
            records.extend(run["trades"]);local.update(run["counts"])
        nets=[r["exploratory_net_usd"] for r in records]
        gp=sum(max(0,x) for x in nets)
        gl=-sum(min(0,x) for x in nets)
        balance=peak=dd=0.
        for pnl in nets:
            balance+=pnl;peak=max(peak,balance);dd=max(dd,peak-balance)
        summary.append({
            "candidate_id":s["id"],"sampled_days":len(indices),
            "model_trades":len(records),"model_net_usd":round(sum(nets),2),
            "gross_profit_usd":round(gp,2),"gross_loss_usd":round(gl,2),
            "model_pf":round(gp/gl,5) if gl>0 else None,
            "closed_trade_dd_usd":round(dd,2),
            "post_fill_unmodelled":sum(v for k,v in local.items()
                                      if k.startswith("POST_FILL_")),
            "pre_order_rejected":sum(v for k,v in local.items()
                                      if k.startswith("PRE_ORDER_")),
            "economic_metrics_incomplete_if_postfill":any(
                v for k,v in local.items() if k.startswith("POST_FILL_")),
            "signal_unavailable":local["UNAVAILABLE_SOME_SIGNAL_DATA"],
            "ambiguous_sl_first_bars":sum(r["ambiguous_bars"] for r in records),
            "research_only_insufficient_three_day_sample":True
        })
        total["trades_across_alternative_AST_not_portfolio"]+=len(records)
        total["post_fill_unmodelled"]+=summary[-1]["post_fill_unmodelled"]
        total["pre_order_rejected"]+=sum(
            v for k,v in local.items() if k.startswith("PRE_ORDER_"))
        total["signal_unavailable"]+=summary[-1]["signal_unavailable"]
    return {
        "schema":"NQ_S034_FROZEN_10K_AST_FIRST_COMPLETE_MODEL_TRADES_PILOT_V1",
        "status":STATUS,"sessions_loaded":len(dates),
        "sessions_sampled":len(indices),"sample_selection":FIXED_SESSION_SELECTION,
        "candidate_count_exploratory":len(strategies),
        "source_years_opened":list(ALLOWED_YEARS),
        "cost_rt_usd":COMMISSION_RT_USD,
        "slippage_ticks_side":DEFAULT_SLIP_TICKS_SIDE,
        "account_loss_limits_only_provisional":True,
        "pre_order_stop_target_risk_checks_causal":True,
        "gap_risk_after_fill_remains_unbounded_on_M1":True,
        "portfolio_jointly_simulated":False,
        "sample_sufficient_for_strategy_selection":False,
        "formal_G0_D0_D1_D2_approved":False,
        "formal_13_gates_verified":0,"all_10k_backtested":False,
        "holdouts_2023_2024_2025_2026_opened":False,
        "ninjatrader_portfolio_parity_done":False,
        "counts":dict(total),"candidates":summary}

def real_archive_pilot(path):
    _gate()
    if sha_file(path)!=EXPECTED_SHA256:
        raise PermissionError("Original ZIP SHA failed BEFORE member read")
    manifest=inspect_archive_manifest(path)
    if (manifest["source_members"]!=15
        or manifest["allowed_years"]!=list(ALLOWED_YEARS)
        or manifest["market_member_contents_opened"]):
        raise PermissionError("Unrecognized source member whitelist")
    dates,bars,source=load_years(path,ALLOWED_YEARS)
    _validate_source(dates,bars,source,expected_counts=True)
    result=evaluate_fixed_sample(dates,bars,source,frozen_sample())
    if (result["sessions_loaded"]!=735 or
        result["sessions_sampled"]!=3 or result["candidate_count_exploratory"]!=12):
        raise RuntimeError("Frozen smoke-test coverage changed")
    result["source_zip_sha256"]=EXPECTED_SHA256
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    r=real_archive_pilot(args.zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:r[k] for k in
        ("status","sessions_sampled","candidate_count_exploratory","counts",
         "formal_13_gates_verified","all_10k_backtested")},sort_keys=True))

if __name__=="__main__":
    main()
