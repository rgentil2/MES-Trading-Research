"""One-shot 25 prespecified NQ 1m mechanism tests. No holdout reads or adaptive tuning."""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.name=='nq' else Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
# H05/H07 loader has independent source-only 2020-24 allowlist and fixed roll.
try:
 from research.nq.nq_h05_h07_level_volume_screen import load_development,roll_contract
except ModuleNotFoundError:
 from nq_h05_h07_level_volume_screen import load_development,roll_contract

FREE_NQ_RT=5.74; POINT=20.; TICK=.25; SLIP_TICKS_EACH_SIDE=2
FRICTION=FREE_NQ_RT+2*SLIP_TICKS_EACH_SIDE*TICK*POINT # $25.74 / one NQ contract
SEED=20261009; B=10000
HYPOTHESES=[f'NQ-H{k:02}' for k in range(8,33)]

def signed(x,eps=0.):
 return 1 if x>eps else (-1 if x< -eps else 0)

def eff(x):
 s=np.abs(np.diff(x)).sum();return abs(x[-1]-x[0])/s if s>0 else 0.

def vwap(g,i):
 sub=g[:i+1];v=sub[:,4]
 return float((((sub[:,1]+sub[:,2]+sub[:,3])/3)*v).sum()/v.sum())

def rrange(g,start,end):
 sub=g[start:end+1];return float(sub[:,1].max()-sub[:,2].min())

