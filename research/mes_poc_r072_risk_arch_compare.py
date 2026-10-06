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
from research.mes_poc_r072_atr_stop import load_news, blocked, forced_event

OUT=ROOT/"results/mes_poc_r072_risk_arch_compare"
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

def ceil05(x):
    return max(0.05, math.ceil((float(x)-1e-12)/0.05)*0.05)

def floor05(x):
    return max(0.05, math.floor((float(x)+1e-12)/0.05)*0.05)

def base_path(strategy,br,g,atr,nd,h):
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
    exit_pos=sig_pos+h
    if exit_pos>=len(g) or entry_pos>=len(g):return None
    timed=g.iloc[exit_pos]
    if timed.timestamp_et-signal_label!=pd.Timedelta(minutes=h):return None

    scheduled_exit_label=timed.timestamp_et
    fe=forced_event(entry_actual,scheduled_exit_label,nd)
    news_exit_label=(fe.blackout_start_et+pd.Timedelta(minutes=1)) if fe is not None else None

    # Path before any news forced-flat minute.
    path=[]
    base_exit_px=None; base_exit_ts=None; base_reason=None
    for i in range(entry_pos,exit_pos+1):
        b=g.iloc[i]
        if news_exit_label is not None and b.timestamp_et>=news_exit_label:
            base_exit_px=float(b.open)
            base_exit_ts=b.timestamp_et
            base_reason="NEWS_EXIT"
            break
        path.append(b)

    if base_exit_px is None:
        base_exit_px=float(timed.close)
        base_exit_ts=timed.timestamp_et
        base_reason=f"TIME_{h}"

    entry=float(br.entry_price)
    if path:
        lo=min(float(b.low) for b in path)
        hi=max(float(b.high) for b in path)
        if direction==1:
            mae=max(0.0,entry-lo); mfe=max(0.0,hi-entry)
        else:
            mae=max(0.0,hi-entry); mfe=max(0.0,entry-lo)
    else:
        mae=mfe=0.0

    gross=direction*(base_exit_px-entry)
    return {
        "strategy":strategy,
        "group_key":br.group_key,
        "session_date":str(br.session_date),
        "year":int(entry_actual.year),
        "semester":f"{entry_actual.year}H{1 if entry_actual.month<=6 else 2}",
        "direction":direction,
        "entry_actual":entry_actual,
        "entry_label":entry_label,
        "entry_price":entry,
        "atr14_prev":float(atr),
        "mae_points":mae,
        "mfe_points":mfe,
        "mae_atr":mae/atr,
        "mfe_atr":mfe/atr,
        "base_exit_price":base_exit_px,
        "base_exit_ts":base_exit_ts,
        "base_exit_reason":base_reason,
        "base_net_pnl_usd":gross*POINT_VALUE-BASE_COST,
        "base_stress_pnl_usd":gross*POINT_VALUE-STRESS_COST,
        "signal_pos":sig_pos,
        "entry_pos":entry_pos,
        "exit_pos":exit_pos,
        "news_exit_label":news_exit_label,
    }

