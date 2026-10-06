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
from research.mes_pdc_small_gap_reconstruction import daily_context as pdc_daily_context, build_events as pdc_build_events
from research.mes_poc_breakdown_reconstruction import build_levels as poc_build_levels, build_events as poc_build_events

OUT=ROOT/"results/mes_stage1_local_robustness"
NEWS=ROOT/"data_external/forexfactory/usd_high_medium_2020_2025.csv"

POINT_VALUE=5.0
BASE_COST=4.38
STRESS_COST=6.57
PDC_CUTOFF=11*60+30

PDC_STOPS=[0.25,0.30,0.35]
POC_HORIZONS=[10,15,20]
R072_HORIZONS=[20,30,40]

def dd_mag(pnl: pd.Series) -> float:
    if len(pnl)==0:
        return np.nan
    eq=pnl.cumsum()
    peak=eq.cummax().clip(lower=0)
    return float(-(eq-peak).min())

def load_news():
    if not NEWS.exists():
        raise FileNotFoundError(NEWS)
    n=pd.read_csv(NEWS)
    for c in ["event_et","blackout_start_et","blackout_end_et"]:
        n[c]=pd.to_datetime(n[c],utc=True).dt.tz_convert("America/New_York")
    n["date_et"]=n.event_et.dt.date.astype(str)
    return {d:g.sort_values("event_et").reset_index(drop=True) for d,g in n.groupby("date_et")}

def is_blocked(entry_actual, nd):
    if nd is None or nd.empty:
        return False
    return bool(((nd.blackout_start_et<=entry_actual)&(entry_actual<=nd.blackout_end_et)).any())

def next_news_flat(entry_actual, scheduled_exit_label, nd):
    if nd is None or nd.empty:
        return None
    z=nd[
        (nd.blackout_start_et>entry_actual)
        & ((nd.blackout_start_et+pd.Timedelta(minutes=1))<=scheduled_exit_label)
    ]
    if z.empty:
        return None
    return z.iloc[0]

def common_fields(session_date, entry_label):
    actual=pd.Timestamp(entry_label)-pd.Timedelta(minutes=1)
    return {
        "entry_actual_et":actual,
        "year":int(actual.year),
        "semester":f"{actual.year}H{1 if actual.month<=6 else 2}",
        "quarter":actual.tz_localize(None).to_period("Q").strftime("%YQ%q"),
        "month":actual.strftime("%Y-%m"),
        "week":f"{actual.isocalendar().year}-W{actual.isocalendar().week:02d}",
        "session_date":str(session_date),
    }

def metrics(g):
    if len(g)==0:
        return {}
    p=g.net_pnl_usd
    sp=g.stress_net_pnl_usd
    sem=g.groupby("semester").net_pnl_usd.sum()
    yrs=g.groupby("year").net_pnl_usd.sum()
    return {
        "trades":int(len(g)),
        "trades_per_month":float(len(g)/72.0),
        "net_pnl_usd":float(p.sum()),
        "expectancy_usd":float(p.mean()),
        "profit_factor":float(profit_factor(p)),
        "stress_expectancy_usd":float(sp.mean()),
        "win_rate":float((p>0).mean()),
        "max_drawdown_usd":dd_mag(p),
        "worst_trade_usd":float(p.min()),
        "p05_trade_usd":float(p.quantile(.05)),
        "positive_semesters":int((sem>0).sum()),
        "semesters_observed":int(len(sem)),
        "positive_years":int((yrs>0).sum()),
        "years_observed":int(len(yrs)),
    }

