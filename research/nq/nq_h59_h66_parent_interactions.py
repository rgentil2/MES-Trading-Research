#!/usr/bin/env python3
"""Deductive, POST-SELECTION NQ H59-H66 parent-interactions: development CSVs only.

Requirements: official frozen family H59-H66. No market ZIP member is read.
An overlapping parent never becomes an independent economic position.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

IDS=[f'NQ-H{i}' for i in range(59,67)]
PARENTS=['NQ-H09','NQ-H29','NQ-H54','NQ-H55','NQ-H56']
FRICTION_NQ=25.74
FRICTION_MNQ=3.88
BOOT=10000
SEED=20261010
ORDER=['NQ-H09','NQ-H56','NQ-H55','NQ-H29']
SLOTS={'NQ-H09':14,'NQ-H29':29,'NQ-H55':14,'NQ-H56':14}

def assert_frozen(root:Path):
    root=root.resolve()
    if not (root/'research/SEARCH_FAMILY_FREEZES.json').is_file():
        raise RuntimeError('Official family freeze absent; refuses to read development outcomes')
    sys.path.insert(0,str(root))
    from tools.research_governance import preflight_family
    preflight_family(root,'NQ-PARENT-INTERACTIONS-H59-H66-V1')

def parent_df(path,kind):
    if kind not in ('h08','h53'):raise ValueError('Unknown parent family')
    df=pd.read_csv(path)
    if kind=='h08':
        if not {'day','hypothesis','side','signal_et','pnl30','entry_open','exit30_open'}.issubset(df.columns):
            raise ValueError('H08 parent file columns missing')
        df=df[df.hypothesis.isin(['NQ-H09','NQ-H29'])].copy()
        df['session']=df.day
        df['signal_idx']=df.signal_et.map({'09:45':14,'10:00':29})
        df['side']=df.side.map({'LONG':1,'SHORT':-1})
    else:
        if not {'session','hypothesis','side','signal_idx','pnl30','entry_open','exit30_open'}.issubset(df.columns):
            raise ValueError('H53 parent file columns missing')
        df=df[df.hypothesis.isin(['NQ-H54','NQ-H55','NQ-H56'])].copy()
    if df.empty:raise ValueError('No parent signals')
    if df[['side','signal_idx']].isna().any().any():raise ValueError('Unrecognized direction or timestamp')
    df['year']=pd.to_datetime(df.session,format='%Y-%m-%d',errors='raise').dt.year
    if not set(df.year.unique()).issubset(set(range(2020,2025))):raise ValueError('Development-only firewall: 2025/2026 data prohibited')
    if not set(df.side.unique()).issubset({1,-1}):raise ValueError('Invalid side')
    for k,n in SLOTS.items():
        v=df[df.hypothesis==k]
        if len(v) and (v.signal_idx!=n).any():raise ValueError('Parent signal time changed: '+k)
    v=df[df.hypothesis=='NQ-H54']
    if len(v) and (~v.signal_idx.between(16,74)).any():raise ValueError('Parent H54 time invalid')
    if df.duplicated(['session','hypothesis']).any():raise ValueError('Duplicated day/hypothesis')
    implied=df.side*(df.exit30_open-df.entry_open)*20-FRICTION_NQ
    if not bool(np.allclose(implied,df.pnl30,atol=.015)):
        raise ValueError('Original NQ event net economics changed')
    fields=['session','year','hypothesis','side','signal_idx','entry_open','exit30_open','pnl30']
    return df[fields].copy()

def pull(rows, output_id, parent):
    d=dict(parent)
    d['hypothesis']=output_id
    d['origin_hypothesis']=parent['hypothesis']
    d['pnl_mnq']=round((float(parent['pnl30'])+FRICTION_NQ)/10-FRICTION_MNQ,3)
    rows.append(d)

def create_children(parent_records):
    """Use only day/signal/side known at child signal; never outcome to select child."""
    out=[]
    by_day={d:{r['hypothesis']:r for r in g.to_dict('records')}
            for d,g in parent_records.groupby('session',sort=True)}
    for day, p in by_day.items():
        h09=p.get('NQ-H09');h29=p.get('NQ-H29');h54=p.get('NQ-H54')
        h55=p.get('NQ-H55');h56=p.get('NQ-H56')
        if h55 and h56 and h55['side']==h56['side']:pull(out,'NQ-H59',h55)
        if h55 and not h56:pull(out,'NQ-H60',h55)
        if h56 and not h55:pull(out,'NQ-H61',h56)
        if h09 and not h55 and not h56:pull(out,'NQ-H62',h09)
        if h09 and h56 and h09['side']==h56['side']:pull(out,'NQ-H63',h09)
        if h29 and not h55 and not h56:pull(out,'NQ-H64',h29)
        if h54 and h55 and h54['side']==h55['side']:pull(out,'NQ-H65',h54)
        if h54 and h55 and h54['side']!=h55['side']:pull(out,'NQ-H66',h54)
    columns=['session','year','hypothesis','side','signal_idx','entry_open','exit30_open','pnl30','origin_hypothesis','pnl_mnq']
    return pd.DataFrame(out,columns=columns).sort_values(['session','hypothesis']).reset_index(drop=True)

def portfolio(parent_records):
    """One fill max per session; earliest signal, fixed 09:45 tie order."""
    raw=[]
    for day,g in parent_records[parent_records.hypothesis.isin(ORDER)].groupby('session'):
        g=g.copy()
        g['priority']=g.hypothesis.map({x:i for i,x in enumerate(ORDER)})
        g=g.sort_values(['signal_idx','priority'])
        r=dict(g.iloc[0]);r['pnl_mnq']=round((float(r['pnl30'])+FRICTION_NQ)/10-FRICTION_MNQ,3)
        r['collision_count']=len(g);raw.append(r)
    return pd.DataFrame(raw).sort_values(['session']).reset_index(drop=True)

def adjust_bh(ps):
    names=sorted(ps,key=lambda k:(ps[k],k));m=len(names);out={};q=1.
    for rank,k in reversed(list(enumerate(names,1))):
        q=min(q,m*ps[k]/rank);out[k]=q
    return out

def adjust_holm(ps):
    names=sorted(ps,key=lambda k:(ps[k],k));m=len(names);out={};prev=0.
    for i,k in enumerate(names):
        prev=max(prev,(m-i)*ps[k]);out[k]=min(1.,prev)
    return out

def stats(events):
    rng=np.random.default_rng(SEED);out={};pvalues={}
    for h in IDS:
        x=events[events.hypothesis==h];n=len(x)
        if n==0:
            out[h]={'n':0,'status':'NOT_ESTIMABLE','p_one_sided':1.,'ci90':None,'positive_years':0};pvalues[h]=1.;continue
        pnl=x.pnl30.to_numpy(float);weeks=x.assign(week=pd.to_datetime(x.session).dt.to_period('W-SUN').astype(str)).groupby('week',sort=True).pnl30.agg(['sum','count']).to_numpy(float)
        total=pnl.sum();ge=0;boots=[]
        for start in range(0,BOOT,250):
            batch=min(250,BOOT-start)
            flip=rng.choice([-1.,1.],size=(batch,len(weeks)))
            ge+=int((flip@weeks[:,0]>=total).sum())
            indices=rng.integers(0,len(weeks),size=(batch,len(weeks)))
            z=weeks[indices];boots.append(z[:,:,0].sum(axis=1)/z[:,:,1].sum(axis=1))
        pval=(ge+1)/(BOOT+1);pvalues[h]=pval
        b=np.concatenate(boots)
        year={str(y):{'n':int((x.year==y).sum()),'total_net_usd':round(float(x.loc[x.year==y,'pnl30'].sum()),2),'avg_net_usd':round(float(x.loc[x.year==y,'pnl30'].mean()),2) if (x.year==y).any() else None} for y in range(2020,2025)}
        posyrs=sum(a['avg_net_usd'] is not None and a['avg_net_usd']>0 for a in year.values())
        pos=pnl[pnl>0].sum();neg=-pnl[pnl<0].sum()
        ds=pd.to_datetime(x.session.unique()).sort_values();gaps=ds.to_series().diff().dt.days.dropna()
        out[h]={'n':int(n),'status':'ESTIMATED','avg_net_nq':round(float(pnl.mean()),2),'total_net_nq':round(float(total),2),'avg_net_mnq':round(float(x.pnl_mnq.mean()),2),'pf_nq':round(float(pos/neg),3) if neg>0 else None,'ci90':[round(float(z),2) for z in np.quantile(b,[.05,.95])],'ci95':[round(float(z),2) for z in np.quantile(b,[.025,.975])],'p_one_sided':float(pval),'positive_years':posyrs,'by_year':year,'max_gap_days':int(gaps.max()) if len(gaps) else None,'gap_gt7_days':int((gaps>7).sum()),'stress_plus_tick_each_side_avg_net_nq':round(float(pnl.mean())-10.,2)}
    q=adjust_bh(pvalues);holm=adjust_holm({k:min(1.,2*min(v,1-v)) for k,v in pvalues.items()})
    for h,v in out.items():
        gate={'N_gt150':v['n']>150,'net_mean_positive':v.get('avg_net_nq',0)>0,'CI90_positive':bool(v['ci90'] and v['ci90'][0]>0),'q_le_010':q[h]<=.10,'years_3_of_5':v['positive_years']>=3}
        v['bh_q_8']=round(float(q[h]),6);v['holm_p_8_approx']=round(float(holm[h]),6);v['gate1']=gate
        v['decision']='PROMISING_EXPLORATORY' if all(gate.values()) else ('INSUFFICIENT_EVIDENCE' if v['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY')
    return out

def portfolio_stats(trades):
    if trades.empty:return {}
    result={}
    for col in ('pnl30','pnl_mnq'):
        eq=trades[col].to_numpy(float).cumsum();peak=np.maximum.accumulate(np.r_[0.,eq]);dd=np.r_[0.,eq]-peak
        result[col]={'n':int(len(trades)),'mean':round(float(trades[col].mean()),2),'sum':round(float(eq[-1]),2),'max_closed_drawdown':round(float(-dd.min()),2),'positive_years':int(sum(trades.groupby('year')[col].sum()>0))}
    ds=pd.to_datetime(trades.session);gap=ds.diff().dt.days.dropna()
    result['sessions_with_collision']=int((trades.collision_count>1).sum());result['max_gap_days']=int(gap.max()) if len(gap) else None
    result['gaps_gt7_days']=int((gap>7).sum());result['by_year']=trades.groupby('year').agg(n=('year','size'),pnl_mnq=('pnl_mnq','sum')).round(2).to_dict('index')
    result['signal_source_counts']=trades.hypothesis.value_counts().to_dict();result['status']='DIAGNOSTIC_NO_STOP_LOSS_NOT_FUNDED_VALIDATION'
    return result

def main(args):
    if not args.source_frozen:raise RuntimeError('Refusing to inspect parent outcomes before source freezes')
    assert_frozen(Path(args.repo_root))
    parents=pd.concat([parent_df(args.h08,'h08'),parent_df(args.h53,'h53')],ignore_index=True)
    if set(parents.hypothesis.unique())!=set(PARENTS):raise ValueError('All five parent hypotheses needed')
    if parents.duplicated(['session','hypothesis']).any():raise ValueError('Parent duplication')
    children=create_children(parents);port=portfolio(parents)
    scores=stats(children);portfolio_report=portfolio_stats(port)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    children.to_csv(out/'NQ_H59_H66_EVENTS_2020_2024.csv',index=False)
    port.to_csv(out/'NQ_PARENT_PORTFOLIO_ONE_MNQ_DAY.csv',index=False)
    report={'stage':'DEVELOPMENT_EXPLORATORY','experiment':'NQ-H59-H66','loaded_years':list(range(2020,2025)),'holdout_2025_loaded':False,'holdout_2026_loaded':False,'basis':'previously viewed parent events; retrospective derived mechanisms, no independent inference','n_parent_events':len(parents),'n_children_events':len(children),'hypotheses':scores,'portfolio_one_mnq_time_exit':portfolio_report,'disclosure':'No stops or intra-bar adverse excursion model; 2025 and 2026 unopened; all estimates biased by reuse of DEV and parent selection.'}
    (out/'NQ_H59_H66_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    family={'stage':'DEVELOPMENT_EXPLORATORY','loaded_years':list(range(2020,2025)),'holdout_2025_loaded':False,'holdout_2026_loaded':False,'family_metrics':{h:{'status':v['status'],'effect':v.get('avg_net_nq',0),'p_value_two_sided':min(1.,2*min(v['p_one_sided'],1-v['p_one_sided']))} for h,v in scores.items()}}
    (out/'nq_h59_h66_family.json').write_text(json.dumps(family,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'n_signals':len(children),'counts':{k:v['n'] for k,v in scores.items()},'gate_pass':[k for k,v in scores.items() if v['decision']=='PROMISING_EXPLORATORY'],'portfolio':portfolio_report},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--h08',required=True);ap.add_argument('--h53',required=True)
    ap.add_argument('--out',required=True);ap.add_argument('--repo-root',required=True)
    ap.add_argument('--source-frozen',action='store_true');main(ap.parse_args())