#!/usr/bin/env python3
"""FIRST fixed-rule NQ mechanism screen 2020-2024 ONLY (H01/H02/H03), no holdout."""
from pathlib import Path
from datetime import date,timedelta
import zipfile,re,json,math
import numpy as np
import pandas as pd
import argparse
cli=argparse.ArgumentParser(description='NQ H01/H02/H03 fixed-rule 2020-24 diagnostic; 2025/26 sealed')
cli.add_argument('--zip',required=True,type=Path);cli.add_argument('--out',type=Path,default=Path('results/nq_first_diagnostic'))
args=cli.parse_args();P=args.zip;O=args.out;O.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parents[2]
FREE_FEES=json.loads((ROOT/'research/costs/NINJATRADER_FREE_ALL_IN_124_SYMBOLS_2026_10_09.json').read_text(encoding='utf-8'))['rates']
FREE_FEE_NQ_RT=float(FREE_FEES['NQ']['all_in_free_round_trip_usd'])
assert FREE_FEE_NQ_RT==5.74
PAT=re.compile(r'^NQ_(03|06|09|12)-(\d\d)_20(20|21|22|23|24)_Minute_Last[.]txt$')

def roll_contract(d):
 for m in (3,6,9,12):
  first=date(d.year,m,1); thirdFri=first+timedelta(days=(4-first.weekday())%7+14)
  if d<thirdFri-timedelta(days=8):return f'NQ_{m:02d}-{d.year%100:02d}'
 return f'NQ_03-{(d.year+1)%100:02d}'

batches=[]
with zipfile.ZipFile(P) as z:
 names=[n for n in z.namelist() if '/development_2020_2024/' in n and n.split('/')[-1].startswith('NQ_') and n.endswith('.txt')]
 assert len(names)==25,len(names)
 for i,n in enumerate(sorted(names)):
  m=PAT.match(n.split('/')[-1]);assert m,(n,m)
  cm,cy,bar_y=m.groups(); contract=f'NQ_{cm}-{cy}'
  with z.open(n) as stream: df=pd.read_csv(stream,sep=';',header=None,names=['time','open','high','low','close','volume'],dtype={'time':'str'})
  ts=pd.to_datetime(df.time,format='%Y%m%d %H%M%S',utc=True).dt.tz_convert('America/New_York')
  mi=ts.dt.hour*60+ts.dt.minute
  idx=(mi>=571)&(mi<=960)&(ts.dt.dayofweek<5)
  x=df.loc[idx].copy()
  x['session']=ts.loc[idx].dt.strftime('%Y-%m-%d').values
  x['minute']=mi[idx].to_numpy()
  dates=[day for day in x.session.unique() if roll_contract(date.fromisoformat(day))==contract]
  x=x[x.session.isin(dates)]
  if len(x):batches.append(x[['session','minute','open','high','low','close','volume']])
  if i%10==9:print('NQ read',i+1,'/25',flush=True)
rth=pd.concat(batches,ignore_index=True).sort_values(['session','minute'])
grp=rth.groupby('session',sort=True)
meta=grp.agg(n=('minute','size'),unique=('minute','nunique'),first=('minute','min'),last=('minute','max'))
valid=meta.index[(meta.n==390)&(meta.unique==390)&(meta['first']==571)&(meta['last']==960)].tolist()
rth=rth[rth.session.isin(valid)]
assert len(valid)==1221,(len(valid),len(rth))
arrs=[]
for _,g in rth.groupby('session',sort=True):
 a=g[['open','high','low','close','volume']].to_numpy(float)
 assert a.shape==(390,5)
 arrs.append(a)
