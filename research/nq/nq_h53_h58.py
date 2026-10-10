#!/usr/bin/env python3
"""H53-H58 NQ 2020-24 DEV only; frozen research rules, no holdouts."""
from __future__ import annotations
import argparse,json,zipfile,sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
try:
 from research.nq.nq_h05_h07_level_volume_screen import load_development, permitted_name, DEV_RE, roll_contract
except ImportError:
 from nq_h05_h07_level_volume_screen import load_development, permitted_name, DEV_RE, roll_contract
HYPOTHESES=[f'NQ-H{n}' for n in range(53,59)]
SEED=20261010;BOOT=10000;TICK=.25;POINT=20.;FEE=5.74;SLIP_RT=20.;FRICTION=FEE+SLIP_RT

def sgn(x):return 1 if x>0 else (-1 if x<0 else 0)
def fullrange(g):return float(g[:,1].max()-g[:,2].min())
def contract(day):return roll_contract(date.fromisoformat(day))
def load_context(zipfile_path):
    """Only permitted 2020-2024 NQ ZIP members opened. For each session, aggregate prices/volume observed <=09:30 ET."""
    parts=[]
    with zipfile.ZipFile(zipfile_path) as z:
        allowed=sorted(n for n in z.namelist() if permitted_name(n))
        if len(allowed)!=25:raise ValueError(f'Expected 25 allowed NQ DEV members, found {len(allowed)}')
        for idx,n in enumerate(allowed):
            yy=2000+int(DEV_RE.fullmatch(n.rsplit('/',1)[-1]).group(3))
            contract_symbol='NQ_'+n.rsplit('/',1)[-1].split('_')[1]
            with z.open(n) as f:
                df=pd.read_csv(f,sep=';',header=None,names=['utc','open','high','low','close','volume'],dtype={'utc':'string'})
            ts=pd.to_datetime(df.utc,format='%Y%m%d %H%M%S',utc=True)
            if not bool((ts.dt.year==yy).all()):raise ValueError('Development-year mismatch')
            ny=ts.dt.tz_convert('America/New_York');minute=ny.dt.hour*60+ny.dt.minute
            keep=((minute>=1081)|(minute<=570))
            if not keep.any():continue
            a=df.loc[keep,['open','high','low','close','volume']].copy();minute=minute.loc[keep];ny=ny.loc[keep]
            ses=ny.dt.tz_localize(None).dt.normalize()+pd.to_timedelta((minute>=1081).astype('int8'),unit='D')
            a['session']=ses.dt.strftime('%Y-%m-%d').values;a['minute']=minute.to_numpy()
            a=a[a.session.str[:4].isin(('2020','2021','2022','2023','2024'))]
            a=a[[roll_contract(date.fromisoformat(d))==contract_symbol for d in a.session]]
            if a.empty:continue
            a['price_volume']=((a.high+a.low+a.close)/3)*a.volume
            a['pm']=(a.minute>=510)&(a.minute<=570) # 08:30–09:30 ET, 61 bars, close-stamped
            a['night']=(a.minute>=1081)|(a.minute<=570)
            def features(g):
                pm=g[g.pm].sort_values('minute')
                night=g[g.night]
                if len(pm)!=61 or pm.minute.nunique()!=61 or int(pm.minute.min())!=510 or int(pm.minute.max())!=570:return None
                mn=float(pm.low.min());mx=float(pm.high.max());body=float(pm.close.iloc[-1]-pm.open.iloc[0]);v=float(pm.volume.sum())
                nm=int(len(night));nv=float(night.volume.sum());vwap=float(night.price_volume.sum()/nv) if nm>=800 and nv>0 else None
                return {'pm_hi':mx,'pm_lo':mn,'pm_range':mx-mn,'pm_body':body,'pm_volume':v,'night_bars':nm,'night_vwap':vwap}
            # groupby apply includes daily context only, never future RTH
            for key,g in a.groupby('session',sort=False):
                v=features(g)
                if v is not None:parts.append((key,v))
            if idx%5==4:print('Context partitions:',idx+1,'/25',flush=True)
    if len(parts)!=len({k for k,v in parts}):raise ValueError('Double-counted context sessions')
    return dict(parts)

