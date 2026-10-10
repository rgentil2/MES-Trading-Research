#!/usr/bin/env python3
"""Frozen one-shot NQ H33-H52 study. Development ONLY; no OOS reads or stop/TP claims."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve()
if str(ROOT.parent) not in sys.path: sys.path.insert(0,str(ROOT.parent))
try:
 from research.nq.nq_h05_h07_level_volume_screen import load_development, roll_contract
except ModuleNotFoundError:
 from nq_h05_h07_level_volume_screen import load_development, roll_contract

HYPOTHESES=[f'NQ-H{i:02d}' for i in range(33,53)]
SEED=20261009; BOOT=10000
NQ_POINT=20.0; TICK=.25; FREE_RT=5.74; SLIP_TICKS_SIDE=2
FRICTION=FREE_RT+2*SLIP_TICKS_SIDE*TICK*NQ_POINT


def sg(x): return 1 if x>0 else (-1 if x<0 else 0)
def range_in(g,i,j): return float(g[i:j+1,1].max()-g[i:j+1,2].min())
def cloc(p,low,high): return float((p-low)/max(high-low,TICK))

def signal_for_day(t, dates, days):
    """All twenty deterministic rules are implemented without accessing today's bar > signal minute."""
    g=days[t]; prev=days[t-1]; prev2=days[t-2]
    thiscontract=roll_contract(date.fromisoformat(dates[t]))
    same=[roll_contract(date.fromisoformat(dates[t-j]))==thiscontract for j in range(1,5)]
    fresh=[]
    for j in range(1,5):
        fresh.append((date.fromisoformat(dates[t-j+1])-date.fromisoformat(dates[t-j])).days<=5)
    ok1=all(same[:1]) and all(fresh[:1]);ok2=all(same[:2]) and all(fresh[:2]);ok3=all(same[:3]) and all(fresh[:3]);ok4=all(same[:4]) and all(fresh[:4])
    atr=max(float(np.median([range_in(days[j],0,389) for j in range(t-14,t)])),TICK)
    prev20=days[t-20:t]; med_first=float(np.median([range_in(a,0,14) for a in prev20]));
    vol1=float(g[:15,4].sum());vol2=float(g[15:30,4].sum())
    medvol1=float(np.median(prev20[:,:15,4].sum(axis=1)));medvol2=float(np.median(prev20[:,15:30,4].sum(axis=1)))
    c15=float(g[14,3]);c30=float(g[29,3]);c45=float(g[44,3]);c60=float(g[59,3])
    o15=float(g[0,0]);o30=float(g[15,0]);body1=c15-o15;body2=c30-o30
    r15=range_in(g,0,14);hi15=float(g[:15,1].max());lo15=float(g[:15,2].min())
    r30=range_in(g,0,29);hi30=float(g[:30,1].max());lo30=float(g[:30,2].min())
    output={}
    def put(n,i,side):
        if side in (-1,1) and n not in output:output[n]=(i,side)
    # A: opening range structures
    if r15>=1.20*med_first:
        loc=cloc(c15,lo15,hi15)
        if loc>=.85:put(33,14,1)
        if loc<=.15:put(33,14,-1)
    if r15<=.70*med_first:
        if c30>=hi15+TICK:put(34,29,1)
        if c30<=lo15-TICK:put(34,29,-1)
    if abs(body1)>=.20*atr:
        ratio=(c15-c30)/body1
        if .30<=ratio<=.65:put(35,29,sg(body1))
    if abs(body1)>=.15*atr and abs(body2)>=.15*atr and sg(body1)==-sg(body2):put(36,29,sg(body2))
    if r15>=.15*atr:
        upper=hi15-max(o15,c15);lower=min(o15,c15)-lo15;loc=cloc(c15,lo15,hi15)
        up=upper>=.50*r15 and loc<=.30
        down=lower>=.50*r15 and loc>=.70
        if up!=down:put(37,14,-1 if up else 1)
    # B: path geometry
    morning=c45-o15
    step_total=np.abs(np.diff(g[:45,3])).sum()
    e=abs(morning)/step_total if step_total>0 else 0
    if e>=.60 and abs(morning)>=.25*atr:put(38,44,sg(morning))
    if e<=.15 and abs(morning)>=.10*atr:put(39,44,-sg(morning))
    last_five=np.diff(g[39:45,3]);pos=int((last_five>0).sum());neg=int((last_five<0).sum())
    direction=1 if pos>=4 and neg==0 else (-1 if neg>=4 and pos==0 else 0)
    if direction and sg(body1)==-direction:put(40,44,direction)
    if c45>=hi30+TICK:put(41,44,1)
    if c45<=lo30-TICK:put(41,44,-1)
    if c45>=hi30+TICK and lo30<c60<hi30:put(42,59,-1)
    if c45<=lo30-TICK and lo30<c60<hi30:put(42,59,1)
    # C: volume allocation
    if vol1>=1.40*medvol1 and abs(body1)>=.15*atr:put(43,14,sg(body1))
    if vol1<=.65*medvol1 and abs(body1)>=.15*atr:put(44,14,-sg(body1))
    if vol2>=1.30*medvol2 and lo15<c30<hi15 and abs(body2)>=.10*atr:put(45,29,sg(body2))
    if vol2>=1.40*medvol2:
        up=float(g[15:30,1].max())>=hi15+TICK and c30<hi15
        down=float(g[15:30,2].min())<=lo15-TICK and c30>lo15
        if up!=down:put(46,29,-1 if up else 1)
    if medvol1>0 and medvol2>0 and vol2/medvol2<=.70*(vol1/medvol1) and abs(body2)>=.12*atr:
        put(47,29,-sg(body2))
    # D: past calendar session geometries, same underlying quarterly contract required
    if ok1:
        phi=float(prev[:,1].max());plo=float(prev[:,2].min());pc=float(prev[-1,3]);pclose_loc=cloc(pc,plo,phi)
        prev_bias=1 if pclose_loc>=.8 else (-1 if pclose_loc<=.2 else 0)
        gap=o15-pc
        if prev_bias and sg(gap)==-prev_bias and abs(gap)>=.15*atr and sg(body1)==sg(gap) and abs(body1)>=.10*atr:
            put(48,14,sg(gap))
    if ok2:
        hi1=float(prev[:,1].max());lo1=float(prev[:,2].min());hi2=float(prev2[:,1].max());lo2=float(prev2[:,2].min())
        if hi1<hi2 and lo1>lo2 and abs(body1)>=.12*atr:put(49,14,sg(body1))
        if hi1>hi2 and lo1<lo2 and .35<=cloc(float(prev[-1,3]),lo1,hi1)<=.65 and abs(body1)>=.12*atr:put(50,14,-sg(body1))
    if ok3:
        rr=[range_in(days[t-k],0,389) for k in (3,2,1)]
        if rr[0]>rr[1]>rr[2] and r15>=med_first and abs(body1)>=.10*atr:put(51,14,sg(body1))
    if ok4:
        closes=[float(days[t-j][-1,3]) for j in (4,3,2,1)]
        x=np.diff(closes)
        prev_trend=1 if np.all(x>0) else (-1 if np.all(x<0) else 0)
        if prev_trend and sg(body1)==-prev_trend and abs(body1)>=.10*atr:put(52,14,sg(body1))
    return {f'NQ-H{n:02d}':event for n,event in output.items()}


