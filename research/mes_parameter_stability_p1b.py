#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import (
    WICKS,CUTOFFS,HORIZONS,FOLDS,STRESS_COST,load_development,
    build_signal_trades,stats_for,add_periods,period_table,train_row,choose,variant_id
)
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.archive.B13.b13_high_directional_triggers import block_features
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

OUT=ROOT/"results/parameter_stability_p1b"

def perf(t,pnl_col):
    if t.empty:
        return {"trades":0,"pnl":0.0,"exp":np.nan,"pf":np.nan}
    pnl=t[pnl_col]
    return {"trades":int(len(t)),"pnl":float(pnl.sum()),"exp":float(pnl.mean()),"pf":float(profit_factor(pnl))}

def temporal_variant_summary(t,w,c,h):
    base=stats_for(t,h)
    x=add_periods(t) if len(t) else pd.DataFrame()
    years=period_table(x,f"net_pnl_{h}","year_eval") if len(x) else pd.DataFrame()
    sem=period_table(x,f"net_pnl_{h}","semester") if len(x) else pd.DataFrame()
    y25=x[x.year_eval==2025] if len(x) else pd.DataFrame()
    y25m=perf(y25,f"net_pnl_{h}")
    return {
        "variant":variant_id(w,c,h),"wick_threshold":w,"cutoff_minute":c,
        "horizon_minutes":h,**base,
        "years_observed":int(len(years)),
        "years_positive":int(years.positive.sum()) if len(years) else 0,
        "median_year_expectancy":float(years.expectancy_usd.median()) if len(years) else np.nan,
        "worst_year_expectancy":float(years.expectancy_usd.min()) if len(years) else np.nan,
        "semesters_observed":int(len(sem)),
        "semesters_positive":int(sem.positive.sum()) if len(sem) else 0,
        "median_semester_expectancy":float(sem.expectancy_usd.median()) if len(sem) else np.nan,
        "y2025_trades":y25m["trades"],"y2025_pnl":y25m["pnl"],
        "y2025_expectancy":y25m["exp"],"y2025_pf":y25m["pf"],
    }

def neighbor_ids(w,c,h):
    wi=WICKS.index(w); ci=CUTOFFS.index(c); hi=HORIZONS.index(h)
    out=[]
    for dw,dc,dh in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
        a,b,d=wi+dw,ci+dc,hi+dh
        if 0<=a<len(WICKS) and 0<=b<len(CUTOFFS) and 0<=d<len(HORIZONS):
            out.append(variant_id(WICKS[a],CUTOFFS[b],HORIZONS[d]))
    return out

def reconstruct_oos(variants):
    tests=[]; selections=[]
    for fold,ts,te,vs,ve,label in FOLDS:
        cand=pd.DataFrame([
            train_row(variants[(w,c)],w,c,h,ts,te)
            for w in WICKS for c in CUTOFFS for h in HORIZONS
        ])
        ch=choose(cand)
        if ch is None:
            selections.append({"fold":fold,"test_label":label,"variant":"NO_TRADE"})
            continue
        w=float(ch["wick_threshold"]); c=int(ch["cutoff_minute"]); h=int(ch["horizon_minutes"])
        t=variants[(w,c)][variants[(w,c)].session_date.between(vs,ve)].copy()
        t["selected_variant"]=ch["variant"]; t["selected_horizon"]=h
        t["selected_net_pnl"]=t[f"net_pnl_{h}"]; t["selected_stress_pnl"]=t[f"stress_net_pnl_{h}"]
        t["fold"]=fold; t["test_label"]=label
        tests.append(t)
        selections.append({"fold":fold,"test_label":label,"variant":ch["variant"]})
    oos=pd.concat(tests,ignore_index=True).sort_values("entry_clock_et") if tests else pd.DataFrame()
    return oos,pd.DataFrame(selections)

def enrich_regime(oos,sessions):
    cols=["group_key","preopen_prediction","update_prediction","prev_state","overnight_state",
          "five_day_state_label","preopen_support","open15_support"]
    s=sessions[[c for c in cols if c in sessions.columns]].drop_duplicates("group_key")
    x=oos.merge(s,on="group_key",how="left",validate="many_to_one")
    for c in ("prev_state","overnight_state"):
        if c in x:
            x[c]=x[c].map({-1.0:"LOW",0.0:"NORMAL",1.0:"HIGH"}).fillna("UNKNOWN")
    return add_periods(x)

