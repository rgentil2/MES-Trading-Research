#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
import json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import (
    FOLDS, STRESS_COST, load_development, build_signal_trades, add_periods,
    period_table, regime_breakdown
)
from research.archive.B12.b12_strategy_architecture import (
    COST_RT, MES_POINT_VALUE, max_drawdown, prepare_rth, profit_factor
)
from research.archive.B13.b13_high_directional_triggers import block_features
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

STOP_MULTS=(None,0.50,0.65,0.80)
TARGET_MULTS=(None,0.75,1.00,1.25)
TICK=0.25
OUT=ROOT/"results/risk_design_p2"

def rid(s,t):
    a="NONE" if s is None else f"{int(round(s*100)):03d}"
    b="NONE" if t is None else f"{int(round(t*100)):03d}"
    return f"S{a}_T{b}"

def stop_distance(raw):
    return max(TICK, math.floor(raw/TICK+1e-12)*TICK)

def target_distance(raw):
    return max(TICK, math.ceil(raw/TICK-1e-12)*TICK)

def simulate_one(r,g,s_mult,t_mult):
    pos=int(r.signal_pos)
    entry=float(r.entry_price)
    direction=int(r.direction)
    block=float(r.block_range_points)
    path=g.iloc[pos+1:pos+31]
    if len(path)!=30: return None

    sd=None if s_mult is None else stop_distance(s_mult*block)
    td=None if t_mult is None else target_distance(t_mult*block)
    if direction==1:
        stop=None if sd is None else entry-sd
        target=None if td is None else entry+td
    else:
        stop=None if sd is None else entry+sd
        target=None if td is None else entry-td

    exit_price=float(r.exit_price_30)
    exit_ts=r.exit_ts_30
    reason="TIME"
    for bar in path.itertuples(index=False):
        if direction==1:
            hit_stop=stop is not None and float(bar.low)<=stop
            hit_target=target is not None and float(bar.high)>=target
        else:
            hit_stop=stop is not None and float(bar.high)>=stop
            hit_target=target is not None and float(bar.low)<=target
        if hit_stop:
            exit_price=float(stop); exit_ts=bar.timestamp_et; reason="STOP"; break
        if hit_target:
            exit_price=float(target); exit_ts=bar.timestamp_et; reason="TARGET"; break

    gross=direction*(exit_price-entry)*MES_POINT_VALUE
    return {
        "exit_price_risk":exit_price,"exit_ts_risk":exit_ts,"exit_reason":reason,
        "gross_pnl_risk":gross,"net_pnl_risk":gross-COST_RT,
        "stress_pnl_risk":gross-STRESS_COST
    }

def build_risk_variant(base,groups,s,t):
    rows=[]
    for r in base.itertuples(index=False):
        g=groups.get(r.group_key)
        if g is None: continue
        sim=simulate_one(r,g,s,t)
        if sim is None: continue
        rows.append({**r._asdict(),"risk_variant":rid(s,t),"stop_mult":s,"target_mult":t,**sim})
    return pd.DataFrame(rows).sort_values("entry_clock_et").reset_index(drop=True)

def metrics(t):
    if t.empty:
        return {"trades":0,"net_pnl_usd":0.0,"expectancy_usd":np.nan,
                "stress_expectancy_usd":np.nan,"profit_factor":np.nan,"max_drawdown_usd":np.nan}
    pnl=t.net_pnl_risk
    return {"trades":int(len(t)),"net_pnl_usd":float(pnl.sum()),"expectancy_usd":float(pnl.mean()),
            "stress_expectancy_usd":float(t.stress_pnl_risk.mean()),
            "profit_factor":float(profit_factor(pnl)),
            "max_drawdown_usd":float(abs(max_drawdown(pnl)))}

def train_row(t,s,trg,start,end):
    x=t[t.session_date.between(start,end)].copy()
    m=metrics(x)
    if len(x):
        x=add_periods(x)
        sem=period_table(x,"net_pnl_risk","semester")
        obs=len(sem); pos=int(sem.positive.sum()); med=float(sem.expectancy_usd.median())
    else:
        obs=pos=0; med=np.nan
    eligible=(m["trades"]>=25 and np.isfinite(m["expectancy_usd"]) and m["expectancy_usd"]>0
              and np.isfinite(m["profit_factor"]) and m["profit_factor"]>1
              and np.isfinite(m["stress_expectancy_usd"]) and m["stress_expectancy_usd"]>0
              and obs>0 and pos>=int(np.ceil(obs/2)))
    return {"risk_variant":rid(s,trg),"stop_mult":s,"target_mult":trg,**m,
            "observed_semesters":obs,"positive_semesters":pos,
            "median_semester_expectancy":med,"eligible":bool(eligible)}

def choose(df):
    e=df[df.eligible].copy()
    if e.empty: return None
    # deterministic values for None in final tie break
    e["stop_order"]=e.stop_mult.fillna(-1)
    e["target_order"]=e.target_mult.fillna(-1)
    e=e.sort_values(
        ["median_semester_expectancy","max_drawdown_usd","profit_factor","expectancy_usd","stop_order","target_order"],
        ascending=[False,True,False,False,True,True]
    )
    return e.iloc[0].to_dict()

