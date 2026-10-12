#!/usr/bin/env python3
"""36 preregistered new hypothesis features in SIX causal D0 mechanism blocks.

NOT standalone trading signals. ONE common 377 bar anchor and side per session.
No future labels, no PNL, no 5-second bar signals, no non-atomic Last prints.
Registry: research/nq/NQ_T61_T96_SIX_BLOCK_D0_FROZEN_2026_10_12.json
"""
from __future__ import annotations
from bisect import bisect_left,bisect_right
from collections import Counter
from fractions import Fraction as Q
from itertools import groupby
from statistics import median

from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge
from nq_tick_short_horizon import dev_day

CASE,CONTROL,OTHER,MISSING='CASE','CONTROL','OTHER','NOT_EVALUABLE'
LABELS=(CASE,CONTROL,OTHER,MISSING)

def sign(v):
    if v is None:return None
    return (v>0)-(v<0)

def weighted(arr):
    """At least one valid Last row, exact VWAP in price ticks."""
    if not arr:return None
    q=sum(z[2] for z in arr)
    if q<=0 or any(z[2]<=0 or z[1]<=0 for z in arr):
        raise ValueError('BAD_LAST_PRICE_QTY')
    return Q(sum(z[1]*z[2] for z in arr),q)

def whole_groups(rows):
    out=[];last=None
    for ts,it in groupby(rows,key=lambda x:x[0]):
        if last is not None and ts<=last:raise ValueError('NONMONOTONIC_LAST_TIME')
        x=list(it);qty=sum(z[2] for z in x)
        if qty<=0 or any(z[1]<=0 or z[2]<=0 for z in x):raise ValueError('BAD_LAST_GROUP')
        out.append((ts,Q(sum(z[1]*z[2] for z in x),qty),qty,len(x)))
        last=ts
    return out

def summary(rows):
    if not rows:return None
    g=whole_groups(rows)
    if len(g)<2:return None
    levels=Counter()
    for _,px,qty in rows:levels[px]+=qty
    maxqty=max(levels.values())
    poc=Q(sum(px for px,q in levels.items() if q==maxqty),
          sum(q==maxqty for q in levels.values()))
    return {'open':g[0][1],'end':g[-1][1],'vwap':weighted(rows),
            'lo':min(z[1] for z in rows),'hi':max(z[1] for z in rows),
            'poc':poc,'groups':g,'n':len(rows),
            'levels':levels}

def contextual(rows,starts,stop):
    """Slices [starts[i], starts[i+1]), exclusively BEFORE bar-E horizon."""
    ts=[r[0] for r in rows]
    chunks=[]
    for a,b in zip(starts,starts[1:]):
        lo,hi=bisect_left(ts,a),bisect_left(ts,b)
        chunks.append(summary(rows[lo:hi]))
    return chunks

def group_weighted(groups):
    if not groups:return None
    q=sum(g[2] for g in groups)
    if q<=0:raise ValueError('BAD_GROUP_QTY')
    return sum((g[1]*g[2] for g in groups),Q(0))/q

