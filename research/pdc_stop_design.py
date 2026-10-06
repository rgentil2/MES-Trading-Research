#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, add_periods
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.mes_pdc_small_gap_reconstruction import daily_context, build_events

OUT=ROOT/"results/pdc_stop_design"
POINT_VALUE=5.0
BASE_COST=4.38
STRESS_COST=6.57
CUTOFF_MINUTE=11*60+30

CANDIDATES=[
    ("NO_STOP","NONE",np.nan),
    ("ATR_015","ATR",0.15),
    ("ATR_020","ATR",0.20),
    ("ATR_025","ATR",0.25),
    ("ATR_030","ATR",0.30),
    ("ATR_035","ATR",0.35),
    ("D_100","D",1.0),
    ("D_150","D",1.5),
    ("D_200","D",2.0),
    ("D_250","D",2.5),
    ("D_300","D",3.0),
]

def dd_magnitude(pnl: pd.Series) -> float:
    if len(pnl)==0:
        return np.nan
    eq=pnl.cumsum()
    peak=eq.cummax().clip(lower=0)
    dd=eq-peak
    return float(-dd.min())

def simulate_one(base_row, g, family, mult):
    direction=int(base_row.direction)
    entry=float(base_row.entry_price)
    pdc=float(base_row.pdc)
    atr=float(base_row.atr14_prev)
    D=abs(entry-pdc)

    if family=="NONE":
        stop=None
    elif family=="ATR":
        dist=float(mult)*atr
        stop=entry-direction*dist
    elif family=="D":
        dist=float(mult)*D
        stop=entry-direction*dist
    else:
        raise ValueError(family)

    # Identify entry bar by exact timestamp.
    et=pd.Timestamp(base_row.entry_ts)
    idxs=g.index[g.timestamp_et==et].tolist()
    if not idxs:
        raise ValueError(f"entry bar missing {base_row.group_key} {et}")
    start=int(idxs[0])

    exit_px=None
    exit_reason=None
    exit_ts=None
    for i in range(start,len(g)):
        b=g.iloc[i]
        if int(b.minute)>CUTOFF_MINUTE:
            break

        if direction==1:
            target_touch=float(b.high)>=pdc
            stop_touch=(stop is not None and float(b.low)<=stop)
            if target_touch and stop_touch:
                px=min(float(b.open),stop) if float(b.open)<stop else stop
                exit_px=float(px); exit_reason="STOP_AMBIGUOUS_FIRST"; exit_ts=b.timestamp_et; break
            if stop_touch:
                px=min(float(b.open),stop) if float(b.open)<stop else stop
                exit_px=float(px); exit_reason="STOP"; exit_ts=b.timestamp_et; break
            if target_touch:
                exit_px=pdc; exit_reason="PDC"; exit_ts=b.timestamp_et; break
        else:
            target_touch=float(b.low)<=pdc
            stop_touch=(stop is not None and float(b.high)>=stop)
            if target_touch and stop_touch:
                px=max(float(b.open),stop) if float(b.open)>stop else stop
                exit_px=float(px); exit_reason="STOP_AMBIGUOUS_FIRST"; exit_ts=b.timestamp_et; break
            if stop_touch:
                px=max(float(b.open),stop) if float(b.open)>stop else stop
                exit_px=float(px); exit_reason="STOP"; exit_ts=b.timestamp_et; break
            if target_touch:
                exit_px=pdc; exit_reason="PDC"; exit_ts=b.timestamp_et; break

    if exit_px is None:
        elig=g[(g.index>=start)&(g.minute<=CUTOFF_MINUTE)]
        if elig.empty:
            return None
        b=elig.iloc[-1]
        exit_px=float(b.close); exit_reason="TIME_1130"; exit_ts=b.timestamp_et

    gross_points=direction*(exit_px-entry)
    return {
        "candidate":base_row.candidate if hasattr(base_row,"candidate") else None,
        "family":family,
        "multiplier":None if family=="NONE" else float(mult),
        "group_key":base_row.group_key,
        "session_date":base_row.session_date,
        "year":int(base_row.year),
        "semester":f"{int(base_row.year)}H{1 if pd.Timestamp(base_row.entry_ts).month<=6 else 2}",
        "direction":direction,
        "entry_ts":base_row.entry_ts,
        "entry_price":entry,
        "pdc":pdc,
        "atr14_prev":atr,
        "reward_distance_D":D,
        "stop_price":np.nan if stop is None else float(stop),
        "exit_ts":exit_ts,
        "exit_price":float(exit_px),
        "exit_reason":exit_reason,
        "target_hit":bool(exit_reason=="PDC"),
        "gross_points":gross_points,
        "net_points":gross_points-BASE_COST/POINT_VALUE,
        "stress_net_points":gross_points-STRESS_COST/POINT_VALUE,
        "net_pnl_usd":(gross_points-BASE_COST/POINT_VALUE)*POINT_VALUE,
        "stress_net_pnl_usd":(gross_points-STRESS_COST/POINT_VALUE)*POINT_VALUE,
    }