def bh(pvals):
    ordered=sorted(pvals,key=lambda k:(pvals[k],k));out={};m=len(pvals);q=1.
    for rank,k in reversed(list(enumerate(ordered,1))):
        q=min(q,m*pvals[k]/rank);out[k]=q
    return out

def holm(pvals):
    ordered=sorted(pvals,key=lambda k:(pvals[k],k));out={};q=0.;m=len(pvals)
    for rank,k in enumerate(ordered):
        q=max(q,(m-rank)*pvals[k]);out[k]=min(q,1.)
    return out


def stats(events):
    rng=np.random.default_rng(SEED);pvals={};out={}
    for h in HYPOTHESES:
        e=events.loc[events.hypothesis==h]
        if e.empty:
            pvals[h]=1.;out[h]={'n':0,'p_one_sided':1.,'years_positive':0,'decision':'INSUFFICIENT_EVIDENCE','fail_reasons':['No events']};continue
        p=e.pnl30.to_numpy(float);mean=float(p.mean());total=float(p.sum())
        groups=e.groupby('week').pnl30.agg(['sum','count']).to_numpy(float);nweek=len(groups)
        exceed=0;boot=[]
        for offset in range(0,BOOT,200):
            sz=min(200,BOOT-offset)
            flip=rng.choice((-1.,1.),size=(sz,nweek));exceed+=int(((flip*groups[:,0]).sum(axis=1)>=total).sum())
            ix=rng.integers(0,nweek,size=(sz,nweek));s=groups[ix];boot.append(s[:,:,0].sum(axis=1)/s[:,:,1].sum(axis=1))
        ps=(1+exceed)/(BOOT+1);pvals[h]=ps;bs=np.concatenate(boot)
        yr={str(y):{'n':int((e.year==y).sum()),'net':round(float(e.loc[e.year==y,'pnl30'].sum()),2),'mean':round(float(e.loc[e.year==y,'pnl30'].mean()),2) if (e.year==y).any() else None} for y in range(2020,2025)}
        npos=sum(v['mean'] is not None and v['mean']>0 for v in yr.values())
        pos=p[p>0].sum();neg=-p[p<0].sum();days=pd.to_datetime(e.session.unique());days.sort();gap=np.diff(days).astype('timedelta64[D]').astype(int)
        out[h]={'n':len(e),'net_usd':round(total,2),'expectancy_usd':round(mean,2),'pf':round(float(pos/neg),3) if neg>0 else None,'win_rate':round(float((p>0).mean()),4),'ci90':[round(float(v),2) for v in np.quantile(bs,[.05,.95])], 'ci95':[round(float(v),2) for v in np.quantile(bs,[.025,.975])],'p_one_sided':ps,'years_positive':npos,'by_year':yr,'nweeks':nweek,'pnl15_total':round(float(e.pnl15.sum()),2),'cost_stress_extra_tick_each_side_total':round(total-10*len(e),2),'max_gap_days':int(gap.max()) if len(gap) else None,'gaps_gt7_days':int((gap>7).sum()),'decision':None}
    q=bh(pvals);holm2=holm({k:min(1,2*min(v,1-v)) for k,v in pvals.items()})
    for h in HYPOTHESES:
        o=out[h];o['q_bh20']=round(q[h],6);o['holm_two_sided_approx']=round(holm2[h],6)
        if o['n']==0:continue
        fail=[]
        if o['n']<=150:fail.append('N <= 150')
        if o['expectancy_usd']<=0:fail.append('Nonpositive net mean')
        if o['ci90'][0]<=0:fail.append('90pct bootstrap CI includes zero')
        if q[h]>.10:fail.append('BH q > .10')
        if o['years_positive']<3:fail.append('Less than 3/5 positive years')
        o['fail_reasons']=fail;o['decision']='PROMISING_EXPLORATORY' if not fail else ('INSUFFICIENT_EVIDENCE' if o['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY')
    return out

def run(zip_path,outdir,preflight=False):
    if not preflight:raise RuntimeError('Family/source preflight must PASS BEFORE opening market data')
    dates,days,overnight,qc=load_development(Path(zip_path))
    if len(dates)!=1221:raise RuntimeError('Unexpected historical dev complete RTH count: '+str(len(dates)))
    ev=[]
    for t in range(20,len(dates)):
        for h,(i,direction) in signal_for_day(t,dates,days).items():
            en=float(days[t,i+1,0]);c30=float(days[t,i+31,0]);c15=float(days[t,i+16,0]);d=dates[t]
            ev.append({'session':d,'year':int(d[:4]),'hypothesis':h,'signal_minute_index':i,'direction':direction,'entry_open':en,'exit30_open':c30,'pnl30':round(direction*(c30-en)*NQ_POINT-FRICTION,2),'pnl15':round(direction*(c15-en)*NQ_POINT-FRICTION,2),'week':str(pd.Timestamp(d).to_period('W-SUN'))})
    events=pd.DataFrame(ev,columns=['session','year','hypothesis','signal_minute_index','direction','entry_open','exit30_open','pnl30','pnl15','week']);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    events.to_csv(outdir/'NQ_H33_H52_EVENTS_2020_2024.csv',index=False)
    results=stats(events)
    report={'experiment':'NQ-H33-H52','status':'DEVELOPMENT_EXPLORATORY','loaded_years':[2020,2021,2022,2023,2024],'holdout_2025_loaded':False,'holdout_2026_loaded':False,'source_qc':qc,'n_hypotheses':20,'n_sessions':len(dates),'total_events':len(events),'fee_nq_free_rt_usd':FREE_RT,'slippage_ticks_per_side':SLIP_TICKS_SIDE,'point_value_usd':NQ_POINT,'friction_rt_usd':FRICTION,'research_limits':['No SL/TP or actual fills','Reusable 2020-2024 data not OOS','No redesign based on results','Same index hypotheses correlated','NQ Free fees NOT MFFU funding fees'],'results':results}
    (outdir/'NQ_H33_H52_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    family={'stage':'DEVELOPMENT_EXPLORATORY','loaded_years':[2020,2021,2022,2023,2024],'holdout_2025_loaded':False,'holdout_2026_loaded':False,'family_metrics':{h:{'status':'ESTIMATED' if v['n'] else 'NOT_ESTIMABLE','effect':v.get('expectancy_usd',0),'p_value_two_sided':min(1.,2*min(v['p_one_sided'],1-v['p_one_sided']))} for h,v in results.items()}}
    (outdir/'nq_h33_h52_minute_family.json').write_text(json.dumps(family,indent=2)+'\n')
    cols=['h','n','expectancy_usd','pf','years_positive','ci90_low','ci90_high','p_one_sided','q_bh20','decision']
    s=[{'h':h,**{z:(r['ci90'][0] if z=='ci90_low' else r['ci90'][1]) if z in ('ci90_low','ci90_high') and 'ci90' in r else r.get(z) for z in cols[1:]}} for h,r in results.items()]
    pd.DataFrame(s)[cols].to_csv(outdir/'NQ_H33_H52_SUMMARY_20.csv',index=False)
    print(json.dumps({'sessions':len(dates),'events':len(events),'promising':[h for h,r in results.items() if r['decision']=='PROMISING_EXPLORATORY'],'full_results':{h:{k:r.get(k) for k in ('n','expectancy_usd','ci90','q_bh20','years_positive','decision')} for h,r in results.items()}},indent=2))
    return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prereg-frozen',action='store_true');args=p.parse_args();run(args.zip,args.out,args.prereg_frozen)