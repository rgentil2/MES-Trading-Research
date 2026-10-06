#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from research.mes_parameter_walkforward_p1 import load_development
from research.archive.B12.b12_strategy_architecture import prepare_rth

NEWS_IN = ROOT / "data_external/forexfactory/usd_high_medium_2020_2025.csv"
OUT = ROOT / "results/ninjatrader_pdc_support"


def build_rollover_dates() -> pd.DataFrame:
    raw = load_development()
    _, groups = prepare_rth(raw)

    rows = []
    for key, g in groups.items():
        g = g.sort_values("timestamp_et")
        rows.append({
            "session_date": str(g.session_date.iloc[0]),
            "contract": str(g.contract.iloc[0]),
            "first_ts": g.timestamp_et.iloc[0],
        })

    d = pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    d["prev_contract"] = d.contract.shift(1)
    x = d[d.prev_contract.notna() & d.contract.ne(d.prev_contract)].copy()
    x = x.rename(columns={"session_date": "rollover_session_date_et"})
    return x[["rollover_session_date_et", "prev_contract", "contract"]]


def build_news() -> pd.DataFrame:
    if not NEWS_IN.exists():
        raise FileNotFoundError(NEWS_IN)

    n = pd.read_csv(NEWS_IN)
    for c in ["blackout_start_et", "blackout_end_et"]:
        n[c] = pd.to_datetime(n[c], utc=True).dt.tz_convert("America/New_York")

    out = pd.DataFrame({
        "start_et": n.blackout_start_et.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_et": n.blackout_end_et.dt.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return out.drop_duplicates().sort_values(["start_et", "end_et"]).reset_index(drop=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    r = build_rollover_dates()
    n = build_news()

    r.to_csv(OUT / "pdc_rollover_sessions_et.csv", index=False)
    n.to_csv(OUT / "pdc_news_blackouts_et.csv", index=False)

    print("ROLLOVERS")
    print(r.to_string(index=False))
    print(f"\nnews windows: {len(n)}")


if __name__ == "__main__":
    main()
