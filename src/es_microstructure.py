from __future__ import annotations

import numpy as np
import pandas as pd


def _check(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")
    if not df["timestamp"].is_monotonic_increasing:
        raise ValueError(f"{name} timestamps must be sorted")


def attach_bbo_to_trades(trades: pd.DataFrame, bids: pd.DataFrame, asks: pd.DataFrame) -> pd.DataFrame:
    """Backward as-of joins only; never attaches future quotes to trades."""
    _check(trades, {"timestamp", "price", "volume"}, "trades")
    _check(bids, {"timestamp", "price"}, "bids")
    _check(asks, {"timestamp", "price"}, "asks")

    out = pd.merge_asof(
        trades.copy(),
        bids[["timestamp", "price"]].rename(columns={"timestamp": "bid_timestamp", "price": "bid"}),
        left_on="timestamp",
        right_on="bid_timestamp",
        direction="backward",
        allow_exact_matches=True,
    )
    out = pd.merge_asof(
        out,
        asks[["timestamp", "price"]].rename(columns={"timestamp": "ask_timestamp", "price": "ask"}),
        left_on="timestamp",
        right_on="ask_timestamp",
        direction="backward",
        allow_exact_matches=True,
    )
    out["bid_age_ms"] = (out["timestamp"] - out["bid_timestamp"]).dt.total_seconds() * 1000.0
    out["ask_age_ms"] = (out["timestamp"] - out["ask_timestamp"]).dt.total_seconds() * 1000.0
    return out


def classify_aggressor(df: pd.DataFrame) -> pd.DataFrame:
    """Primary strict classifier: at/through ask=buy, at/through bid=sell, else 0."""
    required = {"price", "volume", "bid", "ask"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    out = df.copy()
    valid = out["bid"].notna() & out["ask"].notna()
    if (valid & (out["bid"] > out["ask"])).any():
        raise ValueError("crossed BBO observed; resolve QC before classification")

    side = np.zeros(len(out), dtype=np.int8)
    side[(valid & (out["price"] >= out["ask"])).to_numpy()] = 1
    side[(valid & (out["price"] <= out["bid"])).to_numpy()] = -1
    out["aggressor_side"] = side
    out["signed_volume"] = out["aggressor_side"] * out["volume"]
    out["spread"] = out["ask"] - out["bid"]
    return out


def aggregate_flow(classified: pd.DataFrame, freq: str = "5min") -> pd.DataFrame:
    required = {"timestamp", "price", "volume", "aggressor_side", "signed_volume", "spread"}
    missing = required.difference(classified.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    x = classified.copy().set_index("timestamp")
    x["buy_volume"] = np.where(x["aggressor_side"] == 1, x["volume"], 0.0)
    x["sell_volume"] = np.where(x["aggressor_side"] == -1, x["volume"], 0.0)
    x["unclassified_volume"] = np.where(x["aggressor_side"] == 0, x["volume"], 0.0)
    g = x.resample(freq, label="right", closed="right")

    out = pd.DataFrame({
        "open": g["price"].first(),
        "high": g["price"].max(),
        "low": g["price"].min(),
        "close": g["price"].last(),
        "trade_volume": g["volume"].sum(),
        "trade_count": g["price"].count(),
        "buy_volume": g["buy_volume"].sum(),
        "sell_volume": g["sell_volume"].sum(),
        "unclassified_volume": g["unclassified_volume"].sum(),
        "delta": g["signed_volume"].sum(),
        "median_spread": g["spread"].median(),
    })

    denom = out["trade_volume"].replace(0, np.nan)
    out["volume_imbalance"] = out["delta"] / denom
    out["price_displacement"] = out["close"] - out["open"]
    out["price_efficiency"] = out["price_displacement"].abs() / denom
    out["unclassified_share"] = out["unclassified_volume"] / denom
    out["trade_intensity_per_sec"] = out["trade_count"] / pd.Timedelta(freq).total_seconds()
    return out.dropna(subset=["open", "close"])
