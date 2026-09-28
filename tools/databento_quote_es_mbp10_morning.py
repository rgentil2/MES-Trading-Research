from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import databento as db

DATASET = "GLBX.MDP3"
SYMBOL = "ES.v.0"
STYPE_IN = "continuous"
SCHEMA = "mbp-10"
TZ = ZoneInfo("America/New_York")
START_LOCAL = dtime(9, 20)
END_LOCAL = dtime(11, 40)

YEARS = range(2020, 2025)


def daterange(start: date, end: date):
    d = start
    while d < end:
        yield d
        d += timedelta(days=1)


def to_iso_utc(d: date, t: dtime) -> str:
    local = datetime.combine(d, t, TZ)
    return local.astimezone(ZoneInfo("UTC")).isoformat()


def get_cost_retry(client, start, end, tries=5):
    last = None
    for i in range(tries):
        try:
            return float(
                client.metadata.get_cost(
                    dataset=DATASET,
                    symbols=[SYMBOL],
                    schema=SCHEMA,
                    stype_in=STYPE_IN,
                    start=start,
                    end=end,
                )
            )
        except Exception as exc:
            last = exc
            time.sleep(min(2 ** i, 10))
    raise last


def main():
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        raise RuntimeError("DATABENTO_API_KEY secret is missing")

    client = db.Historical(key)
    yearly = []
    daily = []

    for year in YEARS:
        year_cost = 0.0
        queried_days = 0
        nonzero_days = 0

        for d in daterange(date(year, 1, 1), date(year + 1, 1, 1)):
            if d.weekday() >= 5:
                continue

            start = to_iso_utc(d, START_LOCAL)
            end = to_iso_utc(d, END_LOCAL)
            cost = get_cost_retry(client, start, end)
            queried_days += 1
            if cost > 0:
                nonzero_days += 1
                year_cost += cost

            daily.append(
                {
                    "date": d.isoformat(),
                    "year": year,
                    "cost_usd": cost,
                    "start_utc": start,
                    "end_utc": end,
                }
            )

        yearly.append(
            {
                "year": year,
                "cost_usd": year_cost,
                "weekdays_queried": queried_days,
                "nonzero_days": nonzero_days,
            }
        )

    total = sum(r["cost_usd"] for r in yearly)
    report = {
        "dataset": DATASET,
        "symbol": SYMBOL,
        "schema": SCHEMA,
        "stype_in": STYPE_IN,
        "window_et": "09:20-11:40 America/New_York",
        "download_performed": False,
        "yearly": yearly,
        "total_cost_usd": total,
        "daily": daily,
    }

    out = Path("results/databento_es_morning_quote")
    out.mkdir(parents=True, exist_ok=True)
    (out / "quote.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Databento ES MBP-10 Morning Quote — Metadata Only",
        "",
        f"- Symbol: {SYMBOL}",
        f"- Schema: {SCHEMA}",
        "- Window: 09:20–11:40 ET",
        "- Development years: 2020–2024",
        "- Data download performed: **NO**",
        "",
        "| Year | Cost USD | Non-zero weekdays |",
        "|---|---:|---:|",
    ]
    for r in yearly:
        lines.append(
            f"| {r['year']} | USD {r['cost_usd']:,.4f} | "
            f"{r['nonzero_days']} |"
        )
    lines += [
        "",
        f"**Total metadata-estimated cost: USD {total:,.4f}**",
        "",
        "No timeseries or batch download endpoint was called.",
    ]

    (out / "QUOTE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
