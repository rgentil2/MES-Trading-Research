#!/usr/bin/env python3
"""NQ B02: ONLY 2025-10-15 NQ 12-25 DEV Tick Last -> 240 1min SHA256.

Never prints bars/ticks; compare safe canonical hash to private independent
Minute Last source hash generated without reading/using other days.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from datetime import date
from qc_tick_day import file_for,utc_bounds
from qc_tick_to_minutes import source_events,MINUTE_100NS,Bar
from nq_tick_short_horizon import dev_day

DAY="2025-10-15"
CONTRACT="12-25"
NMIN=240

def aggregate_events(events,day=DAY):
    # B02 is ONE fixed DEV date, not new exploration or sealed range.
    if day!=DAY:raise ValueError('B02 selected-day scope violation')
    dev_day(day)
    lo,hi=utc_bounds(date.fromisoformat(day))
    bars={};previous=None
    for ts,px,qty in events:
        if not lo<=ts<hi or (previous is not None and ts<previous):
            raise ValueError('Invalid ET window or tick order')
        if type(px)!=int or px<=0 or type(qty)!=int or qty<=0:
            raise ValueError('Invalid Last print')
        previous=ts
        idx=(ts-lo)//MINUTE_100NS
        if idx not in bars:bars[idx]=Bar.start(px,qty,ts)
        else:bars[idx].add(px,qty,ts)
    if sorted(bars)!=list(range(NMIN)):
        raise ValueError('Incomplete 240-minute Last day')
    records=[[k,bars[k].first,bars[k].high,bars[k].low,bars[k].last,bars[k].qty]
             for k in range(NMIN)]
    digest=hashlib.sha256(json.dumps(records,separators=(',',':'),
                                      ensure_ascii=True).encode('ascii')).hexdigest()
    return {
        'status':'TICK_SOURCE_DIGEST_ONLY',
        'source':'PRIVATE_DEV_TICK_LAST',
        'date_et':DAY,'contract':'NQ_12-25',
        'minute_label':'END_08:01_12:00_ET',
        'source_rows':NMIN,
        'total_volume_contracts':sum(r[-1] for r in records),
        'canonical_ohlcv_sha256':digest,
        'raw_prices_emitted':False,
        'strategy_outcomes_calculated':False}

def analyze(root):
    d=dev_day(DAY)
    f=file_for(root,d,'Last')
    if not f.name.startswith('NQ_'+CONTRACT+'_'):
        raise ValueError('B02 exact NQ 12-25 contract not available')
    return aggregate_events(source_events(f))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=analyze(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('NQ_TICK_DAY_DIGEST='+json.dumps(result,sort_keys=True))
