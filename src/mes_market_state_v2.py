"""MES-MS2: calendar-aware causal market-state map.

V1 is immutable. V2 changes data availability only:
- CME Equity session calendar instead of generic weekdays / observed stray dates;
- scheduled shortened RTH sessions are valid;
- Last-bar coverage >=95% with required session endpoints;
- MAR25 may supply ET-calendar 2024 rows only.

No trading outcomes are computed here.
"""
from __future__ import annotations

from dataclasses import asdict
import math
import re

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from src.mes_market_state_v1 import Config, hysteresis, _bands, _bucket

VERSION = "MES-MS2-20261005"
STATES = ["R0", "R1", "R2", "R3", "R4"]
TZ = "America/New_York"


def cme_equity_schedule(start_date, end_date):
    cal = mcal.get_calendar("CME_Equity")
    schedule = cal.schedule(start_date=start_date, end_date=end_date)
    if schedule.empty:
        raise ValueError("empty CME Equity schedule")
    return schedule


def expected_rth_close_minute(market_close) -> int:
    close = pd.Timestamp(market_close)
    if close.tzinfo is None:
        close = close.tz_localize("UTC")
    close = close.tz_convert(TZ)
    # Project research window is cash-session-like 09:31-16:00 ET.
    return min(close.hour * 60 + close.minute, 960)


def session_usable(g: pd.DataFrame, expected_close_minute: int, min_coverage=.95) -> bool:
    expected = expected_close_minute - 570
    if expected <= 0 or g.empty:
        return False
    if g.contract.nunique() != 1:
        return False
    if not ((g.minute == 571).any() and (g.minute == expected_close_minute).any()):
        return False
    return len(g) >= math.ceil(min_coverage * expected)


