#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
GOLD=ROOT/"results/mes_stage2_parity"

ALIASES={
    "entry_time":["Entry time","Entry Time","entry_time","EntryTime"],
    "exit_time":["Exit time","Exit Time","exit_time","ExitTime"],
    "side":["Market position","Market Position","Market pos.","market_position","Side","side"],
    "entry_price":["Entry price","Entry Price","entry_price","EntryPrice"],
    "exit_price":["Exit price","Exit Price","exit_price","ExitPrice"],
    "profit":["Profit","profit","PnL","P&L","Net profit","Net Profit"],
    "commission":["Commission","commission","Commissions","commissions"],
    "entry_name":["Entry name","Entry Name","entry_name"],
    "exit_name":["Exit name","Exit Name","exit_name"],
}

def detect_separator(path: Path) -> str:
    with path.open("r",encoding="utf-8-sig",errors="replace") as fh:
        line=fh.readline()
    return ";" if line.count(";")>line.count(",") else ","

def read_nt_csv(path: Path) -> pd.DataFrame:
    sep=detect_separator(path)
    return pd.read_csv(path,sep=sep,encoding="utf-8-sig",engine="python")

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

def parse_num(v):
    if pd.isna(v):
        return np.nan
    s=str(v).replace("\u00a0"," ").strip()
    # Strip currency and everything except numeric separators/sign.
    s=re.sub(r"[^0-9,\.\-+]","",s)
    if not s:
        return np.nan
    if "," in s and "." in s:
        # Infer decimal separator from the right-most separator.
        if s.rfind(",")>s.rfind("."):
            s=s.replace(".","").replace(",",".")
        else:
            s=s.replace(",","")
    elif "," in s:
        s=s.replace(",",".")
    try:
        return float(s)
    except ValueError:
        return np.nan

def parse_dt_value(v):
    if pd.isna(v):
        return pd.NaT
    s=str(v).replace("\u00a0"," ").strip().lower()
    # NinjaTrader localized export may use: '9:36:00 a m', '9:36:00 a. m.'
    s=re.sub(r"\ba\s*\.?\s*m\.?\b","AM",s,flags=re.I)
    s=re.sub(r"\bp\s*\.?\s*m\.?\b","PM",s,flags=re.I)
    s=re.sub(r"\s+"," ",s).strip()
    # day-first is necessary for the user's localized NinjaTrader export.
    return pd.to_datetime(s,errors="coerce",dayfirst=True)

