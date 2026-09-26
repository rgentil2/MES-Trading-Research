import pandas as pd

from research.r001_vwap_analysis import rth_mask


def test_rth_mask_uses_ninjatrader_end_of_bar_timestamps():
    ts = pd.Series(pd.to_datetime([
        '2026-01-05 09:30:00-05:00',
        '2026-01-05 09:31:00-05:00',
        '2026-01-05 16:00:00-05:00',
        '2026-01-05 16:01:00-05:00',
    ]))
    assert rth_mask(ts).tolist() == [False, True, True, False]