#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, add_periods
from research.archive.B12.b12_strategy_architecture import prepare_rth, trade_from_signal, profit_factor, max_drawdown
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

OUT=ROOT/"results/poc_breakdown_reconstruction"
TICK=0.25
CUTOFF=11*60+30
H=15
STRESS_COST=6.57

def bin_tick(x: float) -> float:
    return round(np.floor(x/TICK+0.5)*TICK,2)

def session_poc(g: pd.DataFrame) -> float:
    x=g.copy()
    x["typical"]=(x["high"]+x["low"]+x["close"])/3.0
    x["price_bin"]=x["typical"].map(bin_tick)
    vp=x.groupby("price_bin",observed=True)["volume"].sum()
    if vp.empty: return np.nan
    mx=vp.max()
    tied=vp[vp==mx].index.to_numpy(float)
    if len(tied)==1: return float(tied[0])
    # Historical tie-break was not documented. Use nearest to volume-weighted
    # profile mean only to make the reconstruction deterministic.
    center=float(np.average(vp.index.to_numpy(float),weights=vp.to_numpy(float)))
    return float(tied[np.argmin(np.abs(tied-center))])

def build_levels(groups):
    rows=[]
    for key,g in groups.items():
        rows.append({
          "group_key":key,"session_date":g.session_date.iloc[0],"year":int(g.year.iloc[0]),
          "contract":str(g.contract.iloc[0]),"first_ts":g.timestamp_et.iloc[0],
          "rth_open":float(g.open.iloc[0]),"poc":session_poc(g)
        })
    d=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    d["prev_poc"]=d.poc.shift(1)
    d["prev_contract"]=d.contract.shift(1)
    d["prev_poc"]=d.prev_poc.where(d.contract.eq(d.prev_contract))
    return d

def build_events(groups,levels):
    ctx=levels.set_index("group_key")
    rows=[]
    for key,g in groups.items():
        if key not in ctx.index: continue
        c=ctx.loc[key]
        if not np.isfinite(c.prev_poc): continue
        poc=float(c.prev_poc)
        g=g.sort_values("timestamp_et").reset_index(drop=True)
        op=float(g.iloc[0].open)
        if not (op>poc): continue
        window=g[g.minute<=CUTOFF]
        touches=window[window.low<=poc]
        if touches.empty: continue
        pos=int(touches.index[0])
        contact=g.iloc[pos]
        # Exact historical hypothesis: the FIRST test must close below POC.
        if not (float(contact.close)<poc): continue
        tr=trade_from_signal(g,pos,-1)
        if tr is None: continue
        row={
          "group_key":key,"session_date":str(c.session_date),"year":int(c.year),"contract":str(c.contract),
          "prev_poc":poc,"rth_open":op,"open_distance_points":op-poc,
          "contact_ts":contact.timestamp_et,"contact_minute":int(contact.minute),
          "contact_open":float(contact.open),"contact_high":float(contact.high),"contact_low":float(contact.low),
          "contact_close":float(contact.close),"direction":-1,"side":"SHORT",**tr
        }
        row["stress_net_pnl_15"]=row["gross_pnl_15"]-STRESS_COST
        rows.append(row)
    return pd.DataFrame(rows).sort_values("contact_ts").reset_index(drop=True)

def metrics(g):
    if g.empty:
        return dict(trades=0,net_pnl_usd=0.0,expectancy_usd=np.nan,profit_factor=np.nan,
                    stress_expectancy_usd=np.nan,win_rate=np.nan,max_drawdown_usd=np.nan,
                    mean_directional_bps=np.nan)
    p=g.net_pnl_15
    # Gross short return from entry to 15m exit, in bps.
    bps=(-1)*(g.exit_price_15/g.entry_price-1.0)*10000.0
    return dict(
      trades=int(len(g)),net_pnl_usd=float(p.sum()),expectancy_usd=float(p.mean()),
      profit_factor=float(profit_factor(p)),stress_expectancy_usd=float(g.stress_net_pnl_15.mean()),
      win_rate=float((p>0).mean()),max_drawdown_usd=float(max_drawdown(p)),
      mean_directional_bps=float(bps.mean())
    )

