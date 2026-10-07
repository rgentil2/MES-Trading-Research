#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_REF=ROOT/"results/r072_engine_reference/R072_ENGINE_BLOCK_REFERENCE.csv"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ninjatrader-audit",required=True)
    ap.add_argument("--reference",default=str(DEFAULT_REF))
    ap.add_argument("--output-dir",default="results/r072_engine_audit_compare")
    ap.add_argument("--numeric-tolerance",type=float,default=1e-6)
    a=ap.parse_args()

    nt=pd.read_csv(a.ninjatrader_audit)
    ref=pd.read_csv(a.reference)
    out=ROOT/a.output_dir
    out.mkdir(parents=True,exist_ok=True)

    nt["session_date"]=nt["session_date"].astype(str)
    ref["session_date"]=ref["session_date"].astype(str)

    keep_ref=[
        "session_date","block_id","block_end_et","range15_bps","q20","q80",
        "raw_state","engine_state","h017_time","upper_wick_ratio",
        "lower_wick_ratio","r072_candidate_direction"
    ]
    ref=ref[keep_ref].copy()

    m=ref.merge(
        nt,
        on=["session_date","block_id"],
        how="outer",
        suffixes=("_py","_nt"),
        indicator=True,
    )

    both=m[m["_merge"]=="both"].copy()
    py_only=m[m["_merge"]=="left_only"].copy()
    nt_only=m[m["_merge"]=="right_only"].copy()

    tol=float(a.numeric_tolerance)
    numeric_pairs=[
        ("range15_bps_py","range15_bps_nt","range_match"),
        ("q20_py","q20_nt","q20_match"),
        ("q80_py","q80_nt","q80_match"),
        ("upper_wick_ratio_py","upper_wick_ratio_nt","upper_wick_match"),
        ("lower_wick_ratio_py","lower_wick_ratio_nt","lower_wick_match"),
    ]
    for pc,nc,mc in numeric_pairs:
        p=pd.to_numeric(both[pc],errors="coerce")
        n=pd.to_numeric(both[nc],errors="coerce")
        both[mc]=(
            (p.isna()&n.isna())
            | ((p-n).abs()<=tol)
        )

    both["raw_state_match"]=both.raw_state_py.fillna("").eq(both.raw_state_nt.fillna(""))
    both["engine_state_match"]=both.engine_state_py.fillna("").eq(both.engine_state_nt.fillna(""))
    both["direction_match"]=pd.to_numeric(
        both.r072_candidate_direction_py,errors="coerce"
    ).eq(pd.to_numeric(both.candidate_direction,errors="coerce"))

    # H017 is compared by clock string; blank/NaN means no event.
    pht=pd.to_datetime(both.h017_time_py,errors="coerce")
    nht=pd.to_datetime(both.h017_time_nt,errors="coerce")
    both["h017_match"]=(
        (pht.isna()&nht.isna())
        | (pht.dt.floor("min")==nht.dt.floor("min"))
    )

    matched=len(both)
    expected=len(ref)
    actual=len(nt)

    report={
        "python_reference_blocks":int(expected),
        "ninjatrader_blocks":int(actual),
        "common_blocks":int(matched),
        "python_only_blocks":int(len(py_only)),
        "ninjatrader_only_blocks":int(len(nt_only)),
        "common_block_rate":float(matched/expected) if expected else np.nan,
    }

    for col in [
        "range_match","q20_match","q80_match","raw_state_match",
        "engine_state_match","h017_match","upper_wick_match",
        "lower_wick_match","direction_match"
    ]:
        report[col+"_rate"]=float(both[col].mean()) if matched else 0.0

    report["passes_block_state_parity"]=bool(
        report["common_block_rate"]>=0.99
        and report["raw_state_match_rate"]>=0.99
        and report["engine_state_match_rate"]>=0.99
        and report["direction_match_rate"]>=0.99
    )

    mismatch_cols=[
        "range_match","q20_match","q80_match","raw_state_match",
        "engine_state_match","h017_match","upper_wick_match",
        "lower_wick_match","direction_match"
    ]
    mismatches=both[~both[mismatch_cols].all(axis=1)].copy()

    both.to_csv(out/"R072_ENGINE_MATCHED.csv",index=False)
    mismatches.to_csv(out/"R072_ENGINE_MISMATCHES.csv",index=False)
    py_only.to_csv(out/"R072_ENGINE_PYTHON_ONLY.csv",index=False)
    nt_only.to_csv(out/"R072_ENGINE_NINJATRADER_ONLY.csv",index=False)
    (out/"R072_ENGINE_PARITY_REPORT.json").write_text(
        json.dumps(report,indent=2,allow_nan=False)+"\n"
    )

    print(json.dumps(report,indent=2,allow_nan=False))
    if len(mismatches):
        print("\nFIRST MISMATCHES")
        cols=[
            "session_date","block_id",
            "range15_bps_py","range15_bps_nt",
            "q20_py","q20_nt","q80_py","q80_nt",
            "raw_state_py","raw_state_nt",
            "engine_state_py","engine_state_nt",
            "h017_time_py","h017_time_nt",
            "r072_candidate_direction_py","candidate_direction",
        ]
        print(mismatches[[c for c in cols if c in mismatches]].head(25).to_string(index=False))

if __name__=="__main__":
    main()
