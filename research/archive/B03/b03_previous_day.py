from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from src.research_utils import benjamini_hochberg, clustered_mean_stats, prepare_rth_features

REF=60
NARROW_Q=0.20
WIDE_Q=0.80
TREND_Q=0.75
TREND_EFF_MIN=0.35
LATE_Q=0.80
VWAP_Q=0.80

def session_features(raw):
    rth=prepare_rth_features(raw,"2020-01-01","2025-12-31",horizons=[30])
    rows=[]
    for key,g in rth.groupby("group_key",sort=False,observed=True):
        g=g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g)!=390:
            continue
        mins=g["timestamp_et"].dt.hour*60+g["timestamp_et"].dt.minute
        if int(mins.iloc[0])!=571 or int(mins.iloc[-1])!=960:
            continue

        op=float(g["open"].iloc[0]); cl=float(g["close"].iloc[-1])
        hi=float(g["high"].max()); lo=float(g["low"].min())
        if op<=0 or cl<=0 or hi<=lo:
            continue

        first_ret=float(np.log(g["close"].iloc[0]/op))
        pc=g["close"].shift(1)
        exact=g["timestamp_et"].diff()==pd.Timedelta(minutes=1)
        rr=np.log(g.loc[exact,"close"].to_numpy(float)/pc.loc[exact].to_numpy(float))
        path_abs=abs(first_ret)+float(np.abs(rr).sum())
        day_ret=float(np.log(cl/op))
        efficiency=abs(day_ret)/path_abs if path_abs>0 else np.nan
        clv=float((cl-lo)/(hi-lo))

        tp=(g["high"].to_numpy(float)+g["low"].to_numpy(float)+g["close"].to_numpy(float))/3.0
        vol=g["volume"].to_numpy(float)
        vwap=float(np.sum(tp*vol)/np.sum(vol)) if np.sum(vol)>0 else np.nan
        stretch=float(np.log(cl/vwap)) if np.isfinite(vwap) and vwap>0 else np.nan

        late=g[mins>=931].copy()
        if len(late)!=30:
            continue
        late_ret=float(np.log(late["close"].iloc[-1]/late["open"].iloc[0]))

        first30=g.iloc[:30]
        opening_range=float((first30["high"].max()-first30["low"].min())/float(first30["open"].iloc[0])*10000.0)
        opening_ret=float(np.log(float(first30["close"].iloc[-1])/float(first30["open"].iloc[0]))*10000.0)

        rows.append({
            "group_key":key,
            "session_date":g["session_date"].iloc[0],
            "year":int(g["year"].iloc[0]),
            "contract":g["contract"].iloc[0],
            "first_ts":g["timestamp_et"].iloc[0],
            "range_bps":(hi-lo)/cl*10000.0,
            "day_return":day_ret,
            "day_efficiency":efficiency,
            "clv":clv,
            "vwap_stretch":stretch,
            "late_return":late_ret,
            "opening_range_bps":opening_range,
            "opening_return_bps":opening_ret,
        })

    s=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)

    for col in ["contract","range_bps","day_return","day_efficiency","clv","vwap_stretch","late_return"]:
        s[f"prev_{col}"]=s[col].shift(1)

    same=s["contract"]==s["prev_contract"]
    for col in ["prev_range_bps","prev_day_return","prev_day_efficiency","prev_clv","prev_vwap_stretch","prev_late_return"]:
        s.loc[~same,col]=np.nan

    # For a current session, previous-day thresholds may only use sessions before that previous day.
    s["prev_range_q20"]=s["range_bps"].shift(2).rolling(REF,min_periods=REF).quantile(NARROW_Q)
    s["prev_range_q80"]=s["range_bps"].shift(2).rolling(REF,min_periods=REF).quantile(WIDE_Q)
    s["prev_abs_return_q75"]=s["day_return"].abs().shift(2).rolling(REF,min_periods=REF).quantile(TREND_Q)
    s["prev_abs_late_q80"]=s["late_return"].abs().shift(2).rolling(REF,min_periods=REF).quantile(LATE_Q)
    s["prev_abs_vwap_q80"]=s["vwap_stretch"].abs().shift(2).rolling(REF,min_periods=REF).quantile(VWAP_Q)

    # Current opening-range baseline uses completed sessions only.
    s["opening_range_baseline"]=s["opening_range_bps"].shift(1).rolling(REF,min_periods=REF).mean()
    return s

