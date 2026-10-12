#!/usr/bin/env python3
"""Preregistered D1 OBSERVATIONAL markouts T20-T25. Never broker fills or PnL.

Uses ONLY existing 7 DEV months, complete atomic timestamp groups and a fixed
first 377-print anchor. Private session outcomes never leave the runner.
"""
from __future__ import annotations
import argparse
import json
import random
from bisect import bisect_left, bisect_right
from collections import Counter
from fractions import Fraction
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS, month_days
from nq_b05h01_trade_expansion_month import frozen_t05, et_edge
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t20_t25_fixed_anchor_screen import IDS, CASE, CONTROL, OTHER, MISSING, classify, v
from nq_t20_t25_economic_month import SCREEN_COUNTS, MAG, DIRECTIONAL

HORIZON_300_NS = 300 * 10_000_000
HORIZON_900_NS = 900 * 10_000_000
N_SESSIONS = 135
B = 10000
BLOCKS = (3, 5, 10)
GROUPS = (CASE, CONTROL)
LABELS = (CASE, CONTROL, OTHER, MISSING)
PREREG = 'research/nq/NQ_T20_T25_D1_ATOMIC_TIMESTAMP_MARKOUT_PREREG_2026_10_12.md'


def as_of_anchor(events, day):
    """One reusable causal print-bar pass, same formula as frozen Stage0."""
    dev_day(day)
    bars = completed_bars_by_print_count(events, day, (233, 377, 4181))
    lo, hi = et_edge(day, 10, 0), et_edge(day, 10, 15)
    ix = next((i for i, b in enumerate(bars[377])
               if lo <= b.end_timestamp < hi), None)
    if ix is None or ix < 4:
        raise AssertionError('stage0 377 anchor absent on READY session')
    a, b, c, d, e = bars[377][ix-4:ix+1]
    if not (a.end_timestamp < b.end_timestamp < c.end_timestamp <
            d.end_timestamp < e.end_timestamp):
        raise ValueError('NONCAUSAL_BAR_OR_TIMESTAMP_SPLIT')
    prior = {}
    for n in (233, 4181):
        pool = bars[n]
        ends = [row.end_timestamp for row in pool]
        prior[n] = pool[max(0, bisect_left(ends, e.end_timestamp)-2):
                         bisect_left(ends, e.end_timestamp)]
    return classify(a, b, c, d, e, prior[233], prior[4181]), e.end_timestamp, v(e)


def first_post_horizon_atomic_vwap(events, times, threshold):
    """First WHOLE timestamp group strictly AFTER threshold, never last row."""
    i = bisect_right(times, threshold)
    if i >= len(times):
        raise ValueError('NO_LAST_GROUP_AFTER_FROZEN_HORIZON_FAIL_CLOSED')
    j = bisect_right(times, times[i], lo=i)
    total_qty = sum(e[2] for e in events[i:j])
    if total_qty <= 0 or any(e[2] <= 0 for e in events[i:j]):
        raise ValueError('INVALID_LAST_QTY')
    return Fraction(sum(e[1] * e[2] for e in events[i:j]), total_qty)


def range_at_900(events, times, t):
    if not times or times[-1] < t + HORIZON_900_NS:
        raise ValueError('T23_15MIN_COVERAGE_FAIL_CLOSED')
    a, z = bisect_right(times, t), bisect_right(times, t + HORIZON_900_NS)
    if a >= z:
        raise ValueError('T23_NO_LAST_IN_FUTURE_WINDOW')
    vals = [e[1] for e in events[a:z]]
    return max(vals) - min(vals)


def one_day(events, day):
    labels, t, anchor_vwap = as_of_anchor(events, day)
    times = [e[0] for e in events]
    future = first_post_horizon_atomic_vwap(events, times, t + HORIZON_300_NS)
    outcome = {}
    for k in IDS:
        group, side = labels[k]
        if group not in LABELS:
            raise AssertionError('missing stage0 group')
        if group not in GROUPS:
            value = None
        elif k == MAG:
            if side != 0:
                raise AssertionError('magnitude must never have trade side')
            value = range_at_900(events, times, t)
        elif side == 0:
            if group != CONTROL:
                raise AssertionError('case cannot have unknown direction')
            value = None
        elif side in (-1, 1):
            value = float(side * (future - anchor_vwap))
        else:
            raise AssertionError('unregistered case/control side')
        outcome[k] = {'group': group, 'side': side, 'value': value}
    return outcome


