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

OUT=ROOT/"results/r072_news_policy"
NEWS=ROOT/"data_external/forexfactory/usd_high_medium_2020_2025.csv"
BASE_COST=4.38
STRESS_COST=6.57
POINT_VALUE=5.0
WICK=0.50
CUTOFF=660
H=30

def dd_mag(p):
    if len(p)==0:return np.nan
    eq=p.cumsum(); peak=eq.cummax().clip(lower=0)
    return float(-(eq-peak).min())

def load_news():
    n=pd.read_csv(NEWS)
    for c in ["event_et","blackout_start_et","blackout_end_et"]:
        n[c]=pd.to_datetime(n[c],utc=True).dt.tz_convert("America/New_York")
    n["date_et"]=n.event_et.dt.date.astype(str)
    return {d:g.sort_values("event_et").reset_index(drop=True) for d,g in n.groupby("date_et")}

def blocked(entry_actual,nd):
    if nd is None or nd.empty:return False
    return bool(((nd.blackout_start_et<=entry_actual)&(entry_actual<=nd.blackout_end_et)).any())

def forced_event(entry_actual,exit_label,nd):
    if nd is None or nd.empty:return None
    z=nd[(nd.blackout_start_et>entry_actual)&((nd.blackout_start_et+pd.Timedelta(minutes=1))<=exit_label)]
    if z.empty:return None
    return z.iloc[0]

def simulate(br,g,use_news,nd):
    direction=int(br.direction)
    entry=float(br.entry_price)
    entry_label=pd.Timestamp(br.entry_bar_ts)
    entry_actual=entry_label-pd.Timedelta(minutes=1)
    exit_label=pd.Timestamp(getattr(br,f"exit_ts_{H}"))

    if use_news and blocked(entry_actual,nd):
        return {"blocked":True}

    fe=forced_event(entry_actual,exit_label,nd) if use_news else None
    if fe is not None:
        label=fe.blackout_start_et+pd.Timedelta(minutes=1)
        m=g.index[g.timestamp_et==label].tolist()
        if m:
            b=g.loc[m[0]]
            exit_px=float(b.open); exit_ts=b.timestamp_et; reason="NEWS_EXIT"
        else:
            exit_px=float(getattr(br,f"exit_price_{H}")); exit_ts=exit_label; reason="TIME30"
    else:
        exit_px=float(getattr(br,f"exit_price_{H}")); exit_ts=exit_label; reason="TIME30"

    gross_points=direction*(exit_px-entry)
    dt=entry_actual
    return {
      "blocked":False,"group_key":br.group_key,"session_date":br.session_date,"year":int(br.year),
      "quarter":dt.tz_localize(None).to_period("Q").strftime("%YQ%q"),
      "semester":f"{int(br.year)}H{1 if dt.month<=6 else 2}",
      "month":dt.strftime("%Y-%m"),"week":f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}",
      "direction":direction,"side":br.side,"entry_actual_et":entry_actual,"entry_label_et":entry_label,
      "entry_price":entry,"exit_ts":exit_ts,"exit_price":exit_px,"exit_reason":reason,
      "gross_points":gross_points,
      "net_pnl_usd":gross_points*POINT_VALUE-BASE_COST,
      "stress_net_pnl_usd":gross_points*POINT_VALUE-STRESS_COST,
      "news_event":None if fe is None else str(fe.event),
      "news_impact":None if fe is None else str(fe.impact),
    }

def metrics(g):
    if len(g)==0:return {}
    p=g.net_pnl_usd; s=g.stress_net_pnl_usd
    sem=g.groupby("semester").net_pnl_usd.sum()
    return {
      "trades":int(len(g)),"trades_per_month":float(len(g)/72),
      "news_exit_rate":float((g.exit_reason=="NEWS_EXIT").mean()),
      "net_pnl_usd":float(p.sum()),"expectancy_usd":float(p.mean()),
      "profit_factor":float(profit_factor(p)),"stress_expectancy_usd":float(s.mean()),
      "win_rate":float((p>0).mean()),"max_drawdown_usd":dd_mag(p),
      "positive_semesters":int((sem>0).sum()),"semesters_observed":int(len(sem)),
      "worst_trade_usd":float(p.min()),"p05_trade_usd":float(p.quantile(.05)),
    }

def period_table(g,col):
    return pd.DataFrame([{col:k,**metrics(x.sort_values("entry_actual_et"))}
                         for k,x in g.groupby(col,sort=True,observed=True)])

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    base=build_signal_trades(feats,groups,WICK,CUTOFF).copy()
    if base.empty:raise ValueError("no R072 trades")
    if base.year.max()>2025:raise ValueError("2026 leak")
    news=load_news()

    rows=[]; blocks=[]
    for variant,use_news in [("R072_BASE",False),("R072_NEWS",True)]:
        nb=0
        for br in base.itertuples(index=False):
            g=groups.get(br.group_key)
            z=simulate(br,g,use_news,news.get(str(br.session_date)))
            if z is None:continue
            if z.get("blocked"):
                nb+=1;continue
            z["variant"]=variant;rows.append(z)
        blocks.append({"variant":variant,"blocked_entries":nb})

    tr=pd.DataFrame(rows).sort_values(["variant","entry_actual_et"]).reset_index(drop=True)
    OUT.mkdir(parents=True,exist_ok=True)
    tr.to_csv(OUT/"R072_NEWS_TRADES.csv",index=False)
    pd.DataFrame(blocks).to_csv(OUT/"R072_NEWS_BLOCKED.csv",index=False)

    summary=[]
    for v in ["R072_BASE","R072_NEWS"]:
        g=tr[tr.variant==v].sort_values("entry_actual_et")
        summary.append({"variant":v,**metrics(g)})
        for col,name in [("week","WEEKLY"),("month","MONTHLY"),("quarter","QUARTERLY"),
                         ("semester","SEMESTER"),("year","YEARLY")]:
            period_table(g,col).to_csv(OUT/f"{v}_{name}.csv",index=False)
    summary=pd.DataFrame(summary)
    summary.to_csv(OUT/"R072_NEWS_SUMMARY.csv",index=False)

    print("\n=== R072 NEWS POLICY ===")
    print(summary.round(4).to_string(index=False))
    print("\n=== BLOCKED ===")
    print(pd.DataFrame(blocks).to_string(index=False))
    print("\n=== R072 NEWS YEARLY ===")
    print(period_table(tr[tr.variant=="R072_NEWS"],"year").round(4).to_string(index=False))

    report={"authority":"ARCHITECTURE_CHARACTERIZATION_NOT_INDEPENDENT_VALIDATION",
            "contract_2026_opened":False,
            "base":summary[summary.variant=="R072_BASE"].iloc[0].to_dict(),
            "news":summary[summary.variant=="R072_NEWS"].iloc[0].to_dict()}
    (OUT/"R072_NEWS_REPORT.json").write_text(json.dumps(report,indent=2,default=str)+"\n")

if __name__=="__main__":
    main()
