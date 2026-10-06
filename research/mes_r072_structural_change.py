#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, build_signal_trades
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.archive.B13.b13_high_directional_triggers import block_features

OUT=ROOT/"results/r072_structural_change"
WICK=0.50
CUTOFF=660
H=30
COST=4.38
STRESS=6.57

def metrics(g: pd.DataFrame) -> dict:
    if g.empty:
        return {"trades":0,"net_pnl_usd":0.0,"expectancy_usd":np.nan,"profit_factor":np.nan,
                "stress_expectancy_usd":np.nan,"win_rate":np.nan}
    pnl=g[f"net_pnl_{H}"]
    gross=g[f"gross_pnl_{H}"]
    return {
        "trades":int(len(g)),
        "net_pnl_usd":float(pnl.sum()),
        "expectancy_usd":float(pnl.mean()),
        "profit_factor":float(profit_factor(pnl)),
        "stress_expectancy_usd":float((gross-STRESS).mean()),
        "win_rate":float((pnl>0).mean()),
    }

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    t=build_signal_trades(feats,groups,WICK,CUTOFF).copy()
    if t.empty: raise ValueError("no R072 trades")
    t["date"]=pd.to_datetime(t["session_date"])
    if t["date"].dt.year.max()>2025: raise ValueError("2026 leak")
    t=t.sort_values("date").reset_index(drop=True)
    t["trade_no"]=np.arange(1,len(t)+1)
    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"R072_TRADES.csv",index=False)

    # Fixed calendar rolling windows. Window endpoints are calendar month ends.
    month_ends=pd.date_range(t.date.min().to_period("M").to_timestamp("M"),
                             t.date.max().to_period("M").to_timestamp("M"),freq="ME")
    rows=[]
    for months in (6,12):
        for end in month_ends:
            start=(end-pd.DateOffset(months=months))+pd.Timedelta(days=1)
            g=t[(t.date>=start)&(t.date<=end)]
            if len(g)==0: continue
            rows.append({"window_months":months,"window_start":start.date().isoformat(),
                         "window_end":end.date().isoformat(),**metrics(g)})
    pd.DataFrame(rows).to_csv(OUT/"R072_ROLLING_CALENDAR.csv",index=False)

    # Fixed trade-count rolling windows.
    trrows=[]
    for n in (20,40):
        if len(t)<n: continue
        for i in range(n-1,len(t)):
            g=t.iloc[i-n+1:i+1]
            trrows.append({"window_trades":n,"start_trade_no":int(g.trade_no.iloc[0]),
                           "end_trade_no":int(g.trade_no.iloc[-1]),
                           "window_start":g.date.iloc[0].date().isoformat(),
                           "window_end":g.date.iloc[-1].date().isoformat(),**metrics(g)})
    pd.DataFrame(trrows).to_csv(OUT/"R072_ROLLING_TRADES.csv",index=False)

    # Quarter chronology (evaluation horizon, not a selection rule).
    q=t.assign(quarter=t.date.dt.to_period("Q").astype(str))
    qrows=[]
    for key,g in q.groupby("quarter",sort=True):
        qrows.append({"quarter":key,**metrics(g)})
    qdf=pd.DataFrame(qrows)
    qdf.to_csv(OUT/"R072_QUARTER_CHRONOLOGY.csv",index=False)

    # Expanding path, updated every 10 trades, descriptive.
    erows=[]
    for end_n in range(20,len(t)+1,10):
        g=t.iloc[:end_n]
        erows.append({"through_trade":end_n,"through_date":g.date.iloc[-1].date().isoformat(),**metrics(g)})
    if erows[-1]["through_trade"] != len(t):
        g=t.copy()
        erows.append({"through_trade":len(t),"through_date":g.date.iloc[-1].date().isoformat(),**metrics(g)})
    pd.DataFrame(erows).to_csv(OUT/"R072_EXPANDING.csv",index=False)

    # Descriptive single-break scan. It is NOT a strategy filter or validation test.
    # Require >=30 trades on both sides; score by absolute standardized mean difference.
    pnl=t[f"net_pnl_{H}"].to_numpy(float)
    scans=[]
    for k in range(30,len(t)-29):
        a=pnl[:k]; b=pnl[k:]
        va=np.var(a,ddof=1); vb=np.var(b,ddof=1)
        pooled=np.sqrt(((len(a)-1)*va+(len(b)-1)*vb)/(len(a)+len(b)-2)) if len(a)+len(b)>2 else np.nan
        d=(np.mean(b)-np.mean(a))/pooled if pooled and np.isfinite(pooled) and pooled>0 else np.nan
        scans.append({
          "split_after_trade":k,
          "split_date":t.date.iloc[k-1].date().isoformat(),
          "left_trades":len(a),"right_trades":len(b),
          "left_expectancy_usd":float(np.mean(a)),
          "right_expectancy_usd":float(np.mean(b)),
          "difference_usd":float(np.mean(b)-np.mean(a)),
          "standardized_difference":float(d) if np.isfinite(d) else np.nan,
        })
    sdf=pd.DataFrame(scans)
    sdf.to_csv(OUT/"R072_CHANGEPOINT_SCAN.csv",index=False)
    best=sdf.iloc[sdf.standardized_difference.abs().idxmax()].to_dict() if len(sdf) else {}

    # Predefined recent-period comparison, not selected from scan.
    pre=t[t.date.dt.year<=2024]
    y25=t[t.date.dt.year==2025]
    report={
      "authority":"DIAGNOSTIC_ONLY_NO_RETROSPECTIVE_FILTER_SELECTION",
      "contract_2026_opened":False,
      "fixed_signal":"W0.50_C1100_H30",
      "full":metrics(t),
      "through_2024":metrics(pre),
      "year_2025":metrics(y25),
      "descriptive_largest_single_break":best,
      "interpretation_rule":"Rolling/change-point outputs may diagnose deterioration but cannot define a retrospective live filter."
    }
    (OUT/"R072_STRUCTURAL_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