def summarize_oos(t):
    if t.empty:
        return {"trades":0,"net_pnl_usd":0.0,"expectancy_usd":None,"stress_expectancy_usd":None,
                "profit_factor":None,"max_drawdown_usd":None,"positive_semesters":0,"positive_years":0}
    x=add_periods(t)
    sem=period_table(x,"selected_net_pnl","semester")
    yr=period_table(x,"selected_net_pnl","year_eval")
    pnl=x.selected_net_pnl
    return {"trades":int(len(x)),"net_pnl_usd":float(pnl.sum()),"expectancy_usd":float(pnl.mean()),
            "stress_expectancy_usd":float(x.selected_stress_pnl.mean()),
            "profit_factor":float(profit_factor(pnl)),"max_drawdown_usd":float(abs(max_drawdown(pnl))),
            "positive_semesters":int(sem.positive.sum()),"positive_years":int(yr.positive.sum())}

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    sessions=build_session_outputs(raw)
    base=build_signal_trades(feats,groups,0.50,660)
    variants={(s,t):build_risk_variant(base,groups,s,t) for s in STOP_MULTS for t in TARGET_MULTS}

    OUT.mkdir(parents=True,exist_ok=True)
    full=[]
    for (s,t),x in variants.items():
        full.append({"risk_variant":rid(s,t),"stop_mult":s,"target_mult":t,**metrics(x)})
    pd.DataFrame(full).to_csv(OUT/"P2_FULL_DEVELOPMENT_GRID.csv",index=False)

    folds=[]; details=[]; tests=[]
    for fold,ts,te,vs,ve,label in FOLDS:
        cand=pd.DataFrame([train_row(variants[(s,t)],s,t,ts,te) for s in STOP_MULTS for t in TARGET_MULTS])
        cand["fold"]=fold; cand["test_label"]=label; details.append(cand)
        ch=choose(cand)
        if ch is None:
            folds.append({"fold":fold,"test_label":label,"selected":"NO_TRADE","test_trades":0,"test_pnl":0.0})
            continue
        s=None if pd.isna(ch["stop_mult"]) else float(ch["stop_mult"])
        t=None if pd.isna(ch["target_mult"]) else float(ch["target_mult"])
        x=variants[(s,t)][variants[(s,t)].session_date.between(vs,ve)].copy()
        x["selected_net_pnl"]=x.net_pnl_risk
        x["selected_stress_pnl"]=x.stress_pnl_risk
        x["fold"]=fold; x["test_label"]=label
        tests.append(x)
        m=metrics(x)
        folds.append({"fold":fold,"test_label":label,"selected":ch["risk_variant"],
                      "train_trades":int(ch["trades"]),"train_expectancy":float(ch["expectancy_usd"]),
                      "train_pf":float(ch["profit_factor"]),"train_max_dd":float(ch["max_drawdown_usd"]),
                      "test_trades":int(m["trades"]),"test_pnl":float(m["net_pnl_usd"]),
                      "test_expectancy":float(m["expectancy_usd"]) if np.isfinite(m["expectancy_usd"]) else None,
                      "test_pf":float(m["profit_factor"]) if np.isfinite(m["profit_factor"]) else None})
    pd.concat(details,ignore_index=True).to_csv(OUT/"P2_TRAIN_SELECTION_DETAIL.csv",index=False)
    pd.DataFrame(folds).to_csv(OUT/"P2_FOLD_SELECTIONS.csv",index=False)

    oos=pd.concat(tests,ignore_index=True).sort_values("entry_clock_et") if tests else pd.DataFrame()
    if not oos.empty:
        if pd.to_datetime(oos.session_date).dt.year.max()>2025: raise ValueError("2026 leak")
        oos=add_periods(oos)
        oos.to_parquet(OUT/"P2_PSEUDO_OOS_TRADES.parquet",index=False)
        for period,name in [("week","WEEKLY_DIAGNOSTIC"),("month","MONTHLY_DIAGNOSTIC"),
                            ("quarter","QUARTERLY_EVALUATION"),("semester","SEMESTER_EVALUATION"),
                            ("year_eval","YEARLY_ROBUSTNESS")]:
            period_table(oos,"selected_net_pnl",period).to_csv(OUT/f"P2_{name}.csv",index=False)
        regime_breakdown(oos,sessions,"selected_net_pnl").to_csv(OUT/"P2_REGIME_EXPLANATION.csv",index=False)

    control=variants[(None,None)]
    control=control[control.session_date.between("2022-01-01","2025-12-31")].copy()
    control["selected_net_pnl"]=control.net_pnl_risk
    control["selected_stress_pnl"]=control.stress_pnl_risk
    control_summary=summarize_oos(control)
    selected_summary=summarize_oos(oos)

    selected_ids=[r["selected"] for r in folds if r["selected"]!="NO_TRADE"]
    cnt=Counter(selected_ids)
    report={
        "authority":"DEVELOPMENT_RISK_WALK_FORWARD_NOT_INDEPENDENT_OOS",
        "contract_2026_opened":False,
        "fixed_signal":"W0.50_C1100_H30",
        "risk_grid_variants":16,
        "folds":folds,
        "selected_pseudo_oos":selected_summary,
        "control_2022_2025":control_summary,
        "selection_counts":dict(cnt)
    }
    (OUT/"P2_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()

# trigger preregistered R072 risk-design rerun