def median_exact(vals):
    if not vals:return None
    v=sorted(vals);n=len(v)
    return Q(v[n//2]) if n%2 else Q(v[n//2-1]+v[n//2],2)

def bar_votes(rows,summary_e):
    """Atomic print-size and arrival mechanics; no original print order within ties."""
    b=summary_e;g=b['groups'];ans={}
    avg=Q(sum(z[1] for z in rows),len(rows))
    ans['weighted_minus_unweighted']=b['vwap']-avg
    siz=median_exact([z[2] for z in rows])
    large=[z for z in rows if z[2]>siz]
    small=[z for z in rows if z[2]<=siz]
    a,z=weighted(large),weighted(small)
    ans['large_minus_small_vwap']=a-z if a is not None and z is not None else Q(0)
    groupmed=median_exact([z[2] for z in g])
    gl=[z for z in g if z[2]>groupmed]
    gs=[z for z in g if z[2]<=groupmed]
    a,z=group_weighted(gl),group_weighted(gs)
    ans['large_atomic_qty_minus_small']=a-z if a is not None and z is not None else Q(0)
    mid=Q(b['lo']+b['hi'],2)
    upper=sum(qty for px,qty in b['levels'].items() if px>mid)
    lower=sum(qty for px,qty in b['levels'].items() if px<mid)
    ans['qty_upper_vs_lower']=Q(upper-lower)
    # Cut ONLY between whole timestamp groups. First group crossing half of
    # target print count remains in FIRST part; never split equal timestamp.
    boundary=0;cum=0
    for idx,v in enumerate(g):
        cum+=v[3];boundary=idx+1
        if cum*2>=len(rows):break
    a,z=group_weighted(g[:boundary]),group_weighted(g[boundary:])
    ans['late_minus_early_print_vwap']=z-a if a is not None and z is not None else Q(0)
    delays=[g[i][0]-g[i-1][0] for i in range(1,len(g))]
    if any(z<=0 for z in delays):raise ValueError('BAD_TIME_GAP')
    gapmed=median_exact(delays)
    fast=[g[i] for i in range(1,len(g)) if delays[i-1]<gapmed]
    slow=[g[i] for i in range(1,len(g)) if delays[i-1]>=gapmed]
    a,z=group_weighted(fast),group_weighted(slow)
    ans['fast_vs_slow_price']=a-z if a is not None and z is not None else Q(0)
    multi=[v for v in g if v[3]>=2]
    single=[v for v in g if v[3]==1]
    a,z=group_weighted(multi),group_weighted(single)
    ans['multi_vs_single_price']=a-z if a is not None and z is not None else Q(0)
    midgroup=len(g)//2
    a,z=group_weighted(g[:midgroup]),group_weighted(g[midgroup:])
    ans['late_vs_early_atomic_vwap']=z-a if a is not None and z is not None else Q(0)
    # Duration-weighted group VWAP change, includes no future group.
    ans['gap_weighted_move']=(sum(((g[i][1]-g[i-1][1])*delays[i-1]
                                 for i in range(1,len(g))),Q(0))
                              /sum(delays) if delays else Q(0))
    return ans

def first_bars(events,day):
    dev_day(day)
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    lo,hi=et_edge(day,10,0),et_edge(day,10,15)
    ix=next((i for i,b in enumerate(bars) if lo<=b.end_timestamp<hi),None)
    if ix is None or ix<4:raise AssertionError('NO_FIVE_COMPLETE_BARS')
    selected=bars[ix-4:ix+1]
    if any(a.end_timestamp>=b.start_timestamp
           for a,b in zip(selected,selected[1:])):
        raise AssertionError('BAR_TIMESTAMPS_NOT_ATOMIC')
    ts=[r[0] for r in events]
    subsets=[]
    for bar in selected:
        i,j=bisect_left(ts,bar.start_timestamp),bisect_right(ts,bar.end_timestamp)
        part=events[i:j]
        if len(part)!=bar.prints or len(part)<=0 or weighted(part)!=Q(bar.price_times_qty_ticks,bar.total_qty):
            raise AssertionError('COMPLETE_377_LAST_PARITY')
        subsets.append(part)
    return subsets,selected[-1].end_timestamp

def classify_day(events,day,registry):
    dev_day(day)
    bars,anchor=first_bars(events,day)
    abcde=[summary(rows) for rows in bars]
    if any(s is None for s in abcde):raise AssertionError('BAR_NO_ATOMIC_CONTEXT')
    a,b,c,d,e=abcde
    side=sign(e['vwap']-d['vwap'])
    if side is None:raise AssertionError('SIDE_NOT_DEFINED')
    # PREMARKET and 1st 30min RTH; the last segment ends at 10:00
    # E anchor is within [10:00,10:15), so all earlier windows causal.
    edges=[et_edge(day,8,30),et_edge(day,9,0),et_edge(day,9,30),
           et_edge(day,9,45),et_edge(day,10,0)]
    pm1,pm2,o1,o2=contextual(events,edges,anchor)
    # total 08:30..09:30 PM, total RTH 09:30..10:00, each original full window
    ts=[x[0] for x in events]
    def combined(start,end):
        return summary(events[bisect_left(ts,start):bisect_left(ts,end)])
    pm=combined(edges[0],edges[2])
    op=combined(edges[2],edges[4])
    def diff(x,y):
        return (x-y) if x is not None and y is not None else None
    v={}
    v['pm_full_body']=diff(pm['end'],pm['open']) if pm else None
    v['pm_first_half_body']=diff(pm1['end'],pm1['open']) if pm1 else None
    v['pm_second_half_body']=diff(pm2['end'],pm2['open']) if pm2 else None
    v['pm_end_relative_vwap']=diff(pm['end'],pm['vwap']) if pm else None
    v['pm_half_vwap_shift']=diff(pm2['vwap'],pm1['vwap']) if pm1 and pm2 else None
    v['pm_vwap_vs_range_mid']=diff(pm['vwap'],Q(pm['hi']+pm['lo'],2)) if pm else None
    v['open_first15_body']=diff(o1['end'],o1['open']) if o1 else None
    v['open_next15_body']=diff(o2['end'],o2['open']) if o2 else None
    v['open_full30_body']=diff(op['end'],op['open']) if op else None
    v['open_first15_end_vs_vwap']=diff(o1['end'],o1['vwap']) if o1 else None
    v['open_next15_end_vs_vwap']=diff(o2['end'],o2['vwap']) if o2 else None
    v['open_vwap_vs_premarket_vwap']=diff(op['vwap'],pm['vwap']) if op and pm else None
    v['prior_d_minus_c_vwap']=d['vwap']-c['vwap']
    v['prior_c_minus_b_vwap']=c['vwap']-b['vwap']
    v['prior_b_minus_a_vwap']=b['vwap']-a['vwap']
    v['e_high_vs_d_high']=Q(e['hi']-d['hi'])
    v['e_low_vs_d_low']=Q(e['lo']-d['lo'])
    v['e_vwap_vs_prior_abc_mean']=e['vwap']-(a['vwap']+b['vwap']+c['vwap'])/3
    for key,val in bar_votes(bars[-1],e).items():
        v['e_'+key]=val
    d_votes=bar_votes(bars[-2],d)
    v['d_weighted_minus_unweighted']=d_votes['weighted_minus_unweighted']
    v['d_multi_vs_single_price']=d_votes['multi_vs_single_price']
    v['d_gap_weighted_move']=d_votes['gap_weighted_move']
    v['e_vwap_vs_range_mid']=e['vwap']-Q(e['hi']+e['lo'],2)
    v['e_poc_vs_vwap']=e['poc']-e['vwap']
    v['e_last_atomic_vs_poc']=e['end']-e['poc']
    v['e_last_atomic_vs_mid']=e['end']-Q(e['hi']+e['lo'],2)
    v['e_last_atomic_vs_d_mid']=e['end']-Q(d['hi']+d['lo'],2)
    v['e_poc_vs_d_poc']=e['poc']-d['poc']
    names={x['feature'] for x in registry['hypotheses']}
    if set(v)!=names:raise AssertionError('FROZEN_FEATURES_NOT_36')
    result={}
    for x in registry['hypotheses']:
        k=x['id'];vote=sign(v[x['feature']])
        result[k]=(MISSING if vote is None or side==0 else
                   OTHER if vote==0 else CASE if vote==side else CONTROL)
    if len(result)!=36 or anchor>=et_edge(day,10,15):
        raise AssertionError('ANCHOR_OUT_OF_WHITELIST')
    return result
