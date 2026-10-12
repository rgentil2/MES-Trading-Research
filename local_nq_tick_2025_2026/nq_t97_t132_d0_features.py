#!/usr/bin/env python3
"""C97-C132 SIX new research blocks. D0 NO FUTURE, per-session 233/377/4181 context.

All print-count bars end on WHOLE equal-timestamp groups, never on 5s.
Regime, directional vote and two-parent consensus hypotheses share exact anchor.
"""
from __future__ import annotations
from bisect import bisect_left,bisect_right
from fractions import Fraction as F

from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge
from nq_t61_t96_d0_features import first_bars,summary,sign,CASE,CONTROL,OTHER,MISSING

FEATURES=(
'micro_vwap_slope','micro_two_vwap_slope','micro_end_vs_open','micro_end_vs_vwap',
'micro_high_shift','micro_low_shift',
'macro_vwap_slope','macro_end_vs_open','macro_vwap_vs_micro_vwap',
'macro_high_shift','macro_low_shift','macro_end_vs_prev_vwap',
'end_vs_pm_outer','end_vs_rth_outer','end_vs_prior377_outer',
'end_vs_prior233_outer','end_vs_prior4181_outer','end_vs_pm_vwap',
'micro_end_vs_d_vwap','micro_end_vs_macro_vwap','e_end_vs_pm_mid',
'e_end_vs_rth_mid','e_end_vs_prior233_mid','e_end_vs_prior4181_mid',
'micro_range_change','micro_qty_per_sec_change','micro_group_density_change',
'macro_range_change','micro_vs_macro_range_scaled','e377_speed_vs_d377',
'micro_pm_consensus','micro_rth_consensus','micro_macro_consensus',
'macro_pm_consensus','macro_rth_consensus','micro_prior377_consensus')
N=36
LABELS=(CASE,CONTROL,OTHER,MISSING)

def _bar_summary(e,ts,b):
    lo=bisect_left(ts,b.start_timestamp)
    hi=bisect_right(ts,b.end_timestamp)
    subset=e[lo:hi]
    if len(subset)!=b.prints:raise AssertionError('WHOLE_TIMESTAMP_BAR_PARITY')
    s=summary(subset)
    if s is None:raise AssertionError('BAR_UNEXPECTED_SINGLE_TIMESTAMP')
    if s['hi']!=b.high_ticks or s['lo']!=b.low_ticks or (
        s['vwap']!=F(b.price_times_qty_ticks,b.total_qty)):
        raise AssertionError('TIMEGROUP_PRICES_MISMATCH')
    s['_b']=b
    return s

def safe_sub(e,ts,start,end):
    # Note: each end is exclusive, boundary timestamp belongs to NEXT window.
    return summary(e[bisect_left(ts,start):bisect_left(ts,end)])

def _macro_ranges(s):
    return (s['hi'],s['lo']) if s is not None else None

def directional(side,raw):
    return None if side==0 or raw is None else side*raw

def barrier(side,close,hi,lo):
    if side==0 or hi is None or lo is None:return None
    return side*(close-(hi if side>0 else lo))

def midpoint(s):
    return F(s['hi']+s['lo'],2) if s is not None else None

def delta(x,y):
    return None if x is None or y is None else x-y

def cons(side,a,b):
    if side==0 or a is None or b is None:return None
    sa,sb=sign(a),sign(b)
    if sa==0 or sb==0:return F(0)
    return F(1) if sa==side and sb==side else (F(-1) if sa==-side and sb==-side else F(0))

