#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import build_continuous, contract_info
from research.archive.B12.b12_strategy_architecture import COST_RT, max_drawdown, parse_raw, prepare_rth, profit_factor, trade_from_signal
from research.archive.B13.b13_high_directional_triggers import block_features
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

STRESS_COST = COST_RT * 1.5
WICKS = (0.40, 0.45, 0.50, 0.55, 0.60)
CUTOFFS = (630, 660, 690)
HORIZONS = (15, 30, 60)
FOLDS = [
    (1,"2020-01-01","2021-12-31","2022-01-01","2022-06-30","2022H1"),
    (2,"2020-07-01","2022-06-30","2022-07-01","2022-12-31","2022H2"),
    (3,"2021-01-01","2022-12-31","2023-01-01","2023-06-30","2023H1"),
    (4,"2021-07-01","2023-06-30","2023-07-01","2023-12-31","2023H2"),
    (5,"2022-01-01","2023-12-31","2024-01-01","2024-06-30","2024H1"),
    (6,"2022-07-01","2024-06-30","2024-07-01","2024-12-31","2024H2"),
    (7,"2023-01-01","2024-12-31","2025-01-01","2025-06-30","2025H1"),
    (8,"2023-07-01","2025-06-30","2025-07-01","2025-12-31","2025H2"),
]

def development_files():
    files = sorted([p for p in (ROOT/"data/raw").glob("MES ??-??.Last.txt") if 2020 <= contract_info(p)[0] <= 2025], key=lambda p: contract_info(p)[:2])
    expected={(y,m) for y in range(2020,2026) for m in (3,6,9,12)}
    if len(files)!=24 or {contract_info(p)[:2] for p in files}!=expected:
        raise ValueError("require exactly 24 MES quarterly files 2020-2025")
    if any(contract_info(p)[0]>=2026 for p in files):
        raise ValueError("2026 file would be opened")
    return files

def load_development():
    raw,_,_=build_continuous(development_files(),"UTC",.25)
    raw=raw[raw.timestamp_et.dt.year.between(2020,2025)].copy()
    if raw.empty or raw.timestamp_et.dt.year.max()>2025:
        raise ValueError("development scope failure")
    return parse_raw(raw)

def cutoff_label(v): return f"{v//60:02d}:{v%60:02d}"
def variant_id(w,c,h): return f"W{w:.2f}_C{cutoff_label(c).replace(':','')}_H{h}"

def build_signal_trades(feats, groups, wick, cutoff):
    rows=[]
    for key,f in feats.groupby("group_key",sort=False,observed=True):
        g=groups.get(key)
        if g is None: continue
        candidates=[]
        for r in f.sort_values("block_id").itertuples(index=False):
            upper=r.upper_wick_ratio>=wick and r.block_close<r.block_open
            lower=r.lower_wick_ratio>=wick and r.block_close>r.block_open
            direction=1 if upper else (-1 if lower else 0)
            if not direction: continue
            pos=int(r.signal_pos)
            sb=g.iloc[pos]
            minute=sb["timestamp_et"].hour*60+sb["timestamp_et"].minute
            if minute>cutoff: continue
            tr=trade_from_signal(g,pos,direction)
            if tr is None: continue
            rec={**r._asdict(),"direction":direction,"side":"LONG" if direction==1 else "SHORT","wick_threshold":wick,"cutoff_minute":cutoff,**tr}
            for h in HORIZONS:
                rec[f"stress_net_pnl_{h}"]=rec[f"gross_pnl_{h}"]-STRESS_COST
            candidates.append(rec)
        if candidates:
            rows.append(min(candidates,key=lambda z:z["entry_clock_et"]))
    return pd.DataFrame(rows).sort_values("entry_clock_et").reset_index(drop=True) if rows else pd.DataFrame()

def stats_for(t,h):
    if t.empty:
        return dict(trades=0,net_pnl_usd=0.0,expectancy_usd=np.nan,stress_expectancy_usd=np.nan,profit_factor=np.nan,win_rate=np.nan,max_drawdown_usd=np.nan)
    pnl=t[f"net_pnl_{h}"]; stress=t[f"stress_net_pnl_{h}"]
    return dict(trades=len(t),net_pnl_usd=float(pnl.sum()),expectancy_usd=float(pnl.mean()),stress_expectancy_usd=float(stress.mean()),profit_factor=float(profit_factor(pnl)),win_rate=float((pnl>0).mean()),max_drawdown_usd=float(max_drawdown(pnl)))

def add_periods(x):
    y=x.copy(); d=pd.to_datetime(y.session_date); iso=d.dt.isocalendar()
    y["week"]=iso.year.astype(str)+"-W"+iso.week.astype(str).str.zfill(2)
    y["month"]=d.dt.to_period("M").astype(str)
    y["quarter"]=d.dt.to_period("Q").astype(str)
    y["semester"]=d.dt.year.astype(str)+np.where(d.dt.month<=6,"H1","H2")
    y["year_eval"]=d.dt.year
    return y

