#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, add_periods, period_table, regime_breakdown, STRESS_COST
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.archive.B13.b13_high_directional_triggers import block_features
from research.archive.B14.b14_opposite_sign_candidates import build_exact_inverse_trades
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

OUT=ROOT/"results/r071_temporal_diagnostic"
H=30

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    sessions=build_session_outputs(raw)
    t=build_exact_inverse_trades(feats,groups,"H080")
    if t.empty: raise ValueError("no R071/H080 trades")
    if pd.to_datetime(t.session_date).dt.year.max()>2025: raise ValueError("2026 leak")
    t["selected_net_pnl"]=t[f"net_pnl_{H}"]
    t["selected_stress_pnl"]=t[f"gross_pnl_{H}"]-STRESS_COST
    t=add_periods(t)
    OUT.mkdir(parents=True,exist_ok=True)
    t.to_parquet(OUT/"R071_TRADES.parquet",index=False)

    tabs={}
    for period,name in [("week","WEEKLY_DIAGNOSTIC"),("month","MONTHLY_DIAGNOSTIC"),
                        ("quarter","QUARTERLY_EVALUATION"),("semester","SEMESTER_EVALUATION"),
                        ("year_eval","YEARLY_ROBUSTNESS")]:
        tabs[period]=period_table(t,"selected_net_pnl",period)
        tabs[period].to_csv(OUT/f"R071_{name}.csv",index=False)

    regime_breakdown(t,sessions,"selected_net_pnl").to_csv(OUT/"R071_REGIME_EXPLANATION.csv",index=False)

    context_cols=["group_key","preopen_prediction","update_prediction","prev_state","overnight_state",
                  "five_day_state_label","preopen_support","open15_support"]
    sx=sessions[[c for c in context_cols if c in sessions.columns]].drop_duplicates("group_key")
    tx=t.merge(sx,on="group_key",how="left",validate="many_to_one")
    for cc in ("prev_state","overnight_state"):
        if cc in tx:
            tx[cc]=tx[cc].map({-1.0:"LOW",0.0:"NORMAL",1.0:"HIGH"}).fillna("UNKNOWN")
    rows_y=[]; rows_s=[]
    for dim in [c for c in context_cols if c!="group_key" and c in tx.columns]:
        for (yr,val),g in tx.groupby(["year_eval",dim],dropna=False,observed=True):
            p=g["selected_net_pnl"]
            rows_y.append({"year_eval":int(yr),"dimension":dim,
                           "category":"MISSING" if pd.isna(val) else str(val),
                           "trades":len(g),"net_pnl_usd":float(p.sum()),"expectancy_usd":float(p.mean()),
                           "profit_factor":float(profit_factor(p)),"win_rate":float((p>0).mean())})
        for (sem,val),g in tx.groupby(["semester",dim],dropna=False,observed=True):
            p=g["selected_net_pnl"]
            rows_s.append({"semester":str(sem),"dimension":dim,
                           "category":"MISSING" if pd.isna(val) else str(val),
                           "trades":len(g),"net_pnl_usd":float(p.sum()),"expectancy_usd":float(p.mean()),
                           "profit_factor":float(profit_factor(p)),"win_rate":float((p>0).mean())})
    pd.DataFrame(rows_y).to_csv(OUT/"R071_REGIME_BY_YEAR.csv",index=False)
    pd.DataFrame(rows_s).to_csv(OUT/"R071_REGIME_BY_SEMESTER.csv",index=False)

    pnl=t.selected_net_pnl
    stress=t.selected_stress_pnl
    byy=tabs["year_eval"]; bys=tabs["semester"]
    positive_year_pnl=byy.loc[byy.net_pnl_usd>0,"net_pnl_usd"]
    max_share=float(positive_year_pnl.max()/positive_year_pnl.sum()) if len(positive_year_pnl) and positive_year_pnl.sum()>0 else None
    report={
      "authority":"DIAGNOSTIC_ONLY_FROZEN_R071",
      "contract_2026_opened":False,
      "trades":int(len(t)),
      "net_pnl_usd":float(pnl.sum()),
      "expectancy_usd":float(pnl.mean()),
      "stress_expectancy_usd":float(stress.mean()),
      "profit_factor":float(profit_factor(pnl)),
      "positive_years":int(byy.positive.sum()),
      "observed_years":int(len(byy)),
      "positive_semesters":int(bys.positive.sum()),
      "observed_semesters":int(len(bys)),
      "max_positive_year_share":max_share,
    }
    (OUT/"R071_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("\nYEARLY\n",byy.to_string(index=False))
    print("\nSEMESTER\n",bys.to_string(index=False))

if __name__=="__main__":
    main()
