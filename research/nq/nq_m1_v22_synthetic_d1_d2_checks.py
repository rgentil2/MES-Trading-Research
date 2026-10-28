#!/usr/bin/env python3
"""NQ M1 V2.2 D1/D2 PRIMITIVES, synthetic-only under hard IST provenance.

This is NOT an adapted/cohort-parity-certified G0/D0/D1/D2 implementation.
No market files, no portfolio results, no candidate selection.
Input trades MUST be model net pnl including baseline cost. All dates IST.
Exploratory review flags: PF >=1.25, initial closed DD <=2000,
original >=150 trades over 2020-2024 (60 months) scales to an indicative
90-trade 2020-22 IST (36 months) adequacy check; >=5 trades/month is a
separate aspirational frequency diagnostic, NOT a hard generator constraint.
Those exploratory thresholds are not official MFFU rules or strategy passes.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from math import isfinite
import random
import statistics

YEARS=(2020,2021,2022)
MONTHS=36
REFERENCE_TICK_USD=5.
REFERENCE_RT_FEES_USD=4.68
SLIPPAGE_TICKS_EACH_SIDE=2
BASELINE_COST_USD=REFERENCE_RT_FEES_USD+2*SLIPPAGE_TICKS_EACH_SIDE*REFERENCE_TICK_USD
MAX_DD_USD=2000.
MIN_PF=1.25
MIN_TRADES_2020_2024=150
MIN_TRADES=int(MIN_TRADES_2020_2024*36/60)  # 90 for IST; diagnostic only
MIN_TRADES_PER_MONTH=5.
STATUS="V22_SYNTHETIC_GAUGE_NOT_FORMAL_G0_D0_D1_D2"


def _validated(trades:list[dict])->list[dict]:
    previous=None
    out=[]
    for t in trades:
        if not isinstance(t,dict) or not all(k in t for k in ("date","net_usd","contract")):
            raise ValueError("Expected date/net_usd/contract")
        if t["contract"]!="NQ":
            raise PermissionError("Only 1 NQ contract modeled")
        try:
            d=date.fromisoformat(t["date"])
        except (TypeError,ValueError):
            raise ValueError("Bad ISO date") from None
        if d.year not in YEARS:
            raise PermissionError("IST 2020-22 only; ISV/holdouts unavailable")
        if previous and d<previous:
            raise ValueError("Records must be sorted by date, stable intraday order")
        previous=d
        val=float(t["net_usd"])
        if not isfinite(val):
            raise ValueError("Finite pre-cost-adjusted net trades required")
        out.append({"date":t["date"],"net_usd":val,"contract":"NQ"})
    return out


def trade_metrics(trades:list[dict])->dict:
    r=_validated(trades)
    pnl=[x["net_usd"] for x in r]
    count=len(pnl)
    gross_positive=sum(x for x in pnl if x>0)
    gross_negative=-sum(x for x in pnl if x<0)
    pf=(gross_positive/gross_negative if gross_negative>0 else None)
    equity=peak=dd=0.
    for x in pnl:
        equity+=x
        peak=max(peak,equity)
        dd=max(dd,peak-equity)
    years=Counter()
    months=Counter()
    for t in r:
        years[t["date"][:4]]+=1
        months[t["date"][:7]]+=1
    return {
        "label":STATUS,
        "trades":count, "net_usd":round(sum(pnl),2),
        "profit_factor":pf,
        "max_closed_trade_dd_usd":round(dd,2),
        "expectancy_usd":(sum(pnl)/count if count else None),
        "mean_trades_month_all_36":count/MONTHS,
        "months_with_at_least_5_trades":sum(v>=5 for v in months.values()),
        "months_observed":MONTHS,
        "trades_by_year":dict(sorted(years.items())),
        "legacy_cohort_g0_d2_parity_certified":False,
        "funded_intraday_loss_certified":False,
        "holdouts":"SEALED"
    }


def sample_screen(trades:list[dict])->dict:
    """Objective screening mechanics only; never a formal D1 decision."""
    m=trade_metrics(trades)
    reasons=[]
    if m["trades"]<MIN_TRADES:
        reasons.append("LOW_SAMPLE")
    if m["net_usd"]<=0:
        reasons.append("NONPOSITIVE_NET")
    if m["profit_factor"] is None or m["profit_factor"]<MIN_PF:
        reasons.append("LOW_OR_UNDEFINED_PROFIT_FACTOR")
    if m["max_closed_trade_dd_usd"]>MAX_DD_USD:
        reasons.append("CLOSED_DD_EXCEEDS_2000")
    if m["mean_trades_month_all_36"]<MIN_TRADES_PER_MONTH:
        reasons.append("LOW_FREQUENCY_ALL_MONTHS")
    return {"preliminary_screen":"NO_CANDIDATE_EVALUATION",
            "synthetic_rule_consistency":not reasons,"reasons":reasons,
            "metrics":m}


def cost_stress(trades:list[dict],multiplier:float=1.5,
                extra_rt_usd:float=0.)->dict:
    rows=_validated(trades)
    if not isfinite(multiplier) or multiplier<1.0 or not isfinite(extra_rt_usd) or extra_rt_usd<0:
        raise ValueError("Invalid cost stress")
    add=BASELINE_COST_USD*(multiplier-1.)+extra_rt_usd
    net=[t["net_usd"]-add for t in rows]
    return {"label":STATUS,"n":len(net),
            "baseline_round_trip_cost_usd":BASELINE_COST_USD,
            "multiplier":multiplier,"extra_rt_usd":extra_rt_usd,
            "added_cost_per_trade_usd":round(add,2),
            "net_stressed_usd":round(sum(net),2),
            "not_formal_d2":True}


def _max_dd(series:list[float])->float:
    eq=peak=mx=0.
    for x in series:
        eq+=x
        peak=max(peak,eq)
        mx=max(mx,peak-eq)
    return mx


def block_bootstrap(trades:list[dict],seed:int=20261027,
                    reps:int=200,block_size:int=5)->dict:
    rows=_validated(trades)
    if len(rows)<block_size or not 50<=reps<=2000 or not 2<=block_size<=20:
        raise ValueError("Uninformative/bootstrap parameters invalid")
    rng=random.Random(seed)
    pnl=[t["net_usd"] for t in rows]
    profits,drawdowns=[],[]
    n=len(pnl)
    for _ in range(reps):
        # Moving-block bootstrap of contiguous trade PnL, replacement at
        # the BLOCK level, preserving local serial dependence within blocks.
        sample=[]
        while len(sample)<n:
            start=rng.randrange(n-block_size+1)
            sample.extend(pnl[start:start+block_size])
        sample=sample[:n]
        profits.append(sum(sample))
        drawdowns.append(_max_dd(sample))
    profits.sort()
    drawdowns.sort()
    low=max(0,int(.05*(reps-1)))
    high=min(reps-1,int(.95*(reps-1)))
    return {"label":STATUS,"n":n,"reps":reps,
            "block_size":block_size,"seed":seed,
            "bootstrap_net_p05":round(profits[low],2),
            "bootstrap_dd_p95":round(drawdowns[high],2),
            "method":"MOVING_BLOCK_TRADE_PNL_WITH_REPLACEMENT",
            "not_formal_d2":True,"holdouts":"SEALED"}
