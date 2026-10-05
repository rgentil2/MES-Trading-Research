import numpy as np
import pandas as pd
import pytest

from src.mes_market_state_v1 import Config
from src.mes_market_state_v2 import (
    VERSION,
    cme_equity_schedule,
    classify,
    expected_rth_close_minute,
    session_usable,
)


CFG = Config(window=8, minimum_valid=4, atr_sessions=14, trend_sessions=10)


def synthetic_inputs(n=60):
    rows = []
    for i, day in enumerate(pd.bdate_range("2020-01-02", periods=n)):
        vol = 0.01 + 0.003 * np.sin(i * 0.5)
        er = 0.5 + 0.3 * np.cos(i * 0.4)
        rows.append(
            dict(
                date=str(day.date()),
                contract="MES 03-20",
                input_status="READY",
                vol=vol,
                er=er,
                trend_score=0.5,
                overnight_range_atr=1.1 + 0.3 * np.sin(i),
                overnight_return_atr=0.2,
                overnight_volume=1000 + 30 * i,
                preopen_gap_proxy_atr=0.3,
                log_vol=np.log(vol),
                log_on_range=np.log(1.1 + 0.3 * np.sin(i)),
                log_on_volume=np.log(1000 + 30 * i),
            )
        )
    return rows


def minute_group(start="2024-10-01 09:31", periods=390, contract="MES 12-24"):
    ts = pd.date_range(start, periods=periods, freq="min", tz="America/New_York")
    return pd.DataFrame(
        {
            "timestamp_et": ts,
            "minute": ts.hour * 60 + ts.minute,
            "contract": contract,
        }
    )


def test_regular_session_95pct_rule_and_endpoints():
    full = minute_group()
    assert session_usable(full, 960, 0.95)

    sparse = full.drop(full.index[20:39]).copy()  # 371 / 390, both endpoints.
    assert len(sparse) == 371
    assert session_usable(sparse, 960, 0.95)

    too_sparse = full.drop(full.index[20:40]).copy()  # 370 / 390.
    assert not session_usable(too_sparse, 960, 0.95)

    missing_close = full.iloc[:-1].copy()
    assert not session_usable(missing_close, 960, 0.95)


def test_scheduled_short_session_is_eligible_at_its_true_length():
    short = minute_group(periods=210)
    assert int(short.minute.iloc[-1]) == 780  # 13:00 ET
    assert session_usable(short, 780, 0.95)


def test_cme_schedule_excludes_weekend_and_has_shortened_session():
    schedule = cme_equity_schedule("2024-11-27", "2024-12-02")
    weekdays = {pd.Timestamp(x).day_name() for x in schedule.index}
    assert "Saturday" not in weekdays
    assert "Sunday" not in weekdays

    black_friday = schedule.loc[pd.Timestamp("2024-11-29")]
    assert expected_rth_close_minute(black_friday["market_close"]) < 960


def test_classification_prefix_invariance():
    x = synthetic_inputs()
    full = classify(x, CFG)
    assert (full.engine_version == VERSION).all()
    prefix = classify(x[:30], CFG)
    pd.testing.assert_frame_equal(
        full.iloc[:30].reset_index(drop=True),
        prefix.reindex(columns=full.columns).reset_index(drop=True),
    )


def test_future_mutation_does_not_change_past():
    x = synthetic_inputs()
    a = classify(x, CFG)
    changed = [dict(r) for r in x]
    for r in changed[30:]:
        r.update(vol=99.0, er=0.99, log_vol=50.0, overnight_volume=1_000_000_000)
    b = classify(changed, CFG)
    pd.testing.assert_frame_equal(a.iloc[:30], b.iloc[:30])


def test_classify_rejects_2025_feature_date_and_2026_contract():
    x = synthetic_inputs()
    x[-1]["date"] = "2025-01-02"
    with pytest.raises(ValueError, match="scope"):
        classify(x, CFG)

    y = synthetic_inputs()
    y[-1]["contract"] = "MES 03-26"
    with pytest.raises(ValueError, match="contract"):
        classify(y, CFG)