def summarize(h,e,metric,min_n,min_mean):
    y=e[metric]
    st=clustered_mean_stats(y,e["session_date"])
    yearly=e.groupby("year",observed=True)[metric].mean().reset_index(name="mean_effect")
    row={
        "hypothesis":h,"n":int(len(e)),"sessions":int(e["session_date"].nunique()),
        "mean_effect":float(y.mean()) if len(y) else np.nan,
        "median_effect":float(y.median()) if len(y) else np.nan,
        **st,
        "positive_rate":float((y>0).mean()) if len(y) else np.nan,
        "years_positive":int((yearly["mean_effect"]>0).sum()),
        "years_observed":int(yearly["year"].nunique()),
        "min_n_gate":min_n,"min_mean_gate":min_mean,
    }
    return row,yearly

def h033(s):
    e=s[s["prev_range_bps"].notna()&s["prev_range_q20"].notna()&s["opening_range_baseline"].notna()&
        (s["opening_range_baseline"]>0)&(s["prev_range_bps"]<=s["prev_range_q20"])].copy()
    e["effect"]=(1-e["opening_range_bps"]/e["opening_range_baseline"])*100
    return e,*summarize("H033",e,"effect",200,10.0)

def h034(s):
    e=s[s["prev_range_bps"].notna()&s["prev_range_q80"].notna()&s["opening_range_baseline"].notna()&
        (s["opening_range_baseline"]>0)&(s["prev_range_bps"]>=s["prev_range_q80"])].copy()
    e["effect"]=(e["opening_range_bps"]/e["opening_range_baseline"]-1)*100
    return e,*summarize("H034",e,"effect",200,10.0)

def h035(s):
    aligned=((s["prev_day_return"]>0)&(s["prev_clv"]>=0.80))|((s["prev_day_return"]<0)&(s["prev_clv"]<=0.20))
    e=s[s["prev_abs_return_q75"].notna()&s["prev_day_return"].notna()&s["prev_day_efficiency"].notna()&
        aligned&(s["prev_day_return"].abs()>=s["prev_abs_return_q75"])&(s["prev_day_efficiency"]>=TREND_EFF_MIN)].copy()
    e["effect"]=np.sign(e["prev_day_return"])*e["opening_return_bps"]
    return e,*summarize("H035",e,"effect",150,1.0)

def h036(s):
    e=s[s["prev_abs_late_q80"].notna()&s["prev_late_return"].notna()&(s["prev_late_return"]!=0)&
        (s["prev_late_return"].abs()>=s["prev_abs_late_q80"])].copy()
    e["effect"]=np.sign(e["prev_late_return"])*e["opening_return_bps"]
    return e,*summarize("H036",e,"effect",200,1.0)

def h037(s):
    e=s[s["prev_abs_vwap_q80"].notna()&s["prev_vwap_stretch"].notna()&(s["prev_vwap_stretch"]!=0)&
        (s["prev_vwap_stretch"].abs()>=s["prev_abs_vwap_q80"])].copy()
    e["effect"]=-np.sign(e["prev_vwap_stretch"])*e["opening_return_bps"]
    return e,*summarize("H037",e,"effect",200,1.0)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B03")
    a=p.parse_args()
    s=session_features(pd.read_parquet(a.input))

    results=[]; yearly_parts=[]; event_parts=[]
    for h,fn in [("H033",h033),("H034",h034),("H035",h035),("H036",h036),("H037",h037)]:
        e,row,y=fn(s)
        results.append(row); y["hypothesis"]=h
        yearly_parts.append(y); event_parts.append((h,e))

    summary=pd.DataFrame(results)
    summary["q_value_bh"]=benjamini_hochberg(summary["p_value"])
    summary["passes_individual_gate"]=(
        (summary["n"]>=summary["min_n_gate"])&
        (summary["mean_effect"]>=summary["min_mean_gate"])&
        (summary["ci_low"]>0)&
        (summary["years_observed"]==6)&
        (summary["years_positive"]>=4)
    )
    summary["passes_block_gate"]=summary["passes_individual_gate"]&(summary["q_value_bh"]<0.05)

    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    s.to_parquet(out/"session_features.parquet",index=False)
    for h,e in event_parts:
        e.to_parquet(out/f"{h}_events.parquet",index=False)
    pd.concat(yearly_parts,ignore_index=True).to_csv(out/"yearly.csv",index=False)
    summary.to_csv(out/"B03_SUMMARY.csv",index=False)
    print(summary.to_string(index=False))

if __name__=="__main__":
    main()