def period_table(t,col):
    return pd.DataFrame([{col:key,**metrics(g)} for key,g in t.groupby(col,sort=True,observed=True)])

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    levels=build_levels(groups)
    t=build_events(groups,levels)
    if t.empty: raise ValueError("no POC breakdown events")
    if t.year.max()>2025: raise ValueError("2026 leak")
    t=add_periods(t)
    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"POC_BREAKDOWN_TRADES.csv",index=False)
    for col,name in [("week","WEEKLY"),("month","MONTHLY"),("quarter","QUARTERLY"),
                     ("semester","SEMESTER"),("year_eval","YEARLY")]:
        period_table(t,col).to_csv(OUT/f"POC_{name}.csv",index=False)

    # Timing sanity check versus historical notes.
    def bucket(m):
        if m<=600: return "09:30-10:00"
        if m<=630: return "10:00-10:30"
        return "10:30-11:30"
    t["time_bucket"]=t.contact_minute.map(bucket)
    period_table(t,"time_bucket").to_csv(OUT/"POC_TIME_BUCKET.csv",index=False)

    # Fixed 6m/12m rolling diagnostics.
    t["date"]=pd.to_datetime(t.session_date)
    ends=pd.date_range(t.date.min().to_period("M").to_timestamp("M"),
                       t.date.max().to_period("M").to_timestamp("M"),freq="ME")
    rr=[]
    for months in (6,12):
        for end in ends:
            start=(end-pd.DateOffset(months=months))+pd.Timedelta(days=1)
            g=t[(t.date>=start)&(t.date<=end)]
            if len(g):
                rr.append({"window_months":months,"window_start":start.date().isoformat(),
                           "window_end":end.date().isoformat(),**metrics(g)})
    pd.DataFrame(rr).to_csv(OUT/"POC_ROLLING_CALENDAR.csv",index=False)

    # Causal regime explanation only.
    sessions=build_session_outputs(raw)
    cols=["group_key","preopen_prediction","update_prediction","prev_state","overnight_state",
          "five_day_state_label","preopen_support","open15_support"]
    sx=sessions[[c for c in cols if c in sessions.columns]].drop_duplicates("group_key")
    tx=t.merge(sx,on="group_key",how="left",validate="many_to_one")
    for cc in ("prev_state","overnight_state"):
        if cc in tx:
            tx[cc]=tx[cc].map({-1.0:"LOW",0.0:"NORMAL",1.0:"HIGH"}).fillna("UNKNOWN")
    reg=[]
    for dim in [c for c in cols if c!="group_key" and c in tx]:
        for val,g in tx.groupby(dim,dropna=False,observed=True):
            reg.append({"dimension":dim,"category":"MISSING" if pd.isna(val) else str(val),**metrics(g)})
    pd.DataFrame(reg).to_csv(OUT/"POC_REGIME_EXPLANATION.csv",index=False)

    dev=t[t.year<=2024]; y25=t[t.year==2025]
    report={
      "authority":"RECONSTRUCTION_NEAR_HISTORICAL_SPEC",
      "reason":"Historical POC proxy is recovered; only equal-volume POC tie-break was undocumented and is deterministically reconstructed.",
      "contract_2026_opened":False,
      "fixed_rules":{
        "poc":"prior RTH 1m typical-price HLC3 bins at 0.25, volume summed by bin",
        "setup":"current RTH open > prior POC; FIRST bar touching POC must close below POC",
        "entry":"next 1m open",
        "direction":"SHORT",
        "exit":"15-minute fixed time exit",
        "base_cost_rt_usd":4.38,
        "stress_cost_rt_usd":6.57
      },
      "2020_2024":metrics(dev),"2025":metrics(y25),"full_2020_2025":metrics(t),
      "historical_reference":{"events_2020_2024_approx":95,"gross_mean_directional_bps_2020_2024":4.08}
    }
    (OUT/"POC_RECON_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("\nYEARLY\n",period_table(t,"year_eval").to_string(index=False))
    print("\nSEMESTER\n",period_table(t,"semester").to_string(index=False))
    print("\nTIME\n",period_table(t,"time_bucket").to_string(index=False))

if __name__=="__main__":
    main()
