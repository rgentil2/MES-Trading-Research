"""Metadata-only cost quote for NQ front-month Last ticks, full 2020-2025.

Does NOT request, download, stream or open tick prices. Uses the GitHub Actions
DATABENTO_API_KEY secret; never logs the secret.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import databento as db


DATASET = "GLBX.MDP3"
SYMBOLS = ["NQ.v.0"]  # NQ lead contract by PREVIOUS DAY'S volume.
SCHEMA = "trades"  # Last trade prints (tick-by-tick), NOT bid/ask.
STYPE_IN = "continuous"
YEARS = range(2020, 2026)


def quote(client: db.Historical, start: str, end: str) -> dict:
    args = {
        "dataset": DATASET,
        "symbols": SYMBOLS,
        "schema": SCHEMA,
        "stype_in": STYPE_IN,
        "start": start,
        "end": end,
    }
    # Metadata calls only (NO get_range, NO batch.submit_job, NO actual download).
    return {
        "cost_usd": float(client.metadata.get_cost(**args)),
        "billable_size_bytes": int(client.metadata.get_billable_size(**args)),
        "record_count": int(client.metadata.get_record_count(**args)),
    }


def fmt(n: int) -> str:
    x = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if x < 1024:
            return f"{x:,.2f} {unit}"
        x /= 1024
    return f"{x:,.2f} PiB"


def main() -> None:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        raise RuntimeError("Missing DATABENTO_API_KEY (GitHub Actions secret)")

    client = db.Historical(key=key)
    years = []
    for year in YEARS:
        start, end = f"{year}-01-01", f"{year+1}-01-01"
        q = quote(client, start, end)
        years.append({"year": year, "start": start, "end_exclusive": end, **q})
        print(f"QUOTED {year}: USD {q['cost_usd']:,.2f}; "
              f"{q['record_count']:,} trades; {fmt(q['billable_size_bytes'])}", flush=True)

    # Full-span metadata query is optional; annual quotes already provide full coverage.
    full = None
    full_error = None
    try:
        full = quote(client, "2020-01-01", "2026-01-01")
    except Exception as exc:
        full_error = f"{type(exc).__name__}: {exc}"

    summed = {
        "cost_usd": round(sum(row["cost_usd"] for row in years), 6),
        "record_count": sum(row["record_count"] for row in years),
        "billable_size_bytes": sum(row["billable_size_bytes"] for row in years),
    }
    report = {
        "quoted_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": DATASET,
        "symbols": SYMBOLS,
        "stype_in": STYPE_IN,
        "schema": SCHEMA,
        "data": "Last tick trade executions only",
        "contract_scope": "single volume-based continuous front month; NOT all NQ expirations",
        "window": "UTC full calendar years 2020-01-01 through 2025-12-31, end exclusive 2026-01-01",
        "only_metadata_endpoints_called": True,
        "actual_market_data_downloaded": False,
        "holdout_prices_2025_accessed": False,
        "price_is_quote_not_invoice": True,
        "yearly_quotes": years,
        "sum_of_yearly_quotes": summed,
        "full_span_quote": full,
        "full_span_error_if_any": full_error,
    }

    folder = Path("results/databento_nq_trades_2020_2025_quote")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "quote.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Databento NQ.v.0 Last ticks 2020–2025 — LIVE API QUOTE (metadata only)",
        "",
        "- Dataset: GLBX.MDP3",
        "- Symbol: NQ.v.0, stype_in=continuous (one rolling lead contract)",
        "- Schema: trades (Last ticks, not Bid/Ask)",
        "- Time: full UTC calendar years (six years, 2020–2025 inclusive)",
        "- Market data downloaded: **NO**",
        "- 2025 price/tick contents opened: **NO** (metadata pricing only)",
        "",
        "| Year | Quote USD | Trade records | Billable uncompressed size |",
        "|---|---:|---:|---:|",
    ]
    for row in years:
        lines.append(
            f"| {row['year']} | **US$ {row['cost_usd']:,.2f}** | "
            f"{row['record_count']:,} | {fmt(row['billable_size_bytes'])} |"
        )
    lines += [
        "",
        f"**Total, yearly sum: US$ {summed['cost_usd']:,.2f}**",
        f"**Total records: {summed['record_count']:,}**",
        f"**Total billable size: {fmt(summed['billable_size_bytes'])}**",
        "",
    ]
    if full:
        lines.append(
            f"**Direct six-year metadata quote: US$ {full['cost_usd']:,.2f}** "
            f"({full['record_count']:,} trades, {fmt(full['billable_size_bytes'])})."
        )
    if full_error:
        lines.append(f"Direct six-year quote unavailable ({full_error}); annual total remains valid.")
    lines += [
        "",
        "Pricing is account-specific; streaming and batch orders may vary according to",
        "Databento terms and actual bytes delivered. No billable market data was requested.",
        "The estimate does not include every concurrent NQ expiration, MNQ, Bid/Ask, MBO or MBP.",
    ]
    (folder / "QUOTE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
