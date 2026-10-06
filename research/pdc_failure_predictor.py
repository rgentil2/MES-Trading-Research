#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score

from research.mes_parameter_walkforward_p1 import load_development
from research.archive.B12.b12_strategy_architecture import prepare_rth
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_session_outputs
from research.mes_pdc_small_gap_reconstruction import daily_context, build_events

OUT=ROOT/"results/pdc_failure_predictor"
NEWS=ROOT/"data_external/forexfactory/usd_high_medium_2020_2024.csv"

NUMERIC=[
    "gap_atr",
    "first5_progress_frac",
    "first5_range_atr",
    "first5_efficiency",
    "first5_adverse_atr",
    "first5_volume_rvol",
]
CATEGORICAL=[
    "preopen_prediction",
    "overnight_state",
    "five_day_state_label",
    "preopen_support",
]
NEWS_FEATURES=["news_blackout_entry","news_within_30m_after_entry"]
ALL_FEATURES=NUMERIC+CATEGORICAL+NEWS_FEATURES
BASE_FEATURES=["gap_atr"]

def enrich_preentry(events,groups):
    x=events.copy()
    # Causal rolling first-five-minute volume reference.
    volrows=[]
    for key,g in groups.items():
        if len(g)<5: continue
        volrows.append({
            "group_key":key,
            "session_date":str(g.session_date.iloc[0]),
            "first5_volume":float(g.iloc[:5].volume.sum())
        })
    vd=pd.DataFrame(volrows).sort_values("session_date").reset_index(drop=True)
    vd["first5_volume_med20"]=vd.first5_volume.shift(1).rolling(20,min_periods=10).median()
    x=x.merge(vd[["group_key","first5_volume","first5_volume_med20"]],on="group_key",how="left",validate="many_to_one")

    rows=[]
    for r in x.itertuples(index=False):
        g=groups.get(r.group_key)
        if g is None or len(g)<5: continue
        b=g.iloc[:5]
        op=float(r.rth_open); pdc=float(r.pdc); atr=float(r.atr14_prev); direction=int(r.direction)
        hi=float(b.high.max()); lo=float(b.low.min()); c5=float(b.iloc[-1].close)
        gapdist=abs(op-pdc)
        progress=direction*(c5-op)/gapdist if gapdist>0 else np.nan
        rng=hi-lo
        eff=abs(c5-op)/rng if rng>0 else np.nan
        adverse=((hi-op) if direction==-1 else (op-lo))/atr if atr>0 else np.nan
        volr=(float(r.first5_volume)/float(r.first5_volume_med20)
              if np.isfinite(r.first5_volume_med20) and r.first5_volume_med20>0 else np.nan)
        rows.append({
            "group_key":r.group_key,
            "first5_progress_frac":progress,
            "first5_range_atr":rng/atr if atr>0 else np.nan,
            "first5_efficiency":eff,
            "first5_adverse_atr":max(adverse,0.0) if np.isfinite(adverse) else np.nan,
            "first5_volume_rvol":volr,
        })
    ef=pd.DataFrame(rows)
    return x.merge(ef,on="group_key",how="left",validate="one_to_one")

def add_regime(x,raw):
    s=build_session_outputs(raw)
    cols=["group_key","preopen_prediction","overnight_state","five_day_state_label","preopen_support"]
    sx=s[cols].drop_duplicates("group_key").copy()
    sx["overnight_state"]=sx["overnight_state"].map({-1.0:"LOW",0.0:"NORMAL",1.0:"HIGH"}).fillna("UNKNOWN")
    return x.merge(sx,on="group_key",how="left",validate="many_to_one")

