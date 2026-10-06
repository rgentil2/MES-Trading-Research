#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
GOLD=ROOT/"results/mes_stage2_parity"

ALIASES={
    "entry_time":["Entry time","Entry Time","entry_time","EntryTime"],
    "exit_time":["Exit time","Exit Time","exit_time","ExitTime"],
    "side":["Market position","Market Position","market_position","Side","side"],
    "entry_price":["Entry price","Entry Price","entry_price","EntryPrice"],
    "exit_price":["Exit price","Exit Price","exit_price","ExitPrice"],
    "profit":["Profit","profit","PnL","P&L","Net profit","Net Profit"],
    "commission":["Commission","commission","Commissions","commissions"],
}

def find_col(df,key):
    for c in ALIASES[key]:
        if c in df.columns:
            return c
    return None

def norm_side(v):
    s=str(v).strip().upper()
    if "LONG" in s:
        return 1
    if "SHORT" in s:
        return -1
    return np.nan

def parse_dt(s):
    return pd.to_datetime(s,errors="coerce")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--strategy",required=True,choices=["PDC","POC","R072"])
    ap.add_argument("--ninjatrader-csv",required=True)
    ap.add_argument("--output-dir",default="results/ninjatrader_parity_comparison")
    a=ap.parse_args()

    gp=GOLD/f"{a.strategy}_PYTHON_GOLDEN_TRADES.csv"
    if not gp.exists():
        raise FileNotFoundError(f"Golden file missing: {gp}. Generate Stage 2 manifest first.")

    py=pd.read_csv(gp)
    nt=pd.read_csv(a.ninjatrader_csv)
    out=ROOT/a.output_dir
    out.mkdir(parents=True,exist_ok=True)

    ec=find_col(nt,"entry_time")
    xc=find_col(nt,"exit_time")
    sc=find_col(nt,"side")
    epc=find_col(nt,"entry_price")
    xpc=find_col(nt,"exit_price")
    pc=find_col(nt,"profit")
    cc=find_col(nt,"commission")

    if ec is None or sc is None:
        raise ValueError(f"NinjaTrader CSV must contain Entry time and Market position/Side. Columns: {list(nt.columns)}")

    nt2=pd.DataFrame()
    nt2["nt_entry_time"]=parse_dt(nt[ec])
    nt2["date"]=nt2.nt_entry_time.dt.date.astype(str)
    nt2["side"]=nt[sc].map(norm_side)
    nt2["nt_entry_price"]=pd.to_numeric(nt[epc],errors="coerce") if epc else np.nan
    nt2["nt_exit_time"]=parse_dt(nt[xc]) if xc else pd.NaT
    nt2["nt_exit_price"]=pd.to_numeric(nt[xpc],errors="coerce") if xpc else np.nan
    nt2["nt_profit"]=pd.to_numeric(nt[pc],errors="coerce") if pc else np.nan
    nt2["nt_commission"]=pd.to_numeric(nt[cc],errors="coerce") if cc else np.nan
    nt2=nt2.dropna(subset=["nt_entry_time","side"]).copy()
    nt2["entry_minute"]=nt2.nt_entry_time.dt.floor("min")

    py2=py.copy()
    py2["py_entry_time"]=pd.to_datetime(py2["entry_actual_et"],errors="coerce",utc=True)
    # Preserve clock values for minute/date matching even if exported NT CSV is local-naive.
    py2["date"]=pd.to_datetime(py2["entry_actual_et"],errors="coerce").dt.date.astype(str)
    if "direction" in py2:
        py2["side"]=pd.to_numeric(py2.direction,errors="coerce")
    else:
        raise ValueError("Golden file missing direction")
    py2["entry_minute"]=pd.to_datetime(py2["entry_actual_et"],errors="coerce").dt.tz_localize(None).dt.floor("min")

    # First compare by date+side. Duplicate same-date/same-side entries receive occurrence number.
    py2["occ"]=py2.groupby(["date","side"]).cumcount()
    nt2["occ"]=nt2.groupby(["date","side"]).cumcount()
    m=py2.merge(nt2,on=["date","side","occ"],how="outer",indicator=True)

    both=m[m["_merge"]=="both"].copy()
    py_only=m[m["_merge"]=="left_only"].copy()
    nt_only=m[m["_merge"]=="right_only"].copy()

    if len(both):
        both["entry_minute_diff"]=(
            pd.to_datetime(both["nt_entry_time"]).dt.tz_localize(None).dt.floor("min")
            - pd.to_datetime(both["entry_minute_x"]).dt.tz_localize(None)
        ).dt.total_seconds()/60.0
        both["entry_price_diff"]=both["nt_entry_price"]-pd.to_numeric(both["entry_price"],errors="coerce")
        if "exit_price" in both:
            both["exit_price_diff"]=both["nt_exit_price"]-pd.to_numeric(both["exit_price"],errors="coerce")

    expected=len(py2); actual=len(nt2)
    date_side_matches=len(both)
    match_rate=date_side_matches/expected if expected else np.nan
    count_diff=abs(actual-expected)/expected if expected else np.nan
    minute_exact=float((both.entry_minute_diff==0).mean()) if len(both) else 0.0

    report={
        "strategy":a.strategy,
        "expected_python_trades":int(expected),
        "ninjatrader_trades":int(actual),
        "date_side_matches":int(date_side_matches),
        "date_side_match_rate":float(match_rate),
        "trade_count_difference_ratio":float(count_diff),
        "exact_entry_minute_rate_among_matches":minute_exact,
        "python_only":int(len(py_only)),
        "ninjatrader_only":int(len(nt_only)),
        "passes_stage2_signal_parity":bool(match_rate>=0.99 and count_diff<=0.01),
    }

    both.to_csv(out/f"{a.strategy}_MATCHED.csv",index=False)
    py_only.to_csv(out/f"{a.strategy}_PYTHON_ONLY.csv",index=False)
    nt_only.to_csv(out/f"{a.strategy}_NINJATRADER_ONLY.csv",index=False)
    (out/f"{a.strategy}_PARITY_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