def local_prices(t,dates,a,ov):
 """Return {NQ-Hxx: (signal_minute_array_ix, +1/-1)} for exactly 25 fixed questions.

 Every signal is calculated using only bars up to the indicated minute. All day-to-day
 price comparisons require identical active quarterly contracts; cross-roll days
 are rejected for those tests to avoid unadjusted inter-contract price gaps.
 """
 d=dates[t];g=a[t];prior=a[t-1];prev2=a[t-2];prev3=a[t-3]
 contract=roll_contract(date.fromisoformat(d))
 okprev=contract==roll_contract(date.fromisoformat(dates[t-1]))
 ok2=okprev and contract==roll_contract(date.fromisoformat(dates[t-2]))
 ok3=ok2 and contract==roll_contract(date.fromisoformat(dates[t-3]))
 age=(date.fromisoformat(d)-date.fromisoformat(dates[t-1])).days
 okprev=okprev and age<=5
 if not okprev:ok2=ok3=False
 atr=np.median([rrange(a[j],0,389) for j in range(t-14,t)])
 atr=max(float(atr),TICK)
 past20=a[t-20:t]
 range20=np.array([rrange(x,0,389) for x in past20]);medrange=float(np.median(range20))
 first=g[:15];open15=float(g[0,0]);c15=float(g[14,3]);drive15=c15-open15
 hi15=float(first[:,1].max());lo15=float(first[:,2].min());or15=hi15-lo15
 c30=float(g[29,3]);c45=float(g[44,3]);c60=float(g[59,3]);c75=float(g[74,3]);
 pclose=float(prior[389,3]);prev_dir=signed(prior[-1,3]-prior[0,0]);
 result={}
 def add(k,idx,side):
  if side in (-1,1) and 0<=idx<=89:result[f'NQ-H{k:02}']=(idx,side)
 # A: gap and overnight context. Distinct from H01-H07 opening-range break mechanisms.
 if okprev:
  gap=open15-pclose
  gapdir=signed(gap)
  if abs(gap)>=0.25*atr:
   if gapdir*(c15-pclose)>=0.6*abs(gap):add(8,14,-gapdir)        # fade retained gap
   if signed(drive15)==gapdir and abs(drive15)>=0.15*atr:add(9,14,gapdir)  # gap+drive continuation
   # Pullback to within 0.10 ATR of prior close by 09:45, away by 10:00
   if abs(c15-pclose)<=.10*atr and signed(c30-c15)==gapdir and abs(c30-c15)>=.10*atr:add(10,29,gapdir)
 if d in ov.index:
  z=ov.loc[d]
  if float(z.on_count)>=800:
   on_hi=float(z.on_high);on_lo=float(z.on_low);on_width=on_hi-on_lo
   if on_width>=0.4*atr:
    position=(open15-on_lo)/max(on_width,TICK)
    if position>=.8 and drive15>=.12*atr:add(11,14,1)
    if position<=.2 and drive15<=-.12*atr:add(11,14,-1)
    if position>=.8 and drive15<=-.12*atr:add(12,14,-1)
    if position<=.2 and drive15>=.12*atr:add(12,14,1)
 # B: predetermined prior RTH context
 if okprev:
  prev_close_loc=(pclose-float(prior[:,2].min()))/max(rrange(prior,0,389),TICK)
  if prev_close_loc>=.8 and drive15>=.12*atr:add(13,14,1)
  if prev_close_loc<=.2 and drive15<=-.12*atr:add(13,14,-1)
  if rrange(prior,0,389)<=.75*medrange and abs(drive15)>=.2*atr:add(14,14,signed(drive15))
  if rrange(prior,0,389)>=1.25*medrange and signed(drive15)==prev_dir and abs(drive15)>=.12*atr:add(15,14,-prev_dir)
 if ok2:
  p1=signed(a[t-1][-1,3]-a[t-2][-1,3]);p2=signed(a[t-2][-1,3]-a[t-3][-1,3]) if ok3 else 0
  if p1 and signed(drive15)==-p1 and abs(drive15)>=.12*atr:add(16,14,-p1)
  if ok3 and p1 and p2==p1 and prev_dir==p1 and signed(drive15)==p1 and abs(drive15)>=.1*atr:add(17,14,-p1)
 # C: VWAP structure using current 1m only as of observation
 vw45=vwap(g,44);vw59=vwap(g,59)
 if signed(c45-vw45) and signed(vw45-vwap(g,39))==signed(c45-vw45):
  # strict crossing from opposite side within five minutes
  side=signed(c45-vw45)
  if any(signed(float(g[j,3]-vwap(g,j)))==-side for j in range(39,44)):add(18,44,side)
 # scaled VWAP deviation and efficiency; calculated on last completed 20/15 minute closes
 deviation=c45-vw45
 meanabs=np.mean(np.abs(np.diff(g[24:45,3])))
 if abs(deviation)>=1.5*max(meanabs,TICK) and abs(deviation)>=.1*atr:
  if eff(g[29:45,3])>=.6:add(19,44,signed(deviation))
  if eff(g[29:45,3])<=.3:add(20,44,-signed(deviation))
 if signed(c60-vw59) and signed(vw59-vwap(g,44))==-signed(c60-vw59) and abs(c60-vw59)>=.1*atr:
  add(21,59,-signed(c60-vw59))
 vw_cross=sum(signed(g[j,3]-vwap(g,j))*signed(g[j-1,3]-vwap(g,j-1))<0 for j in range(30,60))
 if vw_cross>=3 and abs(c60-c45)>=.15*atr:add(22,59,signed(c60-c45))
 # D: volume/movement interaction compared only with previous 20 eligible days at SAME fixed clock
 vol_15_30=float(g[24:30,4].sum());hist_15_30=float(np.median(past20[:,24:30,4].sum(axis=1)))
 vol_30_45=float(g[39:45,4].sum());hist_30_45=float(np.median(past20[:,39:45,4].sum(axis=1)))
 move5_30=c30-float(g[23,3]);move5_45=c45-float(g[38,3]);
 if vol_15_30>=1.5*hist_15_30 and abs(move5_30)>=.2*atr:add(23,29,signed(move5_30))
 if vol_15_30>=1.5*hist_15_30 and .03*atr<=abs(move5_30)<=.10*atr:add(24,29,-signed(move5_30))
 if vol_30_45<=.75*hist_30_45 and abs(move5_45)>=.15*atr:add(25,44,-signed(move5_45))
 if vol_30_45>=1.5*hist_30_45:
  local_h=float(g[39:45,1].max());local_l=float(g[39:45,2].min())
  clv=(c45-local_l)/max(local_h-local_l,TICK)
  if clv>=.8 and move5_45>.1*atr:add(26,44,1)
  if clv<=.2 and move5_45<-.1*atr:add(26,44,-1)
 vol_last15=float(g[45:60,4].sum());hist15=float(np.median(past20[:,45:60,4].sum(axis=1)))
 slope15=c60-c45
 if vol_last15>=1.5*hist15 and signed(slope15)==-signed(c60-vw59) and abs(slope15)>=.15*atr:add(27,59,signed(slope15))
 # E: intraday patterns, ranges, price sequences
 ret3=np.diff(g[26:30,3]);
 if (np.all(ret3>0) or np.all(ret3<0)) and abs(ret3.sum())>=.1*atr:add(28,29,signed(ret3.sum()))
 if (np.all(ret3>0) or np.all(ret3<0)) and abs(ret3[0])>abs(ret3[1])>abs(ret3[2]):add(29,29,-signed(ret3.sum()))
 # Fixed 09:46-10:00 compression compared to same interval in previous 20 RTH sessions.
 range_first15=rrange(g,15,29)
 historic_first15=np.array([rrange(x,15,29) for x in past20]);p25=float(np.quantile(historic_first15,.25))
 if range_first15<=p25:
  h15=float(g[15:30,1].max());l15=float(g[15:30,2].min())
  if c45>h15+TICK:add(30,44,1)
  if c45<l15-TICK:add(30,44,-1)
 # 10:16-10:30 extreme 15m expansion vs previous 20 days SAME interval
 range_last15=rrange(g,45,59);hist_last15=float(np.median([rrange(x,45,59) for x in past20]))
 if range_last15>=1.5*hist_last15 and abs(c60-c45)>=.15*atr:add(31,59,signed(c60-c45))
 # fixed 10:31-10:45 break of earlier 10:16-10:30 high/low
 h_prior15=float(g[45:60,1].max());l_prior15=float(g[45:60,2].min());
 if c75>h_prior15+TICK:add(32,74,1)
 if c75<l_prior15-TICK:add(32,74,-1)
 return result

