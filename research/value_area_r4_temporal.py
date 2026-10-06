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

OUT=ROOT/"results/value_area_reentry_r4"
TICK=0.25
BASE_COST=4.38
STRESS_COST=6.57
POINT_VALUE=5.0
REENTRY_CUTOFF=10*60+30
TARGET_CUTOFF=11*60+30
ROLL=252
WARM=126

def dd_mag(p):
    if len(p)==0:return np.nan
    eq=p.cumsum(); peak=eq.cummax().clip(lower=0)
    return float(-(eq-peak).min())

def profile_levels(g):
    x=g.copy()
    x["typical"]=(x.high+x.low+x.close)/3.0
    x["bin"]=(np.floor(x.typical/TICK+0.5)*TICK).round(2)
    raw=x.groupby("bin",observed=True).volume.sum().sort_index()
    if raw.empty:return (np.nan,np.nan,np.nan)
    lo=float(raw.index.min()); hi=float(raw.index.max())
    grid=np.round(np.arange(lo,hi+TICK/2,TICK),2)
    vp=raw.reindex(grid,fill_value=0.0)
    mx=vp.max()
    tied=np.asarray(vp[vp==mx].index,float)
    center=float(np.average(np.asarray(vp.index,float),weights=np.asarray(vp.values,float)))
    poc=float(tied[np.argmin(np.abs(tied-center))])
    pi=int(np.where(np.isclose(grid,poc))[0][0])
    total=float(vp.sum()); target=.70*total
    acc=float(vp.iloc[pi]); li=ri=pi
    vals=vp.to_numpy(float)
    while acc<target and (li>0 or ri<len(grid)-1):
        lv=vals[li-1] if li>0 else -1
        rv=vals[ri+1] if ri<len(grid)-1 else -1
        if rv>=lv:
            ri+=1; acc+=vals[ri]
        else:
            li-=1; acc+=vals[li]
    return poc,float(grid[ri]),float(grid[li])