def pdc_variant_rows(groups, base, news, stop_mult):
    rows=[]
    blocked=0
    for br in base.itertuples(index=False):
        g=groups.get(br.group_key)
        if g is None:
            continue

        entry_label=pd.Timestamp(br.entry_ts)
        entry_actual=entry_label-pd.Timedelta(minutes=1)
        nd=news.get(str(br.session_date))
        if is_blocked(entry_actual,nd):
            blocked+=1
            continue

        idxs=g.index[g.timestamp_et==entry_label].tolist()
        if not idxs:
            continue
        start=int(idxs[0])

        direction=int(br.direction)
        entry=float(br.entry_price)
        target=float(br.pdc)
        atr=float(br.atr14_prev)
        stop=entry-direction*stop_mult*atr

        eligible=g[(g.index>=start)&(g.minute<=PDC_CUTOFF)]
        if eligible.empty:
            continue
        scheduled_exit_label=eligible.iloc[-1].timestamp_et
        fe=next_news_flat(entry_actual,scheduled_exit_label,nd)
        cutoff_label=(fe.blackout_start_et+pd.Timedelta(minutes=1)) if fe is not None else None

        exit_px=None; exit_ts=None; reason=None
        for i in range(start,len(g)):
            b=g.iloc[i]
            if int(b.minute)>PDC_CUTOFF:
                break

            if cutoff_label is not None and b.timestamp_et>=cutoff_label:
                exit_px=float(b.open); exit_ts=b.timestamp_et; reason="NEWS_EXIT"; break

            if direction==1:
                target_touch=float(b.high)>=target
                stop_touch=float(b.low)<=stop
                if target_touch and stop_touch:
                    exit_px=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                    exit_ts=b.timestamp_et; reason="STOP_AMBIGUOUS_FIRST"; break
                if stop_touch:
                    exit_px=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                    exit_ts=b.timestamp_et; reason="STOP"; break
                if target_touch:
                    exit_px=target; exit_ts=b.timestamp_et; reason="PDC"; break
            else:
                target_touch=float(b.low)<=target
                stop_touch=float(b.high)>=stop
                if target_touch and stop_touch:
                    exit_px=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                    exit_ts=b.timestamp_et; reason="STOP_AMBIGUOUS_FIRST"; break
                if stop_touch:
                    exit_px=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                    exit_ts=b.timestamp_et; reason="STOP"; break
                if target_touch:
                    exit_px=target; exit_ts=b.timestamp_et; reason="PDC"; break

        if exit_px is None:
            b=eligible.iloc[-1]
            exit_px=float(b.close); exit_ts=b.timestamp_et; reason="TIME_1130"

        gross_pts=direction*(exit_px-entry)
        rows.append({
            "strategy":"PDC","variant":f"SL_{stop_mult:.2f}ATR",
            "stop_mult":stop_mult,"group_key":br.group_key,
            **common_fields(br.session_date,entry_label),
            "entry_price":entry,"exit_price":float(exit_px),"exit_ts":exit_ts,
            "exit_reason":reason,"gross_points":gross_pts,
            "net_pnl_usd":gross_pts*POINT_VALUE-BASE_COST,
            "stress_net_pnl_usd":gross_pts*POINT_VALUE-STRESS_COST,
        })
    return rows,blocked