def period_table(t,pnl_col,period):
    rows=[]
    for key,g in t.groupby(period,sort=True,observed=True):
        pnl=g[pnl_col]
        rows.append({period:key,"trades":len(g),"net_pnl_usd":float(pnl.sum()),"expectancy_usd":float(pnl.mean()),"profit_factor":float(profit_factor(pnl)),"win_rate":float((pnl>0).mean()),"positive":bool(pnl.sum()>0)})
    return pd.DataFrame(rows)

def train_row(trades,w,c,h,start,end):
    t=trades[trades.session_date.between(start,end)].copy(); base=stats_for(t,h)
    if len(t):
        sem=period_table(add_periods(t),f"net_pnl_{h}","semester")
        obs=len(sem); pos=int(sem.positive.sum()); med=float(sem.expectancy_usd.median())
    else:
        obs=pos=0; med=np.nan
    eligible=(base["trades"]>=25 and np.isfinite(base["expectancy_usd"]) and base["expectancy_usd"]>0 and np.isfinite(base["profit_factor"]) and base["profit_factor"]>1 and np.isfinite(base["stress_expectancy_usd"]) and base["stress_expectancy_usd"]>0 and obs>0 and pos>=int(np.ceil(obs/2)))
    return {"variant":variant_id(w,c,h),"wick_threshold":w,"cutoff_minute":c,"cutoff_et":cutoff_label(c),"horizon_minutes":h,**base,"observed_semesters":obs,"positive_semesters":pos,"median_semester_expectancy_usd":med,"eligible":bool(eligible)}

def choose(df):
    e=df[df.eligible].copy()
    if e.empty: return None
    e=e.sort_values(["median_semester_expectancy_usd","profit_factor","expectancy_usd","trades","wick_threshold","cutoff_minute","horizon_minutes"],ascending=[False,False,False,False,True,True,True])
    return e.iloc[0].to_dict()

def regime_breakdown(trades,sessions,pnl_col):
    cols=["group_key","preopen_prediction","update_prediction","prev_state","overnight_state","five_day_state_label","preopen_support","open15_support"]
    s=sessions[[c for c in cols if c in sessions.columns]].drop_duplicates("group_key")
    x=trades.merge(s,on="group_key",how="left",validate="many_to_one")
    for c in ("prev_state","overnight_state"):
        if c in x: x[c]=x[c].map({-1.0:"LOW",0.0:"NORMAL",1.0:"HIGH"}).fillna("UNKNOWN")
    rows=[]
    for dim in [c for c in cols if c!="group_key" and c in x]:
        for val,g in x.groupby(dim,dropna=False,observed=True):
            pnl=g[pnl_col]
            rows.append({"dimension":dim,"category":"MISSING" if pd.isna(val) else str(val),"trades":len(g),"net_pnl_usd":float(pnl.sum()),"expectancy_usd":float(pnl.mean()),"profit_factor":float(profit_factor(pnl)),"win_rate":float((pnl>0).mean())})
    return pd.DataFrame(rows)

