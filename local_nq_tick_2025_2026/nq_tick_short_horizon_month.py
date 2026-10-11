#!/usr/bin/env python3
"""Aggregate preregistered NQ T01-T03 short-horizon pilot to full Oct-Apr DEV months.
Data from PRIVATE DEV Tick Last only. Daily/monthly AGGREGATES, never prices
or individual signals; NO P&L or executions; no May-Sep 2026 access.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path
from statistics import median
from nq_tick_short_horizon import dev_day,FAMILIES,HORIZONS,analyze_day

MONTHS=('2025-10','2025-11','2025-12','2026-01','2026-02','2026-03','2026-04')
NQ_FILE=re.compile(r'^NQ_(?:03|06|09|12)-\d{2}_(\d{4})_(\d{8})_Tick_Last_ET0800_1200\.txt$')

def month_days(root:Path,month:str):
    if month not in MONTHS:
        raise ValueError('Forbidden month: only Oct2025-Apr2026 development')
    names=sorted((root/'Tick_Last').glob('NQ_*_Tick_Last_ET0800_1200.txt'))
    dates=[]
    for path in names:
        match=NQ_FILE.fullmatch(path.name)
        if not match:raise ValueError('Unexpected Last source file')
        year,stamp=match.groups()
        day=f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}'
        if day[:7]!=month or year!=stamp[:4]:
            raise ValueError('Mixed month or contract year')
        dev_day(day) # reject before source file is opened
        dates.append(day)
    if not dates or len(dates)!=len(set(dates)):
        raise ValueError('Empty month or duplicate dates')
    return dates

def summarize_month(month:str, daily:list[dict]):
    if month not in MONTHS:raise ValueError('Forbidden month')
    if not daily:raise ValueError('No days')
    for row in daily:
        d=dev_day(row['date_et'])
        if d.strftime('%Y-%m')!=month or row['holdout_2026_may_sep_opened'] is not False:
            raise ValueError('Mismatched or forbidden source day')
        if row['status'] not in ('DIAGNOSTIC_ONLY','SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
            raise ValueError('Unexpected source status')
    eligible=[r for r in daily if r['status']=='DIAGNOSTIC_ONLY']
    if not eligible:raise ValueError('All opening intervals invalid')
    stats={}
    for key in FAMILIES:
        counts=[r['families'][key]['opportunities'] for r in eligible]
        horizon={}
        for h in HORIZONS:
            measures=[r['families'][key]['forward_ticks'][str(h)] for r in eligible]
            n=sum(x['n'] for x in measures)
            total=sum(x['mean']*x['n'] for x in measures if x['n'])
            daymed=[x['median'] for x in measures if x['n']]
            horizon[str(h)]={
                'n':n,
                'opportunity_weighted_mean_gross_ticks':round(total/n,3) if n else None,
                'median_of_active_day_medians_gross_ticks':round(median(daymed),3) if daymed else None,
                'active_forward_days':len(daymed)}
        stats[key]={
            'total_opportunities':sum(counts),
            'active_days':sum(x>0 for x in counts),
            'median_opportunities_per_eligible_day':median(counts),
            'forward_ticks':horizon}
    return {'month':month,'status':'DIRECTIONAL_DIAGNOSTIC_ONLY',
        'source_days':len(daily),'eligible_days':len(eligible),
        'excluded_days':len(daily)-len(eligible),
        'excluded_reason_counts':dict(Counter(r['status'] for r in daily if r['status']!='DIAGNOSTIC_ONLY')),
        'families':stats,
        'trades_executed_or_costs_applied':False,
        'holdout_2026_may_sep_opened':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--month',required=True)
    a=p.parse_args()
    days=month_days(a.root,a.month)
    results=[analyze_day(a.root,day) for day in days]
    print('NQ_SHORT_HORIZON_MONTH='+json.dumps(summarize_month(a.month,results),sort_keys=True,separators=(',',':')))