def cross_table(x,time_col):
    dims=["preopen_prediction","update_prediction","prev_state","overnight_state",
          "five_day_state_label","preopen_support","open15_support"]
    rows=[]
    for dim in dims:
        if dim not in x: continue
        for (period,val),g in x.groupby([time_col,dim],dropna=False,observed=True):
            pnl=g.selected_net_pnl
            rows.append({
                time_col:period,"dimension":dim,
                "category":"MISSING" if pd.isna(val) else str(val),
                "trades":int(len(g)),"net_pnl_usd":float(pnl.sum()),
                "expectancy_usd":float(pnl.mean()),"profit_factor":float(profit_factor(pnl)),
                "win_rate":float((pnl>0).mean())
            })
    return pd.DataFrame(rows)

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    sessions=build_session_outputs(raw)
    variants={(w,c):build_signal_trades(feats,groups,w,c) for w in WICKS for c in CUTOFFS}

    OUT.mkdir(parents=True,exist_ok=True)

    summaries=[]
    for w in WICKS:
        for c in CUTOFFS:
            t=variants[(w,c)]
            for h in HORIZONS:
                summaries.append(temporal_variant_summary(t,w,c,h))
    v=pd.DataFrame(summaries).set_index("variant",drop=False)

    plateau=[]
    for vid,r in v.iterrows():
        ns=neighbor_ids(float(r.wick_threshold),int(r.cutoff_minute),int(r.horizon_minutes))
        eligible=0
        for nid in ns:
            q=v.loc[nid]
            ok=(q.expectancy_usd>0 and q.stress_expectancy_usd>0 and q.profit_factor>1.0 and q.years_positive>=4)
            eligible+=int(bool(ok))
        plateau.append({
            "variant":vid,"immediate_neighbors":len(ns),"robust_neighbors":eligible,
            "robust_neighbor_fraction":eligible/len(ns) if ns else np.nan
        })
    v=v.merge(pd.DataFrame(plateau),on="variant",how="left")
    v.to_csv(OUT/"P1B_PARAMETER_STABILITY.csv",index=False)

    oos,selections=reconstruct_oos(variants)
    selections.to_csv(OUT/"P1B_REPRODUCED_SELECTIONS.csv",index=False)
    if oos.empty:
        raise ValueError("P1 pseudo-OOS reconstruction produced no trades")
    if pd.to_datetime(oos.session_date).dt.year.max()>2025:
        raise ValueError("2026 leak")
    x=enrich_regime(oos,sessions)
    cross_table(x,"year_eval").to_csv(OUT/"P1B_REGIME_BY_YEAR.csv",index=False)
    cross_table(x,"semester").to_csv(OUT/"P1B_REGIME_BY_SEMESTER.csv",index=False)

    by_variant=[]
    for vid,g in x.groupby("selected_variant",observed=True):
        pnl=g.selected_net_pnl
        by_variant.append({
            "selected_variant":vid,"trades":len(g),"net_pnl_usd":float(pnl.sum()),
            "expectancy_usd":float(pnl.mean()),"profit_factor":float(profit_factor(pnl)),
            "years_positive":int(period_table(g,"selected_net_pnl","year_eval").positive.sum())
        })
    pd.DataFrame(by_variant).to_csv(OUT/"P1B_SELECTED_VARIANT_ATTRIBUTION.csv",index=False)

    # Top descriptive plateau rows; no parameter is selected here.
    display=v.copy()
    display["plateau_sort"]=display.robust_neighbor_fraction.fillna(-1)
    top=display.sort_values(
        ["plateau_sort","years_positive","median_year_expectancy","stress_expectancy_usd"],
        ascending=[False,False,False,False]
    ).head(10)
    report={
        "authority":"DIAGNOSTIC_ONLY_NO_NEW_PARAMETER_SELECTION",
        "contract_2026_opened":False,
        "grid_variants":45,
        "p1_reproduced_selections":selections.to_dict("records"),
        "pseudo_oos_trades":int(len(oos)),
        "top_plateau_descriptive":top[[
            "variant","trades","expectancy_usd","stress_expectancy_usd","profit_factor",
            "years_positive","median_year_expectancy","worst_year_expectancy",
            "y2025_expectancy","y2025_pf","robust_neighbor_fraction"
        ]].replace({np.nan:None}).to_dict("records")
    }
    (OUT/"P1B_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