def add_news(x):
    y=x.copy()
    y["news_blackout_entry"]=0.0
    y["news_within_30m_after_entry"]=0.0
    if not NEWS.exists():
        print("WARNING: news file missing; news features remain zero.")
        return y
    n=pd.read_csv(NEWS)
    n["event_et"]=pd.to_datetime(n["event_et"],utc=True).dt.tz_convert("America/New_York")
    n["blackout_start_et"]=pd.to_datetime(n["blackout_start_et"],utc=True).dt.tz_convert("America/New_York")
    n["blackout_end_et"]=pd.to_datetime(n["blackout_end_et"],utc=True).dt.tz_convert("America/New_York")
    bydate={d:g.copy() for d,g in n.groupby(n.event_et.dt.date.astype(str),sort=True)}
    for i,r in y.iterrows():
        et=pd.Timestamp(r.entry_ts)
        d=et.date().isoformat()
        g=bydate.get(d)
        if g is None: continue
        y.loc[i,"news_blackout_entry"]=float(((g.blackout_start_et<=et)&(et<=g.blackout_end_et)).any())
        y.loc[i,"news_within_30m_after_entry"]=float(((g.event_et>et)&(g.event_et<=et+pd.Timedelta(minutes=30))).any())
    return y

def model_pipeline(features):
    nums=[f for f in features if f in NUMERIC or f in NEWS_FEATURES]
    cats=[f for f in features if f in CATEGORICAL]
    transformers=[]
    if nums:
        transformers.append(("num",Pipeline([
            ("impute",SimpleImputer(strategy="median")),
            ("scale",StandardScaler()),
        ]),nums))
    if cats:
        transformers.append(("cat",Pipeline([
            ("impute",SimpleImputer(strategy="most_frequent")),
            ("onehot",OneHotEncoder(handle_unknown="ignore")),
        ]),cats))
    pre=ColumnTransformer(transformers,remainder="drop")
    return Pipeline([
        ("pre",pre),
        ("model",LogisticRegression(C=1.0,class_weight="balanced",max_iter=5000,random_state=42))
    ])

