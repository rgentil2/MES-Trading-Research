#!/usr/bin/env python3
from __future__ import annotations

import json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, build_signal_trades
from research.archive.B12.b12_strategy_architecture import prepare_rth, profit_factor
from research.archive.B13.b13_high_directional_triggers import block_features
from research.mes_pdc_small_gap_reconstruction import daily_context as daily_atr_context
from research.mes_poc_breakdown_reconstruction import build_levels as poc_build_levels, build_events as poc_build_events

OUT=ROOT/"results/mes_poc_r072_atr_stop"
NEWS=ROOT/"data_external/forexfactory/usd_high_medium_2020_2025.csv"
BASE_COST=4.38
STRESS_COST=6.57
POINT_VALUE=5.0

CONFIG={
    "POC":{"horizon":15},
    "R072":{"horizon":30},
}

def dd_mag(p):
    if len(p)==0:return np.nan
    eq=p.cumsum()
    peak=eq.cummax().clip(lower=0)
    return float(-(eq-peak).min())

def load_news():
    if not NEWS.exists(): raise FileNotFoundError(NEWS)
    n=pd.read_csv(NEWS)
    for c in ["event_et","blackout_start_et","blackout_end_et"]:
        n[c]=pd.to_datetime(n[c],utc=True).dt.tz_convert("America/New_York")
    n["date_et"]=n.event_et.dt.date.astype(str)
    return {d:g.sort_values("event_et").reset_index(drop=True) for d,g in n.groupby("date_et")}

def blocked(entry_actual,nd):
    if nd is None or nd.empty:return False
    return bool(((nd.blackout_start_et<=entry_actual)&(entry_actual<=nd.blackout_end_et)).any())

def forced_event(entry_actual,scheduled_exit_label,nd):
    if nd is None or nd.empty:return None
    z=nd[(nd.blackout_start_et>entry_actual)&((nd.blackout_start_et+pd.Timedelta(minutes=1))<=scheduled_exit_label)]
    if z.empty:return None
    return z.iloc[0]

def ceil05(x):
    return math.ceil((float(x)-1e-12)/0.05)*0.05

def ensure_three(vals,center):
    vals=sorted(set(round(max(0.05,float(v)),2) for v in vals))
    step=0.05
    k=1
    while len(vals)<3:
        for z in [center-k*step,center+k*step]:
            z=round(z,2)
            if z>=0.05 and z not in vals:
                vals.append(z)
                vals=sorted(vals)
                if len(vals)>=3:break
        k+=1
    return vals[:3] if center>=vals[-1] else vals[-3:]

def metrics(g):
    if len(g)==0:return {}
    p=g.net_pnl_usd
    s=g.stress_net_pnl_usd
    sem=g.groupby("semester").net_pnl_usd.sum()
    yr=g.groupby("year").net_pnl_usd.sum()
    return {
      "trades":int(len(g)),
      "net_pnl_usd":float(p.sum()),
      "expectancy_usd":float(p.mean()),
      "profit_factor":float(profit_factor(p)),
      "stress_expectancy_usd":float(s.mean()),
      "win_rate":float((p>0).mean()),
      "max_drawdown_usd":dd_mag(p),
      "worst_trade_usd":float(p.min()),
      "positive_semesters":int((sem>0).sum()),
      "semesters_observed":int(len(sem)),
      "positive_years":int((yr>0).sum()),
      "years_observed":int(len(yr)),
    }

