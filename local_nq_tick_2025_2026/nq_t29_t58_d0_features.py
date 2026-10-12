#!/usr/bin/env python3
"""Thirty predeclared G0/D0 features, ONLY causal complete 377-print Last bars.

No future outcomes, no executions, no new 5-second signals, no OOS.
Registry freezes IDs, mechanism groups and CASE/CONTROL thresholds.
"""
from __future__ import annotations
from bisect import bisect_left,bisect_right
from collections import Counter,defaultdict
from fractions import Fraction
from itertools import groupby
from math import ceil
from pathlib import Path

from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge
from nq_tick_short_horizon import dev_day

LABELS=('CASE','CONTROL','OTHER','NOT_EVALUABLE')
CASE,CONTROL,OTHER,MISSING=LABELS

def histogram_features(rows,bar):
    if len(rows)!=bar.prints or not rows or rows[0][0]!=bar.start_timestamp or rows[-1][0]!=bar.end_timestamp:
        raise AssertionError('B29_WHOLE_BAR_PARITY')
    groups=[];prices=Counter()
    last=None
    for ts,it in groupby(rows,key=lambda e:e[0]):
        arr=list(it)
        if last is not None and ts<=last:
            raise ValueError('NONMONOTONIC_TIMESTAMP')
        if any(e[0]!=ts or e[1]<=0 or e[2]<=0 for e in arr):
            raise ValueError('BAD_LAST')
        q=sum(e[2] for e in arr)
        p=sum(e[1]*e[2] for e in arr)
        groups.append((ts,Fraction(p,q),q,len(arr),arr))
        last=ts
        for e in arr:prices[e[1]]+=e[2]
    if (len(groups)!=bar.whole_timestamp_groups or
        sum(x[2] for x in groups)!=bar.total_qty or
        sum(x[3] for x in groups)!=bar.prints):
        raise AssertionError('SAME_TIMESTAMP_ATOMIC_GROUP_SPLIT')
    n=bar.prints;q=bar.total_qty
    v=Fraction(bar.price_times_qty_ticks,q)
    r=bar.high_ticks-bar.low_ticks
    mids=Fraction(bar.high_ticks+bar.low_ticks,2)
    qtys=[e[2] for e in rows]
    gaps=[groups[i][0]-groups[i-1][0] for i in range(1,len(groups))]
    if any(g<=0 for g in gaps):
        raise ValueError('NONPOSITIVE_GROUP_GAP')
    path=sum((abs(groups[i][1]-groups[i-1][1]) for i in range(1,len(groups))),Fraction(0))
    gcount=len(groups)
    h=gcount//2
    topqty=sorted(qtys,reverse=True)[:ceil(n/10)]
    duplicate_same_px_prints=0
    for _,_,_,_,part in groups:
        counts=Counter(px for _,px,_ in part)
        duplicate_same_px_prints+=sum(n0 for n0 in counts.values() if n0>=2)
    pricevar=sum((e[2]*(e[1]-v)**2 for e in rows),Fraction(0))/q
    priceabs=sum((e[2]*abs(e[1]-v) for e in rows),Fraction(0))/q
    gapratio=(Fraction(sum(gaps[h:]),1+sum(gaps[:h])) if gaps else None)
    sortedg=sorted(gaps)
    gapmedian=(Fraction(sortedg[(len(sortedg)-1)//2]+sortedg[len(sortedg)//2],2) if gaps else None)
    return {
      'range_ticks':Fraction(r),
      'atomic_path_chop':path/r if r>0 else None,
      'qty_price_variance':pricevar,
      'vwap_edge_displacement':abs(v-mids)/r if r>0 else None,
      'price_level_hhi':sum((Fraction(z,q)**2 for z in prices.values()),Fraction(0)),
      'qty_per_print':Fraction(q,n),
      'print_qty_hhi':Fraction(sum(a*a for a in qtys),q*q),
      'top_decile_print_qty_share':Fraction(sum(topqty),q),
      'abs_vwap_unweighted_premium':abs(v-Fraction(sum(e[1] for e in rows),n)),
      'volume_abs_deviation':priceabs,
      'late_group_qty_share':Fraction(sum(g[2] for g in groups[h:]),q),
      'within_bar_arrival_gradient':gapratio,
      'multi_print_group_share':Fraction(sum(g[3]>=2 for g in groups),gcount),
      'largest_gap_share':Fraction(max(gaps),sum(gaps)) if gaps else None,
      'gap_median_mean_ratio':gapmedian*len(gaps)/sum(gaps) if gaps else None,
      'group_count':Fraction(gcount),
      'group_qty_hhi':sum((Fraction(g[2],q)**2 for g in groups),Fraction(0)),
      'unique_price_levels':Fraction(len(prices)),
      'qty_above_vwap_share':Fraction(sum(z for p,z in prices.items() if p>=v),q),
      'top_quartile_qty_share':Fraction(sum(z for p,z in prices.items() if p>=bar.low_ticks+Fraction(3*r,4)),q) if r>0 else None,
      'bottom_quartile_qty_share':Fraction(sum(z for p,z in prices.items() if p<=bar.low_ticks+Fraction(r,4)),q) if r>0 else None,
      'same_price_multifill_share':Fraction(duplicate_same_px_prints,n),
      'poc_qty_share':Fraction(max(prices.values()),q),
      '_v':v,'_high':bar.high_ticks,'_low':bar.low_ticks,
      '_bar_range':r
    }

def rolling_features(m):
    """Context-only metrics at E and at D on shifted causal windows A...E."""
    if len(m)<5:
        raise ValueError('FOUR_PRECEDING_COMPLETE_377_BARS_REQUIRED')
    def compute(ix):
        t=m[ix]
        v=lambda offset:m[ix-offset]['_v']
        w=[v(j) for j in (3,2,1,0)]
        increments=[w[i]-w[i-1] for i in range(1,4)]
        moves=sum((abs(x) for x in increments),Fraction(0))
        signs=[(x>0)-(x<0) for x in increments]
        concordance=1+sum(signs[i]==signs[i-1] and signs[i]!=0 for i in (1,2))
        high=max(m[j]['_high'] for j in (ix-2,ix-1,ix))
        low=min(m[j]['_low'] for j in (ix-2,ix-1,ix))
        prior=(v(1)+v(2)+v(3))/3
        return {
          'normalized_vwap_body':abs(v(0)-v(1))/(1+t['_bar_range']),
          'four_bar_efficiency':abs(v(0)-v(3))/(1+moves),
          'vwap_curvature':abs(v(0)-2*v(1)+v(2)),
          'vwap_acceleration_ratio':abs(v(0)-v(1))/(1+abs(v(1)-v(2))),
          'prior_vwap_proximity':1/(1+abs(v(0)-prior)),
          'rolling_three_range':Fraction(high-low),
          'trend_sign_concordance':Fraction(concordance)
        }
    return compute(3),compute(4)


def classify_features(before,registry):
    """No future input: snapshot of 5 completed 377-print bars A,B,C,D,E."""
    if len(before)!=5:
        raise AssertionError('FROZEN_5_BARS_REQUIRED')
    # before order A B C D E; E is anchor.
    dcontext,econtext=rolling_features(before)
    d={**before[-2],**dcontext}
    e={**before[-1],**econtext}
    result={}
    for row in registry['hypotheses']:
        id_,name=row['id'],row['feature']
        baseline=d[name];current=e[name]
        if (baseline is None or current is None or baseline<=0):
            result[id_]=MISSING
        elif current>=Fraction(11,10)*baseline:
            result[id_]=CASE
        elif current<=Fraction(10,11)*baseline:
            result[id_]=CONTROL
        else:result[id_]=OTHER
    if len(result)!=registry['family_size']:
        raise AssertionError('FAMILY_MEMBER_MISSING')
    return result


def screen_day(events,day,registry):
    dev_day(day)
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    lo,hi=et_edge(day,10,0),et_edge(day,10,15)
    ix=next((i for i,b in enumerate(bars) if lo<=b.end_timestamp<hi),None)
    if ix is None or ix<4:
        raise AssertionError('FROZEN_ANCHOR_MISSING_5_PRIORS')
    selected=bars[ix-4:ix+1]
    if len(selected)!=5 or any(x.end_timestamp>=y.start_timestamp
                                for x,y in zip(selected,selected[1:])):
        raise AssertionError('NON_CAUSAL_COMPLETE_CONTEXT')
    ts=[r[0] for r in events]
    features=[]
    for b in selected:
        i=bisect_left(ts,b.start_timestamp)
        j=bisect_right(ts,b.end_timestamp)
        features.append(histogram_features(events[i:j],b))
    return classify_features(features,registry)
