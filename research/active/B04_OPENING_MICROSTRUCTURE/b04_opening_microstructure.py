from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from src.research_utils import benjamini_hochberg, clustered_mean_stats, prepare_rth_features

REF=60
H038_Q=0.80
H038_BODY_MIN=0.70
H039_RANGE_Q=0.70
H039_WICK_MIN=0.50
H040_Q=0.80
H041_Q=0.20
H042_VOLUME_Q=0.70

def build_session_features(raw):
    rth=prepare_rth_features(raw,"2020-01-01","2025-12-31",horizons=[15,30])
    rows=[]
    for key,g in rth.groupby("group_key",sort=False,observed=True):
        g=g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g)!=390:
            continue
        mins=g["timestamp_et"].dt.hour*60+g["timestamp_et"].dt.minute
        if int(mins.iloc[0])!=571 or int(mins.iloc[-1])!=960:
            continue

        # First 5 minutes: 09:31-09:35
        f5=g.iloc[:5]
        open5=float(f5["open"].iloc[0]); close5=float(f5["close"].iloc[-1])
        high5=float(f5["high"].max()); low5=float(f5["low"].min())
        range5=high5-low5
        if open5<=0 or range5<=0:
            continue
        ret5=float(np.log(close5/open5))
        body5=abs(close5-open5)
        body_ratio=body5/range5
        upper_wick=(high5-max(open5,close5))/range5
        lower_wick=(min(open5,close5)-low5)/range5
        range5_bps=range5/open5*10000.0

        # Return from 09:35 close to 09:50 close.
        close0950=float(g["close"].iloc[19])
        fwd15_from5=float(np.log(close0950/close5)*10000.0)

        # First 15 minutes: 09:31-09:45
        f15=g.iloc[:15]
        close15=float(f15["close"].iloc[-1])
        range15_bps=float((f15["high"].max()-f15["low"].min())/float(f15["open"].iloc[0])*10000.0)

        # Next 30 minutes: 09:46-10:15
        next30=g.iloc[15:45]
        if len(next30)!=30:
            continue
        future30_range_bps=float((next30["high"].max()-next30["low"].min())/close15*10000.0)

        # First 3 bars sequence and 09:33->09:48 return.
        f3=g.iloc[:3]
        candle_ret=(f3["close"]-f3["open"]).to_numpy(float)
        all_up=bool(np.all(candle_ret>0))
        all_down=bool(np.all(candle_ret<0))
        seq_dir=1 if all_up else (-1 if all_down else 0)
        vol3=float(f3["volume"].sum())
        close0933=float(g["close"].iloc[2])
        close0948=float(g["close"].iloc[17])
        seq_fwd15=float(np.log(close0948/close0933)*10000.0)

        rows.append({
            "group_key":key,
            "session_date":g["session_date"].iloc[0],
            "year":int(g["year"].iloc[0]),
            "contract":g["contract"].iloc[0],
            "first_ts":g["timestamp_et"].iloc[0],
            "ret5":ret5,
            "body_ratio5":body_ratio,
            "upper_wick_ratio5":upper_wick,
            "lower_wick_ratio5":lower_wick,
            "range5_bps":range5_bps,
            "fwd15_from5_bps":fwd15_from5,
            "range15_bps":range15_bps,
            "future30_range_bps":future30_range_bps,
            "seq3_direction":seq_dir,
            "vol3":vol3,
            "seq_fwd15_bps":seq_fwd15,
        })

    s=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    s["abs_ret5_q80"]=s["ret5"].abs().shift(1).rolling(REF,min_periods=REF).quantile(H038_Q)
    s["range5_q70"]=s["range5_bps"].shift(1).rolling(REF,min_periods=REF).quantile(H039_RANGE_Q)
    s["range15_q80"]=s["range15_bps"].shift(1).rolling(REF,min_periods=REF).quantile(H040_Q)
    s["range15_q20"]=s["range15_bps"].shift(1).rolling(REF,min_periods=REF).quantile(H041_Q)
    s["future30_baseline"]=s["future30_range_bps"].shift(1).rolling(REF,min_periods=REF).mean()
    s["vol3_q70"]=s["vol3"].shift(1).rolling(REF,min_periods=REF).quantile(H042_VOLUME_Q)
    return s

