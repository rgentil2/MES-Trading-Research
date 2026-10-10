#!/usr/bin/env python3
"""Non-scientific compatibility adapter. Leaves frozen H33-H52 formulas and stats intact.

Frozen experiment's stats() calls DatetimeIndex.sort() (removed in modern pandas).
Only while stats() executes, return an equivalent sortable NumPy datetime64 array.
No signal/fee/outcome/statistical settings are changed. 2025/26 ZIP firewall unchanged.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import nq_h33_h52_minute_2020_2024 as frozen

ORIGINAL_STATS=frozen.stats

def stats_compat(events):
    old=frozen.pd.to_datetime
    def sortable_datetime(*a,**kw):
        values=old(*a,**kw)
        return np.array(values,copy=True)  # .sort() is in-place on numpy, as intended
    frozen.pd.to_datetime=sortable_datetime
    try:
        return ORIGINAL_STATS(events)
    finally:
        frozen.pd.to_datetime=old

frozen.stats=stats_compat

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--zip',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--prereg-frozen',action='store_true')
    a=p.parse_args()
    frozen.run(a.zip,a.out,a.prereg_frozen)