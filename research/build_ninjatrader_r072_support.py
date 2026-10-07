#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, build_signal_trades
from research.archive.B12.b12_strategy_architecture import prepare_rth
from research.archive.B13.b13_high_directional_triggers import block_features
from research.mes_pdc_small_gap_reconstruction import daily_context as daily_atr_context
from research.r072_news_policy import load_news, blocked

NEWS_IN=ROOT/"data_external/forexfactory/usd_high_medium_2020_2025.csv"
OUT=ROOT/"results/ninjatrader_r072_support"

WICK=0.50
CUTOFF=660

def build_session_universe(groups):
    dates=sorted({str(g.session_date.iloc[0]) for g in groups.values()})
    return pd.DataFrame({"session_date_et":dates})

def build_rollover_dates(groups):
    rows=[]
    for key,g in groups.items():
        g=g.sort_values("timestamp_et")
        rows.append({
            "session_date":str(g.session_date.iloc[0]),
            "contract":str(g.contract.iloc[0]),
            "first_ts":g.timestamp_et.iloc[0],
        })
    d=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    d["prev_contract"]=d.contract.shift(1)
    x=d[d.prev_contract.notna() & d.contract.ne(d.prev_contract)].copy()
    x=x.rename(columns={"session_date":"rollover_session_date_et"})
    return x[["rollover_session_date_et","prev_contract","contract"]]

def build_news_csv():
    n=pd.read_csv(NEWS_IN)
    for c in ["blackout_start_et","blackout_end_et"]:
        n[c]=pd.to_datetime(n[c],utc=True).dt.tz_convert("America/New_York")
    return pd.DataFrame({
        "start_et":n.blackout_start_et.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_et":n.blackout_end_et.dt.strftime("%Y-%m-%d %H:%M:%S"),
    }).drop_duplicates().sort_values(["start_et","end_et"]).reset_index(drop=True)

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    feats=block_features(raw,groups)
    base=build_signal_trades(feats,groups,WICK,CUTOFF).copy()
    news=load_news()
    dctx=daily_atr_context(groups)
    atrmap=dctx.set_index("group_key")["atr14_prev"].to_dict()

    rows=[]
    blocked_n=0
    for br in base.itertuples(index=False):
        entry_label=pd.Timestamp(br.entry_bar_ts)
        entry_actual=entry_label-pd.Timedelta(minutes=1)
        nd=news.get(str(br.session_date))
        if blocked(entry_actual,nd):
            blocked_n+=1
            continue
        atr=atrmap.get(br.group_key,np.nan)
        rows.append({
            "signal_et":entry_actual.strftime("%Y-%m-%d %H:%M:%S"),
            "session_date_et":str(br.session_date),
            "direction":int(br.direction),
            "side":"LONG" if int(br.direction)==1 else "SHORT",
            "python_entry_price":float(br.entry_price),
            "atr14_prev":None if not np.isfinite(atr) else float(atr),
            "group_key":br.group_key,
        })

    sig=pd.DataFrame(rows).sort_values("signal_et").reset_index(drop=True)
    if len(sig)!=145:
        raise ValueError(f"expected 145 R072 post-news signals, got {len(sig)}")

    OUT.mkdir(parents=True,exist_ok=True)
    sig.to_csv(OUT/"r072_python_signals_et.csv",index=False)
    build_news_csv().to_csv(OUT/"r072_news_blackouts_et.csv",index=False)
    build_session_universe(groups).to_csv(OUT/"r072_python_eligible_sessions_et.csv",index=False)
    build_rollover_dates(groups).to_csv(OUT/"r072_rollover_sessions_et.csv",index=False)

    print(f"base signals: {len(base)}")
    print(f"blocked by news: {blocked_n}")
    print(f"replay signals: {len(sig)}")
    print(f"first: {sig.signal_et.iloc[0]}")
    print(f"last: {sig.signal_et.iloc[-1]}")

if __name__=="__main__":
    main()
