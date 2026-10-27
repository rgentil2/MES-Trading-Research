#!/usr/bin/env python3
"""NQ V2.1 frozen typed AST engineering PILOT; no economic screening.

Only the earliest 10 complete IST days from 2020-22 and the first 10
lexicographically generated semantically executable ASTs. No selection based
on realized returns. Trade PnL is neither aggregated nor exported. Prior-RTH
warmup contract is not wired into order execution: this remains a narrow
ENGINEERING diagnostic, not a fair full-period strategy backtest.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

from research.nq.nq_m1_chrono_discovery import load_years
from research.nq import nq_m1_v21_semantic_generator as gen
from research.nq import nq_m1_v2_orders as orders

FROZEN_SEED = 20261027
FROZEN_ENGINEERING_SHA = "fcf49b77937bc3eb687f741e7fa9c2e6e42d59407a59ffb09d9bc51ca9a8d098"
FROZEN_BROAD_SHA = "c20f12fe8d9a4242395c8abb61adb6eeee692601b7867edfa4120cbd0dd1f8bc"
STATUS = "V21_NQ_ONE_CONTRACT_IST_ENGINEERING_ONLY_NO_ECONOMIC_ASSESSMENT"


def registered():
    b=gen.generate(300,seed=FROZEN_SEED,supported_only=False)
    x=gen.generate(100,seed=FROZEN_SEED,supported_only=True)
    if (b["rows_sha256"]!=FROZEN_BROAD_SHA or
        x["rows_sha256"]!=FROZEN_ENGINEERING_SHA or
        x["registered_blocks_total"]!=132 or
        x["implemented_scalar_blocks"]!=38 or
        not x["nq_only_one_contract"]):
        raise RuntimeError("NQ V2.1 frozen source or candidate mismatch BEFORE price access")
    eligible=[r["strategy"] for r in x["rows"] if
              r["audit"]["semantic_status"]=="SEMANTICALLY_EXECUTABLE_UNCERTIFIED"]
    if len(eligible)!=82:
        raise RuntimeError("Unexpected NQ semantic executable count")
    for s in eligible:
        if (s["position_sizing"] != {"instrument":"NQ","contracts":1}
                or s["market_data_years_permitted_for_discovery"] != [2020,2021,2022]
                or s["ast_version"]!=gen.AST_VERSION):
            raise RuntimeError("Non-NQ AST or prohibited years")
        orders.validate_supported(s)
    return eligible


def pilot(zip_path:Path, max_days:int=10, max_strategies:int=10):
    if (type(max_days) is not int or not 1<=max_days<=10 or
        type(max_strategies) is not int or not 1<=max_strategies<=10):
        raise ValueError("Only 1..10 fixed initial engineering dimensions")
    strategies=registered()[:max_strategies]  # frozen BEFORE any price access
    dates,bars,source=load_years(zip_path,(2020,2021,2022))
    if (source.get("years_opened") != [2020,2021,2022]
            or source.get("holdout_2025_opened") is not False
            or source.get("holdout_2026_opened") is not False
            or len(dates)<max_days):
        raise RuntimeError("Market data source whitelist failed")
    result=[]
    for s in strategies:
        summary=Counter()
        for date,bar in zip(dates[:max_days],bars[:max_days]):
            o=orders.simulate_day(bar,s,date)
            if o["holdouts"]!="SEALED":
                raise RuntimeError("Unexpected exposure to sealed years")
            summary["days"]+=1
            summary["model_fills"]+=o["filled"]
            for k,v in o["rejected"].items():
                summary["reject_"+k]+=v
            for k,v in o["signal_diagnostics"].items():
                summary["signal_"+k]+=v
        result.append({"strategy_id":s["id"],
                       "fingerprint_sha256":s["lineage"]["fingerprint_sha256"],
                       "counts":dict(summary),
                       "status":"TECHNICAL_ONLY_NO_ECONOMIC_RESULT"})
    return {
        "status":STATUS,
        "universe":"NQ_1_CONTRACT_ONLY",
        "frozen_seed":FROZEN_SEED,
        "frozen_broad_sha256":FROZEN_BROAD_SHA,
        "frozen_engineering_sha256":FROZEN_ENGINEERING_SHA,
        "stage":"IST_2020_2022_TECHNICAL_ONLY",
        "source":source,
        "strategies_total":len(strategies),
        "days_per_strategy":max_days,
        "fully_verified_indicators":False,
        "multi_session_warmup_wired":False,
        "formal_g0_d0_d1_d2_applied":False,
        "outcomes_or_pnl_exported":False,
        "reserved_periods":"ISV1_2023_ISV2_2024_H2025_H2026_T_UNOPENED",
        "strategies":result,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--days",type=int,default=10)
    p.add_argument("--strategies",type=int,default=10)
    a=p.parse_args()
    out=pilot(a.zip,a.days,a.strategies)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":out["status"],"strategies_total":out["strategies_total"],
                      "days_per_strategy":out["days_per_strategy"],
                      "total_model_fills":sum(r["counts"].get("model_fills",0) for r in out["strategies"]),
                      "source":out["source"],"reserved_periods":out["reserved_periods"]},
                     sort_keys=True))


if __name__=="__main__":
    main()