def timed_variant_rows(groups, base, news, strategy, horizons):
    rows=[]
    blocked_by_h={h:0 for h in horizons}

    for br in base.itertuples(index=False):
        g=groups.get(br.group_key)
        if g is None:
            continue

        if strategy=="POC":
            signal_label=pd.Timestamp(br.contact_ts)
            entry_label=pd.Timestamp(br.entry_bar_ts)
            direction=-1
        elif strategy=="R072":
            signal_label=pd.Timestamp(br.entry_clock_et)
            entry_label=pd.Timestamp(br.entry_bar_ts)
            direction=int(br.direction)
        else:
            raise ValueError(strategy)

        entry_actual=entry_label-pd.Timedelta(minutes=1)
        nd=news.get(str(br.session_date))
        idxs=g.index[g.timestamp_et==signal_label].tolist()
        if not idxs:
            continue
        signal_pos=int(idxs[0])
        entry=float(br.entry_price)

        for h in horizons:
            if is_blocked(entry_actual,nd):
                blocked_by_h[h]+=1
                continue
            exit_pos=signal_pos+h
            if exit_pos>=len(g):
                continue
            eb=g.iloc[exit_pos]
            if eb.timestamp_et-signal_label!=pd.Timedelta(minutes=h):
                continue

            scheduled_exit_label=eb.timestamp_et
            fe=next_news_flat(entry_actual,scheduled_exit_label,nd)
            if fe is not None:
                label=fe.blackout_start_et+pd.Timedelta(minutes=1)
                m=g.index[g.timestamp_et==label].tolist()
                if m:
                    b=g.loc[m[0]]
                    exit_px=float(b.open); exit_ts=b.timestamp_et; reason="NEWS_EXIT"
                else:
                    exit_px=float(eb.close); exit_ts=scheduled_exit_label; reason=f"TIME_{h}"
            else:
                exit_px=float(eb.close); exit_ts=scheduled_exit_label; reason=f"TIME_{h}"

            gross_pts=direction*(exit_px-entry)
            rows.append({
                "strategy":strategy,"variant":f"H{h}","horizon_minutes":h,
                "group_key":br.group_key,**common_fields(br.session_date,entry_label),
                "direction":direction,"entry_price":entry,"exit_price":float(exit_px),
                "exit_ts":exit_ts,"exit_reason":reason,"gross_points":gross_pts,
                "net_pnl_usd":gross_pts*POINT_VALUE-BASE_COST,
                "stress_net_pnl_usd":gross_pts*POINT_VALUE-STRESS_COST,
            })
    return rows,blocked_by_h

def yearly_table(g):
    return pd.DataFrame([
        {"year":int(y),**metrics(x.sort_values("entry_actual_et"))}
        for y,x in g.groupby("year",sort=True)
    ])

