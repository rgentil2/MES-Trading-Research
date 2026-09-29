# Requote requested 2026-09-29
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import databento as db

DATASET = "GLBX.MDP3"
SYMBOL = "ES.v.0"
STYPE_IN = "continuous"
SCHEMAS = ["trades", "tbbo"]
TZ = ZoneInfo("America/New_York")
START_LOCAL = dtime(9, 30)
END_LOCAL = dtime(11, 30)
START_DATE = date(2020, 1, 1)
END_DATE = date(2025, 1, 1)
MAX_WORKERS = 8


def weekdays(start: date, end: date):
    d = start
    while d < end:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def to_utc(d: date, t: dtime) -> str:
    local = datetime.combine(d, t, TZ)
    return local.astimezone(ZoneInfo("UTC")).isoformat()


def quote_one(schema: str, d: date) -> dict:
    client = db.Historical()
    cost = float(
        client.metadata.get_cost(
            dataset=DATASET,
            symbols=[SYMBOL],
            schema=schema,
            stype_in=STYPE_IN,
            start=to_utc(d, START_LOCAL),
            end=to_utc(d, END_LOCAL),
        )
    )
    return {
        "schema": schema,
        "date": d.isoformat(),
        "year": d.year,
        "cost_usd": cost,
    }


def main():
    days = list(weekdays(START_DATE, END_DATE))
    rows = []

    tasks = [(schema, d) for schema in SCHEMAS for d in days]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(quote_one, schema, d): (schema, d)
            for schema, d in tasks
        }
        for fut in as_completed(futures):
            rows.append(fut.result())

    rows.sort(key=lambda r: (r["schema"], r["date"]))

    summary = {}
    for schema in SCHEMAS:
        summary[schema] = {
            "years": {},
            "total_cost_usd": 0.0,
        }

    for r in rows:
        s = r["schema"]
        y = str(r["year"])
        summary[s]["years"].setdefault(y, 0.0)
        summary[s]["years"][y] += r["cost_usd"]
        summary[s]["total_cost_usd"] += r["cost_usd"]

    report = {
        "dataset": DATASET,
        "symbol": SYMBOL,
        "stype_in": STYPE_IN,
        "window_et": "09:30-11:30",
        "period": "2020-01-01 through 2024-12-31",
        "download_performed": False,
        "summary": summary,
    }

    out = Path("results/databento_es_l1_quote")
    out.mkdir(parents=True, exist_ok=True)
    (out / "quote.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Databento ES L1 Quote — Metadata Only",
        "",
        "- Instrument: ES.v.0",
        "- Window: 09:30–11:30 ET",
        "- Period: 2020–2024",
        "- Data download performed: **NO**",
        "",
        "| Schema | 2020 | 2021 | 2022 | 2023 | 2024 | Total |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for schema in SCHEMAS:
        yrs = summary[schema]["years"]
        lines.append(
            "| " + schema.upper() + " | "
            + " | ".join(f"USD {yrs.get(str(y), 0.0):,.2f}" for y in range(2020, 2025))
            + f" | **USD {summary[schema]['total_cost_usd']:,.2f}** |"
        )

    lines += [
        "",
        "These are exact sums of daily metadata.get_cost queries for weekdays.",
        "No timeseries or batch download endpoint was called.",
    ]

    (out / "QUOTE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
