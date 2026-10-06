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

OUT=ROOT/"results/or15_r1_temporal"
BASE_COST=4.38
STRESS_COST=6.57
POINT_VALUE=5.0
CUTOFF=11*60+30
ROLL=252
WARM=126

def dd_mag(p):
    if len(p)==0:return np.nan
    eq=p.cumsum(); peak=eq.cummax().clip(lower=0)
    return float(-(eq-peak).min())

def make_daily(groups):
    rows=[]
    for k,g in groups.items():
        g=g.sort_values("timestamp_et")
        rows.append({
            "group_key":k,
            "session_date":str(g.session_date.iloc[0]),
            "year":int(g.year.iloc[0]),
            "contract":str(g.contract.iloc[0]),
            "first_ts":g.timestamp_et.iloc[0],
            "high":float(g.high.max()),
            "low":float(g.low.min()),
            "close":float(g.close.iloc[-1]),
        })
    d=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    pc=d.close.shift(1)
    d["tr"]=pd.concat([(d.high-d.low),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    d["atr14"]=d.tr.rolling(14,min_periods=14).mean()
    d["vol_ratio"]=d.atr14/d.close
    dc=d.close.diff().abs()
    d["er10"]=(d.close-d.close.shift(10)).abs()/dc.rolling(10,min_periods=10).sum()

    # Thresholds available before today's open, built from prior completed sessions.
    d["vol_p67"]=d.vol_ratio.shift(1).rolling(ROLL,min_periods=WARM).quantile(.67)
    d["er_p33"]=d.er10.shift(1).rolling(ROLL,min_periods=WARM).quantile(.33)
    d["prev_vol_ratio"]=d.vol_ratio.shift(1)
    d["prev_er10"]=d.er10.shift(1)
    d["R1"]=(d.prev_vol_ratio>d.vol_p67)&(d.prev_er10>d.er_p33)
    return d

def signal(g):
    g=g.sort_values("timestamp_et").reset_index(drop=True)
    if len(g)<76:return None
    o=g.iloc[:15]
    if len(o)!=15:return None
    orh=float(o.high.max()); orl=float(o.low.min())
    for i in range(15,len(g)):
        b=g.iloc[i]
        if int(b.minute)>CUTOFF:break
        if float(b.close)>orh:
            if i+60>=len(g) or i+1>=len(g):return None
            # Exact continuous horizons.
            if g.iloc[i+60].timestamp_et-b.timestamp_et != pd.Timedelta(minutes=60):return None
            if g.iloc[i+30].timestamp_et-b.timestamp_et != pd.Timedelta(minutes=30):return None
            if g.iloc[i+15].timestamp_et-b.timestamp_et != pd.Timedelta(minutes=15):return None
            entry=g.iloc[i+1]
            return {
                "signal_idx":i,
                "signal_ts":b.timestamp_et,
                "signal_close":float(b.close),
                "or_high":orh,"or_low":orl,
                "entry_ts":entry.timestamp_et,
                "entry_price":float(entry.open),
                "exit15":float(g.iloc[i+15].close),
                "exit30":float(g.iloc[i+30].close),
                "exit60":float(g.iloc[i+60].close),
                "exit60_ts":g.iloc[i+60].timestamp_et,
            }
    return None

def build_events(groups,daily):
    r1=set(daily.loc[daily.R1,"group_key"])
    rows=[]
    for k in r1:
        g=groups.get(k)
        if g is None:continue
        s=signal(g)
        if s is None:continue
        meta=daily.loc[daily.group_key==k].iloc[0]
        sc=s["signal_close"]
        bps15=(s["exit15"]/sc-1)*10000
        bps30=(s["exit30"]/sc-1)*10000
        bps60=(s["exit60"]/sc-1)*10000
        gross_pts=s["exit60"]-s["entry_price"]
        dt=pd.Timestamp(s["entry_ts"])-pd.Timedelta(minutes=1)
        rows.append({
            "group_key":k,"session_date":str(meta.session_date),"year":int(meta.year),
            "contract":meta.contract,"signal_ts":s["signal_ts"],"entry_ts":s["entry_ts"],
            "entry_actual_et":dt,"signal_close":sc,"entry_price":s["entry_price"],
            "exit60_ts":s["exit60_ts"],"exit60_price":s["exit60"],
            "or_high":s["or_high"],"or_low":s["or_low"],
            "directional_15m_bps":bps15,"directional_30m_bps":bps30,
            "directional_60m_bps":bps60,
            "gross_points":gross_pts,
            "gross_pnl_usd":gross_pts*POINT_VALUE,
            "net_pnl_usd":gross_pts*POINT_VALUE-BASE_COST,
            "stress_net_pnl_usd":gross_pts*POINT_VALUE-STRESS_COST,
            "week":f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}",
            "month":dt.strftime("%Y-%m"),
            "quarter":dt.tz_localize(None).to_period("Q").strftime("%YQ%q"),
            "semester":f"{dt.year}H{1 if dt.month<=6 else 2}",
        })
    return pd.DataFrame(rows).sort_values("entry_actual_et").reset_index(drop=True)

def metrics(g):
    if len(g)==0:return {}
    p=g.net_pnl_usd; s=g.stress_net_pnl_usd
    return {
        "trades":int(len(g)),
        "gross_15m_bps":float(g.directional_15m_bps.mean()),
        "gross_30m_bps":float(g.directional_30m_bps.mean()),
        "gross_60m_bps":float(g.directional_60m_bps.mean()),
        "net_pnl_usd":float(p.sum()),
        "expectancy_usd":float(p.mean()),
        "profit_factor":float(profit_factor(p)),
        "stress_expectancy_usd":float(s.mean()),
        "win_rate":float((p>0).mean()),
        "max_drawdown_usd":dd_mag(p),
        "worst_trade_usd":float(p.min()),
    }

def period_table(t,col):
    return pd.DataFrame([{col:k,**metrics(g.sort_values("entry_actual_et"))}
                         for k,g in t.groupby(col,sort=True,observed=True)])

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    d=make_daily(groups)
    t=build_events(groups,d)
    if t.empty:raise ValueError("no OR15 R1 events")
    if t.year.max()>2025:raise ValueError("2026 leak")

    dev=t[t.year<=2024]
    y25=t[t.year==2025]
    fidelity={
      "r1_sessions_2020_2024":int(d[(d.year<=2024)&d.R1].shape[0]),
      "events_2020_2024":int(len(dev)),
      "mean_60m_bps_2020_2024":float(dev.directional_60m_bps.mean()),
      "reference_events":106,
      "reference_60m_bps":6.48,
    }

    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"OR15_R1_TRADES.csv",index=False)
    d.to_csv(OUT/"OR15_R1_DAILY_REGIME.csv",index=False)
    for col,name in [("week","WEEKLY_DIAGNOSTIC"),("month","MONTHLY_DIAGNOSTIC"),
                     ("quarter","QUARTERLY_EVALUATION"),("semester","SEMESTER_EVALUATION"),
                     ("year","YEARLY_ROBUSTNESS")]:
        period_table(t,col).to_csv(OUT/f"OR15_R1_{name}.csv",index=False)

    # Rolling 6/12-month diagnostic.
    x=t.copy()
    x["date_naive"]=x.entry_actual_et.dt.tz_localize(None)
    ends=pd.date_range(x.date_naive.min().to_period("M").to_timestamp("M"),
                       x.date_naive.max().to_period("M").to_timestamp("M"),freq="ME")
    rr=[]
    for months in (6,12):
        for end in ends:
            start=(end-pd.DateOffset(months=months))+pd.Timedelta(days=1)
            g=x[(x.date_naive>=start)&(x.date_naive<=end)]
            if len(g):
                rr.append({"window_months":months,"window_start":start.date().isoformat(),
                           "window_end":end.date().isoformat(),**metrics(g)})
    pd.DataFrame(rr).to_csv(OUT/"OR15_R1_ROLLING.csv",index=False)

    yearly=period_table(t,"year")
    semester=period_table(t,"semester")
    report={
      "authority":"TEMPORAL_DIAGNOSTIC_OF_HISTORICALLY_FROZEN_SIGNAL",
      "contract_2026_opened":False,
      "fidelity":fidelity,
      "2020_2024":metrics(dev),
      "2025":metrics(y25),
      "full_2020_2025":metrics(t),
      "positive_years":int((yearly.net_pnl_usd>0).sum()),
      "years_observed":int(len(yearly)),
      "positive_semesters":int((semester.net_pnl_usd>0).sum()),
      "semesters_observed":int(len(semester)),
    }
    (OUT/"OR15_R1_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("\nYEARLY\n",yearly.round(4).to_string(index=False))
    print("\nSEMESTER\n",semester.round(4).to_string(index=False))

if __name__=="__main__":
    main()
