#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import (
    load_development, build_signal_trades, add_periods, period_table, regime_breakdown, STRESS_COST
)
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.archive.B13.b13_high_directional_triggers import block_features
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

OUT=ROOT/"results/fixed_base_path_p1c"
WICK=0.50
CUTOFF=660
H=30

def loss_concentration(t):
    pnl=t[f"net_pnl_{H}"]
    losses=(-pnl[pnl<0]).sort_values(ascending=False)
    total=float(losses.sum())
    out={"losing_trades":int(len(losses)),"total_losses_usd":total}
    for n in (1,3,5):
        share=float(losses.head(n).sum()/total) if total>0 else np.nan
        out[f"worst_{n}_loss_share"]=share
    return out

def quantiles(t,label):
    if t.empty: return []
    x=t.copy()
    x["mae_block_ratio"]=x["mae30_points"]/x["block_range_points"]
    x["mfe_block_ratio"]=x["mfe30_points"]/x["block_range_points"]
    rows=[]
    for metric in ["mae30_points","mfe30_points","mae30_usd","mfe30_usd","mae_block_ratio","mfe_block_ratio"]:
        s=x[metric].replace([np.inf,-np.inf],np.nan).dropna()
        if s.empty: continue
        q=s.quantile([.10,.25,.50,.75,.90,.95]).to_dict()
        rows.append({"sample":label,"metric":metric,"n":int(len(s)),
                     "q10":float(q[.10]),"q25":float(q[.25]),"q50":float(q[.50]),
                     "q75":float(q[.75]),"q90":float(q[.90]),"q95":float(q[.95])})
    return rows

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    sessions=build_session_outputs(raw)
    t=build_signal_trades(feats,groups,WICK,CUTOFF)
    if t.empty: raise ValueError("no fixed-base trades")
    if pd.to_datetime(t.session_date).dt.year.max()>2025: raise ValueError("2026 leak")
    t["selected_net_pnl"]=t[f"net_pnl_{H}"]
    t["selected_stress_pnl"]=t[f"gross_pnl_{H}"]-STRESS_COST
    t=add_periods(t)
    t["mae_block_ratio"]=t["mae30_points"]/t["block_range_points"]
    t["mfe_block_ratio"]=t["mfe30_points"]/t["block_range_points"]

    OUT.mkdir(parents=True,exist_ok=True)
    t.to_parquet(OUT/"P1C_FIXED_BASE_TRADES.parquet",index=False)

    for period,name in [("week","WEEKLY_DIAGNOSTIC"),("month","MONTHLY_DIAGNOSTIC"),
                        ("quarter","QUARTERLY_EVALUATION"),("semester","SEMESTER_EVALUATION"),
                        ("year_eval","YEARLY_ROBUSTNESS")]:
        period_table(t,"selected_net_pnl",period).to_csv(OUT/f"P1C_{name}.csv",index=False)
    regime_breakdown(t,sessions,"selected_net_pnl").to_csv(OUT/"P1C_REGIME_EXPLANATION.csv",index=False)

    qrows=[]
    qrows += quantiles(t,"ALL")
    qrows += quantiles(t[t.selected_net_pnl>0],"WINNERS")
    qrows += quantiles(t[t.selected_net_pnl<=0],"LOSERS")
    qrows += quantiles(t[t.year_eval==2025],"2025_ALL")
    qrows += quantiles(t[(t.year_eval==2025)&(t.selected_net_pnl<=0)],"2025_LOSERS")
    pd.DataFrame(qrows).to_csv(OUT/"P1C_PATH_QUANTILES.csv",index=False)

    worst=t.nsmallest(15,"selected_net_pnl")[[
        "session_date","entry_clock_et","side","block_range_points","mae30_points","mfe30_points",
        "mae_block_ratio","mfe_block_ratio","selected_net_pnl"
    ]]
    worst.to_csv(OUT/"P1C_WORST_TRADES.csv",index=False)

    overall_loss=loss_concentration(t)
    loss_2025=loss_concentration(t[t.year_eval==2025])
    pnl=t.selected_net_pnl
    stress=t.selected_stress_pnl
    byyear=period_table(t,"selected_net_pnl","year_eval")
    report={
        "authority":"DIAGNOSTIC_ONLY_FIXED_SIGNAL_BASE",
        "contract_2026_opened":False,
        "fixed_base":"W0.50_C1100_H30",
        "trades":int(len(t)),
        "net_pnl_usd":float(pnl.sum()),
        "expectancy_usd":float(pnl.mean()),
        "stress_expectancy_usd":float(stress.mean()),
        "profit_factor":float(profit_factor(pnl)),
        "years_positive":int(byyear.positive.sum()),
        "overall_loss_concentration":overall_loss,
        "y2025_loss_concentration":loss_2025,
    }
    (OUT/"P1C_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
