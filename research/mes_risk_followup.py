#!/usr/bin/env python3
from __future__ import annotations

import json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, build_signal_trades
from research.archive.B12.b12_strategy_architecture import prepare_rth
from research.archive.B13.b13_high_directional_triggers import block_features
from research.mes_pdc_small_gap_reconstruction import daily_context as daily_atr_context
from research.mes_poc_breakdown_reconstruction import build_levels as poc_build_levels, build_events as poc_build_events
from research.mes_stage1_local_robustness import timed_variant_rows, metrics as stage1_metrics, load_news
from research.mes_poc_r072_atr_stop import trade_geometry, simulate_with_stop, no_stop_row, metrics as risk_metrics, ceil05

OUT=ROOT/"results/mes_risk_followup"
POC_H=[10,15,20]

def period_metrics(g):
    return stage1_metrics(g.sort_values("entry_actual_et"))

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    news=load_news()
    OUT.mkdir(parents=True,exist_ok=True)

    # ---- POC H10/H15/H20 temporal diagnosis ----
    levels=poc_build_levels(groups)
    pocbase=poc_build_events(groups,levels)
    pocrows,blocked=timed_variant_rows(groups,pocbase,news,"POC",POC_H)
    p=pd.DataFrame(pocrows).sort_values(["variant","entry_actual_et"]).reset_index(drop=True)

    poc_summary=[]
    for h in POC_H:
        v=f"H{h}"
        g=p[p.variant==v]
        for label,mask in [
            ("2020-2022",g.year<=2022),
            ("2023-2025",g.year>=2023),
            ("2020-2025",g.year.between(2020,2025)),
        ]:
            poc_summary.append({"variant":v,"period":label,**period_metrics(g[mask])})
        # year / semester transparency
        yr=pd.DataFrame([{"year":int(y),**period_metrics(x)} for y,x in g.groupby("year",sort=True)])
        yr.to_csv(OUT/f"POC_{v}_YEARLY.csv",index=False)
        sm=pd.DataFrame([{"semester":str(s),**period_metrics(x)} for s,x in g.groupby("semester",sort=True)])
        sm.to_csv(OUT/f"POC_{v}_SEMESTER.csv",index=False)

    ps=pd.DataFrame(poc_summary)
    ps.to_csv(OUT/"POC_HORIZON_TEMPORAL_SUMMARY.csv",index=False)
    p.to_csv(OUT/"POC_HORIZON_TRADES.csv",index=False)

    # ---- R072 catastrophe stop ----
    feats=block_features(raw,groups)
    base=build_signal_trades(feats,groups,0.50,660)
    dctx=daily_atr_context(groups)
    atrmap=dctx.set_index("group_key")["atr14_prev"].to_dict()

    geo=[]
    for br in base.itertuples(index=False):
        atr=atrmap.get(br.group_key,np.nan)
        if not np.isfinite(atr) or atr<=0:continue
        g=groups.get(br.group_key)
        if g is None:continue
        rec=trade_geometry("R072",br,g,float(atr),news.get(str(br.session_date)),30)
        if rec is not None:geo.append(rec)

    geo=pd.DataFrame(geo).sort_values("entry_actual").reset_index(drop=True)
    design=geo[(geo.year<=2022)&(geo.base_net_pnl_usd>0)]
    if design.empty:raise ValueError("No R072 design winners")
    envelope_raw=float(design.mae_atr.max())
    E=ceil05(envelope_raw)
    vals=[E,ceil05(1.5*E),ceil05(2.0*E)]
    vals=sorted(set(round(v,2) for v in vals))
    while len(vals)<3:
        vals.append(round(vals[-1]+0.05,2))

    rows=[]
    for rec in geo.itertuples(index=False):
        g=groups[rec.group_key]
        common={
          "strategy":"R072","group_key":rec.group_key,"session_date":rec.session_date,
          "year":int(rec.year),"semester":rec.semester,"entry_actual":rec.entry_actual,
          "mae_atr":float(rec.mae_atr),"mfe_atr":float(rec.mfe_atr),"atr14_prev":float(rec.atr14_prev),
        }
        rows.append({**common,**no_stop_row(rec)})
        for k in vals:
            rows.append({**common,**simulate_with_stop(rec,g,k)})

    t=pd.DataFrame(rows).sort_values(["candidate","entry_actual"]).reset_index(drop=True)
    t.to_csv(OUT/"R072_CATASTROPHE_STOP_TRADES.csv",index=False)

    control=risk_metrics(t[(t.candidate=="NO_STOP")&(t.year>=2023)].sort_values("entry_actual"))
    summary=[]
    passing=[]
    for cand,g in t.groupby("candidate",sort=True):
        gd=g[g.year<=2022].sort_values("entry_actual")
        gv=g[g.year>=2023].sort_values("entry_actual")
        md=risk_metrics(gd); mv=risk_metrics(gv)
        row={"candidate":cand,
             **{f"design_{k}":v for k,v in md.items()},
             **{f"validation_{k}":v for k,v in mv.items()}}
        if cand!="NO_STOP":
            dd_imp=(control["max_drawdown_usd"]-mv["max_drawdown_usd"])/control["max_drawdown_usd"]
            worst_imp=(abs(control["worst_trade_usd"])-abs(mv["worst_trade_usd"]))/abs(control["worst_trade_usd"])
            pnl_red=(control["net_pnl_usd"]-mv["net_pnl_usd"])/control["net_pnl_usd"]
            gate={
              "expectancy_gt_0":mv["expectancy_usd"]>0,
              "pf_ge_1_25":mv["profit_factor"]>=1.25,
              "stress_expectancy_gt_0":mv["stress_expectancy_usd"]>0,
              "worst_trade_improvement_ge_25pct":worst_imp>=.25,
              "dd_improvement_ge_15pct":dd_imp>=.15,
              "pnl_reduction_le_10pct":pnl_red<=.10,
              "positive_semesters_ge_4":mv["positive_semesters"]>=4,
            }
            row.update({
              "validation_dd_improvement_pct":dd_imp,
              "validation_worst_trade_improvement_pct":worst_imp,
              "validation_pnl_reduction_pct":pnl_red,
              "passes_gate":bool(all(gate.values()))
            })
            if row["passes_gate"]:passing.append(row)
        else:
            row["passes_gate"]=False
        summary.append(row)

    rs=pd.DataFrame(summary)
    rs.to_csv(OUT/"R072_CATASTROPHE_STOP_SUMMARY.csv",index=False)

    center_id=f"SL_{vals[1]:.2f}ATR"
    passdf=rs[rs.passes_gate==True]
    if center_id in set(passdf.candidate):
        selected=center_id; reason="CENTER_PASSES"
    elif len(passdf):
        z=passdf.sort_values(["validation_max_drawdown_usd","validation_profit_factor"],ascending=[True,False])
        selected=str(z.iloc[0].candidate); reason="NEIGHBOR_PASSES_CENTER_FAILS"
    else:
        selected=None; reason="NO_CATASTROPHE_STOP_PASSES"

    report={
      "authority":"PREREGISTERED_RISK_FOLLOWUP",
      "contract_2026_opened":False,
      "POC":{
        "status":"TEMPORAL_DIAGNOSTIC_ONLY",
        "horizons":[10,15,20]
      },
      "R072":{
        "design_winner_max_mae_atr_raw":envelope_raw,
        "design_winner_envelope_E_atr":E,
        "catastrophe_candidates_atr":vals,
        "selected_research_candidate":selected,
        "selection_reason":reason,
      }
    }
    (OUT/"RISK_FOLLOWUP_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")

    print("\n=== POC TEMPORAL HORIZONS ===")
    print(ps.round(4).to_string(index=False))
    print("\n=== R072 CATASTROPHE STOPS ===")
    cols=["candidate","design_trades","design_expectancy_usd","design_profit_factor",
          "validation_trades","validation_expectancy_usd","validation_profit_factor",
          "validation_stress_expectancy_usd","validation_max_drawdown_usd",
          "validation_worst_trade_usd","validation_positive_semesters",
          "validation_dd_improvement_pct","validation_worst_trade_improvement_pct",
          "validation_pnl_reduction_pct","passes_gate"]
    print(rs[[c for c in cols if c in rs.columns]].round(4).to_string(index=False))
    print("\n=== REPORT ===")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