def parse_dt(series):
    return series.map(parse_dt_value)

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
    nt=read_nt_csv(Path(a.ninjatrader_csv))
    out=ROOT/a.output_dir
    out.mkdir(parents=True,exist_ok=True)

    ec=find_col(nt,"entry_time")
    xc=find_col(nt,"exit_time")
    sc=find_col(nt,"side")
    epc=find_col(nt,"entry_price")
    xpc=find_col(nt,"exit_price")
    pc=find_col(nt,"profit")
    cc=find_col(nt,"commission")
    enc=find_col(nt,"entry_name")
    exc=find_col(nt,"exit_name")

    if ec is None or sc is None:
        raise ValueError(
            "NinjaTrader CSV must contain Entry time and Market pos./Side. "
            f"Detected separator and columns: {list(nt.columns)}"
        )

    nt2=pd.DataFrame()
    nt2["nt_entry_time"]=parse_dt(nt[ec])
    nt2["date"]=nt2.nt_entry_time.dt.date.astype(str)
    nt2["side"]=nt[sc].map(norm_side)
    nt2["nt_entry_price"]=nt[epc].map(parse_num) if epc else np.nan
    nt2["nt_exit_time"]=parse_dt(nt[xc]) if xc else pd.NaT
    nt2["nt_exit_price"]=nt[xpc].map(parse_num) if xpc else np.nan
    nt2["nt_profit"]=nt[pc].map(parse_num) if pc else np.nan
    nt2["nt_commission"]=nt[cc].map(parse_num) if cc else np.nan
    nt2["nt_entry_name"]=nt[enc].astype(str) if enc else ""
    nt2["nt_exit_name"]=nt[exc].astype(str) if exc else ""
    nt2=nt2.dropna(subset=["nt_entry_time","side"]).copy()
    nt2["nt_entry_minute"]=nt2.nt_entry_time.dt.floor("min")

    py2=py.copy()
    py2["py_entry_time"]=pd.to_datetime(py2["entry_actual_et"],errors="coerce",utc=True)
    py_clock=pd.to_datetime(py2["entry_actual_et"],errors="coerce")
    # Preserve wall clock values for comparison with local-naive NinjaTrader export.
    if getattr(py_clock.dt,"tz",None) is not None:
        py_clock=py_clock.dt.tz_localize(None)
    py2["date"]=py_clock.dt.date.astype(str)
    if "direction" not in py2:
        raise ValueError("Golden file missing direction")
    py2["side"]=pd.to_numeric(py2.direction,errors="coerce")
    py2["py_entry_minute"]=py_clock.dt.floor("min")

    py2["occ"]=py2.groupby(["date","side"]).cumcount()
    nt2["occ"]=nt2.groupby(["date","side"]).cumcount()
    m=py2.merge(nt2,on=["date","side","occ"],how="outer",indicator=True)

    both=m[m["_merge"]=="both"].copy()
    py_only=m[m["_merge"]=="left_only"].copy()
    nt_only=m[m["_merge"]=="right_only"].copy()

    if len(both):
        both["entry_minute_diff"]=(
            pd.to_datetime(both["nt_entry_minute"])
            - pd.to_datetime(both["py_entry_minute"])
        ).dt.total_seconds()/60.0
        both["entry_price_diff"]=both["nt_entry_price"]-pd.to_numeric(both["entry_price"],errors="coerce")
        both["entry_price_exact"]=both["entry_price_diff"].abs()<=1e-9

        if "exit_price" in both:
            both["exit_price_diff"]=both["nt_exit_price"]-pd.to_numeric(both["exit_price"],errors="coerce")
            both["exit_price_exact"]=both["exit_price_diff"].abs()<=1e-9

        if "exit_ts" in both:
            py_exit=pd.to_datetime(both["exit_ts"],errors="coerce")
            try:
                py_exit=py_exit.dt.tz_localize(None)
            except TypeError:
                pass
            both["exit_minute_diff"]=(
                pd.to_datetime(both["nt_exit_time"]).dt.floor("min")
                - py_exit.dt.floor("min")
            ).dt.total_seconds()/60.0

    expected=len(py2)
    actual=len(nt2)
    date_side_matches=len(both)
    match_rate=date_side_matches/expected if expected else np.nan
    count_diff=abs(actual-expected)/expected if expected else np.nan
    entry_price_rate=float(both.entry_price_exact.mean()) if len(both) else 0.0

    if len(both):
        offsets=both.entry_minute_diff.dropna()
        if len(offsets):
            mode=float(offsets.mode().iloc[0])
            mode_rate=float((offsets==mode).mean())
        else:
            mode=np.nan
            mode_rate=np.nan
    else:
        mode=np.nan
        mode_rate=np.nan

    exit_price_rate=(
        float(both.exit_price_exact.mean())
        if len(both) and "exit_price_exact" in both
        else np.nan
    )

    report={
        "strategy":a.strategy,
        "expected_python_trades":int(expected),
        "ninjatrader_trades":int(actual),
        "date_side_matches":int(date_side_matches),
        "date_side_match_rate":float(match_rate),
        "trade_count_difference_ratio":float(count_diff),
        "entry_price_exact_rate":entry_price_rate,
        "modal_entry_timestamp_offset_minutes":None if not np.isfinite(mode) else mode,
        "modal_entry_timestamp_offset_rate":None if not np.isfinite(mode_rate) else mode_rate,
        "exit_price_exact_rate":None if not np.isfinite(exit_price_rate) else exit_price_rate,
        "python_only":int(len(py_only)),
        "ninjatrader_only":int(len(nt_only)),
        "passes_stage2_signal_parity":bool(
            match_rate>=0.99
            and count_diff<=0.01
            and entry_price_rate>=0.99
        ),
    }

    both.to_csv(out/f"{a.strategy}_MATCHED.csv",index=False)
    py_only.to_csv(out/f"{a.strategy}_PYTHON_ONLY.csv",index=False)
    nt_only.to_csv(out/f"{a.strategy}_NINJATRADER_ONLY.csv",index=False)
    (out/f"{a.strategy}_PARITY_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