def causal_inputs(bars: pd.DataFrame, cfg=Config(), min_rth_coverage=.95):
    required = {"timestamp_et", "open", "high", "low", "close", "volume", "contract"}
    if not required <= set(bars):
        raise ValueError("missing bar fields")
    b = bars.copy()
    if b.empty or b.timestamp_et.dt.tz is None:
        raise ValueError("nonempty timezone-aware bars required")
    b["timestamp_et"] = b.timestamp_et.dt.tz_convert(TZ)
    if b.timestamp_et.duplicated().any() or not b.timestamp_et.is_monotonic_increasing:
        raise ValueError("sorted unique bars required")
    if not b.timestamp_et.dt.year.between(2020, 2024).all():
        raise ValueError("MES-MS2 accepts only ET calendar 2020-2024")
    if not b.contract.str.match(r"^MES (03|06|09|12)-(20|21|22|23|24|25)$").all():
        raise ValueError("wrong instrument or source contract scope")

    b["day"] = b.timestamp_et.dt.date
    b["minute"] = b.timestamp_et.dt.hour * 60 + b.timestamp_et.dt.minute

    schedule = cme_equity_schedule(str(b.day.min()), str(b.day.max()))
    schedule = schedule[(schedule.index.year >= 2020) & (schedule.index.year <= 2024)]

    daily = []
    previous = None
    for session_idx, s in schedule.iterrows():
        day = pd.Timestamp(session_idx).date()
        close_min = expected_rth_close_minute(s["market_close"])
        g = b[(b.day == day) & (b.minute >= 571) & (b.minute <= close_min)]
        usable = session_usable(g, close_min, min_rth_coverage)
        row = {
            "day": day,
            "contract": str(g.contract.iloc[-1]) if len(g) else "",
            "usable": bool(usable),
            "expected_close_minute": int(close_min),
            "expected_bars": int(max(0, close_min - 570)),
            "observed_bars": int(len(g)),
        }
        if len(g):
            row.update(
                high=float(g.high.max()),
                low=float(g.low.min()),
                close=float(g.close.iloc[-1]),
                volume=float(g.volume.sum()),
            )
        else:
            row.update(high=np.nan, low=np.nan, close=np.nan, volume=np.nan)

        same_prior = (
            previous is not None
            and previous["usable"]
            and usable
            and previous["contract"] == row["contract"]
        )
        if usable:
            reference = previous["close"] if same_prior else row["close"]
            row["tr"] = max(
                row["high"] - row["low"],
                abs(row["high"] - reference),
                abs(row["low"] - reference),
            )
        else:
            row["tr"] = np.nan
        daily.append(row)
        previous = row

    nights = b[(b.minute >= 1081) | (b.minute <= 570)].copy()
    nights["asof_day"] = nights.day
    evening = nights.minute >= 1081
    nights.loc[evening, "asof_day"] = (
        nights.loc[evening, "timestamp_et"] + pd.Timedelta(days=1)
    ).dt.date
    overnight = {d: g for d, g in nights.groupby("asof_day", sort=True)}

    result = []
    for i, drow in enumerate(daily):
        day = drow["day"]
        cutoff = pd.Timestamp(day).tz_localize(TZ) + pd.Timedelta(minutes=570)
        row = {
            "date": str(day),
            "asof_et": cutoff.isoformat(),
            "contract": "",
            "input_status": "UNKNOWN_NO_OVERNIGHT",
            "overnight_bars": 0,
            "previous_rth_date": str(daily[i - 1]["day"]) if i else "",
            "source_max_et": "",
            "roll_reset": False,
            "previous_rth_expected_bars": int(daily[i - 1]["expected_bars"]) if i else 0,
            "previous_rth_observed_bars": int(daily[i - 1]["observed_bars"]) if i else 0,
        }
        g = overnight.get(day)
        if g is None:
            result.append(row)
            continue
        row.update(
            contract=str(g.contract.iloc[-1]),
            overnight_bars=int(len(g)),
            source_max_et=g.timestamp_et.iloc[-1].isoformat(),
        )
        start = cutoff - pd.Timedelta(minutes=929)
        if (
            len(g) < cfg.overnight_min_bars
            or g.timestamp_et.iloc[0] != start
            or g.timestamp_et.iloc[-1] != cutoff
            or g.contract.nunique() != 1
        ):
            row["input_status"] = "UNKNOWN_OVERNIGHT_COVERAGE"
            result.append(row)
            continue
        if i == 0 or not daily[i - 1]["usable"]:
            row["input_status"] = "UNKNOWN_PREVIOUS_RTH"
            result.append(row)
            continue

        p = daily[i - 1]
        same = p["contract"] == row["contract"]
        row["roll_reset"] = not same
        eligible = [
            r
            for r in daily[:i]
            if r["contract"] == row["contract"] and r["usable"]
        ]
        if not same or len(eligible) < cfg.atr_sessions:
            row["input_status"] = "UNKNOWN_CONTRACT_WARMUP"
            result.append(row)
            continue

        h = eligible[-cfg.atr_sessions :]
        atr = float(np.mean([r["tr"] for r in h]))
        closes = np.asarray([r["close"] for r in h[-cfg.trend_sessions - 1 :]], float)
        path = float(np.abs(np.diff(closes)).sum())
        if atr <= 0 or p["close"] <= 0 or path <= 0:
            row["input_status"] = "UNKNOWN_DEGENERATE_HISTORY"
            result.append(row)
            continue

        onclose, onfirst = float(g.close.iloc[-1]), float(g.open.iloc[0])
        row.update(
            input_status="READY",
            atr14=atr,
            vol=atr / p["close"],
            trend_score=(closes[-1] - closes[0]) / atr,
            er=abs(closes[-1] - closes[0]) / path,
            overnight_range_atr=(float(g.high.max()) - float(g.low.min())) / atr,
            overnight_return_atr=(onclose - onfirst) / atr,
            overnight_volume=float(g.volume.sum()),
            preopen_gap_proxy_atr=(onclose - p["close"]) / atr,
            pdc=p["close"],
            pdh=p["high"],
            pdl=p["low"],
            pdc_distance_atr=(onclose - p["close"]) / atr,
            pdh_distance_atr=(onclose - p["high"]) / atr,
            pdl_distance_atr=(onclose - p["low"]) / atr,
            value_location=(
                "ABOVE_PDH"
                if onclose > p["high"]
                else "BELOW_PDL"
                if onclose < p["low"]
                else "INSIDE_PREVIOUS_RANGE"
            ),
            log_vol=float(np.log(atr / p["close"])),
            log_on_range=float(
                np.log(max((g.high.max() - g.low.min()) / atr, 1e-9))
            ),
            log_on_volume=float(np.log(g.volume.sum())),
        )
        result.append(row)
    return result