def trade_geometry(strategy,br,g,atr,nd,h):
    if strategy=="POC":
        signal_label=pd.Timestamp(br.contact_ts)
        entry_label=pd.Timestamp(br.entry_bar_ts)
        direction=-1
    else:
        signal_label=pd.Timestamp(br.entry_clock_et)
        entry_label=pd.Timestamp(br.entry_bar_ts)
        direction=int(br.direction)

    entry_actual=entry_label-pd.Timedelta(minutes=1)
    if blocked(entry_actual,nd):
        return None

    idxs=g.index[g.timestamp_et==signal_label].tolist()
    if not idxs:return None
    sig_pos=int(idxs[0])
    entry_pos=sig_pos+1
    if entry_pos>=len(g):return None
    exit_pos=sig_pos+h
    if exit_pos>=len(g):return None
    eb=g.iloc[exit_pos]
    if eb.timestamp_et-signal_label!=pd.Timedelta(minutes=h):return None
    scheduled_exit_label=eb.timestamp_et

    fe=forced_event(entry_actual,scheduled_exit_label,nd)
    news_exit_label=(fe.blackout_start_et+pd.Timedelta(minutes=1)) if fe is not None else None

    path_rows=[]
    exit_price=None; exit_ts=None; exit_reason=None
    for i in range(entry_pos,exit_pos+1):
        b=g.iloc[i]
        # Forced news exit occurs at this bar OPEN, before this bar's path.
        if news_exit_label is not None and b.timestamp_et>=news_exit_label:
            exit_price=float(b.open); exit_ts=b.timestamp_et; exit_reason="NEWS_EXIT"
            break
        path_rows.append(b)
    if exit_price is None:
        exit_price=float(eb.close); exit_ts=eb.timestamp_et; exit_reason=f"TIME_{h}"

    entry=float(br.entry_price)
    if not path_rows:
        mae_pts=0.0; mfe_pts=0.0
    else:
        lows=min(float(b.low) for b in path_rows)
        highs=max(float(b.high) for b in path_rows)
        if direction==1:
            mae_pts=max(0.0,entry-lows)
            mfe_pts=max(0.0,highs-entry)
        else:
            mae_pts=max(0.0,highs-entry)
            mfe_pts=max(0.0,entry-lows)

    gross=direction*(exit_price-entry)
    dt=entry_actual
    return {
      "strategy":strategy,"group_key":br.group_key,"session_date":str(br.session_date),
      "year":int(dt.year),"semester":f"{dt.year}H{1 if dt.month<=6 else 2}",
      "direction":direction,"entry_label":entry_label,"entry_actual":entry_actual,
      "entry_price":entry,"scheduled_exit_label":scheduled_exit_label,
      "base_exit_ts":exit_ts,"base_exit_price":exit_price,"base_exit_reason":exit_reason,
      "atr14_prev":float(atr),"mae_points":mae_pts,"mfe_points":mfe_pts,
      "mae_atr":mae_pts/atr if atr>0 else np.nan,
      "mfe_atr":mfe_pts/atr if atr>0 else np.nan,
      "base_net_pnl_usd":gross*POINT_VALUE-BASE_COST,
      "base_stress_pnl_usd":gross*POINT_VALUE-STRESS_COST,
      "news_exit_label":news_exit_label,
      "signal_pos":sig_pos,"entry_pos":entry_pos,"exit_pos":exit_pos,
    }

def simulate_with_stop(rec,g,k):
    direction=int(rec.direction)
    entry=float(rec.entry_price)
    stop=entry-direction*float(k)*float(rec.atr14_prev)
    news_exit_label=rec.news_exit_label
    exit_pos=int(rec.exit_pos)
    entry_pos=int(rec.entry_pos)

    exit_price=None; exit_ts=None; reason=None
    for i in range(entry_pos,exit_pos+1):
        b=g.iloc[i]
        if pd.notna(news_exit_label) and b.timestamp_et>=news_exit_label:
            exit_price=float(b.open); exit_ts=b.timestamp_et; reason="NEWS_EXIT"; break
        if direction==1:
            if float(b.low)<=stop:
                exit_price=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                exit_ts=b.timestamp_et; reason="STOP"; break
        else:
            if float(b.high)>=stop:
                exit_price=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                exit_ts=b.timestamp_et; reason="STOP"; break

    if exit_price is None:
        b=g.iloc[exit_pos]
        exit_price=float(b.close); exit_ts=b.timestamp_et; reason="TIME"

    gross=direction*(exit_price-entry)
    return {
      "candidate":f"SL_{k:.2f}ATR","stop_atr":float(k),
      "exit_ts":exit_ts,"exit_price":float(exit_price),"exit_reason":reason,
      "net_pnl_usd":gross*POINT_VALUE-BASE_COST,
      "stress_net_pnl_usd":gross*POINT_VALUE-STRESS_COST,
    }