def month_stage(root, month, out):
    if month not in MONTHS:
        raise ValueError('SEALED_MONTH_DENIED_BEFORE_IO')
    if out.exists():
        raise ValueError('private report cannot be overwritten')
    qc = Counter()
    labels = {k: Counter() for k in IDS}
    side0 = {k: Counter() for k in IDS}
    daily = []
    source = 0
    for day in sorted(month_days(root, month)):
        dev_day(day)
        source += 1
        events = list(source_events(file_for(root, dev_day(day), 'Last')))
        ready, _, _ = frozen_t05(events, day)
        qc[ready] += 1
        if ready != 'READY':
            continue
        out_day = one_day(events, day)
        for k in IDS:
            row = out_day[k]
            labels[k][row['group']] += 1
            if row['group'] in GROUPS and row['side'] == 0:
                side0[k][row['group']] += 1
        # Private session vectors; no dates/prices released in PUBLIC artifact.
        daily.append(out_day)
    eligible = qc['READY']
    if source != sum(qc.values()) or eligible != len(daily):
        raise AssertionError('DEV eligibility/count broken')
    for k in IDS:
        if sum(labels[k].values()) != eligible:
            raise AssertionError('missing per-question class')
    result = {'status':'T20_T25_D1_PRIVATE_OBSERVATIONAL_MARKOUT_NO_PNL',
              'month':month, 'source':source,'eligible':eligible,
              'labels':{k:{g:labels[k][g] for g in LABELS} for k in IDS},
              'no_direction':{k:{g:side0[k][g] for g in GROUPS} for k in IDS},
              'daily':daily, 'private':True, 'holdouts_opened':False,
              'new_history_acquired':False,'new_5second_signals':False,
              'trades_simulated':False,'broker_fills_modelled':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,separators=(',',':'))+'\n')
    return {'month':month,'source':source,'eligible':eligible,
            'outcomes_private':True,'PnL':None,'N_trades':0}


def pct(sorted_values, q):
    if not sorted_values:
        return None
    index = (len(sorted_values)-1)*q
    a = int(index)
    return sorted_values[a] + (index-a)*(sorted_values[min(a+1,len(sorted_values)-1)]-sorted_values[a])


def bootstrap_delta(rows, k, block_size, repeats=B):
    """Session-dependent case/control sign; no independent-trade assumptions."""
    if len(rows) != N_SESSIONS:
        raise ValueError('require ALL 135 eligible session labels')
    x = [day[k] for day in rows]
    case = [a['value'] for a in x if a['group']==CASE and a['value'] is not None]
    control = [a['value'] for a in x if a['group']==CONTROL and a['value'] is not None]
    if min(len(case),len(control)) < 15:
        return {'ci90':None,'p_exploratory':None,'valid_replicates':0,'reason':'LOW_GROUP_N'}
    direction = -1 if k == MAG else 1
    observed = direction * (sum(case)/len(case)-sum(control)/len(control))
    rng = random.Random(20261012+100*block_size+int(k[1:3]))
    draws = []
    n = len(x)
    for _ in range(repeats):
        sum_case = sum_ctrl = 0.
        n_case = n_ctrl = 0
        sampled = 0
        while sampled < n:
            start = rng.randrange(0, n - block_size + 1)
            for idx in range(start, min(start+block_size, n)):
                if sampled >= n:
                    break
                a = x[idx]
                if a['value'] is not None:
                    if a['group'] == CASE:
                        sum_case += a['value'];n_case += 1
                    elif a['group'] == CONTROL:
                        sum_ctrl += a['value'];n_ctrl += 1
                sampled += 1
        if n_case and n_ctrl:
            draws.append(direction*(sum_case/n_case-sum_ctrl/n_ctrl))
    if len(draws) < repeats * .9:
        return {'ci90':None,'p_exploratory':None,'valid_replicates':len(draws),
                'reason':'LOW_VALID_BOOTSTRAP'}
    draws.sort()
    p = (1+sum((a-observed)>=observed for a in draws))/(len(draws)+1)
    return {'ci90':[pct(draws,.05),pct(draws,.95)],'p_exploratory':p,
            'valid_replicates':len(draws),'reason':None}