def main():
    raw=load_development(); _,groups=prepare_rth(raw); feats=block_features(raw,groups); sessions=build_session_outputs(raw)
    variants={(w,c):build_signal_trades(feats,groups,w,c) for w in WICKS for c in CUTOFFS}
    out=ROOT/"results/parameter_walkforward_p1"; out.mkdir(parents=True,exist_ok=True)

    full=[]
    for (w,c),t in variants.items():
        for h in HORIZONS:
            full.append({"variant":variant_id(w,c,h),"wick_threshold":w,"cutoff_et":cutoff_label(c),"horizon_minutes":h,**stats_for(t,h)})
    pd.DataFrame(full).to_csv(out/"P1_FULL_SAMPLE_GRID.csv",index=False)

    folds=[]; details=[]; tests=[]
    for fold,ts,te,vs,ve,label in FOLDS:
        cand=pd.DataFrame([train_row(variants[(w,c)],w,c,h,ts,te) for w in WICKS for c in CUTOFFS for h in HORIZONS])
        cand["fold"]=fold; cand["test_label"]=label; details.append(cand); ch=choose(cand)
        if ch is None:
            folds.append({"fold":fold,"test_label":label,"selected_variant":"NO_TRADE","train_trades":0,"train_pf":None,"train_expectancy":None,"test_trades":0,"test_pnl":0.0,"test_expectancy":None,"test_pf":None}); continue
        w=float(ch["wick_threshold"]); c=int(ch["cutoff_minute"]); h=int(ch["horizon_minutes"])
        t=variants[(w,c)][variants[(w,c)].session_date.between(vs,ve)].copy()
        t["selected_horizon"]=h; t["selected_variant"]=ch["variant"]; t["fold"]=fold; t["test_label"]=label
        t["selected_net_pnl"]=t[f"net_pnl_{h}"]; t["selected_stress_pnl"]=t[f"stress_net_pnl_{h}"]; tests.append(t)
        m=stats_for(t,h)
        folds.append({"fold":fold,"test_label":label,"selected_variant":ch["variant"],"train_trades":int(ch["trades"]),"train_pf":round(float(ch["profit_factor"]),3),"train_expectancy":round(float(ch["expectancy_usd"]),2),"test_trades":int(m["trades"]),"test_pnl":round(float(m["net_pnl_usd"]),2),"test_expectancy":None if not np.isfinite(m["expectancy_usd"]) else round(float(m["expectancy_usd"]),2),"test_pf":None if not np.isfinite(m["profit_factor"]) else round(float(m["profit_factor"]),3)})
    pd.concat(details,ignore_index=True).to_csv(out/"P1_TRAIN_SELECTION_DETAIL.csv",index=False)
    pd.DataFrame(folds).to_csv(out/"P1_FOLD_SELECTIONS.csv",index=False)

    oos=pd.concat(tests,ignore_index=True).sort_values("entry_clock_et") if tests else pd.DataFrame()
    if oos.empty:
        overall={"trades":0,"net_pnl_usd":0.0,"expectancy_usd":None,"stress_expectancy_usd":None,"profit_factor":None,"positive_semesters":0,"positive_years":0,"max_positive_year_share":None,"passes_numeric_gate":False}
    else:
        if pd.to_datetime(oos.session_date).dt.year.max()>2025: raise ValueError("2026 leak")
        oos=add_periods(oos); oos.to_parquet(out/"P1_PSEUDO_OOS_TRADES.parquet",index=False)
        tabs={}
        for period,name in [("week","WEEKLY_DIAGNOSTIC"),("month","MONTHLY_DIAGNOSTIC"),("quarter","QUARTERLY_EVALUATION"),("semester","SEMESTER_EVALUATION"),("year_eval","YEARLY_ROBUSTNESS")]:
            tabs[period]=period_table(oos,"selected_net_pnl",period); tabs[period].to_csv(out/f"P1_{name}.csv",index=False)
        regime_breakdown(oos,sessions,"selected_net_pnl").to_csv(out/"P1_REGIME_EXPLANATION.csv",index=False)
        pnl=oos.selected_net_pnl; stress=oos.selected_stress_pnl
        posy=tabs["year_eval"].loc[tabs["year_eval"].net_pnl_usd>0,"net_pnl_usd"]
        share=float(posy.max()/posy.sum()) if len(posy) and posy.sum()>0 else np.nan
        overall={"trades":len(oos),"net_pnl_usd":float(pnl.sum()),"expectancy_usd":float(pnl.mean()),"stress_expectancy_usd":float(stress.mean()),"profit_factor":float(profit_factor(pnl)),"positive_semesters":int(tabs["semester"].positive.sum()),"positive_years":int(tabs["year_eval"].positive.sum()),"max_positive_year_share":None if not np.isfinite(share) else share}
        overall["passes_numeric_gate"]=bool(overall["expectancy_usd"]>0 and overall["profit_factor"]>=1.15 and overall["stress_expectancy_usd"]>0 and overall["positive_semesters"]>=5 and overall["positive_years"]>=3 and overall["max_positive_year_share"] is not None and overall["max_positive_year_share"]<=0.50)

    sel=[r["selected_variant"] for r in folds if r["selected_variant"]!="NO_TRADE"]; cnt=Counter(sel)
    if cnt:
        mode,n=cnt.most_common(1)[0]; stability={"unique_variants":len(cnt),"mode_variant":mode,"mode_count":n,"mode_share":n/len(sel),"selection_counts":dict(cnt)}
    else:
        stability={"unique_variants":0,"mode_variant":"NONE","mode_count":0,"mode_share":None,"selection_counts":{}}

    report={"authority":"REUSED_DEVELOPMENT_WALK_FORWARD_NOT_INDEPENDENT_OOS","source_start_et":str(raw.timestamp_et.min()),"source_end_et":str(raw.timestamp_et.max()),"opened_contract_years":sorted({contract_info(p)[0] for p in development_files()}),"contract_2026_opened":False,"weeks_months_used_for_selection":False,"folds":folds,"pseudo_oos":overall,"parameter_stability":stability,"grid_variants":45,"base_cost_rt_usd":COST_RT,"stress_cost_rt_usd":STRESS_COST}
    (out/"P1_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