def summarize(h,e,metric,min_n,min_mean):
    y=e[metric]
    st=clustered_mean_stats(y,e["session_date"])
    yearly=e.groupby("year",observed=True)[metric].mean().reset_index(name="mean_effect")
    return {
        "hypothesis":h,
        "n":int(len(e)),
        "sessions":int(e["session_date"].nunique()),
        "mean_effect":float(y.mean()) if len(y) else np.nan,
        "median_effect":float(y.median()) if len(y) else np.nan,
        **st,
        "positive_rate":float((y>0).mean()) if len(y) else np.nan,
        "years_positive":int((yearly["mean_effect"]>0).sum()),
        "years_observed":int(yearly["year"].nunique()),
        "min_n_gate":min_n,
        "min_mean_gate":min_mean,
    },yearly

def h038(s):
    e=s[s["abs_ret5_q80"].notna()&(s["ret5"].abs()>=s["abs_ret5_q80"])&
        (s["body_ratio5"]>=H038_BODY_MIN)&(s["ret5"]!=0)].copy()
    e["effect"]=np.sign(e["ret5"])*e["fwd15_from5_bps"]
    return e,*summarize("H038",e,"effect",150,1.0)

def h039(s):
    upper=(s["upper_wick_ratio5"]>=H039_WICK_MIN)&(s["ret5"]<0)
    lower=(s["lower_wick_ratio5"]>=H039_WICK_MIN)&(s["ret5"]>0)
    e=s[s["range5_q70"].notna()&(s["range5_bps"]>=s["range5_q70"])&(upper|lower)].copy()
    e["expected_direction"]=np.where(upper.loc[e.index],-1,1)
    e["effect"]=e["expected_direction"]*e["fwd15_from5_bps"]
    return e,*summarize("H039",e,"effect",100,1.0)

def h040(s):
    e=s[s["range15_q80"].notna()&s["future30_baseline"].notna()&(s["future30_baseline"]>0)&
        (s["range15_bps"]>=s["range15_q80"])].copy()
    e["effect"]=(e["future30_range_bps"]/e["future30_baseline"]-1)*100
    return e,*summarize("H040",e,"effect",200,10.0)

def h041(s):
    e=s[s["range15_q20"].notna()&s["future30_baseline"].notna()&(s["future30_baseline"]>0)&
        (s["range15_bps"]<=s["range15_q20"])].copy()
    e["effect"]=(1-e["future30_range_bps"]/e["future30_baseline"])*100
    return e,*summarize("H041",e,"effect",200,10.0)

def h042(s):
    e=s[s["vol3_q70"].notna()&(s["seq3_direction"]!=0)&(s["vol3"]>=s["vol3_q70"])].copy()
    e["effect"]=e["seq3_direction"]*e["seq_fwd15_bps"]
    return e,*summarize("H042",e,"effect",100,1.0)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B04")
    a=p.parse_args()
    s=build_session_features(pd.read_parquet(a.input))
    results=[]; yearly=[]; events=[]
    for h,fn in [("H038",h038),("H039",h039),("H040",h040),("H041",h041),("H042",h042)]:
        e,row,y=fn(s)
        results.append(row); y["hypothesis"]=h
        yearly.append(y); events.append((h,e))

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
    for h,e in events:
        e.to_parquet(out/f"{h}_events.parquet",index=False)
    pd.concat(yearly,ignore_index=True).to_csv(out/"yearly.csv",index=False)
    summary.to_csv(out/"B04_SUMMARY.csv",index=False)
    print(summary.to_string(index=False))

if __name__=="__main__":
    main()