def bh_six(pvals):
    if len(pvals)!=6 or any(not 0<=p<=1 for p in pvals):
        raise ValueError('full frozen six-member family required')
    order=sorted(range(6),key=lambda i:pvals[i])
    result=[None]*6
    running=1.
    for rank in range(6,0,-1):
        i=order[rank-1]
        running=min(running,pvals[i]*6/rank)
        result[i]=running
    return result


def aggregate(months):
    if set(months)!=set(MONTHS):
        raise ValueError('all seven DEV months required')
    totals=Counter()
    labels={k:Counter() for k in IDS}
    side0={k:Counter() for k in IDS}
    daily=[]
    month_table=[]
    for m in MONTHS:
        x=months[m]
        if (x['month']!=m or x['status']!='T20_T25_D1_PRIVATE_OBSERVATIONAL_MARKOUT_NO_PNL'
            or x['private'] is not True
            or any(x[z] is not False for z in ('holdouts_opened','new_history_acquired',
                                             'new_5second_signals','trades_simulated',
                                             'broker_fills_modelled'))):
            raise ValueError('unsafe or invalid monthly result')
        totals['source']+=x['source']
        totals['eligible']+=x['eligible']
        if len(x['daily'])!=x['eligible'] or set(x['labels'])!=set(IDS):
            raise AssertionError('missing eligible-day outcomes')
        daily.extend(x['daily'])
        month_table.append({'month':m,'source':x['source'],'eligible':x['eligible'],
            'cases_controls':{k:[x['labels'][k][CASE],x['labels'][k][CONTROL]] for k in IDS}})
        for k in IDS:
            labels[k].update(x['labels'][k])
            side0[k].update(x['no_direction'][k])
    if (totals['source'],totals['eligible'])!=(140,N_SESSIONS):
        raise AssertionError('140/135 baseline changed')
    if len(daily)!=N_SESSIONS:
        raise AssertionError('135 samples changed')
    for k in IDS:
        if (labels[k][CASE],labels[k][CONTROL])!=SCREEN_COUNTS[k]:
            raise AssertionError('preregistered stage0 counts altered')
        if sum(labels[k].values()) != N_SESSIONS:
            raise AssertionError('missing stage0 label')
    summary={}
    bh_p=[]
    for k in IDS:
        all_case=[d[k]['value'] for d in daily if d[k]['group']==CASE and d[k]['value'] is not None]
        all_ctrl=[d[k]['value'] for d in daily if d[k]['group']==CONTROL and d[k]['value'] is not None]
        a=sum(all_case)/len(all_case) if all_case else None
        b=sum(all_ctrl)/len(all_ctrl) if all_ctrl else None
        delta=((b-a) if k==MAG else (a-b)) if a is not None and b is not None else None
        detail={str(L):bootstrap_delta(daily,k,L) for L in BLOCKS}
        p=detail['5']['p_exploratory']
        bh_p.append(p if p is not None else 1.)
        summary[k]={'N_case':labels[k][CASE],'N_control':labels[k][CONTROL],
             'N_case_markouts':len(all_case),'N_control_markouts':len(all_ctrl),
             'N_side0_case':side0[k][CASE],'N_side0_control':side0[k][CONTROL],
             'mean_case':a,'mean_control':b,'differential_expected_sign':delta,
             'unit':'NQ_price_ticks_range' if k==MAG else 'NQ_price_ticks_signed_VWAP_markout',
             'bootstrap_by_L':detail,'BH_p_denominator':p if p is not None else 1.,
             'BH_missing_member_sentinel':p is None,'D1':'PENDING_INFERENCE'}
    q=bh_six(bh_p)
    for i,k in enumerate(IDS):
        z=summary[k]
        z['BH_q_descriptive'] = q[i] if not z['BH_missing_member_sentinel'] else None
        l=z['bootstrap_by_L']['5']
        if l['ci90'] is None:
            z['D1']='NOT_ESTIMABLE_LOW_GROUP_N'
        elif z['differential_expected_sign']<=0 or z['mean_case'] is None or (k!=MAG and z['mean_case']<=0):
            z['D1']='NOT_SUPPORTED_DESCRIPTIVE'
        elif l['ci90'][0]<=0:
            z['D1']='INCONCLUSIVE'
        else:
            z['D1']='PROMISING_PREDICTIVE_IN_SAMPLE_NOT_EXECUTABLE'
    return {'status':'T20_T25_D1_OBSERVATIONAL_ONLY_NOT_TRADING',
            'source_sessions':totals['source'],'eligible_sessions':totals['eligible'],
            'N_trades_simulated':0,'N_effective':None,'result_units':'TICKS_NOT_USD',
            'friction_threshold_diagnostic_ticks_only':7.5,
            'questions':summary,'months_coverage_counts_only':month_table,
            'hypothesis_family_size':6,'selection_valid_p_values':False,
            'holm_confirmatory':None,'historical_3_of_5_years':None,
            'broker_fills_validated':False,'router_pnl':None,'profit_factor':None,
            'drawdown':None,'funding_approved':False,'holdouts_opened':False,
            'new_market_history_acquired':False,'individual_rows_exported':False}


