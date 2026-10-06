#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.mes_poc_breakdown_reconstruction import build_levels, build_events

OUT=ROOT/"results/poc_complete_candidate"
NEWS=ROOT/"data_external/forexfactory/usd_high_medium_2020_2025.csv"
BASE_COST=4.38
STRESS_COST=6.57
POINT_VALUE=5.0

def dd_mag(pnl):
    if len(pnl)==0: return np.nan
    eq=pnl.cumsum()
    peak=eq.cummax().clip(lower=0)
    return float(-(eq-peak).min())

def load_news():
    n=pd.read_csv(NEWS)
    for c in ["event_et","blackout_start_et","blackout_end_et"]:
        n[c]=pd.to_datetime(n[c],utc=True).dt.tz_convert("America/New_York")
    n["date_et"]=n.event_et.dt.date.astype(str)
    return {d:g.sort_values("event_et").reset_index(drop=True) for d,g in n.groupby("date_et")}

def blocked(entry_actual,nd):
    if nd is None or nd.empty: return False
    return bool(((nd.blackout_start_et<=entry_actual)&(entry_actual<=nd.blackout_end_et)).any())

def next_cutoff(entry_actual,scheduled_exit_label,nd):
    if nd is None or nd.empty: return None
    z=nd[(nd.blackout_start_et>entry_actual)&((nd.blackout_start_et+pd.Timedelta(minutes=1))<=scheduled_exit_label)]
    if z.empty: return None
    return z.iloc[0]

def simulate(br,g,use_news,nd):
    entry_label=pd.Timestamp(br.entry_bar_ts)
    entry_actual=entry_label-pd.Timedelta(minutes=1)
    scheduled_exit_label=pd.Timestamp(br.exit_ts_15)
    entry=float(br.entry_price)
    if use_news and blocked(entry_actual,nd):
        return {"blocked":True}

    forced=next_cutoff(entry_actual,scheduled_exit_label,nd) if use_news else None
    if forced is not None:
        label=forced.blackout_start_et+pd.Timedelta(minutes=1)
        m=g.index[g.timestamp_et==label].tolist()
        if m:
            b=g.loc[m[0]]
            exit_px=float(b.open)
            exit_ts=b.timestamp_et
            reason="NEWS_EXIT"
        else:
            exit_px=float(br.exit_price_15)
            exit_ts=scheduled_exit_label
            reason="TIME15"
    else:
        exit_px=float(br.exit_price_15)
        exit_ts=scheduled_exit_label
        reason="TIME15"

    gross_points=-(exit_px-entry)  # short
    dt=entry_actual
    return {
      "blocked":False,
      "group_key":br.group_key,"session_date":br.session_date,"year":int(br.year),
      "quarter":dt.tz_localize(None).to_period("Q").strftime("%YQ%q"),
      "semester":f"{int(br.year)}H{1 if dt.month<=6 else 2}",
      "month":dt.strftime("%Y-%m"),"week":f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}",
      "entry_actual_et":entry_actual,"entry_label_et":entry_label,"entry_price":entry,
      "prev_poc":float(br.prev_poc),"exit_ts":exit_ts,"exit_price":exit_px,
      "exit_reason":reason,
      "gross_points":gross_points,
      "net_pnl_usd":gross_points*POINT_VALUE-BASE_COST,
      "stress_net_pnl_usd":gross_points*POINT_VALUE-STRESS_COST,
      "news_event":None if forced is None else str(forced.event),
      "news_impact":None if forced is None else str(forced.impact),
    }

def metrics(g):
    if len(g)==0: return {}
    p=g.net_pnl_usd; s=g.stress_net_pnl_usd
    sem=g.groupby("semester").net_pnl_usd.sum()
    return {
      "trades":int(len(g)),"trades_per_month":float(len(g)/72.0),
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
    levels=build_levels(groups)
    base=build_events(groups,levels)
    if base.empty: raise ValueError("no POC events")
    if base.year.max()>2025: raise ValueError("2026 leak")
    news=load_news()

    rows=[]; blocked_rows=[]
    for variant,use_news in [("POC_BASE",False),("POC_NEWS",True)]:
        nblock=0
        for br in base.itertuples(index=False):
            g=groups.get(br.group_key)
            z=simulate(br,g,use_news,news.get(str(br.session_date)))
            if z is None: continue
            if z.get("blocked"):
                nblock+=1; continue
            z["variant"]=variant
            rows.append(z)
        blocked_rows.append({"variant":variant,"blocked_entries":nblock})

    tr=pd.DataFrame(rows).sort_values(["variant","entry_actual_et"]).reset_index(drop=True)
    OUT.mkdir(parents=True,exist_ok=True)
    tr.to_csv(OUT/"POC_COMPLETE_TRADES.csv",index=False)
    pd.DataFrame(blocked_rows).to_csv(OUT/"POC_COMPLETE_BLOCKED.csv",index=False)

    summary=[]
    for v in ["POC_BASE","POC_NEWS"]:
        g=tr[tr.variant==v].sort_values("entry_actual_et")
        summary.append({"variant":v,**metrics(g)})
        for col,name in [("week","WEEKLY"),("month","MONTHLY"),("quarter","QUARTERLY"),
                         ("semester","SEMESTER"),("year","YEARLY")]:
            period_table(g,col).to_csv(OUT/f"{v}_{name}.csv",index=False)
    summary=pd.DataFrame(summary)
    summary.to_csv(OUT/"POC_COMPLETE_SUMMARY.csv",index=False)

    print("\n=== POC VARIANTS ===")
    print(summary.round(4).to_string(index=False))
    print("\n=== BLOCKED ===")
    print(pd.DataFrame(blocked_rows).to_string(index=False))
    print("\n=== POC NEWS YEARLY ===")
    print(period_table(tr[tr.variant=="POC_NEWS"],"year").round(4).to_string(index=False))

    report={
      "authority":"ARCHITECTURE_CHARACTERIZATION_NOT_INDEPENDENT_VALIDATION",
      "contract_2026_opened":False,
      "base":summary[summary.variant=="POC_BASE"].iloc[0].to_dict(),
      "news":summary[summary.variant=="POC_NEWS"].iloc[0].to_dict(),
    }
    (OUT/"POC_COMPLETE_REPORT.json").write_text(json.dumps(report,indent=2,default=str)+"\n")

if __name__=="__main__":
    main()
