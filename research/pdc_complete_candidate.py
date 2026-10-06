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
from research.mes_pdc_small_gap_reconstruction import daily_context, build_events

OUT=ROOT/"results/pdc_complete_candidate"
NEWS=ROOT/"data_external/forexfactory/usd_high_medium_2020_2025.csv"
POINT_VALUE=5.0
BASE_COST=4.38
STRESS_COST=6.57
CUTOFF_MINUTE=11*60+30
STOP_MULT=0.30

VARIANTS=[
    ("NO_STOP_NO_NEWS",False,False),
    ("STOP030_NO_NEWS",True,False),
    ("NO_STOP_NEWS",False,True),
    ("STOP030_NEWS",True,True),
]

def dd_mag(pnl: pd.Series)->float:
    if len(pnl)==0: return np.nan
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

def entry_is_blocked(entry_actual, nd):
    if nd is None or nd.empty: return False
    return bool(((nd.blackout_start_et<=entry_actual)&(entry_actual<=nd.blackout_end_et)).any())

def next_news_cutoff(entry_actual, nd):
    if nd is None or nd.empty: return None
    z=nd[nd.blackout_start_et>entry_actual]
    if z.empty: return None
    return z.iloc[0]

def simulate(br,g,use_stop,use_news,nd):
    direction=int(br.direction)
    entry=float(br.entry_price)
    pdc=float(br.pdc)
    atr=float(br.atr14_prev)
    stop=entry-direction*STOP_MULT*atr if use_stop else None

    entry_label=pd.Timestamp(br.entry_ts)
    entry_actual=entry_label-pd.Timedelta(minutes=1)
    if use_news and entry_is_blocked(entry_actual,nd):
        return {"blocked":True}

    idxs=g.index[g.timestamp_et==entry_label].tolist()
    if not idxs: return None
    start=int(idxs[0])

    forced=next_news_cutoff(entry_actual,nd) if use_news else None
    cutoff=forced.blackout_start_et if forced is not None else None
    cutoff_label=(cutoff+pd.Timedelta(minutes=1)) if cutoff is not None else None

    exit_px=None; reason=None; exit_ts=None
    for i in range(start,len(g)):
        b=g.iloc[i]
        if int(b.minute)>CUTOFF_MINUTE: break

        # News flat at minute open takes precedence over that minute's path.
        if cutoff_label is not None and b.timestamp_et>=cutoff_label:
            exit_px=float(b.open); reason="NEWS_EXIT"; exit_ts=b.timestamp_et; break

        if direction==1:
            target_touch=float(b.high)>=pdc
            stop_touch=(stop is not None and float(b.low)<=stop)
            if target_touch and stop_touch:
                exit_px=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                reason="STOP_AMBIGUOUS_FIRST"; exit_ts=b.timestamp_et; break
            if stop_touch:
                exit_px=min(float(b.open),stop) if float(b.open)<stop else float(stop)
                reason="STOP"; exit_ts=b.timestamp_et; break
            if target_touch:
                exit_px=pdc; reason="PDC"; exit_ts=b.timestamp_et; break
        else:
            target_touch=float(b.low)<=pdc
            stop_touch=(stop is not None and float(b.high)>=stop)
            if target_touch and stop_touch:
                exit_px=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                reason="STOP_AMBIGUOUS_FIRST"; exit_ts=b.timestamp_et; break
            if stop_touch:
                exit_px=max(float(b.open),stop) if float(b.open)>stop else float(stop)
                reason="STOP"; exit_ts=b.timestamp_et; break
            if target_touch:
                exit_px=pdc; reason="PDC"; exit_ts=b.timestamp_et; break

    if exit_px is None:
        elig=g[(g.index>=start)&(g.minute<=CUTOFF_MINUTE)]
        if elig.empty: return None
        b=elig.iloc[-1]
        exit_px=float(b.close); reason="TIME_1130"; exit_ts=b.timestamp_et

    gross=direction*(exit_px-entry)
    return {
        "blocked":False,
        "group_key":br.group_key,
        "session_date":br.session_date,
        "year":int(br.year),
        "quarter":pd.Timestamp(entry_actual).to_period("Q").strftime("%YQ%q"),
        "semester":f"{int(br.year)}H{1 if entry_actual.month<=6 else 2}",
        "month":entry_actual.strftime("%Y-%m"),
        "week":f"{entry_actual.isocalendar().year}-W{entry_actual.isocalendar().week:02d}",
        "direction":direction,
        "entry_actual_et":entry_actual,
        "entry_label_et":entry_label,
        "entry_price":entry,
        "pdc":pdc,
        "atr14_prev":atr,
        "stop_price":np.nan if stop is None else float(stop),
        "exit_ts":exit_ts,
        "exit_price":float(exit_px),
        "exit_reason":reason,
        "target_hit":bool(reason=="PDC"),
        "gross_points":gross,
        "net_pnl_usd":gross*POINT_VALUE-BASE_COST,
        "stress_net_pnl_usd":gross*POINT_VALUE-STRESS_COST,
        "news_event":None if forced is None else str(forced.event),
        "news_impact":None if forced is None else str(forced.impact),
    }

def metrics(g):
    if len(g)==0: return {}
    p=g.net_pnl_usd
    s=g.stress_net_pnl_usd
    sem=g.groupby("semester").net_pnl_usd.sum()
    return {
      "trades":int(len(g)),
      "trades_per_month":float(len(g)/72.0),
      "target_hit_rate":float(g.target_hit.mean()),
      "stop_rate":float(g.exit_reason.str.startswith("STOP").mean()),
      "news_exit_rate":float((g.exit_reason=="NEWS_EXIT").mean()),
      "net_pnl_usd":float(p.sum()),
      "expectancy_usd":float(p.mean()),
      "profit_factor":float(profit_factor(p)),
      "stress_expectancy_usd":float(s.mean()),
      "win_rate":float((p>0).mean()),
      "max_drawdown_usd":dd_mag(p),
      "positive_semesters":int((sem>0).sum()),
      "semesters_observed":int(len(sem)),
      "worst_trade_usd":float(p.min()),
      "p05_trade_usd":float(p.quantile(0.05)),
    }