def report(z):
    s=['# NQ T20–T25: D1 markout observacional (NO P&L NI FILLS)','',
       '7/7 meses, 140 fuente y 135 sesiones elegibles; cinco contrastes direccionales',
       'de VWAP de barra E a VWAP del primer grupo timestamp POST+300s; T23 rango 15m.',
       'Ningún resultado representa operación ejecutada, PF, DD o alfa confirmado.','',
       '| Pregunta | N casos/controles | N markouts casos/controles | Caso media | Control media | Δ ticks (sentido prereg.) | CI90 L5 | q BH descriptiva | D1 |',
       '|---|---:|---:|---:|---:|---:|---|---:|---|']
    def fmt(x):
        return 'N/D' if x is None else f'{x:+.3f}'
    for k in IDS:
        x=z['questions'][k]
        ic=x['bootstrap_by_L']['5']['ci90']
        s.append(f"| {k} | {x['N_case']}/{x['N_control']} | {x['N_case_markouts']}/{x['N_control_markouts']} | "
                 f"{fmt(x['mean_case'])} | {fmt(x['mean_control'])} | "
                 f"{fmt(x['differential_expected_sign'])} | "
                 f"{('['+fmt(ic[0])+', '+fmt(ic[1])+']') if ic else 'N/D'} | "
                 f"{fmt(x['BH_q_descriptive'])} | {x['D1']} |")
    s+=['','BH aplica denominador de 6; para un miembro no estimable usa p=1',
        'solo como sentinela de ajuste, sin convertir su p/q inferencial N/D en evidencia.',
        'Todos p/q en DEV adaptativo son DESCRIPTIVOS, no Holm/OOS.',
        'Umbral de fricción de 7,5 ticks es ORIENTATIVO, VWAP NO negociable, NO P&L.',
        'Sin datos nuevos, sin 5s nuevas señales, con holdouts cerrados.',
        '']
    return '\n'.join(s)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--inputs',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    if args.month:
        if args.month not in MONTHS:
            raise SystemExit('SEALED_BEFORE_IO')
        x=month_stage(args.root,args.month,args.out)
        print('T20_T25_D1_SAFE_MONTH='+json.dumps(x,sort_keys=True))
    else:
        if args.inputs is None or args.report is None:
            raise ValueError('aggregate requires inputs/report')
        ms={m:json.loads((args.inputs/f'd1_{m}.json').read_text()) for m in MONTHS}
        z=aggregate(ms)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        args.report.write_text(report(z)+'\n')
        print('T20_T25_D1_SAFE_AGGREGATE='+json.dumps({
            'source':z['source_sessions'],'eligible':z['eligible_sessions'],
            'summaries':{k:{'N_case':v['N_case'],'N_control':v['N_control'],
                         'differential_ticks':v['differential_expected_sign'],
                         'CI90':v['bootstrap_by_L']['5']['ci90'],
                         'D1':v['D1']} for k,v in z['questions'].items()},
            'PnL':None,'holdouts_opened':False},sort_keys=True))
