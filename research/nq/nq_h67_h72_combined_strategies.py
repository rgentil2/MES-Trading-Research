#!/usr/bin/env python3
"""H67-H72: six prespecified combined MNQ proxy strategies; DEV 2020-24 only.

All six: 1 position/day with explicit router; 2025/26 never read. No market outcomes
can load until the official family-6 freeze preflight has passed.
"""
from __future__ import annotations
import argparse,json,math,sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.name=='nq' else Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
try:
 from research.nq.nq_h05_h07_level_volume_screen import load_development,roll_contract
except ModuleNotFoundError:
 from nq_h05_h07_level_volume_screen import load_development,roll_contract

FAMILY='NQ-DEDUCTIVE-ENSEMBLE-H67-H72-V1'
HIDS=[f'NQ-H{i}' for i in range(67,73)]
PIDS=['NQ-H09','NQ-H29','NQ-H54','NQ-H55','NQ-H56']
POINT=2.; COMMISSION=1.88;SLIPPAGE=2.; COST=3.88
TICK=.25;BOOT=10000;SEED=20261010
YEARS=[2020,2021,2022,2023,2024]

def assert_frozen(root:Path):
 root=root.resolve()
 if not (root/'research/SEARCH_FAMILY_FREEZES.json').is_file():
  raise RuntimeError('Family must be frozen before inspecting parent or market outcome data')
 sys.path.insert(0,str(root))
 from tools.research_governance import preflight_family
 preflight_family(root,FAMILY)

def parents(h08,h53):
 a=pd.read_csv(h08);b=pd.read_csv(h53)
 needa={'day','hypothesis','side','signal_et','entry_open','exit30_open','pnl30'}
 needb={'session','hypothesis','side','signal_idx','entry_open','exit30_open','pnl30'}
 if not needa.issubset(a.columns) or not needb.issubset(b.columns):raise ValueError('Parent schema mismatch')
 a=a[a.hypothesis.isin(('NQ-H09','NQ-H29'))].copy();b=b[b.hypothesis.isin(('NQ-H54','NQ-H55','NQ-H56'))].copy()
 a['session']=a.day;a['signal_idx']=a.signal_et.map({'09:45':14,'10:00':29});a['side']=a.side.map({'LONG':1,'SHORT':-1})
 c=pd.concat([a,b],ignore_index=True);c['year']=pd.to_datetime(c.session,format='%Y-%m-%d').dt.year
 if set(c.hypothesis)!=set(PIDS) or not set(c.year).issubset(set(YEARS)):raise ValueError('Unexpected year or parent missing')
 if c.duplicated(['session','hypothesis']).any():raise ValueError('Duplicate session/parent signal')
 if c[['side','signal_idx']].isna().any().any() or not set(c.side)=={-1,1}:raise ValueError('Invalid signal side/time')
 for h,idx in [('NQ-H09',14),('NQ-H29',29),('NQ-H55',14),('NQ-H56',14)]:
  if bool((c.loc[c.hypothesis==h,'signal_idx']!=idx).any()):raise ValueError(h+' time unexpectedly changed')
 if bool((~c.loc[c.hypothesis=='NQ-H54','signal_idx'].between(16,74)).any()):raise ValueError('H54 signal cannot be before 09:45')
 if not np.allclose(c.side*(c.exit30_open-c.entry_open)*20-25.74,c.pnl30,atol=.02):
  raise ValueError('Parent prices/returns no longer match original Free NQ cost')
 return c[['session','year','hypothesis','signal_idx','side','entry_open','exit30_open']].sort_values(['session','signal_idx','hypothesis']).reset_index(drop=True)

def active_regime(dates,days):
 """Only previous completed RTH range compared to 20 sessions before that previous RTH."""
 out={}
 for t in range(21,len(dates)):
  d=dates[t];prev=dates[t-1]
  valid=(date.fromisoformat(d)-date.fromisoformat(prev)).days<=5 and roll_contract(date.fromisoformat(d))==roll_contract(date.fromisoformat(prev))
  if not valid:continue
  prior=float(days[t-1,:,1].max()-days[t-1,:,2].min())
  earlier=np.max(days[t-21:t-1,:,1],axis=1)-np.min(days[t-21:t-1,:,2],axis=1)
  out[d]='HIGH' if prior>float(np.median(earlier)) else 'LOW'
 return out

