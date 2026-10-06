#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, add_periods
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor, max_drawdown
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs

OUT=ROOT/"results/pdc_small_gap_reconstruction"
ATR_N=14
GAP_LO=0.10
GAP_HI=0.20
TARGET_CUTOFF=11*60+30
COST_POINTS=4.38/5.0
STRESS_COST_POINTS=6.57/5.0

def wilder_atr(tr: pd.Series, n:int=14) -> pd.Series:
    x=tr.to_numpy(float)
    out=np.full(len(x),np.nan,float)
    valid=np.where(np.isfinite(x))[0]
    if len(valid)<n: return pd.Series(out,index=tr.index)
    # data here is contiguous; seed on first n observations
    seed_end=n-1
    out[seed_end]=np.mean(x[:n])
    for i in range(seed_end+1,len(x)):
        if not np.isfinite(x[i]) or not np.isfinite(out[i-1]):
            out[i]=np.nan
        else:
            out[i]=(out[i-1]*(n-1)+x[i])/n
    return pd.Series(out,index=tr.index)

def daily_context(groups):
    rows=[]
    for key,g in groups.items():
        g=g.sort_values("timestamp_et")
        rows.append({
          "group_key":key,
          "session_date":g.session_date.iloc[0],
          "year":int(g.year.iloc[0]),
          "contract":str(g.contract.iloc[0]),
          "first_ts":g.timestamp_et.iloc[0],
          "rth_open":float(g.open.iloc[0]),
          "rth_high":float(g.high.max()),
          "rth_low":float(g.low.min()),
          "rth_close":float(g.close.iloc[-1]),
        })
    d=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    d["prev_close"]=d.rth_close.shift(1)
    d["prev_contract"]=d.contract.shift(1)
    same=d.contract.eq(d.prev_contract)
    tr1=d.rth_high-d.rth_low
    tr2=(d.rth_high-d.prev_close).abs()
    tr3=(d.rth_low-d.prev_close).abs()
    d["true_range"]=np.where(same,np.maximum(tr1,np.maximum(tr2,tr3)),tr1)
    d["atr14_close"]=wilder_atr(d.true_range,ATR_N)
    # Causal ATR available before today's open.
    d["atr14_prev"]=d.atr14_close.shift(1)
    d["pdc"]=d.prev_close.where(same)
    return d

def build_events(groups,daily):
    ctx=daily.set_index("group_key")
    rows=[]
    for key,g in groups.items():
        if key not in ctx.index: continue
        c=ctx.loc[key]
        if not np.isfinite(c.pdc) or not np.isfinite(c.atr14_prev) or c.atr14_prev<=0:
            continue
        if int(c.year)>2025: continue
        g=g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g)<6: continue
        op=float(g.iloc[0].open)
        pdc=float(c.pdc)
        gap=op-pdc
        if gap==0: continue
        ratio=abs(gap)/float(c.atr14_prev)
        if not (GAP_LO <= ratio < GAP_HI): continue
        direction=-1 if gap>0 else 1
        first5=g.iloc[:5]
        # Target must remain untouched during first five minutes.
        untouched=(float(first5.low.min())>pdc) if direction==-1 else (float(first5.high.max())<pdc)
        if not untouched: continue
        close5=float(first5.iloc[-1].close)
        toward=(close5<op) if direction==-1 else (close5>op)
        if not toward: continue

        entry_bar=g.iloc[5]
        entry=float(entry_bar.open)
        # If PDC was crossed at the boundary before the entry can be established,
        # do not count a trade.
        if (direction==-1 and entry<=pdc) or (direction==1 and entry>=pdc):
            continue

        eligible=g[(g.minute>=int(entry_bar.minute))&(g.minute<=TARGET_CUTOFF)].copy()
        hit=False; exit_px=np.nan; exit_ts=pd.NaT; reason="TIME_1130"
        for _,b in eligible.iterrows():
            if direction==-1 and float(b.low)<=pdc:
                hit=True; exit_px=pdc; exit_ts=b.timestamp_et; reason="PDC"; break
            if direction==1 and float(b.high)>=pdc:
                hit=True; exit_px=pdc; exit_ts=b.timestamp_et; reason="PDC"; break
        if not hit:
            if eligible.empty: continue
            b=eligible.iloc[-1]
            exit_px=float(b.close); exit_ts=b.timestamp_et
        gross_points=direction*(exit_px-entry)
        rows.append({
          "group_key":key,"session_date":str(c.session_date),"year":int(c.year),"contract":str(c.contract),
          "rth_open":op,"pdc":pdc,"atr14_prev":float(c.atr14_prev),"gap_points":float(gap),
          "gap_atr":float(ratio),"direction":direction,"side":"SHORT" if direction==-1 else "LONG",
          "first5_close":close5,"entry_ts":entry_bar.timestamp_et,"entry_price":entry,
          "exit_ts":exit_ts,"exit_price":float(exit_px),"exit_reason":reason,"target_hit":bool(hit),
          "gross_points":float(gross_points),
          "net_points":float(gross_points-COST_POINTS),
          "stress_net_points":float(gross_points-STRESS_COST_POINTS),
          "net_pnl_usd":float((gross_points-COST_POINTS)*5.0),
          "stress_net_pnl_usd":float((gross_points-STRESS_COST_POINTS)*5.0),
        })
    return pd.DataFrame(rows).sort_values("entry_ts").reset_index(drop=True)