def semester_table(g):
    return pd.DataFrame([
        {"semester":str(s),**metrics(x.sort_values("entry_actual_et"))}
        for s,x in g.groupby("semester",sort=True)
    ])

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    if pd.to_datetime(raw["timestamp_et"]).dt.year.max()>2026:
        raise ValueError("unexpected data horizon")

    news=load_news()

    # PDC
    pdcd=pdc_daily_context(groups)
    pdcbase=pdc_build_events(groups,pdcd)
    if pdcbase.year.max()>2025:
        raise ValueError("2026 PDC leak")

    allrows=[]; blocked=[]
    for sm in PDC_STOPS:
        r,b=pdc_variant_rows(groups,pdcbase,news,sm)
        allrows.extend(r)
        blocked.append({"strategy":"PDC","variant":f"SL_{sm:.2f}ATR","blocked_entries":b})

    # POC
    levels=poc_build_levels(groups)
    pocbase=poc_build_events(groups,levels)
    if pocbase.year.max()>2025:
        raise ValueError("2026 POC leak")
    r,b=timed_variant_rows(groups,pocbase,news,"POC",POC_HORIZONS)
    allrows.extend(r)
    for h,n in b.items():
        blocked.append({"strategy":"POC","variant":f"H{h}","blocked_entries":n})

    # R072
    feats=block_features(raw,groups)
    rbase=build_signal_trades(feats,groups,0.50,660)
    if rbase.year.max()>2025:
        raise ValueError("2026 R072 leak")
    r,b=timed_variant_rows(groups,rbase,news,"R072",R072_HORIZONS)
    allrows.extend(r)
    for h,n in b.items():
        blocked.append({"strategy":"R072","variant":f"H{h}","blocked_entries":n})

    t=pd.DataFrame(allrows).sort_values(["strategy","variant","entry_actual_et"]).reset_index(drop=True)
    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"STAGE1_TRADES.csv",index=False)
    pd.DataFrame(blocked).to_csv(OUT/"STAGE1_BLOCKED_ENTRIES.csv",index=False)

    summary=[]
    for (strategy,variant),g in t.groupby(["strategy","variant"],sort=True):
        summary.append({"strategy":strategy,"variant":variant,**metrics(g.sort_values("entry_actual_et"))})
        yearly_table(g).to_csv(OUT/f"{strategy}_{variant}_YEARLY.csv",index=False)
        semester_table(g).to_csv(OUT/f"{strategy}_{variant}_SEMESTER.csv",index=False)
    s=pd.DataFrame(summary).sort_values(["strategy","variant"])
    s.to_csv(OUT/"STAGE1_SUMMARY.csv",index=False)

    # Frozen plateau interpretation.
    pdc={r.variant:r for _,r in s[s.strategy=="PDC"].iterrows()}
    c25=pdc["SL_0.25ATR"]; c30=pdc["SL_0.30ATR"]; c35=pdc["SL_0.35ATR"]
    pdc_neighbors=[c25,c35]
    pdc_criteria={
      "all_pf_ge_1_25":bool(all(r.profit_factor>=1.25 for r in [c25,c30,c35])),
      "all_stress_expectancy_positive":bool(all(r.stress_expectancy_usd>0 for r in [c25,c30,c35])),
      "at_least_two_have_7_positive_semesters":bool(sum(r.positive_semesters>=7 for r in [c25,c30,c35])>=2),
      "center_not_isolated":bool(any(
          r.expectancy_usd>=0.8*c30.expectancy_usd and r.profit_factor>=c30.profit_factor-0.15
          for r in pdc_neighbors
      )),
    }

    poc={r.variant:r for _,r in s[s.strategy=="POC"].iterrows()}
    p10=poc["H10"]; p15=poc["H15"]; p20=poc["H20"]
    poc_criteria={
      "neighbor_stress_positive":bool(p10.stress_expectancy_usd>0 and p20.stress_expectancy_usd>0),
      "neighbor_pf_ge_1_10":bool(p10.profit_factor>=1.10 and p20.profit_factor>=1.10),
      "center_not_isolated":bool(
          (p10.expectancy_usd>=0.7*p15.expectancy_usd)
          or (p20.expectancy_usd>=0.7*p15.expectancy_usd)
          or (p10.expectancy_usd>p15.expectancy_usd and p10.max_drawdown_usd<=1.25*p15.max_drawdown_usd)
          or (p20.expectancy_usd>p15.expectancy_usd and p20.max_drawdown_usd<=1.25*p15.max_drawdown_usd)
      ),
    }

    r72={r.variant:r for _,r in s[s.strategy=="R072"].iterrows()}
    r20=r72["H20"]; r30=r72["H30"]; r40=r72["H40"]
    r072_criteria={
      "neighbor_stress_positive":bool(r20.stress_expectancy_usd>0 and r40.stress_expectancy_usd>0),
      "neighbor_pf_ge_1_10":bool(r20.profit_factor>=1.10 and r40.profit_factor>=1.10),
      "center_not_isolated":bool(
          (r20.expectancy_usd>=0.7*r30.expectancy_usd)
          or (r40.expectancy_usd>=0.7*r30.expectancy_usd)
          or (r20.expectancy_usd>r30.expectancy_usd and r20.max_drawdown_usd<=1.25*r30.max_drawdown_usd)
          or (r40.expectancy_usd>r30.expectancy_usd and r40.max_drawdown_usd<=1.25*r30.max_drawdown_usd)
      ),
    }

    report={
      "authority":"STAGE1_LOCAL_ROBUSTNESS_DEVELOPMENT_NOT_VALIDATION",
      "contract_2026_opened":False,
      "PDC":{"center":"SL_0.30ATR","criteria":pdc_criteria,"plateau_pass":bool(all(pdc_criteria.values()))},
      "POC":{"center":"H15","criteria":poc_criteria,"plateau_pass":bool(all(poc_criteria.values()))},
      "R072":{"center":"H30","criteria":r072_criteria,"plateau_pass":bool(all(r072_criteria.values()))},
    }
    (OUT/"STAGE1_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print("\n=== STAGE 1 LOCAL ROBUSTNESS ===")
    print(s.round(4).to_string(index=False))
    print("\n=== INTERPRETATION ===")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