def period_table(t,col):
    return pd.DataFrame([{col:k,**metrics(g.sort_values("entry_actual_et"))}
                         for k,g in t.groupby(col,sort=True,observed=True)])

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    daily=daily_context(groups)
    base=build_events(groups,daily).copy()
    if base.empty: raise ValueError("no PDC events")
    if base.year.max()>2025: raise ValueError("2026 leak")
    news=load_news()

    rows=[]; blocked=[]
    for name,use_stop,use_news in VARIANTS:
        blocked_n=0
        for br in base.itertuples(index=False):
            g=groups.get(br.group_key)
            if g is None: continue
            d=str(br.session_date)
            z=simulate(br,g,use_stop,use_news,news.get(d))
            if z is None: continue
            if z.get("blocked"):
                blocked_n+=1
                continue
            z["variant"]=name
            rows.append(z)
        blocked.append({"variant":name,"blocked_entries":blocked_n})

    tr=pd.DataFrame(rows).sort_values(["variant","entry_actual_et"]).reset_index(drop=True)
    OUT.mkdir(parents=True,exist_ok=True)
    tr.to_csv(OUT/"PDC_COMPLETE_TRADES.csv",index=False)
    pd.DataFrame(blocked).to_csv(OUT/"PDC_COMPLETE_BLOCKED.csv",index=False)

    summaries=[]
    for name,_,_ in VARIANTS:
        g=tr[tr.variant==name].sort_values("entry_actual_et")
        summaries.append({"variant":name,**metrics(g)})
        for col,fn in [("week","WEEKLY"),("month","MONTHLY"),("quarter","QUARTERLY"),
                       ("semester","SEMESTER"),("year","YEARLY")]:
            period_table(g,col).to_csv(OUT/f"{name}_{fn}.csv",index=False)
    summary=pd.DataFrame(summaries)
    summary.to_csv(OUT/"PDC_COMPLETE_SUMMARY.csv",index=False)

    # Rolling calendar diagnostics for full candidate only.
    cand=tr[tr.variant=="STOP030_NEWS"].copy().sort_values("entry_actual_et")
    ends=pd.date_range(cand.entry_actual_et.min().tz_localize(None).to_period("M").to_timestamp("M"),
                       cand.entry_actual_et.max().tz_localize(None).to_period("M").to_timestamp("M"),freq="ME")
    rr=[]
    naive=cand.copy()
    naive["naive_date"]=cand.entry_actual_et.dt.tz_localize(None)
    for months in (6,12):
        for end in ends:
            start=(end-pd.DateOffset(months=months))+pd.Timedelta(days=1)
            g=naive[(naive.naive_date>=start)&(naive.naive_date<=end)]
            if len(g):
                rr.append({"window_months":months,"window_start":start.date().isoformat(),
                           "window_end":end.date().isoformat(),**metrics(g)})
    pd.DataFrame(rr).to_csv(OUT/"STOP030_NEWS_ROLLING.csv",index=False)

    s={r.variant:r for _,r in summary.iterrows()}
    c=s["STOP030_NEWS"]; sn=s["STOP030_NO_NEWS"]
    pnl_reduction=(sn.net_pnl_usd-c.net_pnl_usd)/sn.net_pnl_usd if sn.net_pnl_usd>0 else np.inf
    yearly=period_table(cand,"year")
    ymap={int(r.year):float(r.net_pnl_usd) for _,r in yearly.iterrows()}
    criteria={
      "pf_ge_1_30":bool(c.profit_factor>=1.30),
      "stress_expectancy_gt_0":bool(c.stress_expectancy_usd>0),
      "max_dd_le_250":bool(c.max_drawdown_usd<=250),
      "positive_semesters_ge_7":bool(c.positive_semesters>=7),
      "year_2024_positive":bool(ymap.get(2024,-np.inf)>0),
      "year_2025_positive":bool(ymap.get(2025,-np.inf)>0),
      "news_pnl_reduction_le_25pct":bool(pnl_reduction<=0.25),
      "worst_trade_ge_minus175":bool(c.worst_trade_usd>=-175),
    }
    report={
      "authority":"ARCHITECTURE_CHARACTERIZATION_NOT_INDEPENDENT_VALIDATION",
      "contract_2026_opened":False,
      "candidate":"PDC + SL 0.30 ATR + FF USD High/Medium T-5/T+5 + TP PDC + 11:30 time exit",
      "candidate_metrics":{k:(v.item() if hasattr(v,"item") else v) for k,v in c.to_dict().items()},
      "stop_only_metrics":{k:(v.item() if hasattr(v,"item") else v) for k,v in sn.to_dict().items()},
      "news_pnl_reduction_vs_stop_only":float(pnl_reduction),
      "freeze_criteria":criteria,
      "eligible_to_freeze_for_2026":bool(all(criteria.values())),
    }
    (OUT/"PDC_COMPLETE_REPORT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print("\n=== COMPLETE PDC VARIANTS ===")
    print(summary.round(4).to_string(index=False))
    print("\n=== BLOCKED ===")
    print(pd.DataFrame(blocked).to_string(index=False))
    print("\n=== CANDIDATE YEARS ===")
    print(yearly.round(4).to_string(index=False))
    print("\n=== FREEZE DECISION ===")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