def metrics(g):
    if len(g)==0:
        return {}
    p=g.net_pnl_usd
    sp=g.stress_net_pnl_usd
    sem=g.groupby("semester").net_pnl_usd.sum()
    return {
        "trades":int(len(g)),
        "target_hit_rate":float(g.target_hit.mean()),
        "stop_rate":float(g.exit_reason.str.startswith("STOP").mean()),
        "net_pnl_usd":float(p.sum()),
        "expectancy_usd":float(p.mean()),
        "profit_factor":float(profit_factor(p)),
        "stress_expectancy_usd":float(sp.mean()),
        "win_rate":float((p>0).mean()),
        "max_drawdown_usd":dd_magnitude(p),
        "positive_semesters":int((sem>0).sum()),
        "semesters_observed":int(len(sem)),
        "worst_trade_usd":float(p.min()),
        "p05_trade_usd":float(p.quantile(0.05)),
    }

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    daily=daily_context(groups)
    base=build_events(groups,daily).copy()
    if base.empty: raise ValueError("no PDC events")
    if base.year.max()>2025: raise ValueError("2026 leak")

    rows=[]
    for name,family,mult in CANDIDATES:
        for br in base.itertuples(index=False):
            g=groups.get(br.group_key)
            if g is None: continue
            z=simulate_one(br,g,family,mult)
            if z is None: continue
            z["candidate"]=name
            rows.append(z)
    tr=pd.DataFrame(rows).sort_values(["candidate","entry_ts"]).reset_index(drop=True)

    design=tr[tr.year<=2022].copy()
    val=tr[tr.year>=2023].copy()

    # Summaries.
    srows=[]
    for name,_,_ in CANDIDATES:
        gd=design[design.candidate==name].sort_values("entry_ts")
        gv=val[val.candidate==name].sort_values("entry_ts")
        md=metrics(gd); mv=metrics(gv)
        srows.append({
            "candidate":name,
            **{f"design_{k}":v for k,v in md.items()},
            **{f"validation_{k}":v for k,v in mv.items()},
        })
    summ=pd.DataFrame(srows)

    ctrl=summ.loc[summ.candidate=="NO_STOP"].iloc[0]
    summ["design_dd_improvement_pct"]=(ctrl.design_max_drawdown_usd-summ.design_max_drawdown_usd)/ctrl.design_max_drawdown_usd
    summ["design_score"]=summ.design_expectancy_usd-0.02*summ.design_max_drawdown_usd
    summ["design_eligible"]=(
        ((summ.design_expectancy_usd>ctrl.design_expectancy_usd) | (summ.design_dd_improvement_pct>=0.30))
        & (summ.design_expectancy_usd>0)
        & (summ.design_stress_expectancy_usd>0)
        & (summ.design_trades>=30)
        & (summ.design_semesters_observed>=3)
        & (summ.design_target_hit_rate>=0.70)
        & (summ.candidate!="NO_STOP")
    )

    elig=summ[summ.design_eligible].sort_values(["design_score","design_expectancy_usd"],ascending=False)
    selected=None if elig.empty else str(elig.iloc[0].candidate)

    # Frozen validation gate for selected design stop.
    gate={}
    if selected is not None:
        r=summ[summ.candidate==selected].iloc[0]
        vctrl=ctrl
        dd_imp=(vctrl.validation_max_drawdown_usd-r.validation_max_drawdown_usd)/vctrl.validation_max_drawdown_usd
        pnl_reduction=(vctrl.validation_net_pnl_usd-r.validation_net_pnl_usd)/vctrl.validation_net_pnl_usd if vctrl.validation_net_pnl_usd>0 else np.inf
        gate={
            "validation_expectancy_gt_0":bool(r.validation_expectancy_usd>0),
            "validation_pf_ge_1_20":bool(r.validation_profit_factor>=1.20),
            "validation_stress_expectancy_gt_0":bool(r.validation_stress_expectancy_usd>0),
            "validation_dd_improvement_ge_25pct":bool(dd_imp>=0.25),
            "validation_pnl_reduction_le_20pct":bool(pnl_reduction<=0.20),
            "validation_positive_semesters_ge_4":bool(r.validation_positive_semesters>=4),
        }
        selected_detail={
            "candidate":selected,
            "validation_dd_improvement_pct":float(dd_imp),
            "validation_pnl_reduction_pct":float(pnl_reduction),
            **gate,
            "passes_validation_gate":bool(all(gate.values()))
        }
    else:
        selected_detail={
            "candidate":None,
            "passes_validation_gate":False,
            "reason":"No stop candidate passed the frozen design eligibility gate."
        }

    # Yearly validation/control transparency.
    yearly=[]
    for name in ["NO_STOP"]+([selected] if selected else []):
        if name is None: continue
        g=tr[tr.candidate==name]
        for yr,gy in g.groupby("year",sort=True):
            yearly.append({"candidate":name,"year":int(yr),**metrics(gy.sort_values("entry_ts"))})
    yearly=pd.DataFrame(yearly)

    OUT.mkdir(parents=True,exist_ok=True)
    tr.to_csv(OUT/"PDC_STOP_TRADES.csv",index=False)
    summ.to_csv(OUT/"PDC_STOP_CANDIDATES.csv",index=False)
    yearly.to_csv(OUT/"PDC_STOP_YEARLY.csv",index=False)
    report={
        "authority":"PREREGISTERED_STOP_DESIGN",
        "contract_2026_opened":False,
        "design_period":"2020-2022",
        "validation_period":"2023-2025",
        "selected_stop":selected_detail,
    }
    (OUT/"PDC_STOP_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")

    print("\n=== STOP CANDIDATES ===")
    cols=["candidate","design_trades","design_expectancy_usd","design_profit_factor",
          "design_stress_expectancy_usd","design_max_drawdown_usd","design_dd_improvement_pct",
          "design_target_hit_rate","design_eligible","design_score",
          "validation_expectancy_usd","validation_profit_factor","validation_stress_expectancy_usd",
          "validation_max_drawdown_usd","validation_target_hit_rate","validation_worst_trade_usd"]
    print(summ[cols].round(4).to_string(index=False))
    print("\n=== SELECTED ===")
    print(json.dumps(selected_detail,indent=2))
    print("\n=== YEARLY ===")
    print(yearly.round(4).to_string(index=False))

if __name__=="__main__":
    main()