def simulate(rec,g,architecture,hard_sl=None,avg_sl=None,avg_tp=None):
    direction=int(rec.direction)
    entry=float(rec.entry_price)
    atr=float(rec.atr14_prev)

    if architecture=="CURRENT":
        gross=direction*(float(rec.base_exit_price)-entry)
        return {
            "exit_ts":rec.base_exit_ts,
            "exit_price":float(rec.base_exit_price),
            "exit_reason":rec.base_exit_reason,
            "net_pnl_usd":gross*POINT_VALUE-BASE_COST,
            "stress_net_pnl_usd":gross*POINT_VALUE-STRESS_COST,
            "stop_atr":np.nan,"target_atr":np.nan,
        }

    if architecture=="HARD_STOP":
        sl=float(hard_sl); tp=None
    elif architecture=="AVG_BRACKET":
        sl=float(avg_sl); tp=float(avg_tp)
    else:
        raise ValueError(architecture)

    stop=entry-direction*sl*atr
    target=None if tp is None else entry+direction*tp*atr
    exit_px=None; exit_ts=None; reason=None

    for i in range(int(rec.entry_pos),int(rec.exit_pos)+1):
        b=g.iloc[i]

        # news flat first at minute open
        if pd.notna(rec.news_exit_label) and b.timestamp_et>=rec.news_exit_label:
            exit_px=float(b.open); exit_ts=b.timestamp_et; reason="NEWS_EXIT"; break

        if direction==1:
            stop_touch=float(b.low)<=stop
            target_touch=(target is not None and float(b.high)>=target)
            if stop_touch and target_touch:
                exit_px=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                exit_ts=b.timestamp_et; reason="STOP_AMBIGUOUS_FIRST"; break
            if stop_touch:
                exit_px=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                exit_ts=b.timestamp_et; reason="STOP"; break
            if target_touch:
                exit_px=float(target); exit_ts=b.timestamp_et; reason="TARGET"; break
        else:
            stop_touch=float(b.high)>=stop
            target_touch=(target is not None and float(b.low)<=target)
            if stop_touch and target_touch:
                exit_px=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                exit_ts=b.timestamp_et; reason="STOP_AMBIGUOUS_FIRST"; break
            if stop_touch:
                exit_px=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                exit_ts=b.timestamp_et; reason="STOP"; break
            if target_touch:
                exit_px=float(target); exit_ts=b.timestamp_et; reason="TARGET"; break

    if exit_px is None:
        b=g.iloc[int(rec.exit_pos)]
        exit_px=float(b.close); exit_ts=b.timestamp_et; reason="TIME"

    gross=direction*(exit_px-entry)
    return {
        "exit_ts":exit_ts,"exit_price":float(exit_px),"exit_reason":reason,
        "net_pnl_usd":gross*POINT_VALUE-BASE_COST,
        "stress_net_pnl_usd":gross*POINT_VALUE-STRESS_COST,
        "stop_atr":sl,"target_atr":np.nan if tp is None else tp,
    }

def metrics(g):
    if len(g)==0:return {}
    p=g.net_pnl_usd
    s=g.stress_net_pnl_usd
    wins=p[p>0]; losses=p[p<=0]
    sem=g.groupby("semester").net_pnl_usd.sum()
    yr=g.groupby("year").net_pnl_usd.sum()
    avgwin=float(wins.mean()) if len(wins) else np.nan
    avgloss=float(losses.mean()) if len(losses) else np.nan
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
        "stop_rate":float(g.exit_reason.str.startswith("STOP").mean()),
        "target_rate":float((g.exit_reason=="TARGET").mean()),
        "news_exit_rate":float((g.exit_reason=="NEWS_EXIT").mean()),
        "time_exit_rate":float(g.exit_reason.str.startswith("TIME").mean()),
        "average_win_usd":avgwin,
        "average_loss_usd":avgloss,
        "payoff_ratio":float(avgwin/abs(avgloss)) if len(wins) and len(losses) and avgloss!=0 else np.nan,
    }