def no_stop_row(rec):
    return {
      "candidate":"NO_STOP","stop_atr":np.nan,
      "exit_ts":rec.base_exit_ts,"exit_price":rec.base_exit_price,"exit_reason":rec.base_exit_reason,
      "net_pnl_usd":rec.base_net_pnl_usd,
      "stress_net_pnl_usd":rec.base_stress_pnl_usd,
    }

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    news=load_news()

    # Same causal Wilder ATR14 used in PDC risk design.
    dctx=daily_atr_context(groups)
    atrmap=dctx.set_index("group_key")["atr14_prev"].to_dict()

    levels=poc_build_levels(groups)
    poc=poc_build_events(groups,levels)
    feats=block_features(raw,groups)
    r072=build_signal_trades(feats,groups,0.50,660)

    bases={"POC":poc,"R072":r072}
    geometry=[]

    for strategy,base in bases.items():
        h=CONFIG[strategy]["horizon"]
        for br in base.itertuples(index=False):
            atr=atrmap.get(br.group_key,np.nan)
            if not np.isfinite(atr) or atr<=0:continue
            g=groups.get(br.group_key)
            if g is None:continue
            rec=trade_geometry(strategy,br,g,float(atr),news.get(str(br.session_date)),h)
            if rec is not None:
                geometry.append(rec)

    geo=pd.DataFrame(geometry).sort_values(["strategy","entry_actual"]).reset_index(drop=True)
    if geo.year.max()>2025:raise ValueError("2026 leak")

    OUT.mkdir(parents=True,exist_ok=True)
    geo.to_csv(OUT/"RISK_GEOMETRY.csv",index=False)

    design_summary=[]
    candidates={}
    for strategy,g in geo[geo.year<=2022].groupby("strategy",sort=True):
        winners=g[g.base_net_pnl_usd>0]
        losers=g[g.base_net_pnl_usd<=0]
        qs=winners.mae_atr.quantile([.50,.75,.85,.95]).to_dict()
        mfe=winners.mfe_atr.quantile([.50,.75,.85,.95]).to_dict()
        vals=[ceil05(qs[.75]),ceil05(qs[.85]),ceil05(qs[.95])]
        center=ceil05(qs[.85])
        vals=ensure_three(vals,center)
        candidates[strategy]=vals
        design_summary.append({
          "strategy":strategy,
          "design_trades":int(len(g)),"design_winners":int(len(winners)),"design_losers":int(len(losers)),
          "winner_mae_median_atr":float(qs[.50]),"winner_mae_p75_atr":float(qs[.75]),
          "winner_mae_p85_atr":float(qs[.85]),"winner_mae_p95_atr":float(qs[.95]),
          "winner_mfe_median_atr":float(mfe[.50]),"winner_mfe_p75_atr":float(mfe[.75]),
          "winner_mfe_p85_atr":float(mfe[.85]),"winner_mfe_p95_atr":float(mfe[.95]),
          "loser_mae_median_atr":float(losers.mae_atr.median()),
          "loser_mae_p75_atr":float(losers.mae_atr.quantile(.75)),
          "candidate_tight_atr":float(vals[0]),"candidate_center_atr":float(vals[1]),"candidate_wide_atr":float(vals[2]),
        })
    ds=pd.DataFrame(design_summary)
    ds.to_csv(OUT/"DESIGN_MAE_MFE_SUMMARY.csv",index=False)

    allrows=[]
    for rec in geo.itertuples(index=False):
        g=groups[rec.group_key]
        base_common={
          "strategy":rec.strategy,"group_key":rec.group_key,"session_date":rec.session_date,
          "year":int(rec.year),"semester":rec.semester,"entry_actual":rec.entry_actual,
          "atr14_prev":float(rec.atr14_prev),"mae_atr":float(rec.mae_atr),"mfe_atr":float(rec.mfe_atr)
        }
        allrows.append({**base_common,**no_stop_row(rec)})
        for k in candidates[rec.strategy]:
            allrows.append({**base_common,**simulate_with_stop(rec,g,k)})

    tr=pd.DataFrame(allrows).sort_values(["strategy","candidate","entry_actual"]).reset_index(drop=True)
    tr.to_csv(OUT/"ATR_STOP_TRADES.csv",index=False)

    summary=[]
    validation_decisions={}
    for strategy in sorted(tr.strategy.unique()):
        sv=tr[tr.strategy==strategy]
        control=metrics(sv[(sv.candidate=="NO_STOP")&(sv.year>=2023)].sort_values("entry_actual"))
        rows=[]
        for cand,g in sv.groupby("candidate",sort=True):
            gd=g[g.year<=2022].sort_values("entry_actual")
            gv=g[g.year>=2023].sort_values("entry_actual")
            md=metrics(gd); mv=metrics(gv)
            row={"strategy":strategy,"candidate":cand,
                 **{f"design_{k}":v for k,v in md.items()},
                 **{f"validation_{k}":v for k,v in mv.items()}}
            if cand!="NO_STOP":
                dd_imp=(control["max_drawdown_usd"]-mv["max_drawdown_usd"])/control["max_drawdown_usd"] if control["max_drawdown_usd"]>0 else np.nan
                worst_imp=(abs(control["worst_trade_usd"])-abs(mv["worst_trade_usd"]))/abs(control["worst_trade_usd"]) if control["worst_trade_usd"]<0 else np.nan
                pnl_reduction=(control["net_pnl_usd"]-mv["net_pnl_usd"])/control["net_pnl_usd"] if control["net_pnl_usd"]>0 else np.nan
                gate={
                  "expectancy_gt_0":mv["expectancy_usd"]>0,
                  "pf_ge_1_15":mv["profit_factor"]>=1.15,
                  "stress_expectancy_gt_0":mv["stress_expectancy_usd"]>0,
                  "dd_improvement_ge_25pct":np.isfinite(dd_imp) and dd_imp>=.25,
                  "worst_trade_improvement_ge_25pct":np.isfinite(worst_imp) and worst_imp>=.25,
                  "pnl_reduction_le_25pct_or_control_nonpositive":(not np.isfinite(pnl_reduction)) or pnl_reduction<=.25,
                  "positive_semesters_ge_3":mv["positive_semesters"]>=3,
                }
                row["validation_dd_improvement_pct"]=dd_imp
                row["validation_worst_trade_improvement_pct"]=worst_imp
                row["validation_pnl_reduction_pct"]=pnl_reduction
                row["passes_gate"]=bool(all(gate.values()))
            else:
                row["passes_gate"]=False
            rows.append(row)
        ss=pd.DataFrame(rows)
        summary.append(ss)

        vals=candidates[strategy]
        center=vals[1]
        center_id=f"SL_{center:.2f}ATR"
        passing=ss[ss.passes_gate==True].copy()
        if center_id in set(passing.candidate):
            selected=center_id
            reason="CENTER_PASSES"
        elif len(passing):
            passing=passing.sort_values(["validation_max_drawdown_usd","validation_profit_factor"],ascending=[True,False])
            selected=str(passing.iloc[0].candidate)
            reason="NEIGHBOR_PASSES_CENTER_FAILS"
        else:
            selected=None
            reason="NO_CANDIDATE_PASSES"
        validation_decisions[strategy]={
          "design_candidates_atr":vals,
          "center_candidate":center_id,
          "selected_research_candidate":selected,
          "selection_reason":reason,
        }

    summ=pd.concat(summary,ignore_index=True)
    summ.to_csv(OUT/"ATR_STOP_SUMMARY.csv",index=False)

    # transparency by year/semester
    for strategy in sorted(tr.strategy.unique()):
        for cand in sorted(tr[tr.strategy==strategy].candidate.unique()):
            g=tr[(tr.strategy==strategy)&(tr.candidate==cand)]
            yr=pd.DataFrame([{"year":int(y),**metrics(x.sort_values("entry_actual"))} for y,x in g.groupby("year",sort=True)])
            yr.to_csv(OUT/f"{strategy}_{cand}_YEARLY.csv",index=False)
            sm=pd.DataFrame([{"semester":str(s),**metrics(x.sort_values("entry_actual"))} for s,x in g.groupby("semester",sort=True)])
            sm.to_csv(OUT/f"{strategy}_{cand}_SEMESTER.csv",index=False)

    report={
      "authority":"PREREGISTERED_ATR_STOP_RISK_DESIGN",
      "contract_2026_opened":False,
      "design_period":"2020-2022",
      "validation_period":"2023-2025",
      "candidate_construction":"winner MAE P75/P85/P95, rounded up to 0.05 ATR",
      "decisions":validation_decisions,
    }
    (OUT/"ATR_STOP_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")

    print("\n=== DESIGN MAE/MFE ===")
    print(ds.round(4).to_string(index=False))
    print("\n=== STOP SUMMARY ===")
    cols=["strategy","candidate","design_trades","design_expectancy_usd","design_profit_factor",
          "validation_trades","validation_expectancy_usd","validation_profit_factor",
          "validation_stress_expectancy_usd","validation_max_drawdown_usd","validation_worst_trade_usd",
          "validation_positive_semesters","validation_dd_improvement_pct",
          "validation_worst_trade_improvement_pct","passes_gate"]
    print(summ[[c for c in cols if c in summ.columns]].round(4).to_string(index=False))
    print("\n=== DECISION ===")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