def ordered_records(day_rows):
 p={x['hypothesis']:x for x in day_rows}
 consensus=None
 if 'NQ-H55' in p and 'NQ-H56' in p and p['NQ-H55']['side']==p['NQ-H56']['side']:
  consensus=dict(p['NQ-H55']);consensus['hypothesis']='CONSENSUS55_56'
 return p,consensus

def select(h,p,consensus,regime=None):
 """Return signal record or None; all choices depend on signal clocks and prior regime only."""
 h09=p.get('NQ-H09');h55=p.get('NQ-H55');h56=p.get('NQ-H56');h29=p.get('NQ-H29');h54=p.get('NQ-H54')
 early=h09 or consensus
 if h==67:return early
 if h==68:return h09 or h55
 if h==69:return h09 or h56
 if h==70:return early or h29
 if h==71:return early or h54
 if h==72:
  if regime=='HIGH':return h09 or h54
  if regime=='LOW':return consensus or h29
  return None
 raise ValueError('Unknown H67-H72 model')

def bracket(g,i,side,entry,atr):
 risk=max(TICK,math.ceil(.15*atr/TICK-1e-9)*TICK)
 target_ticks=math.ceil(1.5*risk/TICK-1e-9)
 target=entry+side*target_ticks*TICK
 stop=entry-side*risk
 worst_adverse=0.
 for j in range(i+1,i+31):
  o,hi,lo,cl,v=g[j]
  adv=(entry-lo) if side==1 else (hi-entry)
  worst_adverse=max(worst_adverse,max(0.,float(adv)))
  stop_hit=lo<=stop if side==1 else hi>=stop
  tgt_hit=hi>=target if side==1 else lo<=target
  if stop_hit:
   px=min(o,stop) if side==1 else max(o,stop)
   return round(side*(px-entry)*POINT-COST,3),'STOP',round(risk,3),round(worst_adverse*POINT,3),j
  if tgt_hit:return round(side*(target-entry)*POINT-COST,3),'TARGET',round(risk,3),round(worst_adverse*POINT,3),j
 return round(side*(g[i+31,0]-entry)*POINT-COST,3),'TIME',round(risk,3),round(worst_adverse*POINT,3),i+31

def portfolio_equity(trades):
 """Closed-only risk: floating equity path still unverified at 1m resolution."""
 if len(trades)==0:return {'n':0,'net_usd':0,'closed_dd_usd':None,'equivalent_50k_cagr':None}
 x=trades.sort_values(['session','signal_idx']).copy();p=x.pnl_bracket.to_numpy(float)
 eq=np.r_[0,np.cumsum(p)]; dd=np.maximum.accumulate(eq)-eq
 initial=50000.;last=initial+eq[-1]
 days=(pd.Timestamp('2024-12-31')-pd.Timestamp('2020-01-01')).days
 cagr=(last/initial)**(365.2425/days)-1 if last>0 else None
 d=pd.to_datetime(x.session);gaps=d.diff().dt.days.dropna()
 return {'n':int(len(x)),'net_usd':round(float(p.sum()),2),'closed_dd_usd':round(float(dd.max()),2),
 'max_single_trade_mae_proxy_usd':round(float(x.mae_gross_usd.max()),2),
 'gaps_gt7':int((gaps>7).sum()),'max_gap_days':int(gaps.max()) if len(gaps) else 0,
 'equivalent_50k_cagr_full_dev_2020_2024':round(float(cagr),6) if cagr is not None else None,
 'same_window_benchmarks_available':False,'economic_gate':'ECONOMIC_DATA_PENDING',
 'intratrade_trailing_rule_audit':'NOT_VALIDATED_MINUTE_OHLC_INSUFFICIENT',
 'strategy_authorized':False}