def classify(inputs, cfg=Config()):
    history, output = [], []
    vol_state = efficiency_state = None
    channels = ["log_vol", "log_on_range", "log_on_volume"]
    sums = {f: [0.0, 0.0] for f in channels}
    cooldown = 0
    last_contract = None
    previous_ready = False

    for source in inputs:
        row = dict(source)
        if history and row["date"] <= history[-1]["date"]:
            raise ValueError("inputs must be sorted, unique")
        if not "2020-01-01" <= row["date"] < "2025-01-01":
            raise ValueError("input outside development scope")
        if row["contract"] and not re.fullmatch(
            r"MES (03|06|09|12)-(20|21|22|23|24|25)", row["contract"]
        ):
            raise ValueError("wrong instrument or contract scope")

        contract_changed = last_contract is not None and row["contract"] != last_contract
        ready = row["input_status"] == "READY"
        if not ready or contract_changed or not previous_ready:
            vol_state = efficiency_state = None
            sums = {f: [0.0, 0.0] for f in channels}
            cooldown = 0
        if row["contract"]:
            last_contract = row["contract"]

        row.update(
            engine_version=VERSION,
            regime="R0",
            r0_reason="",
            volatility_state="UNKNOWN",
            efficiency_state="UNKNOWN",
            change_alert=False,
            change_channels="",
            transition_remaining=0,
            direction="UNKNOWN",
            overnight_state="UNKNOWN",
            overnight_direction="UNKNOWN",
            gap_state="UNKNOWN",
            volume_state="UNKNOWN",
        )

        for field in ["vol", "er", "overnight_range_atr", "overnight_volume"]:
            lo, hi, n = _bands(history, field, cfg)
            row[field + "_q33"], row[field + "_q67"], row[field + "_reference_n"] = lo, hi, n

        calibrated = (
            len(history) >= cfg.window
            and row["vol_reference_n"] >= cfg.minimum_valid
            and row["er_reference_n"] >= cfg.minimum_valid
        )
        if not ready:
            row["r0_reason"] = row["input_status"]
        elif not calibrated:
            row["r0_reason"] = "UNKNOWN_REFERENCE_WARMUP"
        else:
            alerts = []
            for f in channels:
                prior = np.asarray(
                    [r.get(f, np.nan) for r in history[-cfg.window :]], float
                )
                prior = prior[np.isfinite(prior)]
                if len(prior) < cfg.minimum_valid or not np.isfinite(row.get(f, np.nan)):
                    continue
                sd = float(prior.std(ddof=1))
                if sd <= 1e-12:
                    continue
                z = float(np.clip((row[f] - prior.mean()) / sd, -6, 6))
                plus, minus = sums[f]
                plus = max(0.0, plus + z - cfg.cusum_k)
                minus = max(0.0, minus - z - cfg.cusum_k)
                row[f + "_cusum_z"] = z
                row[f + "_cusum_plus"] = plus
                row[f + "_cusum_minus"] = minus
                sums[f] = [plus, minus]
                if max(plus, minus) >= cfg.cusum_h:
                    alerts.append(f)
            if alerts:
                cooldown = cfg.transition_sessions
                sums = {f: [0.0, 0.0] for f in channels}
            row.update(
                change_alert=bool(alerts),
                change_channels=",".join(alerts),
                transition_remaining=cooldown,
            )
            vol_state = hysteresis(row["vol"], row["vol_q33"], row["vol_q67"], vol_state)
            efficiency_state = hysteresis(
                row["er"], row["er_q33"], row["er_q67"], efficiency_state
            )
            row["volatility_state"] = vol_state or "UNKNOWN"
            row["efficiency_state"] = (
                "DIRECTIONAL"
                if efficiency_state == "HIGH"
                else "CHOP"
                if efficiency_state == "LOW"
                else "UNKNOWN"
            )
            if cooldown:
                row["r0_reason"] = "TRANSITION_CUSUM_ALERT"
                cooldown -= 1
            elif vol_state is None or efficiency_state is None:
                row["r0_reason"] = "UNKNOWN_BAND_OR_DEGENERATE_REFERENCE"
            else:
                row["regime"] = {
                    ("HIGH", "HIGH"): "R1",
                    ("HIGH", "LOW"): "R2",
                    ("LOW", "HIGH"): "R3",
                    ("LOW", "LOW"): "R4",
                }[(vol_state, efficiency_state)]

        if ready:
            score = row["trend_score"]
            row["direction"] = (
                "BULL"
                if score > cfg.trend_neutral_atr
                else "BEAR"
                if score < -cfg.trend_neutral_atr
                else "NEUTRAL"
            )
            row["overnight_state"] = _bucket(
                row["overnight_range_atr"],
                row["overnight_range_atr_q33"],
                row["overnight_range_atr_q67"],
                ["COMPRESSED", "NORMAL", "EXPANDED"],
            )
            row["volume_state"] = _bucket(
                row["overnight_volume"],
                row["overnight_volume_q33"],
                row["overnight_volume_q67"],
                ["LOW", "NORMAL", "HIGH"],
            )
            onret, gap = row["overnight_return_atr"], row["preopen_gap_proxy_atr"]
            row["overnight_direction"] = (
                "UP"
                if onret > cfg.overnight_flat_atr
                else "DOWN"
                if onret < -cfg.overnight_flat_atr
                else "FLAT"
            )
            row["gap_state"] = (
                "UP_PROXY"
                if gap > cfg.overnight_flat_atr
                else "DOWN_PROXY"
                if gap < -cfg.overnight_flat_atr
                else "FLAT_PROXY"
            )
            volumes = np.asarray(
                [r.get("overnight_volume", np.nan) for r in history[-cfg.window :]],
                float,
            )
            volumes = volumes[np.isfinite(volumes)]
            row["overnight_volume_over_median"] = (
                row["overnight_volume"] / np.median(volumes)
                if calibrated and len(volumes) >= cfg.minimum_valid
                else np.nan
            )

        output.append(row)
        history.append(dict(source))
        previous_ready = ready

    episode, elapsed, previous_key = 0, 0, None
    for row in output:
        key = (row["regime"], row["r0_reason"], row["contract"])
        if key != previous_key:
            episode += 1
            elapsed = 0
        elapsed += 1
        row["episode_id"] = episode
        row["episode_elapsed_sessions"] = elapsed
        previous_key = key
    return pd.DataFrame(output)


def diagnose(features: pd.DataFrame):
    counts = pd.DataFrame(0, index=STATES, columns=STATES, dtype=int)
    records = features.to_dict("records")
    for a, b in zip(records, records[1:]):
        if a["contract"] and a["contract"] == b["contract"]:
            counts.loc[a["regime"], b["regime"]] += 1
    probs = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0)

    episodes = []
    for eid, g in features.groupby("episode_id", sort=True):
        episodes.append(
            {
                "episode_id": int(eid),
                "regime": g.regime.iloc[0],
                "r0_reason": g.r0_reason.iloc[0],
                "contract": g.contract.iloc[0],
                "start": g.date.iloc[0],
                "end": g.date.iloc[-1],
                "sessions": len(g),
            }
        )
    return counts, probs, pd.DataFrame(episodes)


def configuration():
    c = asdict(Config())
    c["rth_min_coverage"] = 0.95
    c["calendar"] = "pandas_market_calendars.CME_Equity"
    c["calendar_package_version"] = "5.4.0"
    return c