def first_reject(g,hi,lo,start=15,end=75):
    """First crossed boundary consumes day; only one rejection attempt."""
    for i in range(start,end):
        up=g[i,1]>=hi+TICK;dn=g[i,2]<=lo-TICK
        if not up and not dn:continue
        if up and dn:return None
        if up and g[i,3]<hi:return(i,-1)
        if dn and g[i,3]>lo:return(i,1)
        return None
    return None

def accepted_pm_break(g,hi,lo,medvol):
    for i in range(16,75):
        up=g[i-1,3]>=hi+TICK and g[i,3]>=hi+TICK
        dn=g[i-1,3]<=lo-TICK and g[i,3]<=lo-TICK
        if up and dn:return None
        if (up or dn) and g[i,4]>=1.20*medvol[i]:return(i,1 if up else -1)
    return None

def previous_week(dates,days,t):
    day=date.fromisoformat(dates[t]);yy,ww,_=day.isocalendar();current=(yy,ww)
    previous_week_indices=[]
    for j in range(t-1,-1,-1):
        dj=date.fromisoformat(dates[j]);w=(dj.isocalendar().year,dj.isocalendar().week)
        if w!=current:
            oldest=j
            previous_week_indices=[k for k in range(j,-1,-1) if (date.fromisoformat(dates[k]).isocalendar().year,date.fromisoformat(dates[k]).isocalendar().week)==w]
            break
    else:return None
    if len(previous_week_indices)<3:return None
    if any(contract(dates[i])!=contract(dates[t]) for i in previous_week_indices):return None
    if (day-date.fromisoformat(dates[previous_week_indices[-1]])).days>8:return None
    return (max(float(days[j][:,1].max()) for j in previous_week_indices),min(float(days[j][:,2].min()) for j in previous_week_indices))

def signals_for_day(t,dates,days,context):
    g=days[t];d=dates[t];ctx=context.get(d)
    if ctx is None:return {},None
    if t<20:return {},None
    past=[context.get(x) for x in dates[t-20:t]]
    if any(p is None for p in past):return {},None
    atr=max(float(np.median([fullrange(x) for x in days[t-14:t]])),TICK)
    medvol=np.median(days[t-20:t,:,4],axis=0)
    medpm=float(np.median([p['pm_range'] for p in past]));med15=float(np.median([fullrange(x[:15]) for x in days[t-20:t]]))
    hi=ctx['pm_hi'];lo=ctx['pm_lo'];out={}
    def put(n,event):
        if event and event[1] in (-1,1):out[f'NQ-H{n}']=event
    put(53,first_reject(g,hi,lo))
    put(54,accepted_pm_break(g,hi,lo,medvol))
    vw=ctx['night_vwap'];initial=g[0,0];close15=g[14,3];body15=close15-initial
    if vw is not None:
        dist=initial-vw
        if abs(dist)>=.15*atr and abs(body15)>=.07*atr and sgn(body15)==-sgn(dist) and abs(close15-vw)>=.05*atr:
            put(55,(14,-sgn(dist)))
    if abs(ctx['pm_body'])>=.20*atr and abs(body15)>=.10*atr and sgn(ctx['pm_body'])==-sgn(body15):
        put(56,(14,sgn(body15)))
    w=previous_week(dates,days,t)
    if w:put(57,first_reject(g,w[0],w[1]))
    if ctx['pm_range']<=.65*medpm and fullrange(g[:15])>=1.10*med15 and abs(body15)>=.10*atr:
        put(58,(14,sgn(body15)))
    return out,atr

def bracket(g,i,side,entry,atr):
    """Single frozen diagnostic bracket: stop 0.15 past-ATR; TP 1.5R; 30m max, first-hit stop priority."""
    risk=max(0.15*atr,TICK);stop=entry-side*risk;take=entry+side*1.5*risk
    for j in range(i+1,i+31):
        b=g[j];bad=b[2]<=stop if side==1 else b[1]>=stop
        good=b[1]>=take if side==1 else b[2]<=take
        if bad:
            # gap through stop must fill at worse open; stop assumed touched within minute even if target too
            px=min(stop,b[0]) if side==1 else max(stop,b[0]);return side*(px-entry)*POINT-FRICTION,'STOP'
        if good:return side*(take-entry)*POINT-FRICTION,'TARGET'
    return side*(g[i+31,0]-entry)*POINT-FRICTION,'TIME'