S=np.stack(arrs)
print('NQ active complete sessions',S.shape,flush=True)
OP,HI,LO,CL,V=[S[:,:,j] for j in range(5)]
T=len(valid)
# Causal session VWAP using only the bar up through signal time
TP=(HI+LO+CL)/3
VWAP=(TP*V).cumsum(axis=1)/V.cumsum(axis=1)
ABS_D=np.abs(CL-VWAP)
# For each session t, current 1m volume threshold and VWAP displacement
# are computed ONLY on previous 20 full sessions, at the same minute-index.
rows=[]
for t in range(20,T):
 session=valid[t];op,hi,lo,cl,vol=OP[t],HI[t],LO[t],CL[t],V[t]
 or_hi=float(hi[:15].max());or_lo=float(lo[:15].min())
 # H01 first outside-close with preprevious-20 volume quality
 h1=None
 for i in range(15,90):
  side=1 if cl[i]>or_hi else (-1 if cl[i]<or_lo else 0)
  if side==0:continue
  past_median=float(np.median(V[t-20:t,i]))
  if vol[i]>=1.25*past_median:
   h1=(i,side);break
 # H02 first close breakout; rejection <=5m or no event
 h2=None
 for i in range(15,85):
  side=1 if cl[i]>or_hi else (-1 if cl[i]<or_lo else 0)
  if side==0: continue
  for j in range(i+1,min(i+6,90)):
   if or_lo<cl[j]<or_hi:
    h2=(j,-side);break
  break # first breakout in session is consumed
 # H03 causal VWAP dev + low efficiency and past 20 same-minute 80% displacement
 h3=None
 for i in range(29,90):
  z=cl[i]-VWAP[t,i]
  threshold=float(np.quantile(ABS_D[t-20:t,i],.80))
  if abs(z)<=threshold or z==0: continue
  moves=np.abs(np.diff(cl[i-15:i+1])).sum()
  if moves<=0:continue
  eff=abs(cl[i]-cl[i-15])/moves
  if eff<=0.30:
   h3=(i,-1 if z>0 else 1);break
 for hypothesis,tr in (('NQ-H01',h1),('NQ-H02',h2),('NQ-H03',h3)):
  if tr is None:continue
  i,side=tr
  if i+31>=390:continue
  entry=float(op[i+1]);exit15=float(op[i+16]);exit30=float(op[i+31]);
  # Two extra ticks of adverse price per market order (NQ tick = 0.25, multiplier = 20).
  # Combined price slippage = 1.0pt per round trip ($20); separate Free fee = $5.74.
  cost=1.0*20+FREE_FEE_NQ_RT
  p15=(exit15-entry)*side*20-cost;p30=(exit30-entry)*side*20-cost
  rows.append({'session':session,'hypothesis':hypothesis,'signal_time_et':f'{(571+i)//60:02d}:{(571+i)%60:02d}',
              'side':'LONG' if side>0 else 'SHORT','entry_open':entry,'exit_open_30m':exit30,
              'pnl_15m_usd':round(float(p15),2),'pnl_30m_usd':round(float(p30),2),
              'gross_30m_points':round((exit30-entry)*side,4),
              'year':int(session[:4]),'week':str(pd.Timestamp(session).to_period('W-SUN'))})
trades=pd.DataFrame(rows)
trades.to_csv(O/'NQ_H01_H03_FIRST_DIAGNOSTIC_EVENTS_2020_2024.csv',index=False)

# 5000 week-sign-flip, one-sided positive directional signal p-value under symmetry
seed=20261009; rng=np.random.default_rng(seed)
results={};pvals={}
for name,x in trades.groupby('hypothesis',sort=True):
 p=x.pnl_30m_usd.to_numpy(float)
 win=p[p>0].sum();loss=-p[p<0].sum()
 net=float(p.sum());avg=float(p.mean())
 weekly=x.groupby('week').pnl_30m_usd.sum().to_numpy(float)
 obs=weekly.sum();null=(rng.choice([-1,1],size=(5000,len(weekly)))*weekly).sum(axis=1)
 onep=float((1+sum(null>=obs))/(1+len(null)))
 # Week-level bootstrap CI of signal expectancy
 grouped=x.groupby('week').pnl_30m_usd.agg(['sum','count']); v=grouped[['sum','count']].to_numpy()
 picks=rng.integers(0,len(v),size=(5000,len(v)))
 sim=v[picks];sums=sim[:,:,0].sum(axis=1);counts=sim[:,:,1].sum(axis=1)
 ci=np.quantile(sums/counts,[.025,.975]).tolist()
 results[name]={'events':len(x),'net_30m_usd':round(net,2),'expectancy_30m_usd':round(avg,2),
                'profit_factor_30m':round(float(win/loss),3) if loss>0 else None,
                'win_rate_30m':round(float(np.mean(p>0)),4),
                'net_15m_usd':round(float(x.pnl_15m_usd.sum()),2),
                'net_30m_plus_1_extra_tick_per_side_usd':round(net-10*len(x),2),
                'positive_years':int(sum(x.groupby('year').pnl_30m_usd.sum()>0)),
                'yearly':{str(int(y)):{'n':len(g),'net':round(float(g.pnl_30m_usd.sum()),2)} for y,g in x.groupby('year')},
                'week_bootstrap_avg_95pct_interval':[round(float(ci[0]),2),round(float(ci[1]),2)],
                'week_sign_flip_one_sided_p':round(onep,5)}
 pvals[name]=onep
# Benjamini-Hochberg q-values (3 preregistered first-screen families)
keys=sorted(pvals,key=pvals.get);m=len(keys);q=1.0
for rank,key in reversed(list(enumerate(keys,1))):
 q=min(q,pvals[key]*m/rank);results[key]['BH_q_3_test_families']=round(float(q),5)
print(json.dumps(results,indent=2),flush=True)
(O/'NQ_H01_H03_FIRST_DIAGNOSTIC_REPORT.json').write_text(json.dumps({'authority':'EXPLORATORY 2020–24 DEVELOPMENT ONLY; NOT EXECUTABLE; NO STOP/TP; NO NEWS; 2025/26 SEALED','preregistered':'research/nq/NQ_H01_H03_FIXED_DIAGNOSTIC_PREREG_2026_10_09.md','sessions':len(valid),'costs':'NQ $20/point; 2 adverse ticks each side + Free all-in $5.74 fee = $25.74 round-trip at horizon open fills; Free NOT MFFU','statistical_method':'weekly sign-flip 5000, week-bootstrap 5000, BH across 3 hypotheses','results':results},indent=2))