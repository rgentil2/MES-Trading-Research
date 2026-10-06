#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"results/mes_stage1_local_robustness/STAGE1_TRADES.csv"
OUT=ROOT/"results/mes_stage2_parity"
CENTERS={
    "PDC":"SL_0.30ATR",
    "POC":"H15",
    "R072":"H30",
}

def main():
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    x=pd.read_csv(SRC)
    if "year" not in x.columns:
        raise ValueError("year missing")
    if int(x.year.max())>2025:
        raise ValueError("2026 leak")
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[]
    for strategy,variant in CENTERS.items():
        g=x[(x.strategy==strategy)&(x.variant==variant)].copy()
        g=g.sort_values(["entry_actual_et","group_key"]).reset_index(drop=True)
        cols=[c for c in [
            "strategy","variant","session_date","year","group_key","direction",
            "entry_actual_et","entry_price","exit_ts","exit_price","exit_reason",
            "gross_points","net_pnl_usd","stress_net_pnl_usd"
        ] if c in g.columns]
        g[cols].to_csv(OUT/f"{strategy}_PYTHON_GOLDEN_TRADES.csv",index=False)

        yearly=g.groupby("year",sort=True).agg(
            trades=("strategy","size"),
            net_pnl_usd=("net_pnl_usd","sum"),
            expectancy_usd=("net_pnl_usd","mean"),
        ).reset_index()
        yearly.to_csv(OUT/f"{strategy}_PYTHON_GOLDEN_YEARLY.csv",index=False)
        summary.append({
            "strategy":strategy,
            "variant":variant,
            "trades":int(len(g)),
            "first_trade":None if g.empty else str(g.entry_actual_et.iloc[0]),
            "last_trade":None if g.empty else str(g.entry_actual_et.iloc[-1]),
            "net_pnl_usd":float(g.net_pnl_usd.sum()),
            "expectancy_usd":float(g.net_pnl_usd.mean()),
        })

    s=pd.DataFrame(summary)
    s.to_csv(OUT/"PYTHON_GOLDEN_SUMMARY.csv",index=False)
    report={
        "authority":"NINJATRADER_STAGE2_GOLDEN_MANIFEST",
        "contract_2026_opened":False,
        "centers":CENTERS,
        "summary":summary,
        "parity_rule":{
            "signal_date_side_match_min":0.99,
            "trade_count_difference_max":0.01,
            "unexplained_timezone_rollover_mismatches_allowed":0
        }
    }
    (OUT/"PARITY_MANIFEST.json").write_text(json.dumps(report,indent=2)+"\n")
    print(s.to_string(index=False))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
