import numpy as np
import pandas as pd

from src.research_utils import add_forward_extrema, prepare_rth_features
from research.archive.R005.r005_morning_orb import build_events


def _session(date, breakout_minute):
    start=pd.Timestamp(f"{date} 09:31:00",tz="America/New_York").tz_convert("UTC")
    ts=pd.date_range(start,periods=180,freq="min")
    n=len(ts); close=np.full(n,100.0); high=np.full(n,100.5); low=np.full(n,99.5)
    bts=pd.Timestamp(f"{date} {breakout_minute//60:02d}:{breakout_minute%60:02d}:00",tz="America/New_York").tz_convert("UTC")
    idx=int(np.where(ts==bts)[0][0])
    close[idx:]=101.25; high[idx:]=101.5; low[idx:]=100.75
    return pd.DataFrame({"timestamp_et":ts,"open":close,"high":high,"low":low,"close":close,"volume":np.full(n,100),"contract":["MES 03-26"]*n})


def test_1130_allowed_1131_excluded():
    raw=pd.concat([_session("2026-01-05",690),_session("2026-01-06",691)],ignore_index=True)
    feat=prepare_rth_features(raw,"2026-01-05","2026-01-06",horizons=[30])
    feat=add_forward_extrema(feat,horizons=[30])
    events=build_events(feat)
    assert len(events)==1
    assert events.iloc[0]["session_date"]=="2026-01-05"
    assert events.iloc[0]["breakout_time_et"]=="11:30"