def dist_stats(s):
    return {
        "mean":float(s.mean()),"median":float(s.median()),
        "p75":float(s.quantile(.75)),"p90":float(s.quantile(.90)),
        "p95":float(s.quantile(.95)),"p99":float(s.quantile(.99)),
        "max":float(s.max())
    }

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    news=load_news()

    dctx=daily_atr_context(groups)
    atrmap=dctx.set_index("group_key")["atr14_prev"].to_dict()

    poc=poc_build_events(groups,poc_build_levels(groups))
    r072=build_signal_trades(block_features(raw,groups),groups,0.50,660)
    bases={"POC":poc,"R072":r072}

    paths=[]
    for strategy,base in bases.items():
        h=CONFIG[strategy]["horizon"]
        for br in base.itertuples(index=False):
            atr=atrmap.get(br.group_key,np.nan)
            if not np.isfinite(atr) or atr<=0:continue
            g=groups.get(br.group_key)
            if g is None:continue
            r=base_path(strategy,br,g,float(atr),news.get(str(br.session_date)),h)
            if r is not None:paths.append(r)

    geo=pd.DataFrame(paths).sort_values(["strategy","entry_actual"]).reset_index(drop=True)
    if geo.year.max()>2025:raise ValueError("2026 leak")
    OUT.mkdir(parents=True,exist_ok=True)
    geo.to_csv(OUT/"PATH_GEOMETRY.csv",index=False)

    # Freeze architecture levels from design only.
    levels={}
    dist_rows=[]
    for strategy,g in geo[geo.year<=2022].groupby("strategy",sort=True):
        winners=g[g.base_net_pnl_usd>0]
        losers=g[g.base_net_pnl_usd<=0]
        all_mae=dist_stats(g.mae_atr)
        all_mfe=dist_stats(g.mfe_atr)
        win_mae=dist_stats(winners.mae_atr)
        win_mfe=dist_stats(winners.mfe_atr)
        lose_mae=dist_stats(losers.mae_atr)
        lose_mfe=dist_stats(losers.mfe_atr)

        hard=ceil05(1.10*max(all_mae["p99"],win_mae["max"]))
        avg_sl=ceil05(lose_mae["mean"])
        avg_tp=floor05(win_mfe["mean"])
        levels[strategy]={"hard_sl_atr":hard,"avg_sl_atr":avg_sl,"avg_tp_atr":avg_tp}

        for group_name,mae_stats,mfe_stats in [
            ("ALL",all_mae,all_mfe),("WINNERS",win_mae,win_mfe),("LOSERS",lose_mae,lose_mfe)
        ]:
            dist_rows.append({
                "strategy":strategy,"group":group_name,
                **{f"mae_{k}":v for k,v in mae_stats.items()},
                **{f"mfe_{k}":v for k,v in mfe_stats.items()},
            })

    pd.DataFrame(dist_rows).to_csv(OUT/"DESIGN_EXCURSION_DISTRIBUTIONS.csv",index=False)
    pd.DataFrame([{"strategy":k,**v} for k,v in levels.items()]).to_csv(OUT/"FROZEN_RISK_LEVELS.csv",index=False)

    rows=[]
    for rec in geo.itertuples(index=False):
        g=groups[rec.group_key]
        lv=levels[rec.strategy]
        for arch in ["CURRENT","HARD_STOP","AVG_BRACKET"]:
            z=simulate(rec,g,arch,
                       hard_sl=lv["hard_sl_atr"],
                       avg_sl=lv["avg_sl_atr"],
                       avg_tp=lv["avg_tp_atr"])
            stop_risk=np.nan
            if np.isfinite(z["stop_atr"]):
                stop_risk=float(z["stop_atr"])*float(rec.atr14_prev)*POINT_VALUE+BASE_COST
            rows.append({
                "strategy":rec.strategy,"architecture":arch,
                "group_key":rec.group_key,"session_date":rec.session_date,
                "year":int(rec.year),"semester":rec.semester,
                "entry_actual":rec.entry_actual,"entry_price":float(rec.entry_price),
                "atr14_prev":float(rec.atr14_prev),
                "mae_atr":float(rec.mae_atr),"mfe_atr":float(rec.mfe_atr),
                "implied_stop_risk_usd":stop_risk,
                **z
            })

    t=pd.DataFrame(rows).sort_values(["strategy","architecture","entry_actual"]).reset_index(drop=True)
    t.to_csv(OUT/"ARCHITECTURE_TRADES.csv",index=False)

    summaries=[]
    decision={}
    for strategy in sorted(t.strategy.unique()):
        st=t[t.strategy==strategy]
        ctrl_val=metrics(st[(st.architecture=="CURRENT")&(st.year>=2023)].sort_values("entry_actual"))
        strategy_dec={}
        for arch,g in st.groupby("architecture",sort=True):
            gd=g[g.year<=2022].sort_values("entry_actual")
            gv=g[g.year>=2023].sort_values("entry_actual")
            md=metrics(gd); mv=metrics(gv)
            risk=gv.implied_stop_risk_usd.dropna()
            row={
                "strategy":strategy,"architecture":arch,
                **{f"design_{k}":v for k,v in md.items()},
                **{f"validation_{k}":v for k,v in mv.items()},
                "validation_stop_risk_median_usd":float(risk.median()) if len(risk) else np.nan,
                "validation_stop_risk_p90_usd":float(risk.quantile(.90)) if len(risk) else np.nan,
            }
            summaries.append(row)

            if arch=="HARD_STOP":
                retain=mv["expectancy_usd"]/ctrl_val["expectancy_usd"] if ctrl_val["expectancy_usd"]>0 else np.nan
                strategy_dec["HARD_STOP"]={
                    "expectancy_gt_0":bool(mv["expectancy_usd"]>0),
                    "stress_gt_0":bool(mv["stress_expectancy_usd"]>0),
                    "pf_ge_1_10":bool(mv["profit_factor"]>=1.10),
                    "expectancy_retention_ge_70pct":bool((not np.isfinite(retain)) or retain>=.70),
                    "worst_trade_vs_current_usd":float(mv["worst_trade_usd"]-ctrl_val["worst_trade_usd"]),
                }
                strategy_dec["HARD_STOP"]["acceptable"]=bool(
                    strategy_dec["HARD_STOP"]["expectancy_gt_0"]
                    and strategy_dec["HARD_STOP"]["stress_gt_0"]
                    and strategy_dec["HARD_STOP"]["pf_ge_1_10"]
                    and strategy_dec["HARD_STOP"]["expectancy_retention_ge_70pct"]
                )

            if arch=="AVG_BRACKET":
                retain=mv["expectancy_usd"]/ctrl_val["expectancy_usd"] if ctrl_val["expectancy_usd"]>0 else np.nan
                strategy_dec["AVG_BRACKET"]={
                    "expectancy_gt_0":bool(mv["expectancy_usd"]>0),
                    "stress_gt_0":bool(mv["stress_expectancy_usd"]>0),
                    "pf_ge_1_15":bool(mv["profit_factor"]>=1.15),
                    "positive_semesters_ge_3":bool(mv["positive_semesters"]>=3),
                    "dd_le_current":bool(mv["max_drawdown_usd"]<=ctrl_val["max_drawdown_usd"]),
                    "expectancy_retention_ge_70pct":bool((not np.isfinite(retain)) or retain>=.70),
                }
                strategy_dec["AVG_BRACKET"]["viable"]=bool(all(strategy_dec["AVG_BRACKET"].values()))

        decision[strategy]=strategy_dec

        # annual transparency
        for arch in ["CURRENT","HARD_STOP","AVG_BRACKET"]:
            g=st[st.architecture==arch]
            yr=pd.DataFrame([
                {"year":int(y),**metrics(x.sort_values("entry_actual"))}
                for y,x in g.groupby("year",sort=True)
            ])
            yr.to_csv(OUT/f"{strategy}_{arch}_YEARLY.csv",index=False)

    summ=pd.DataFrame(summaries)
    summ.to_csv(OUT/"ARCHITECTURE_SUMMARY.csv",index=False)

    report={
        "authority":"PREREGISTERED_RISK_ARCHITECTURE_COMPARISON",
        "contract_2026_opened":False,
        "design_period":"2020-2022",
        "validation_period":"2023-2025",
        "frozen_levels":levels,
        "validation_decisions":decision,
    }
    (OUT/"RISK_ARCH_COMPARE_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")

    print("\n=== FROZEN LEVELS ===")
    print(pd.DataFrame([{"strategy":k,**v} for k,v in levels.items()]).to_string(index=False))
    print("\n=== VALIDATION COMPARISON 2023-2025 ===")
    cols=["strategy","architecture","validation_trades","validation_net_pnl_usd",
          "validation_expectancy_usd","validation_profit_factor","validation_stress_expectancy_usd",
          "validation_win_rate","validation_max_drawdown_usd","validation_worst_trade_usd",
          "validation_positive_semesters","validation_stop_rate","validation_target_rate",
          "validation_average_win_usd","validation_average_loss_usd","validation_payoff_ratio",
          "validation_stop_risk_median_usd","validation_stop_risk_p90_usd"]
    print(summ[[c for c in cols if c in summ.columns]].round(4).to_string(index=False))
    print("\n=== DECISION ===")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