def daily_context(groups):
    rows=[]
    for k,g in groups.items():
        g=g.sort_values("timestamp_et")
        poc,vah,val=profile_levels(g)
        rows.append({
          "group_key":k,"session_date":str(g.session_date.iloc[0]),"year":int(g.year.iloc[0]),
          "contract":str(g.contract.iloc[0]),"first_ts":g.timestamp_et.iloc[0],
          "high":float(g.high.max()),"low":float(g.low.min()),"close":float(g.close.iloc[-1]),
          "poc":poc,"vah":vah,"val":val
        })
    d=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    pc=d.close.shift(1)
    d["tr"]=pd.concat([(d.high-d.low),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    d["atr14"]=d.tr.rolling(14,min_periods=14).mean()
    d["vol_ratio"]=d.atr14/d.close
    dc=d.close.diff().abs()
    d["er10"]=(d.close-d.close.shift(10)).abs()/dc.rolling(10,min_periods=10).sum()
    d["vol_p33"]=d.vol_ratio.shift(1).rolling(ROLL,min_periods=WARM).quantile(.33)
    d["er_p33"]=d.er10.shift(1).rolling(ROLL,min_periods=WARM).quantile(.33)
    d["prev_vol_ratio"]=d.vol_ratio.shift(1)
    d["prev_er10"]=d.er10.shift(1)
    d["R4"]=(d.prev_vol_ratio<d.vol_p33)&(d.prev_er10<=d.er_p33)

    for c in ["poc","vah","val","contract"]:
        d["prev_"+c]=d[c].shift(1)
    d["same_contract"]=d.contract.eq(d.prev_contract)
    for c in ["prev_poc","prev_vah","prev_val"]:
        d[c]=d[c].where(d.same_contract)
    return d

def find_event(g,meta):
    poc=float(meta.prev_poc); vah=float(meta.prev_vah); val=float(meta.prev_val)
    if not all(np.isfinite([poc,vah,val])):return None
    g=g.sort_values("timestamp_et").reset_index(drop=True)
    op=float(g.iloc[0].open)
    if op>vah:
        direction=-1; origin="ABOVE"
    elif op<val:
        direction=1; origin="BELOW"
    else:
        return None

    # POC may not have been touched before the qualifying re-entry close.
    for i,b in g.iterrows():
        m=int(b.minute)
        if m>REENTRY_CUTOFF:break
        # If POC is touched before/inside this bar, it cannot be a valid
        # "re-entry with POC still untouched" signal.
        poc_touched=(float(b.low)<=poc<=float(b.high))
        inside=(val<=float(b.close)<=vah)
        if inside and not poc_touched:
            # Ensure no earlier bar touched POC.
            prior=g.iloc[:i+1]
            earlier=((prior.low<=poc)&(prior.high>=poc)).any()
            if earlier:return None
            if i+1>=len(g):return None
            entry=g.iloc[i+1]
            # Entry itself should not already be through target.
            ep=float(entry.open)
            if direction==-1 and ep<=poc:return None
            if direction==1 and ep>=poc:return None

            # Outcome to 11:30.
            hit=False; exit_px=np.nan; exit_ts=None; reason="TIME_1130"
            for j in range(i+1,len(g)):
                z=g.iloc[j]
                if int(z.minute)>TARGET_CUTOFF:break
                if direction==-1 and float(z.low)<=poc:
                    hit=True; exit_px=poc; exit_ts=z.timestamp_et; reason="POC"; break
                if direction==1 and float(z.high)>=poc:
                    hit=True; exit_px=poc; exit_ts=z.timestamp_et; reason="POC"; break
            if not hit:
                elig=g[(g.index>=i+1)&(g.minute<=TARGET_CUTOFF)]
                if elig.empty:return None
                z=elig.iloc[-1]; exit_px=float(z.close); exit_ts=z.timestamp_et
            gross_pts=direction*(exit_px-ep)
            dt=entry.timestamp_et-pd.Timedelta(minutes=1)
            return {
              "origin":origin,"direction":direction,"signal_ts":b.timestamp_et,
              "entry_ts":entry.timestamp_et,"entry_actual_et":dt,"entry_price":ep,
              "poc":poc,"vah":vah,"val":val,"target_hit":bool(hit),
              "exit_ts":exit_ts,"exit_price":float(exit_px),"exit_reason":reason,
              "gross_points":gross_pts,"net_pnl_usd":gross_pts*POINT_VALUE-BASE_COST,
              "stress_net_pnl_usd":gross_pts*POINT_VALUE-STRESS_COST,
              "week":f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}",
              "month":dt.strftime("%Y-%m"),
              "quarter":dt.tz_localize(None).to_period("Q").strftime("%YQ%q"),
              "semester":f"{dt.year}H{1 if dt.month<=6 else 2}",
            }
        if poc_touched:
            return None
    return None

def build_events(groups,d):
    rows=[]
    for _,m in d.iterrows():
        if not bool(m.R4):continue
        g=groups.get(m.group_key)
        if g is None:continue
        e=find_event(g,m)
        if e is None:continue
        rows.append({"group_key":m.group_key,"session_date":m.session_date,"year":int(m.year),**e})
    return pd.DataFrame(rows).sort_values("entry_actual_et").reset_index(drop=True)

def metrics(g):
    if len(g)==0:return {}
    p=g.net_pnl_usd; s=g.stress_net_pnl_usd
    return {
      "trades":int(len(g)),"target_hit_rate":float(g.target_hit.mean()),
      "net_pnl_usd":float(p.sum()),"expectancy_usd":float(p.mean()),
      "profit_factor":float(profit_factor(p)),"stress_expectancy_usd":float(s.mean()),
      "win_rate":float((p>0).mean()),"max_drawdown_usd":dd_mag(p),
      "worst_trade_usd":float(p.min())
    }

def table(t,col):
    return pd.DataFrame([{col:k,**metrics(g.sort_values("entry_actual_et"))}
                         for k,g in t.groupby(col,sort=True,observed=True)])

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    d=daily_context(groups)
    t=build_events(groups,d)
    if t.empty:raise ValueError("no value-area R4 events")
    if t.year.max()>2025:raise ValueError("2026 leak")
    dev=t[t.year<=2024]; y25=t[t.year==2025]
    fidelity={
      "events_2020_2024":int(len(dev)),
      "poc_hits_2020_2024":int(dev.target_hit.sum()),
      "hit_rate_2020_2024":float(dev.target_hit.mean()),
      "reference_events":37,"reference_hits":25,"reference_hit_rate":25/37
    }
    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"VALUE_AREA_R4_TRADES.csv",index=False)
    d.to_csv(OUT/"VALUE_AREA_R4_DAILY.csv",index=False)
    for col,name in [("week","WEEKLY"),("month","MONTHLY"),("quarter","QUARTERLY"),
                     ("semester","SEMESTER"),("year","YEARLY")]:
        table(t,col).to_csv(OUT/f"VALUE_AREA_R4_{name}.csv",index=False)
    yr=table(t,"year"); sm=table(t,"semester")
    report={
      "authority":"RECONSTRUCTION_WITH_FIDELITY_CHECK",
      "contract_2026_opened":False,
      "fidelity":fidelity,
      "2020_2024":metrics(dev),"2025":metrics(y25),"full_2020_2025":metrics(t),
      "positive_years":int((yr.net_pnl_usd>0).sum()),"years_observed":int(len(yr)),
      "positive_semesters":int((sm.net_pnl_usd>0).sum()),"semesters_observed":int(len(sm))
    }
    (OUT/"VALUE_AREA_R4_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("\nYEARLY\n",yr.round(4).to_string(index=False))
    print("\nSEMESTER\n",sm.round(4).to_string(index=False))

if __name__=="__main__":
    main()