def summary(events,models):
 rng=np.random.default_rng(SEED);res={};ps={}
 for h in HIDS:
  g=events[events.hypothesis==h].copy();n=len(g)
  if n==0:
   res[h]={'n':0,'status':'NOT_ESTIMABLE','p_one_sided':1.,'ci90':None,'positive_years':0};ps[h]=1.;continue
  pnl=g.pnl_bracket.to_numpy(float);total=float(pnl.sum());mean=float(pnl.mean())
  weeks=g.groupby('week').pnl_bracket.agg(['sum','count']).to_numpy(float)
  n_weeks=len(weeks);null_ge=0;boot=[]
  for off in range(0,BOOT,200):
   k=min(200,BOOT-off)
   flips=rng.choice([-1.,1.],size=(k,n_weeks));null_ge+=int(((flips*weeks[:,0]).sum(axis=1)>=total).sum())
   samp=weeks[rng.integers(0,n_weeks,size=(k,n_weeks))]
   boot.append(samp[:,:,0].sum(axis=1)/samp[:,:,1].sum(axis=1))
  p=(1+null_ge)/(BOOT+1);ps[h]=p
  ci=np.quantile(np.concatenate(boot),[.05,.95]);pos=pnl[pnl>0].sum();neg=-pnl[pnl<0].sum()
  years={str(y):{'n':int((g.year==y).sum()),'net_usd':round(float(g.loc[g.year==y,'pnl_bracket'].sum()),2),
  'mean_usd':round(float(g.loc[g.year==y,'pnl_bracket'].mean()),2) if (g.year==y).any() else None}for y in YEARS}
  py=sum(v['mean_usd'] is not None and v['mean_usd']>0 for v in years.values())
  r=portfolio_equity(g)
  res[h]={**r,'status':'ESTIMATED','mean_net_mnq_usd':round(mean,2),'pf':round(float(pos/neg),3) if neg>0 else None,
  'win_rate':round(float((pnl>0).mean()),4),'ci90':list(map(lambda z:round(float(z),2),ci)),
  'p_one_sided':round(float(p),6),'positive_years':py,'by_year':years,'source_counts':g.origin.value_counts().to_dict(),
  'secondary_30m_avg_net_mnq_usd':round(float(g.pnl_time30.mean()),2),
  'stress_1_5x_costs_net_usd':round(float(total-0.5*COST*n),2),
  'units':'one MNQ price proxy calculated from underlying NQ 1m OHLC',
  'risk_note':'Closed DD is NOT floating trailing DD; slippage and MNQ price parity are modeled only'}
 ordered=sorted(ps,key=lambda k:(ps[k],k));adj={};q=1.;m=len(ps)
 for rank,k in reversed(list(enumerate(ordered,1))):q=min(q,m*ps[k]/rank);adj[k]=q
 for h,r in res.items():
  r['bh_q6']=round(float(adj[h]),6)
  if not r['n']:
   r['decision']='INSUFFICIENT_EVIDENCE';continue
  gate={'N_gt150':r['n']>150,'net_mean_positive':r['mean_net_mnq_usd']>0,
        'ci90_lower_above_zero':r['ci90'][0]>0,'bh_q_le_010':adj[h]<=.10,'positive_years_3_of_5':r['positive_years']>=3}
  r['gate1_exploratory_screen']=gate
  r['decision']='PROMISING_EXPLORATORY' if all(gate.values()) else ('INSUFFICIENT_EVIDENCE' if r['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY')
 return res

def evaluate(dates,days,p,regimes):
 lookup={d:i for i,d in enumerate(dates)}
 all_records=[];parents_ref=[];collisions=[]
 by_day={d:ordered_records(g.to_dict('records')) for d,g in p.groupby('session')}
 for d,(signals,consensus) in by_day.items():
  if d not in lookup:raise ValueError('Parent event session missing in eligible NQ RTH market sessions')
  idx=lookup[d];g=days[idx];atr=float(np.median(np.max(days[idx-14:idx,:,1],axis=1)-np.min(days[idx-14:idx,:,2],axis=1)))
  early=sum(int(n in signals) for n in ['NQ-H09','NQ-H55','NQ-H56'])
  if early>=2:collisions.append({'session':d,'early_parent_count':early,'early_side_conflict':len({signals[n]['side'] for n in ['NQ-H09','NQ-H55','NQ-H56'] if n in signals})>1})
  strategies={f'NQ-H{k}':select(k,signals,consensus,regimes.get(d)) for k in range(67,73)}
  comparators={k:signals.get(k) for k in PIDS};comparators['CONSENSUS55_56']=consensus
  for category,by in [('strategy',strategies),('parent',comparators)]:
   for h,s in by.items():
    if s is None:continue
    sig=int(s['signal_idx']);side=int(s['side']);entry=float(g[sig+1,0]);exit=float(g[sig+31,0]);
    # Compare inherited source with actual development bar; frozen proxy has not been repriced.
    if abs(float(s['entry_open'])-entry)>1e-9 or abs(float(s['exit30_open'])-exit)>1e-9:raise ValueError(f'Parent timing/price parity failed {h} {d}')
    pnl,status,risk,mae,end_idx=bracket(g,sig,side,entry,atr)
    all_records.append({'session':d,'year':int(d[:4]),'week':str(pd.Timestamp(d).to_period('W-SUN')),
     'model_type':category,'hypothesis':h,'origin':s['hypothesis'],'signal_idx':sig,'side':side,
     'regime':regimes.get(d,'UNAVAILABLE'),'entry_open_nq':entry,'risk_points':risk,'bracket_reason':status,
     'exit_bar_idx':end_idx,'pnl_bracket':pnl,'pnl_time30':round(side*(exit-entry)*POINT-COST,3),
     'mae_gross_usd':mae})
 all_df=pd.DataFrame(all_records)
 strategies=all_df[all_df.model_type=='strategy'].copy();parent=all_df[all_df.model_type=='parent'].copy()
 if strategies.duplicated(['session','hypothesis']).any():raise ValueError('Duplicate same-day strategy fills')
 return strategies,parent,pd.DataFrame(collisions)

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--zip',required=True);pa.add_argument('--h08',required=True);pa.add_argument('--h53',required=True);
 pa.add_argument('--repo-root',required=True);pa.add_argument('--out',required=True);pa.add_argument('--source-frozen',action='store_true')
 a=pa.parse_args()
 if not a.source_frozen:raise RuntimeError('Refuse market data before source freeze')
 assert_frozen(Path(a.repo_root))
 p=parents(a.h08,a.h53) # nothing read until official preflight
 dates,days,_,qc=load_development(Path(a.zip))
 if len(dates)!=1221:raise ValueError('Unexpected 2020–24 session count')
 regimes=active_regime(dates,days)
 evt,cmp,conflicts=evaluate(dates,days,p,regimes)
 stats=summary(evt,HIDS)
 comparisons={k:portfolio_equity(v) for k,v in cmp.groupby('hypothesis')}
 if len(evt)==0:raise RuntimeError('No joint strategies fired')
 report={'stage':'DEVELOPMENT_EXPLORATORY','family':FAMILY,'hypotheses':stats,
 'comparators':comparisons,'risk_proxy':'NQ minute bars used to simulate MNQ, no direct MNQ parity or float equity audit',
 'n_market_sessions':len(dates),'n_prior_parent_event_rows':len(p),'n_joint_strategy_trades_across_six_variants':len(evt),
 'week_dates_loaded_years':YEARS,'loaded_years':YEARS,'holdout_2025_loaded':False,'holdout_2026_loaded':False,
 'costs':{'MNQ_fee_rt':COMMISSION,'MNQ_slippage_rt':SLIPPAGE,'MNQ_total_rt':COST},
 'source_qc':qc,'regimes_available_sessions':len(regimes),'early_overlaps':{'sessions':len(conflicts),'opposing_side_sessions':int(conflicts.early_side_conflict.sum()) if len(conflicts) else 0},
 'economic_gate':'ECONOMIC_DATA_PENDING', 'estimated_50k_funding_rule_verified':False,
 'bias_notice':'All variants derived from observations in repeatedly reviewed 2020-24. Post-selection inference exploratory only.'}
 family={'stage':'DEVELOPMENT_EXPLORATORY','loaded_years':YEARS,'holdout_2025_loaded':False,'holdout_2026_loaded':False,
 'family_metrics':{h:{'status':('ESTIMATED' if v['n'] else 'NOT_ESTIMABLE'),
  'effect':v.get('mean_net_mnq_usd',0),'p_value_two_sided':min(1.,2*min(v['p_one_sided'],1-v['p_one_sided']))} for h,v in stats.items()}}
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 evt.to_csv(out/'NQ_H67_H72_JOINT_STRATEGY_TRADES_DEV.csv',index=False)
 cmp.to_csv(out/'NQ_H67_H72_PARENT_COMPARATORS_DEV.csv',index=False)
 conflicts.to_csv(out/'NQ_H67_H72_EARLY_OVERLAPS.csv',index=False)
 (out/'NQ_H67_H72_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 (out/'nq_h67_h72_family.json').write_text(json.dumps(family,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'family':FAMILY,'hypotheses':{k:{'n':v['n'],'mean':v.get('mean_net_mnq_usd'),'net':v.get('net_usd'),'pf':v.get('pf'),'dd':v.get('closed_dd_usd'),'q':v.get('bh_q6'),'gate':v['decision']} for k,v in stats.items()},
 'all_gates_passed':[k for k,v in stats.items() if v['decision']=='PROMISING_EXPLORATORY']},indent=2))
if __name__=='__main__':main()