def loyo_predict(df,features):
    years=sorted(df.year.unique())
    pred=np.full(len(df),np.nan)
    folds=[]
    y=df.pdc_miss.astype(int).to_numpy()
    for yr in years:
        te=np.where(df.year.to_numpy()==yr)[0]
        tr=np.where(df.year.to_numpy()!=yr)[0]
        if len(te)==0 or len(tr)==0: continue
        ytr=y[tr]; yte=y[te]
        if len(np.unique(ytr))<2:
            p=np.repeat(float(np.mean(ytr)),len(te))
        else:
            m=model_pipeline(features)
            m.fit(df.iloc[tr][features],ytr)
            p=m.predict_proba(df.iloc[te][features])[:,1]
        pred[te]=p
        auc=np.nan
        ap=np.nan
        if len(np.unique(yte))==2:
            auc=float(roc_auc_score(yte,p))
            ap=float(average_precision_score(yte,p))
        folds.append({
            "heldout_year":int(yr),
            "test_n":int(len(te)),
            "misses":int(yte.sum()),
            "miss_rate":float(yte.mean()),
            "auc":auc,
            "average_precision":ap,
        })
    mask=np.isfinite(pred)
    pooled_auc=float(roc_auc_score(y[mask],pred[mask])) if len(np.unique(y[mask]))==2 else np.nan
    pooled_ap=float(average_precision_score(y[mask],pred[mask])) if mask.sum() else np.nan
    return pred,pd.DataFrame(folds),pooled_auc,pooled_ap

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    daily=daily_context(groups)
    t=build_events(groups,daily)
    if t.empty: raise ValueError("no PDC events")
    if t.year.max()>2025: raise ValueError("2026 leak")
    t=enrich_preentry(t,groups)
    t=add_regime(t,raw)
    t=add_news(t)
    t["pdc_miss"]=(~t.target_hit.astype(bool)).astype(int)
    t=t.sort_values("entry_ts").reset_index(drop=True)

    pb,fb,auc_b,ap_b=loyo_predict(t,BASE_FEATURES)
    pe,fe,auc_e,ap_e=loyo_predict(t,ALL_FEATURES)
    t["pred_gap_only_oof"]=pb
    t["pred_expanded_oof"]=pe

    valid=t[np.isfinite(t.pred_expanded_oof)].copy()
    rank=valid.pred_expanded_oof.rank(method="first",pct=True)
    bottom=valid[rank<=1/3]
    top=valid[rank>2/3]
    top_miss=float(top.pdc_miss.mean()) if len(top) else np.nan
    bot_miss=float(bottom.pdc_miss.mean()) if len(bottom) else np.nan
    risk_ratio=(top_miss/bot_miss) if np.isfinite(bot_miss) and bot_miss>0 else np.inf
    good_folds=int((fe.auc>0.50).sum())
    base_miss=float(t.pdc_miss.mean())

    gate={
      "expanded_auc_ge_062":bool(np.isfinite(auc_e) and auc_e>=0.62),
      "auc_lift_ge_005":bool(np.isfinite(auc_e) and np.isfinite(auc_b) and auc_e-auc_b>=0.05),
      "ap_lift_over_base_rate_ge_005":bool(np.isfinite(ap_e) and ap_e-base_miss>=0.05),
      "four_folds_auc_gt_050":bool(good_folds>=4),
      "top_bottom_miss_ratio_ge_15":bool(np.isfinite(risk_ratio) and risk_ratio>=1.5),
    }

    # Descriptive full-sample standardized coefficients, not used for selection.
    full=model_pipeline(ALL_FEATURES)
    full.fit(t[ALL_FEATURES],t.pdc_miss.astype(int))
    pre=full.named_steps["pre"]
    fn=list(pre.get_feature_names_out())
    co=full.named_steps["model"].coef_[0]
    coef=pd.DataFrame({"encoded_feature":fn,"coef":co})
    coef["abs_coef"]=coef.coef.abs()
    coef=coef.sort_values("abs_coef",ascending=False)

    OUT.mkdir(parents=True,exist_ok=True)
    t.to_csv(OUT/"PDC_FAILURE_EVENTS.csv",index=False)
    fb.assign(model="gap_only").to_csv(OUT/"PDC_FAILURE_FOLDS_BASE.csv",index=False)
    fe.assign(model="expanded").to_csv(OUT/"PDC_FAILURE_FOLDS_EXPANDED.csv",index=False)
    coef.to_csv(OUT/"PDC_FAILURE_COEFFICIENTS_DESCRIPTIVE.csv",index=False)

    summary={
      "authority":"DIAGNOSTIC_ONLY",
      "contract_2026_opened":False,
      "events":int(len(t)),
      "misses":int(t.pdc_miss.sum()),
      "unconditional_miss_rate":base_miss,
      "gap_only_oof_auc":auc_b,
      "gap_only_oof_average_precision":ap_b,
      "expanded_oof_auc":auc_e,
      "expanded_oof_average_precision":ap_e,
      "auc_lift_vs_gap_only":auc_e-auc_b if np.isfinite(auc_e) and np.isfinite(auc_b) else np.nan,
      "folds_auc_gt_050":good_folds,
      "top_risk_tercile_n":int(len(top)),
      "top_risk_tercile_miss_rate":top_miss,
      "top_risk_tercile_net_pnl_usd":float(top.net_pnl_usd.sum()) if len(top) else np.nan,
      "bottom_risk_tercile_n":int(len(bottom)),
      "bottom_risk_tercile_miss_rate":bot_miss,
      "bottom_risk_tercile_net_pnl_usd":float(bottom.net_pnl_usd.sum()) if len(bottom) else np.nan,
      "top_bottom_miss_risk_ratio":risk_ratio,
      **gate,
      "passes_second_stage_filter_gate":bool(all(gate.values())),
    }
    (OUT/"PDC_FAILURE_REPORT.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    print(json.dumps(summary,indent=2,allow_nan=False))
    print("\nEXPANDED FOLDS\n",fe.to_string(index=False))
    print("\nTOP COEFFICIENTS DESCRIPTIVE\n",coef.head(15).to_string(index=False))

if __name__=="__main__":
    main()
