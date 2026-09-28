from __future__ import annotations

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import databento as db

DATASET = "GLBX.MDP3"
SCHEMA = "mbp-10"
SYMBOLS = ["ES.v.0", "MES.v.0"]
START = "2020-01-01T00:00:00Z"
END = "2025-01-01T00:00:00Z"

# Representative 5-session week, chosen only to estimate the relative
# cost of a narrow morning window vs full-day depth. No data are downloaded.
SAMPLE_DATES = [
    "2024-06-03",
    "2024-06-04",
    "2024-06-05",
    "2024-06-06",
    "2024-06-07",
]
NY = ZoneInfo("America/New_York")


def utc_iso(date_str: str, hour: int, minute: int) -> str:
    local = datetime.fromisoformat(date_str).replace(
        hour=hour, minute=minute, second=0, tzinfo=NY
    )
    return local.astimezone(ZoneInfo("UTC")).isoformat()


def main() -> None:
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        raise RuntimeError("DATABENTO_API_KEY secret is not available")

    client = db.Historical(api_key)

    out = {
        "dataset": DATASET,
        "schema": SCHEMA,
        "development_period": {"start": START, "end": END},
        "symbols": {},
        "note": "metadata.get_cost only; no historical data downloaded",
    }

    for symbol in SYMBOLS:
        full_cost = client.metadata.get_cost(
            dataset=DATASET,
            symbols=[symbol],
            schema=SCHEMA,
            stype_in="continuous",
            start=START,
            end=END,
        )

        sample_full = client.metadata.get_cost(
            dataset=DATASET,
            symbols=[symbol],
            schema=SCHEMA,
            stype_in="continuous",
            start="2024-06-03T00:00:00Z",
            end="2024-06-08T00:00:00Z",
        )

        # Sum exact 09:20–11:40 ET windows for the 5 representative sessions.
        sample_morning = 0.0
        daily = []
        for day in SAMPLE_DATES:
            s = utc_iso(day, 9, 20)
            e = utc_iso(day, 11, 40)
            c = client.metadata.get_cost(
                dataset=DATASET,
                symbols=[symbol],
                schema=SCHEMA,
                stype_in="continuous",
                start=s,
                end=e,
            )
            sample_morning += float(c)
            daily.append({"date": day, "cost_usd": float(c)})

        ratio = (
            sample_morning / float(sample_full)
            if float(sample_full) > 0
            else None
        )
        estimated_morning_2020_2024 = (
            float(full_cost) * ratio if ratio is not None else None
        )

        out["symbols"][symbol] = {
            "full_2020_2024_cost_usd": float(full_cost),
            "sample_week_full_cost_usd": float(sample_full),
            "sample_week_0920_1140_et_cost_usd": float(sample_morning),
            "sample_morning_to_full_ratio": ratio,
            "estimated_0920_1140_et_2020_2024_cost_usd": estimated_morning_2020_2024,
            "sample_daily_morning_costs": daily,
        }

    out["combined"] = {
        "full_2020_2024_cost_usd": sum(
            x["full_2020_2024_cost_usd"] for x in out["symbols"].values()
        ),
        "estimated_0920_1140_et_2020_2024_cost_usd": sum(
            x["estimated_0920_1140_et_2020_2024_cost_usd"]
            for x in out["symbols"].values()
        ),
    }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