def bh(pvals):
 out={};ordered=sorted(pvals,key=pvals.get);m=len(ordered);q=1.
 for i,k in reversed(list(enumerate(ordered,1))):q=min(q,m*pvals[k]/i);out[k]=q
 return out

def holm(pvals):
 out={};ordr=sorted(pvals,key=pvals.get);lo=0.;m=len(ordr)
 for j,k in enumerate(ordr):lo=max(lo,(m-j)*pvals[k]);out[k]=min(lo,1.)
 return out

def stats(df):
 rng=np.random.default_rng(SEED);results={};pvals={}
 for h in HYPOTHESES:
  g=df[df.hypothesis==h]
  if g.empty:
   results[h]={'n':0,'p_one_sided':1.0,'decision':'INSUFFICIENT_EVIDENCE'};pvals[h]=1.;continue
  pnl=g.pnl30.to_numpy(float);net=float(pnl.sum())
  blocks=g.groupby('week').pnl30.agg(['sum','count']).to_numpy(float)
  # Block sign flipping uses entire calendar-week profit; week bootstrap uses week pairs (sum,count).
  exceed=0;resampled=[]
  for batch in range(0,B,250):
   n=min(250,B-batch);sgn=rng.choice((-1.,1.),size=(n,len(blocks)))
   exceed+=int(np.count_nonzero((sgn*blocks[:,0]).sum(axis=1)>=net))
   idx=rng.integers(0,len(blocks),size=(n,len(blocks)))
   w=blocks[idx];resampled.extend((w[:,:,0].sum(axis=1)/w[:,:,1].sum(axis=1)).tolist())
  p=(1+exceed)/(B+1);pvals[h]=p
  ci90=np.quantile(resampled,[.05,.95]);ci95=np.quantile(resampled,[.025,.975])
  years={str(y):{'n':int((g.year==y).sum()),'net':round(float(g.loc[g.year==y,'pnl30'].sum()),2),'mean':round(float(g.loc[g.year==y,'pnl30'].mean()),2) if (g.year==y).any() else None} for y in range(2020,2025)}
  positive=sum(v['mean'] is not None and v['mean']>0 for v in years.values())
  gains=float(pnl[pnl>0].sum());loss=-float(pnl[pnl<0].sum());days=pd.to_datetime(g.day.drop_duplicates().sort_values());gaps=days.diff().dt.days.dropna()
  results[h]={'n':len(g),'net_usd':round(net,2),'expectancy_usd':round(float(pnl.mean()),2),
   'pf':round(gains/loss,3) if loss>0 else None,'win_rate':round(float((pnl>0).mean()),4),
   'ci90':[round(float(x),2) for x in ci90],'ci95':[round(float(x),2) for x in ci95],
   'p_one_sided':p,'positive_years':positive,'yearly':years,'weeks':len(blocks),
   'net_15m':round(float(g.pnl15.sum()),2), 'net_stress_extra_tick_each_side':round(net-10*len(g),2),
   'gaps_gt7':int((gaps>7).sum()),'max_gap_days':int(gaps.max()) if len(gaps) else 0}
 q=bh(pvals);hh=holm(pvals)
 for h in HYPOTHESES:
  r=results[h];r.update(q_bh=q[h],p_holm=hh[h]);
  if r['n']==0:continue
  reasons=[]
  if not r['n']>150:reasons.append('N<=150')
  if not r['expectancy_usd']>0:reasons.append('nonpositive net effect')
  if not r['ci90'][0]>0:reasons.append('CI90 includes or below zero')
  if not r['q_bh']<=.1:reasons.append('BH q >0.10')
  if not r['positive_years']>=3:reasons.append('positive years <3/5')
  r.update(decision='PROMISING_EXPLORATORY' if not reasons else ('INSUFFICIENT_EVIDENCE' if r['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY'),fail_reasons=reasons)
 return results

def run(zip_path:Path,out:Path,preflight:bool=False):
 if not preflight:raise RuntimeError('H08-H32 preregistration preflight must be verified BEFORE loading ZIP prices')
 dates,a,ov,qc=load_development(zip_path)
 if len(dates)!=1221:raise ValueError('Unexpected full-session source '+str(len(dates)))
 events=[]
 for t in range(20,len(dates)):
  signals=local_prices(t,dates,a,ov)
  for hyp,(i,side) in signals.items():
   if i+31>=390:raise ValueError('Missing causal 30-min exit')
   entry=float(a[t,i+1,0]);exit30=float(a[t,i+31,0]);exit15=float(a[t,i+16,0])
   events.append({'day':dates[t],'year':int(dates[t][:4]),'hypothesis':hyp,
                  'signal_et':f'{(571+i)//60:02d}:{(571+i)%60:02d}',
                  'side':'LONG' if side>0 else 'SHORT','entry_open':entry,'exit30_open':exit30,
                  'pnl30':round((exit30-entry)*side*POINT-FRICTION,2),
                  'pnl15':round((exit15-entry)*side*POINT-FRICTION,2),
                  'week':str(pd.Timestamp(dates[t]).to_period('W-SUN'))})
 e=pd.DataFrame(events)
 if not len(e):raise ValueError('No events; bad study')
 out.mkdir(parents=True,exist_ok=True);e.to_csv(out/'NQ_H08_H32_EVENTS_2020_2024.csv',index=False)
 results=stats(e)
 report={'stage':'DEVELOPMENT_EXPLORATORY','authority':'EXPLORATORY_ONLY_REUSED_NQ_2020_2024','loaded_years':[2020,2021,2022,2023,2024],
  'holdout_2025_loaded':False,'holdout_2026_loaded':False,'fee_NQ_Free_RT':FREE_NQ_RT,
  'adverse_slippage_ticks_each_side':SLIP_TICKS_EACH_SIDE,'total_friction_RT':FRICTION,
  'source':qc,'hypothesis_count':25,'events':len(e),'Gate1':'N>150, positive net, 90pct weekly bootstrap lower >0, BH<=0.10, >=3/5 years, no posthoc selection',
  'results':results,'limitations':['Minute OHLCV only; fixed horizon not tradable fills','No protective stop/target/news exclusion','25 related hypotheses and previously explored time ranges; confirm independently','2025 and 2026 sealed; no ticks read']}
 (out/'NQ_H08_H32_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 family={'stage':'DEVELOPMENT_EXPLORATORY','loaded_years':[2020,2021,2022,2023,2024],'holdout_2025_loaded':False,'holdout_2026_loaded':False,
         'family_metrics':{k:{'status':'ESTIMATED' if v['n'] else 'NOT_ESTIMABLE',
                              'effect':v.get('expectancy_usd',0.),'p_value_two_sided':min(1.,2*min(v['p_one_sided'],1-v['p_one_sided'])) if v['n'] else 1.}
                           for k,v in results.items()},
         'caveat':'Fixed-rule weekly signflip two-sided inversion is an approximate sign-symmetry test; long/short are prespecified. No OOS or executable strategy.'}
 (out/'nq_h08_h32_minute_family.json').write_text(json.dumps(family,indent=2)+'\n')
 print(json.dumps({'status':'EXECUTED_25_DEVELOPMENT_ONLY','sessions':len(dates),'total_events':len(e),
                   'passes':[k for k,v in results.items() if v['decision']=='PROMISING_EXPLORATORY'],
                   'summary':{k:{z:v.get(z) for z in ('n','expectancy_usd','ci90','q_bh','positive_years','decision')} for k,v in results.items()}},indent=2))
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--zip',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--prereg-frozen',action='store_true');c=parser.parse_args()
 run(c.zip,c.out,preflight=c.prereg_frozen)