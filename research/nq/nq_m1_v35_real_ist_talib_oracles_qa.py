#!/usr/bin/env python3
"""S0.30 independent TA-Lib numeric spot-check on AUTHORIZED REAL NQ IST M1.

This tool only computes unparameterized formula agreement at 2 fixed indices
over 15 fixed sessions; NEVER evaluates a strategy expression, signal, entry,
exit, model fill, PnL, fitness, or candidate ranking. Only 2020-2022 whitelisted
archive members are read after verifying frozen original ZIP SHA256.
Neither 2023/24 validation nor 2025/26 sealed data are opened.

Numerical agreement at these 330 parameter-index observations does NOT
certify the other indicator names, every parameter range or NinjaTrader.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import json
import numpy as np
import talib
from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v22_contract_provenance import metadata_for_sessions
from research.nq.nq_m1_v23_source_contract_qa import inspect_archive_manifest
from research.nq.nq_m1_v26_all_132_router import value as formula
from research.nq.nq_m1_v32_real_ist_source_readonly_qa import (
    EXPECTED_SHA256,ALLOWED_YEARS,EXPECTED,_gate,_validate_source,sha_file
)

STATUS="S0_30_REAL_IST_M1_TALIB_NUMERIC_ORACLES_11_NAMES_NO_STRATEGIES_NO_PNL"
INDEXES=(118,389)
NAMES=("SMA","EMA","WMA","DEMA","TEMA","TRIMA",
       "APO","TRIX","ATR","NATR","ADXR")
TOL={"ADXR":.20,"APO":.025}
BASE_TOL=.001

def references(g:np.ndarray):
    o,h,l,c=g[:,0],g[:,1],g[:,2],g[:,3]
    n=20
    result=[]
    for name,func in (("SMA",talib.SMA),("EMA",talib.EMA),("WMA",talib.WMA),
                      ("DEMA",talib.DEMA),("TEMA",talib.TEMA),("TRIMA",talib.TRIMA)):
        result.append((name,{"period":n,"source":"close"},func(c,timeperiod=n)))
    result.extend([
        ("APO",{"fast_period":5,"slow_period":20},
         talib.APO(c,fastperiod=5,slowperiod=20,matype=1)),
        ("TRIX",{"period":12},talib.TRIX(c,timeperiod=12)),
        ("ATR",{"period":14},talib.ATR(h,l,c,timeperiod=14)),
        ("NATR",{"period":14,"multiplier":1.0},
         talib.NATR(h,l,c,timeperiod=14)),
        ("ADXR",{"period":14,"threshold":10},
         talib.ADXR(h,l,c,timeperiod=14))
    ])
    if tuple(x[0] for x in result)!=NAMES:raise RuntimeError("Oracle list changed")
    return result

def compare_selected_ist(dates,bars,source,expected_counts=False):
    _gate()
    metadata=_validate_source(dates,bars,source,expected_counts=expected_counts)
    rolls=[i for i in range(1,len(metadata))
           if metadata[i].contract_id!=metadata[i-1].contract_id]
    if expected_counts and len(rolls)!=EXPECTED["roll_boundaries"]:
        raise ValueError("Quarterly roll count changed")
    chosen=sorted(set([0,len(dates)//2,len(dates)-1,*rolls]))
    counts=Counter()
    mismatches=Counter()
    for i in chosen:
        g=bars[i]
        for name,params,ref in references(g):
            for t in INDEXES:
                try:
                    actual=formula(g,t,{"name":name,"parameters":params})
                except (ValueError,IndexError,KeyError,TypeError,
                        FloatingPointError,ZeroDivisionError) as exc:
                    mismatches[name+"_RUNTIME_"+type(exc).__name__]+=1
                    continue
                # AST router explicitly normalizes ADXR to a signed
                # distance from its registered threshold. Compare to the
                # *same* TA-Lib ADXR transform; raw-vs-transformed is not
                # evidence of a mathematical mismatch.
                expected=float(ref[t])
                if name=="ADXR" and np.isfinite(expected):
                    expected-=float(params["threshold"])
                if actual is None or not np.isfinite(expected):
                    mismatches[name+"_UNAVAILABLE_WHEN_REFERENCE_READY"]+=1
                    continue
                counts[name]+=1
                if not np.isfinite(actual) or abs(actual-expected)>TOL.get(name,BASE_TOL):
                    mismatches[name+"_EXTERNAL_NUMERIC_MISMATCH"]+=1
    if mismatches:
        # Strictly output labels and counts, not original OHLC or indicator values.
        raise AssertionError("Independent oracle discrepancies (counts only): "+
                             json.dumps(dict(sorted(mismatches.items()))))
    if len(chosen)!=15 and expected_counts:
        raise ValueError("Context sample changed")
    if expected_counts and sum(counts.values())!=330:
        raise AssertionError("Expected 11 independently compared formula names x 15 sessions x 2 bar indices")
    return {
        "status":STATUS,"source":"NQ_M1_IST_2020_2022_ONLY",
        "source_days":len(dates),"partial_rth_sessions_excluded":source["partial_sessions_excluded"],
        "rollovers":len(rolls),"chosen_contexts":len(chosen),
        "compared_formula_names":list(NAMES),
        "external_library":"TA-Lib==0.6.8",
        "indexes_per_context":list(INDEXES),
        "external_formula_comparisons":sum(counts.values()),
        "comparisons_by_name":dict(sorted(counts.items())),
        "error_categories":dict(sorted(mismatches.items())),
        "all_132_formula_names_certified":False,
        "parameters_full_domain_certified":False,
        "years_opened":list(ALLOWED_YEARS),
        "isv1_2023_opened":False,"isv2_2024_opened":False,
        "sealed_2025_2026_opened":False,
        "strategies_or_signals_evaluated":False,
        "model_fills_or_trades_evaluated":False,
        "financial_metrics_or_fitness_computed":False,
        "holdout_selection_performed":False,
        "formal_quality_gates_passed":0,
        "ninjatrader_parity_completed":False
    }

def audit_archive(zip_path:Path):
    _gate()
    if sha_file(zip_path)!=EXPECTED_SHA256:
        raise PermissionError("Original NQ IST M1 SHA mismatch: stop before member read")
    manifest=inspect_archive_manifest(zip_path)
    if manifest["source_members"]!=15 or manifest["market_member_contents_opened"]:
        raise RuntimeError("Frozen IST 15-member manifest changed")
    dates,bars,source=load_years(zip_path,ALLOWED_YEARS)
    report=compare_selected_ist(dates,bars,source,expected_counts=True)
    report["source_zip_sha256"]=EXPECTED_SHA256
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=audit_archive(a.zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in
         ("status","source_days","rollovers","chosen_contexts",
          "external_formula_comparisons","error_categories",
          "financial_metrics_or_fitness_computed","formal_quality_gates_passed")},
         sort_keys=True))

if __name__=="__main__":main()