def classify_day(e,day,registry):
    # dev_day asserted before source_events by the month-level loader.
    es,anchor=first_bars(e,day)
    abcde=[summary(x) for x in es]
    if any(x is None for x in abcde):raise AssertionError('MISSING_377_CONTEXT')
    a,b,c,d,last=abcde
    impulse=last['vwap']-d['vwap'];side=sign(impulse)
    if anchor!=es[-1][-1][0]:raise AssertionError('E_ANCHOR_PARITY')
    nbar=completed_bars_by_print_count(e,day,(233,4181))
    ts=[z[0] for z in e]
    microbars=[b for b in nbar[233] if b.end_timestamp<=anchor][-3:]
    macrobar=[b for b in nbar[4181] if b.end_timestamp<=anchor][-2:]
    m=[_bar_summary(e,ts,x) for x in microbars]
    k=[_bar_summary(e,ts,x) for x in macrobar]
    m0,m1,m2=([None]*(3-len(m))+m)
    k0,k1=([None]*(2-len(k))+k)
    pm=safe_sub(e,ts,et_edge(day,8,30),et_edge(day,9,30))
    rth=safe_sub(e,ts,et_edge(day,9,30),et_edge(day,10,0))
    # Timestamps strictly earlier than E anchor. No future markout computed.
    time_ok=anchor>=et_edge(day,10,0)
    if not time_ok:raise AssertionError('BAD_DECISION_CLOCK')
    def v(x,field):
        return x[field] if x is not None else None
    def r(x):
        return x['hi']-x['lo'] if x is not None else None
    def dur(x):
        if x is None:return None
        z=x['_b'].end_timestamp-x['_b'].start_timestamp
        return z if z>0 else None
    def w(x):
        return x['_b'].total_qty if x is not None else None
    def density(x):
        return F(len(x['groups']),x['_b'].prints) if x is not None else None
    def outer(s):
        return (s['hi'],s['lo']) if s is not None else (None,None)
    ph,pl=outer(pm);oh,ol=outer(rth)
    dh=max(c['hi'],d['hi']);dl=min(c['lo'],d['lo'])
    mh=max([x['hi'] for x in m if x is not None],default=None)
    ml=min([x['lo'] for x in m if x is not None],default=None)
    kh,kl=outer(k1)
    end=last['end']
    micro_slope=delta(v(m2,'vwap'),v(m1,'vwap'))
    macro_slope=delta(v(k1,'vwap'),v(k0,'vwap'))
    pm_body=delta(v(pm,'end'),v(pm,'open'))
    rth_body=delta(v(rth,'end'),v(rth,'open'))
    prior_slope=d['vwap']-c['vwap']
    feature={}
    raw={
        'micro_vwap_slope':micro_slope,
        'micro_two_vwap_slope':delta(v(m2,'vwap'),v(m0,'vwap')),
        'micro_end_vs_open':delta(v(m2,'end'),v(m2,'open')),
        'micro_end_vs_vwap':delta(v(m2,'end'),v(m2,'vwap')),
        'micro_high_shift':delta(v(m2,'hi'),v(m1,'hi')),
        'micro_low_shift':delta(v(m2,'lo'),v(m1,'lo')),
        'macro_vwap_slope':macro_slope,
        'macro_end_vs_open':delta(v(k1,'end'),v(k1,'open')),
        'macro_vwap_vs_micro_vwap':delta(v(k1,'vwap'),v(m2,'vwap')),
        'macro_high_shift':delta(v(k1,'hi'),v(k0,'hi')),
        'macro_low_shift':delta(v(k1,'lo'),v(k0,'lo')),
        'macro_end_vs_prev_vwap':delta(v(k1,'end'),v(k0,'vwap')),
        'end_vs_pm_outer':barrier(side,end,ph,pl),
        'end_vs_rth_outer':barrier(side,end,oh,ol),
        'end_vs_prior377_outer':barrier(side,end,dh,dl),
        'end_vs_prior233_outer':barrier(side,end,mh,ml) if len(m)==3 else None,
        'end_vs_prior4181_outer':barrier(side,end,kh,kl),
        'end_vs_pm_vwap':delta(end,v(pm,'vwap')),
        'micro_end_vs_d_vwap':delta(v(m2,'end'),d['vwap']),
        'micro_end_vs_macro_vwap':delta(v(m2,'end'),v(k1,'vwap')),
        'e_end_vs_pm_mid':delta(end,midpoint(pm)),
        'e_end_vs_rth_mid':delta(end,midpoint(rth)),
        'e_end_vs_prior233_mid':delta(end,F(mh+ml,2) if len(m)==3 else None),
        'e_end_vs_prior4181_mid':delta(end,midpoint(k1))
    }
    for x in registry['members']:
        if x['mode']=='VOTO':
            name=x['feature']
            if name in ('end_vs_pm_outer','end_vs_rth_outer',
                        'end_vs_prior377_outer','end_vs_prior233_outer',
                        'end_vs_prior4181_outer'):
                feature[name]=raw[name]  # already sign-side adjusted
            else:
                feature[name]=directional(side,raw[name])
    feature['micro_range_change']=delta(r(m2),r(m1))
    feature['micro_qty_per_sec_change']=(delta(F(w(m2),dur(m2)),F(w(m1),dur(m1)))
      if m2 and m1 and dur(m2) and dur(m1) else None)
    feature['micro_group_density_change']=delta(density(m2),density(m1))
    feature['macro_range_change']=delta(r(k1),r(k0))
    feature['micro_vs_macro_range_scaled']=(delta(F(r(m2),m2['_b'].prints),F(r(k1),k1['_b'].prints))
      if m2 and k1 else None)
    feature['e377_speed_vs_d377']=(
        d['_b'].end_timestamp-d['_b'].start_timestamp
        -(last['_b'].end_timestamp-last['_b'].start_timestamp)
        if '_b' in d and '_b' in last else
        # fall back to raw E+D bar group spans (identical meaning)
        ((es[-2][-1][0]-es[-2][0][0])-(es[-1][-1][0]-es[-1][0][0])))
    feature['micro_pm_consensus']=cons(side,micro_slope,pm_body)
    feature['micro_rth_consensus']=cons(side,micro_slope,rth_body)
    feature['micro_macro_consensus']=cons(side,micro_slope,macro_slope)
    feature['macro_pm_consensus']=cons(side,macro_slope,pm_body)
    feature['macro_rth_consensus']=cons(side,macro_slope,rth_body)
    feature['micro_prior377_consensus']=cons(side,micro_slope,prior_slope)
    if set(feature)!=set(FEATURES):raise AssertionError('NOT_ALL_36_FEATURES_CALCULATED')
    labels={}
    for member in registry['members']:
        id_=member['id'];x=feature[member['feature']]
        vote=sign(x)
        labels[id_]=(MISSING if vote is None else
            OTHER if vote==0 else CASE if vote>0 else CONTROL)
    if len(labels)!=N:raise AssertionError('BAD_FAMILY_LENGTH')
    return labels