def bh(vals):
    order=sorted(vals,key=lambda k:(vals[k],k));out={};q=1.;m=len(vals)
    for rank,k in reversed(list(enumerate(order,1))):q=min(q,m*vals[k]/rank);out[k]=q
    return out

def holm(vals):
    order=sorted(vals,key=lambda k:(vals[k],k));out={};prev=0;m=len(vals)
    for idx,k in enumerate(order):prev=max(prev,(m-idx)*vals[k]);out[k]=min(prev,1.)
    return out

def statistics(e):
    rng=np.random.default_rng(SEED);raw={};ps={}
    for h in HYPOTHESES:
        x=e[e.hypothesis==h];n=len(x)
        if n==0:raw[h]={'n':0,'decision':'INSUFFICIENT_EVIDENCE','p_one_sided':1.,'positive_years':0};ps[h]=1.;continue
        pnl=x.pnl30.to_numpy(float);total=float(pnl.sum());mean=float(pnl.mean())
        weeks=x.groupby('week',sort=True).pnl30.agg(['sum','count']).to_numpy(float)
        neg=0;arr=[]
        for off in range(0,BOOT,200):
            b=min(200,BOOT-off);flips=rng.choice([-1.,1.],size=(b,len(weeks)))
            neg+=int(((flips*weeks[:,0]).sum(axis=1)>=total).sum())
            ind=rng.integers(0,len(weeks),size=(b,len(weeks)));w=weeks[ind]
            arr.append(w[:,:,0].sum(axis=1)/w[:,:,1].sum(axis=1))
        p=(neg+1)/(BOOT+1);ps[h]=p;boot=np.concatenate(arr)
        year={str(yy):{'n':int((x.year==yy).sum()),'mean_usd':round(float(x.loc[x.year==yy,'pnl30'].mean()),2) if (x.year==yy).any() else None,'total_usd':round(float(x.loc[x.year==yy,'pnl30'].sum()),2)} for yy in range(2020,2025)}
        posyrs=sum(v['mean_usd'] is not None and v['mean_usd']>0 for v in year.values())
        profits=float(pnl[pnl>0].sum());losses=-float(pnl[pnl<0].sum())
        bp=x.bracket_pnl.to_numpy(float);bpos=bp[bp>0].sum();bneg=-bp[bp<0].sum()
        dates=pd.to_datetime(x.session.unique()).sort_values();gaps=dates.to_series().diff().dt.days.dropna()
        raw[h]={'n':n,'mean_net_usd':round(mean,2),'net_usd':round(total,2),'pf':round(profits/losses,3) if losses>0 else None,'ci90':[round(float(z),2) for z in np.quantile(boot,[.05,.95])],'ci95':[round(float(z),2) for z in np.quantile(boot,[.025,.975])],'p_one_sided':p,'positive_years':posyrs,'by_year':year,'week_blocks':len(weeks),'mean_bracket_usd':round(float(bp.mean()),2),'bracket_pf':round(float(bpos/bneg),3) if bneg>0 else None,'bracket_net_usd':round(float(bp.sum()),2),'stop_count':int((x.bracket_reason=='STOP').sum()),'target_count':int((x.bracket_reason=='TARGET').sum()),'time_count':int((x.bracket_reason=='TIME').sum()),'stress_extra_tick_each_side_net_usd':round(total-10*n,2),'max_gap_days':int(gaps.max()) if len(gaps) else None,'gaps_gt7_days':int((gaps>7).sum())}
    q=bh(ps);holm_p=holm({k:min(1.,2*min(v,1.-v)) for k,v in ps.items()})
    for h,v in raw.items():
        v['q_bh6']=round(q[h],6);v['holm_p_approx_two_sided']=round(holm_p[h],6)
        if v['n']:
            gate={'N_gt150':v['n']>150,'positive_net':v['mean_net_usd']>0,'CI90_above_zero':v['ci90'][0]>0,'BH_q_le_010':q[h]<=.10,'positive_3_of_5_years':v['positive_years']>=3}
            v['gate1']=gate;v['decision']='PROMISING_EXPLORATORY' if all(gate.values()) else ('INSUFFICIENT_EVIDENCE' if v['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY')
    return raw

def main(zip_path,out,source_frozen):
    if not source_frozen:raise RuntimeError('Preregister & freeze all definitions BEFORE loading any development market prices')
    dates,days,overnight,qc=load_development(Path(zip_path))
    if len(dates)!=1221:raise RuntimeError('Unexpected NQ 2020-24 sessions, stopped')
    context=load_context(Path(zip_path))
    data=[]
    for t in range(20,len(dates)):
        result,atr=signals_for_day(t,dates,days,context)
        for h,(i,side) in result.items():
            entry=float(days[t,i+1,0]);exit30=float(days[t,i+31,0]);exit15=float(days[t,i+16,0]);pnlb,reason=bracket(days[t],i,side,entry,atr)
            d=dates[t];data.append({'session':d,'year':int(d[:4]),'hypothesis':h,'signal_idx':i,'side':side,'entry_open':entry,'exit30_open':exit30,'atr_prior':atr,'pnl30':round(side*(exit30-entry)*POINT-FRICTION,2),'pnl15':round(side*(exit15-entry)*POINT-FRICTION,2),'bracket_pnl':round(pnlb,2),'bracket_reason':reason,'week':str(pd.Timestamp(d).to_period('W-SUN'))})
    ev=pd.DataFrame(data,columns=['session','year','hypothesis','signal_idx','side','entry_open','exit30_open','atr_prior','pnl30','pnl15','bracket_pnl','bracket_reason','week'])
    out=Path(out);out.mkdir(parents=True,exist_ok=True);ev.to_csv(out/'NQ_H53_H58_EVENTS_2020_2024.csv',index=False)
    st=statistics(ev)
    result={'stage':'DEVELOPMENT_EXPLORATORY','experiment':'NQ-H53-H58','loaded_years':list(range(2020,2025)),'holdout_2025_loaded':False,'holdout_2026_loaded':False,'source_qc':qc,'context_61bar_sessions':len(context),'complete_rth_sessions':len(dates),'signal_events':len(ev),'fee_nq_free_rt':FEE,'adverse_slippage_rt':SLIP_RT,'friction_rt':FRICTION,'bracket_method':'stop 0.15 prior median RTH range, take 1.5x stop, time 30m, stop first on OHLC tie; gap-worse stop; no tick fills','hypotheses':st,'warnings':['Reused DEV 2020-24 is not independent validation','Date/signal overlap across hypotheses','Contract and minute OHLC data, no quote-level execution','MNQ transfer and funded costs not tested','No 2025/26 opened']}
    (out/'NQ_H53_H58_REPORT_2020_2024.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    family={'stage':'DEVELOPMENT_EXPLORATORY','loaded_years':list(range(2020,2025)),'holdout_2025_loaded':False,'holdout_2026_loaded':False,'family_metrics':{k:{'status':'ESTIMATED' if v['n'] else 'NOT_ESTIMABLE','effect':v.get('mean_net_usd',0),'p_value_two_sided':min(1.,2*min(v['p_one_sided'],1-v['p_one_sided']))} for k,v in st.items()}}
    (out/'nq_h53_h58_family.json').write_text(json.dumps(family,indent=2)+'\n')
    print(json.dumps({'events':len(ev),'counts':{h:x['n'] for h,x in st.items()},'gate1_pass':[h for h,x in st.items() if x['decision']=='PROMISING_EXPLORATORY']},indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--zip',required=True);a.add_argument('--out',required=True);a.add_argument('--source-frozen',action='store_true');x=a.parse_args();main(x.zip,x.out,x.source_frozen)