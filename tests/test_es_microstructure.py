import pandas as pd

from src.es_microstructure import aggregate_flow, attach_bbo_to_trades, classify_aggressor


def ts(values):
    return pd.to_datetime(values, utc=True)


def test_backward_asof_and_classifier():
    trades = pd.DataFrame({
        "timestamp": ts(["2024-06-03 13:30:00.150", "2024-06-03 13:30:00.250"]),
        "price": [5000.25, 5000.00],
        "volume": [3, 2],
    })
    bids = pd.DataFrame({
        "timestamp": ts(["2024-06-03 13:30:00.100", "2024-06-03 13:30:00.200"]),
        "price": [5000.00, 5000.00],
    })
    asks = pd.DataFrame({
        "timestamp": ts(["2024-06-03 13:30:00.120", "2024-06-03 13:30:00.220"]),
        "price": [5000.25, 5000.25],
    })

    out = classify_aggressor(attach_bbo_to_trades(trades, bids, asks))
    assert out["aggressor_side"].tolist() == [1, -1]
    assert (out["bid_timestamp"] <= out["timestamp"]).all()
    assert (out["ask_timestamp"] <= out["timestamp"]).all()


def test_aggregate_flow():
    df = pd.DataFrame({
        "timestamp": ts(["2024-06-03 13:30:01", "2024-06-03 13:30:02", "2024-06-03 13:30:03"]),
        "price": [5000.25, 5000.00, 5000.25],
        "volume": [3, 2, 5],
        "aggressor_side": [1, -1, 1],
        "signed_volume": [3, -2, 5],
        "spread": [0.25, 0.25, 0.25],
    })
    row = aggregate_flow(df).iloc[0]
    assert row["trade_volume"] == 10
    assert row["delta"] == 6
    assert abs(row["volume_imbalance"] - 0.6) < 1e-12