def metrics(g):
    if g.empty:
        return dict(trades=0,target_hit_rate=np.nan,net_pnl_usd=0.0,expectancy_usd=np.nan,
                    expectancy_points=np.nan,profit_factor=np.nan,stress_expectancy_usd=np.nan,
                    win_rate=np.nan,max_drawdown_usd=np.nan)
    p=g.net_pnl_usd
    return dict(
      trades=int(len(g)),target_hit_rate=float(g.target_hit.mean()),net_pnl_usd=float(p.sum()),
      expectancy_usd=float(p.mean()),expectancy_points=float(g.net_points.mean()),
      profit_factor=float(profit_factor(p)),stress_expectancy_usd=float(g.stress_net_pnl_usd.mean()),
      win_rate=float((p>0).mean()),max_drawdown_usd=float(max_drawdown(p))
    )

def period_table(t,col):
    rows=[]
    for key,g in t.groupby(col,sort=True,observed=True):
        rows.append({col:key,**metrics(g)})
    return pd.DataFrame(rows)

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    daily=daily_context(groups)
    t=build_events(groups,daily)
    if t.empty: raise ValueError("no PDC events")
    if t.year.max()>2025: raise ValueError("2026 leak")
    t=add_periods(t)
    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"PDC_RECON_TRADES.csv",index=False)

    for col,name in [("week","WEEKLY"),("month","MONTHLY"),("quarter","QUARTERLY"),
                     ("semester","SEMESTER"),("year_eval","YEARLY")]:
        period_table(t,col).to_csv(OUT/f"PDC_{name}.csv",index=False)

    # 6m / 12m rolling calendar diagnostics
    dates=pd.to_datetime(t.session_date)
    t["date"]=dates
    ends=pd.date_range(dates.min().to_period("M").to_timestamp("M"),
                       dates.max().to_period("M").to_timestamp("M"),freq="ME")
    rr=[]
    for months in (6,12):
        for end in ends:
            start=(end-pd.DateOffset(months=months))+pd.Timedelta(days=1)
            g=t[(t.date>=start)&(t.date<=end)]
            if len(g):
                rr.append({"window_months":months,"window_start":start.date().isoformat(),
                           "window_end":end.date().isoformat(),**metrics(g)})
    pd.DataFrame(rr).to_csv(OUT/"PDC_ROLLING_CALENDAR.csv",index=False)

    # Existing R063 context used only as explanation.
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
    pd.DataFrame(reg).to_csv(OUT/"PDC_REGIME_EXPLANATION.csv",index=False)

    dev=t[t.year<=2024]
    y25=t[t.year==2025]
    report={
      "authority":"RECONSTRUCTION_NOT_EXACT_HISTORICAL_REPLICATION",
      "reason":"Original PDC code/ATR implementation was not preserved; reconstruction uses causal Wilder ATR14 on completed RTH daily HLC, shifted one session.",
      "contract_2026_opened":False,
      "fixed_rules":{
        "gap_atr":"0.10 <= abs(RTH_open-PDC)/ATR14_prev < 0.20",
        "first5":"PDC untouched and 5-minute close moves toward PDC",
        "entry":"open of sixth RTH 1-minute bar (09:35 start / 09:36 EOB label)",
        "target":"PDC",
        "stop":"NONE",
        "time_exit":"11:30 ET",
        "base_cost_rt_usd":4.38,
        "stress_cost_rt_usd":6.57
      },
      "2020_2024":metrics(dev),
      "2025":metrics(y25),
      "full_2020_2025":metrics(t),
      "historical_reference":{"expected_event_count_2020_2024_approx":82,"historical_pdc_hit_rate_2020_2024":0.829}
    }
    (OUT/"PDC_RECON_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("\nYEARLY\n",period_table(t,"year_eval").to_string(index=False))
    print("\nSEMESTER\n",period_table(t,"semester").to_string(index=False))

if __name__=="__main__":
    main()
