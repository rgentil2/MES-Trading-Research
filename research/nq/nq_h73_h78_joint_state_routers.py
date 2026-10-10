#!/usr/bin/env python3
"""Six preregistered two-component NQ->MNQ router strategies H73-H78.

Price data must not be read before official GitHub family-7 freeze and local
SHA attestation of this preregistration. Strict 2020-2024 source allowlists.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
try:
 from research.nq.nq_h67_h72_combined_strategies import parents,bracket,active_regime,COST,POINT,SEED,YEARS,portfolio_equity
 from research.nq.nq_h05_h07_level_volume_screen import load_development,roll_contract
 from research.nq.nq_h53_h58 import load_context
except ImportError:
 from nq_h67_h72_combined_strategies import parents,bracket,active_regime,COST,POINT,SEED,YEARS,portfolio_equity
 from nq_h05_h07_level_volume_screen import load_development,roll_contract
 from nq_h53_h58 import load_context

FAMILY='NQ-DEDUCTIVE-ENSEMBLE-H73-H78-V1'
HIDS=[f'NQ-H{x}' for x in range(73,79)]
BOOT=10000
SOURCE_FILES=['research/nq/NQ_H73_H78_PREREG_2026_10_10.md',
'research/nq/nq_h73_h78_joint_state_routers.py',
'research/nq/test_nq_h73_h78_joint_state_routers.py',
'research/nq/nq_h05_h07_level_volume_screen.py',
'research/nq/nq_h53_h58.py',
'research/nq/nq_h67_h72_combined_strategies.py']

def check_attestation(root:Path,attest:Path):
    """Prove source bytes identical to an officially frozen GitHub manifest.

    The preflight is independently run in GitHub Actions before producing this
    attestation. Never silently accept a source-frozen CLI flag as sufficient.
    """
    if not attest.is_file():raise RuntimeError('Missing frozen GitHub family-7 SHA256 attestation')
    a=json.loads(attest.read_text())
    if a.get('family')!=FAMILY or a.get('index')!=7 or a.get('status')!='FROZEN_GITHUB_PREFLIGHT_SUCCESS':
        raise RuntimeError('Invalid frozen family-7 attestation')
    given=a.get('sha256',{})
    if set(given)!=set(SOURCE_FILES):raise RuntimeError('Incomplete or changed family definition scope')
    for relative in SOURCE_FILES:
        path=root/relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=given[relative]:
            raise RuntimeError('Frozen source SHA mismatch: '+relative)
    return a

def prior_same_contract(dates,i):
    if i<1:return False
    a,b=date.fromisoformat(dates[i]),date.fromisoformat(dates[i-1])
    return (a-b).days<=5 and roll_contract(a)==roll_contract(b)

def classifications(i,dates,days,ctx,volreg):
    """Three past-only states known strictly by end of 09:30 ET, before H09/H56.

    Missing context -> None, never treatment assignment by future outcome.
    """
    d=dates[i];c=ctx.get(d)
    v=volreg.get(d)
    p=g=None
    if c is not None and i>=20:
        preceding=[ctx.get(x) for x in dates[i-20:i]]
        if all(x is not None for x in preceding):
            med=float(np.median([x['pm_range'] for x in preceding]))
            p='EXPANDED' if c['pm_range']>med else 'CONTRACTED'
        if prior_same_contract(dates,i):
            gap=float(days[i,0,0]-days[i-1,-1,3])
            body=float(c['pm_body'])
            if gap!=0 and body!=0:
                g='ALIGNED' if (gap>0)==(body>0) else 'OPPOSED'
    return {'V':v,'P':p,'G':g}

# Frozen complementary assignment, all six variants (not selected by results).
PAIR={
 73:('V','HIGH','NQ-H09','LOW','NQ-H56'),
 74:('V','LOW','NQ-H09','HIGH','NQ-H56'),
 75:('P','CONTRACTED','NQ-H09','EXPANDED','NQ-H56'),
 76:('P','EXPANDED','NQ-H09','CONTRACTED','NQ-H56'),
 77:('G','ALIGNED','NQ-H09','OPPOSED','NQ-H56'),
 78:('G','OPPOSED','NQ-H09','ALIGNED','NQ-H56'),
}

def pick(model,regime,signals):
    """Permit ONE parent dictated by the pre-known state; never after-the-fact fallback."""
    key,s1,parent1,s2,parent2=PAIR[model]
    status=regime.get(key)
    if status==s1:return signals.get(parent1)
    if status==s2:return signals.get(parent2)
    return None

def synthetic_execution(market,day,model,source,category,atr):
    if source is None:return None
    sig=int(source['signal_idx']);side=int(source['side'])
    if sig!=14:raise RuntimeError('Parent H09/H56 shifted from 09:45')
    entry=float(market[sig+1,0]);exit30=float(market[sig+31,0])
    if abs(float(source['entry_open'])-entry)>1e-9 or abs(float(source['exit30_open'])-exit30)>1e-9:
        raise RuntimeError('Parent entry/exit parity failed '+str(day))
    pnl,exit_kind,risk,mae,endbar=bracket(market,sig,side,entry,atr)
    return {'session':day,'year':int(day[:4]),'week':str(pd.Timestamp(day).to_period('W-SUN')),
        'model_type':category,'hypothesis':model,'origin':source['hypothesis'],
        'signal_idx':sig,'side':side,'pnl_bracket':float(pnl),
        'pnl_time30':float(round(side*(exit30-entry)*POINT-COST,3)),
        'risk_points':risk,'mae_gross_usd':mae,'bracket_reason':exit_kind,'exit_bar_idx':endbar}

def score(trades):
    if not len(trades):return {'n':0,'net_usd':0,'pf':None,'closed_dd_usd':None,'mean_net_mnq_usd':None}
    x=trades.sort_values('session').copy();a=x.pnl_bracket.to_numpy(float)
    win=a[a>0].sum();lose=-a[a<0].sum()
    base=portfolio_equity(x)
    return {**base,'mean_net_mnq_usd':round(float(a.mean()),2),'pf':round(float(win/lose),3) if lose>0 else None,
       'positive_years':sum(x.groupby('year').pnl_bracket.sum()>0),
       'win_rate':round(float((a>0).mean()),3),
       'by_year':{str(y):{'n':int((x.year==y).sum()),'net_usd':round(float(x.loc[x.year==y,'pnl_bracket'].sum()),2)}for y in YEARS},
       'cost_1_5x_total_net_usd':round(float(a.sum()-0.5*COST*len(a)),2)}

def week_inference(weeks,seed,ratio_mean=True):
    """Unilateral week-signflip plus bilateral week bootstrap CI90, with fixed 10k draws."""
    rng=np.random.default_rng(seed)
    w=np.asarray(weeks,float)
    if not len(w) or not np.any(w[:,1]>0):return 1.,[None,None]
    total=float(w[:,0].sum());m=len(w);n_ge=0;z=[]
    for i in range(0,BOOT,200):
        b=min(200,BOOT-i)
        signed=rng.choice([-1.,1.],size=(b,m))
        n_ge+=int(((signed*w[:,0]).sum(axis=1)>=total).sum())
        drawn=w[rng.integers(0,m,size=(b,m))]
        z.extend((drawn[:,:,0].sum(axis=1)/drawn[:,:,1].sum(axis=1)).tolist())
    p=(n_ge+1)/(BOOT+1)
    return float(p),[round(float(q),4) for q in np.quantile(z,[.05,.95])]

def bh(p):
    ids=sorted(p,key=lambda k:(p[k],k));m=len(ids);out={};q=1.
    for rank,key in reversed(list(enumerate(ids,start=1))):q=min(q,p[key]*m/rank);out[key]=round(q,6)
    return out

def infer(models,base_daily,universe_days):
    raw={};primary_p={};diff_p={}
    for idx,h in enumerate(HIDS):
        x=models[models.hypothesis==h].copy()
        a=score(x);n=a['n'];net=a['net_usd']
        if n:
            w=x.groupby('week').pnl_bracket.agg(['sum','count']).to_numpy(float)
            p,ci=week_inference(w,SEED+idx)
            primary_p[h]=p
        else:p=1.;ci=[None,None];primary_p[h]=p
        # Daily paired comparison over the exact same research calendar, zero PnL on no-trade days.
        byday=dict(x.groupby('session').pnl_bracket.sum());delta=pd.DataFrame({'session':universe_days})
        delta['week']=pd.to_datetime(delta.session).dt.to_period('W-SUN').astype(str)
        delta['difference']=delta.session.map(lambda d:float(byday.get(d,0))-float(base_daily.get(d,0)))
        w_delta=delta.groupby('week').difference.agg(['sum','count']).to_numpy(float)
        p_inc,ci_inc=week_inference(w_delta,SEED+100+idx)
        diff_p[h]=p_inc
        raw[h]={**a,'ci90_mean_trade_usd':ci,'p_one_sided':round(p,6),
          'incremental_total_vs_h69_usd':round(float(delta.difference.sum()),2),
          'incremental_mean_daily_vs_h69_usd':round(float(delta.difference.mean()),5),
          'incremental_daily_ci90_usd':ci_inc,'incremental_p_one_sided':round(p_inc,6)}
    q=bh(primary_p);dq=bh(diff_p)
    for h,v in raw.items():
        v['bh_q6']=q[h];v['incremental_bh_q6']=dq[h]
        v['gate1']={'N_gt150':v['n']>150,'mean_positive':v.get('mean_net_mnq_usd') is not None and v['mean_net_mnq_usd']>0,
          'ci90_lower_positive':v['ci90_mean_trade_usd'][0] is not None and v['ci90_mean_trade_usd'][0]>0,
          'BH_q_at_most_010':q[h]<=.10,'years_positive_at_least3':v.get('positive_years',0)>=3}
        v['decision']='PROMISING_EXPLORATORY' if all(v['gate1'].values()) else ('INSUFFICIENT_EVIDENCE' if v['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY')
        v['economic_floor_15pct_pass']=bool((v.get('equivalent_50k_cagr_full_dev_2020_2024') or 0)>.15)
    return raw

def evaluate(dates,days,signal_df,ctx):
    if len(dates)!=1221:raise ValueError('Unexpected full-session development universe')
    byday={d:{z['hypothesis']:z for z in x.to_dict('records')} for d,x in signal_df.groupby('session')}
    # Past known RTH/PM states computed for all days, not limited by observed winners.
    regimes=active_regime(dates,days)
    trades=[];parents_all=[];ablation=[];daily_base={};states={}
    for i,d in enumerate(dates):
        if i<21:continue
        state=classifications(i,dates,days,ctx,regimes);states[d]=state
        if d not in byday:continue
        p=byday[d]
        p={k:v for k,v in p.items() if k in ('NQ-H09','NQ-H56')}
        if not p:continue
        g=days[i]
        atr=float(np.median(np.max(days[i-14:i,:,1],axis=1)-np.min(days[i-14:i,:,2],axis=1)))
        ref=p.get('NQ-H09') or p.get('NQ-H56')
        row=synthetic_execution(g,d,'NQ-H69',ref,'baseline',atr)
        if row:daily_base[d]=row['pnl_bracket'];parents_all.append(row)
        for k in (73,74,75,76,77,78):
            s=pick(k,state,p)
            if s is None:continue
            row=synthetic_execution(g,d,f'NQ-H{k}',s,'strategy',atr)
            trades.append(row)
            ablation.append({'hypothesis':f'NQ-H{k}','session':d,'selected_component':s['hypothesis'],
              'pnl':row['pnl_bracket'],'state':state[PAIR[k][0]]})
    r=pd.DataFrame(trades);c=pd.DataFrame(parents_all);ab=pd.DataFrame(ablation)
    if r.empty:raise RuntimeError('No joint strategies fired')
    if r.duplicated(['hypothesis','session']).any():raise RuntimeError('Duplicate portfolio position on a day')
    # exact H69 baseline over all allowed t>=21, no state-filter selection
    base=score(c)
    if abs(base['net_usd']-2704.44)>0.02 or base['n']!=262:
        raise RuntimeError(f'H69 baseline parity failed: {base}; abort analysis')
    metrics=infer(r,daily_base,dates[21:])
    ablation={}
    for h in HIDS:
        x=ab[ab.hypothesis==h]
        ablation[h]={
          'selected_parent_counts':x.selected_component.value_counts().to_dict(),
          'leave_out_H09_net_usd':round(float(x.loc[x.selected_component=='NQ-H56','pnl'].sum()),2),
          'leave_out_H56_net_usd':round(float(x.loc[x.selected_component=='NQ-H09','pnl'].sum()),2),
          'full_net_usd':round(float(x.pnl.sum()),2),
          'compared_to_h69_same_session_total_usd':round(float(x.pnl.sum()-base['net_usd']),2)}
    status_hist={str(k):{s:sum(z.get(k)==s for z in states.values()) for s in sorted({z.get(k) for z in states.values() if z.get(k)})} for k in ('V','P','G')}
    return r,c,metrics,ablation,base,status_hist

def main():
    p=argparse.ArgumentParser()
    for name in ('zip','h08','h53','repo-root','attestation','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args()
    root=Path(a.repo_root)
    check_attestation(root,Path(a.attestation)) # MUST run before reading any market or parent data
    pr=parents(a.h08,a.h53)
    pr=pr[pr.hypothesis.isin(('NQ-H09','NQ-H56'))].copy()
    dates,days,overnight,qc=load_development(Path(a.zip))
    ctx=load_context(Path(a.zip))
    r,c,stats,ab,base,hist=evaluate(dates,days,pr,ctx)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    r.to_csv(out/'NQ_H73_H78_COMBINED_STRATEGY_TRADES_PRIVATE.csv',index=False)
    c.to_csv(out/'NQ_H69_FROZEN_BASELINE_TRADES_PRIVATE.csv',index=False)
    report={'stage':'DEVELOPMENT_EXPLORATORY','family':FAMILY,'loaded_years':YEARS,
    'holdout_2025_loaded':False,'holdout_2026_loaded':False,
    'hypotheses':stats,'baseline_H69':base,'ablations':ab,'contexts':hist,
    'num_sessions_complete_RTH':len(dates),'num_parent_events':len(pr),
    'execution_proxy':'1 MNQ at NQ-minute OHLC price, no MNQ quotes, stop-first 1m intrabar',
    'fee_and_slippage_rt_mnq':COST,'floating_trailing_funding_risk_validated':False,
    'exact_VOO_QQQM_total_return_loaded':False,'real_funded_ROI_validated':False,
    'research_quality':'Adaptive testing repeated 2020-2024, all apparent results exploratory only'}
    (out/'NQ_H73_H78_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    fam={'stage':'DEVELOPMENT_EXPLORATORY','loaded_years':YEARS,
      'holdout_2025_loaded':False,'holdout_2026_loaded':False,
      'family_metrics':{h:{'status':'ESTIMATED' if v['n'] else 'NOT_ESTIMABLE',
       'effect':v['mean_net_mnq_usd'] or 0,
       'p_value_two_sided':min(1.,2*min(v['p_one_sided'],1.-v['p_one_sided']))} for h,v in stats.items()}}
    (out/'nq_h73_h78_family.json').write_text(json.dumps(fam,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'H69':base,'strategies':{h:{k:v[k] for k in ['n','net_usd','pf','closed_dd_usd','ci90_mean_trade_usd','bh_q6','decision','incremental_total_vs_h69_usd','incremental_bh_q6']}for h,v in stats.items()}},indent=2))

if __name__=='__main__':main()