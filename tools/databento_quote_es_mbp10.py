from __future__ import annotations

import json
import os
from pathlib import Path

import databento as db

DATASET = "GLBX.MDP3"
SYMBOL = "ES.v.0"
STYPE_IN = "continuous"
SCHEMA = "mbp-10"

PERIODS = [
    ("2020", "2020-01-01", "2021-01-01"),
    ("2021", "2021-01-01", "2022-01-01"),
    ("2022", "2022-01-01", "2023-01-01"),
    ("2023", "2023-01-01", "2024-01-01"),
    ("2024", "2024-01-01", "2025-01-01"),
]


def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    x = float(n)
    for unit in units:
        if x < 1024 or unit == units[-1]:
            return f"{x:,.2f} {unit}"
        x /= 1024
    return f"{x:,.2f} PB"


def query(client, start, end):
    kwargs = dict(
        dataset=DATASET,
        symbols=[SYMBOL],
        schema=SCHEMA,
        stype_in=STYPE_IN,
        start=start,
        end=end,
    )
    return {
        "cost_usd": float(client.metadata.get_cost(**kwargs)),
        "billable_size_bytes": int(client.metadata.get_billable_size(**kwargs)),
        "record_count": int(client.metadata.get_record_count(**kwargs)),
    }


def main():
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        raise RuntimeError("DATABENTO_API_KEY secret is missing")

    client = db.Historical(key)

    rows = []
    for label, start, end in PERIODS:
        q = query(client, start, end)
        q.update({"period": label, "start": start, "end": end})
        rows.append(q)

    total = {
        "cost_usd": sum(r["cost_usd"] for r in rows),
        "billable_size_bytes": sum(r["billable_size_bytes"] for r in rows),
        "record_count": sum(r["record_count"] for r in rows),
    }

    full = query(client, "2020-01-01", "2025-01-01")

    report = {
        "dataset": DATASET,
        "symbol": SYMBOL,
        "stype_in": STYPE_IN,
        "schema": SCHEMA,
        "download_performed": False,
        "periods": rows,
        "sum_of_years": total,
        "full_interval_direct_query": full,
    }

    out = Path("results/databento_es_quote")
    out.mkdir(parents=True, exist_ok=True)
    (out / "quote.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Databento ES MBP-10 Quote — Metadata Only",
        "",
        f"- Dataset: {DATASET}",
        f"- Symbol: {SYMBOL}",
        f"- Input symbology: {STYPE_IN}",
        f"- Schema: {SCHEMA}",
        "- Data download performed: **NO**",
        "",
        "| Period | Cost USD | Billable size | Records |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['period']} | USD {r['cost_usd']:,.4f} | "
            f"{fmt_bytes(r['billable_size_bytes'])} | "
            f"{r['record_count']:,} |"
        )
    lines += [
        "",
        "## Sum of yearly metadata queries",
        f"- Cost: USD {total['cost_usd']:,.4f}",
        f"- Billable size: {fmt_bytes(total['billable_size_bytes'])}",
        f"- Records: {total['record_count']:,}",
        "",
        "## Direct 2020–2024 interval metadata query",
        f"- Cost: USD {full['cost_usd']:,.4f}",
        f"- Billable size: {fmt_bytes(full['billable_size_bytes'])}",
        f"- Records: {full['record_count']:,}",
        "",
        "No timeseries or batch download endpoint was called.",
    ]
    (out / "QUOTE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
