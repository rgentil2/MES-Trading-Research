#!/usr/bin/env python3
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.mes_parameter_walkforward_p1 import load_development
from research.archive.B12.b12_strategy_architecture import prepare_rth
from src.research_utils import rth_mask

TARGETS=[
"2021-08-24","2021-11-25","2022-08-30","2023-04-05","2023-05-29",
"2023-07-04","2025-02-17","2025-07-04","2025-12-17"
]

def main():
    raw=load_development().copy()
    d=raw[rth_mask(raw["timestamp_et"])].copy()
    d["session_date"]=d["timestamp_et"].dt.date.astype(str)
    d["minute"]=d["timestamp_et"].dt.hour*60+d["timestamp_et"].dt.minute
    _,groups=prepare_rth(raw)

    rows=[]
    missing_rows=[]
    expected=set(range(571,961))
    for date in TARGETS:
        x=d[d.session_date==date].copy().sort_values("timestamp_et")
        if x.empty:
            rows.append({"date":date,"raw_rth_rows":0,"contracts":"","complete_groups":0,"reason":"NO_RTH_ROWS"})
            continue
        complete_keys=[k for k in groups if k.startswith(date+"|")]
        for contract,g in x.groupby("contract",sort=False):
            mins=g["minute"].astype(int).tolist()
            unique=set(mins)
            missing=sorted(expected-unique)
            dup=len(mins)-len(unique)
            rows.append({
                "date":date,
                "contract":str(contract),
                "raw_rth_rows":int(len(g)),
                "unique_minutes":int(len(unique)),
                "first_ts":str(g.timestamp_et.iloc[0]),
                "last_ts":str(g.timestamp_et.iloc[-1]),
                "first_minute":int(mins[0]),
                "last_minute":int(mins[-1]),
                "missing_minutes":int(len(missing)),
                "duplicate_minutes":int(dup),
                "complete_in_python":bool(f"{date}|{contract}" in groups),
                "complete_groups_on_date":int(len(complete_keys)),
                "first_missing":",".join(map(str,missing[:12]))
            })
    out=ROOT/"results/pdc_nt_extra_diagnostic"
    out.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(rows)
    df.to_csv(out/"EXTRA_DATE_COMPLETENESS.csv",index=False)
    print(df.to_string(index=False))

if __name__=="__main__":
    main()
