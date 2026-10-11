#!/usr/bin/env python3
"""Predeclared, day-level BBO diagnostic on PRIVATE DEV Oct 2025-Jun 2026 ONLY.
Zero prices/events published. No fills, no strategy tuning, no sealed access.
Four dates per month were selected for weekly and weekday coverage using
ONLY the NinjaTrader export manifest, before inspecting BBO outcomes.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from statistics import median

DAYS_BY_MONTH={
 '2025-10':('15','21','27','31'),
 '2025-11':('04','12','20','24'),
 '2025-12':('02','10','18','29'),
 '2026-01':('06','14','22','30'),
 '2026-02':('03','11','19','27'),
 '2026-03':('03','11','19','27'),
 '2026-04':('07','15','23','24'),
 '2026-05':('05','13','21','29'),
 '2026-06':('02','10','18','26'),
}
FOCUS=('open_0930_1000','mid_1000_1030','late_1030_1130')

def percent(n,d):
    return round(100*n/d,3) if d else None

def summarize_day(raw):
    from qc_tick_day import check_day
    day=raw['date_et']
    check_day(day)
    if raw['status']!='DIAGNOSTIC_ONLY' or raw.get('holdout_2026_jul_sep_opened') is not False:
        raise ValueError('QC not approved for '+day)
    qc=raw.get('source_qc_counts',{})
    for kind in ('Last','Bid','Ask'):
        if qc.get(kind+'_rows',0)<=0:
            raise ValueError('Missing '+kind+' for '+day)
    total={k:0 for k in ('trades','valid','outside','sameprior','fix','age50n','age50o','age250n','age250o','age1000n','age1000o')}
    by_segment={}
    for seg in FOCUS:
        s=raw['segments'][seg]
        a=s['same_timestamp_alternative_NONCAUSAL']
        n,o=int(s['valid_prior']),int(s['outside'])
        if n<1 or o<0 or o>n:
            raise ValueError('Bad denominator '+day+'/'+seg)
        info={}
        total['trades']+=int(s['trades'])
        total['valid']+=n;total['outside']+=o
        for age in (50,250,1000):
            entry=s['age_thresholds_ms'][str(age)]
            dn,on=int(entry['n']),int(entry['outside'])
            if on>dn or dn>n:raise ValueError('Invalid age counts')
            total['age'+str(age)+'n']+=dn
            total['age'+str(age)+'o']+=on
            info['age'+str(age)+'_outside_pct']=percent(on,dn)
        same,fix=int(a['prior_outside']),int(a['prior_outside_alt_inside'])
        if fix>same:raise ValueError('Invalid same-time sensitivity')
        total['sameprior']+=same;total['fix']+=fix
        by_segment[seg]={
            'last_events':int(s['trades']),
            'prior_outside_pct':percent(o,n),
            'same_time_pct':s['same_time_pct'],
            'same_time_NONCAUSAL_reclassifies_pct':percent(fix,same),
            **info}
    if total['valid']<1 or total['trades']<1:raise ValueError('Empty focus window '+day)
    if not total['age50n']<=total['age250n']<=total['age1000n']<=total['valid']:
        raise ValueError('Non-nested age thresholds')
    return {
        'day_et':day,'last_events':total['trades'],
        'prior_valid':total['valid'],'prior_outside':total['outside'],
        'outside_pct':percent(total['outside'],total['valid']),
        'outside_age50ms_pct':percent(total['age50o'],total['age50n']),
        'outside_age250ms_pct':percent(total['age250o'],total['age250n']),
        'outside_age1000ms_pct':percent(total['age1000o'],total['age1000n']),
        'same_time_prior_outside':total['sameprior'],
        'same_time_NONCAUSAL_reclassifies_inside':total['fix'],
        'same_time_NONCAUSAL_reclassification_pct':percent(total['fix'],total['sameprior']),
        'segments':by_segment}

def summarize_month(month,daily):
    if month not in DAYS_BY_MONTH:raise ValueError('Sealed/out-of-scope month')
    expected={month+'-'+d for d in DAYS_BY_MONTH[month]}
    if len(daily)!=4 or {d['day_et'] for d in daily}!=expected:
        raise ValueError('Not all predeclared days completed')
    rates=[d['outside_pct'] for d in daily]
    n=sum(d['prior_valid'] for d in daily)
    o=sum(d['prior_outside'] for d in daily)
    same=sum(d['same_time_prior_outside'] for d in daily)
    fixes=sum(d['same_time_NONCAUSAL_reclassifies_inside'] for d in daily)
    return {
        'month':month,'status':'DIAGNOSTIC_ONLY_NOT_BACKTEST',
        'sample_design':'four predeclared weekdays across trading weeks from source manifest',
        'window_et':'09:30-11:30',
        'daily':daily,
        'median_daily_outside_pct':round(median(rates),3),
        'min_daily_outside_pct':min(rates),
        'max_daily_outside_pct':max(rates),
        'tick_weighted_outside_pct_DESCRIPTIVE':percent(o,n),
        'same_time_NONCAUSAL_reclassification_pct_DESCRIPTIVE':percent(fixes,same),
        'holdout_2026_jul_sep_opened':False,
        'strategy_return_or_fill_test':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--month',required=True,choices=sorted(DAYS_BY_MONTH))
    a=ap.parse_args()
    from qc_bbo_dislocation import analyze_day
    daily=[summarize_day(analyze_day(a.root,a.month+'-'+d)) for d in DAYS_BY_MONTH[a.month]]
    print('NQ_MONTH_QC_JSON='+json.dumps(summarize_month(a.month,daily),separators=(',',':'),sort_keys=True))

if __name__=='__main__':main()
