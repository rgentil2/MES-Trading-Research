#!/usr/bin/env python3
"""NQ H05-H07: three pre-registered exploratory mechanisms; 2020-24 DEV only.

Never opens ZIP members containing 2025/2026 market bars. No post-hoc tuning.
Uses cached in-memory 1-minute NQ bars; no SL/TP; NOT trading strategies.
"""
from __future__ import annotations
import argparse, json, re, zipfile
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

DEV_RE=re.compile(r'^NQ_(03|06|09|12)-(20|21|22|23|24|25)_20(20|21|22|23|24)_Minute_Last[.]txt$')
TICK=.25
NQ_POINT_VALUE=20.0
FREE_FEE_RT=5.74
SLIPPAGE_EACH_SIDE_TICKS=2
FRICTION=FREE_FEE_RT+2*SLIPPAGE_EACH_SIDE_TICKS*TICK*NQ_POINT_VALUE
SEED=20261009
ITER=10000


def roll_contract(d: date)->str:
    for mo in (3,6,9,12):
        first=date(d.year,mo,1)
        third=first+timedelta(days=(4-first.weekday())%7+14)
        if d < third-timedelta(days=8):
            return f'NQ_{mo:02d}-{d.year%100:02d}'
    return f'NQ_03-{(d.year+1)%100:02d}'


def permitted_name(member: str)->bool:
    # Require a known development directory AND restrict the complete filename.
    return '/development_2020_2024/' in member and bool(DEV_RE.fullmatch(member.rsplit('/',1)[-1]))


def load_development(zip_path:Path):
    rth_parts=[]; overnight_parts=[]
    with zipfile.ZipFile(zip_path) as z:
        members=sorted(n for n in z.namelist() if permitted_name(n))
        if len(members)!=25:
            raise ValueError(f'25 NQ development files required, found {len(members)}')
        for idx,member in enumerate(members):
            mo, expiry, byear=DEV_RE.fullmatch(member.rsplit('/',1)[-1]).groups()
            contract=f'NQ_{mo}-{expiry}'
            # Crucial: only development member is ever opened here.
            with z.open(member) as f:
                data=pd.read_csv(f,sep=';',header=None,
                    names=['utc','open','high','low','close','volume'],dtype={'utc':'string'})
            timestamps=pd.to_datetime(data.utc,format='%Y%m%d %H%M%S',utc=True)
            if not bool((timestamps.dt.year==(2000+int(byear))).all()):
                raise ValueError('Wrong calendar year in development: '+member)
            et=timestamps.dt.tz_convert('America/New_York')
            minute=et.dt.hour*60+et.dt.minute
            rth=minute.between(571,960)
            overnight=(minute>=1081)|(minute<=570)
            keep=rth|overnight
            if not bool(keep.any()):continue
            data=data.loc[keep,['open','high','low','close','volume']].copy()
            t=et.loc[keep]
            m=minute.loc[keep]
            day=t.dt.tz_localize(None).dt.normalize()
            session=day+pd.to_timedelta((m>=1081).astype('int8'),unit='D')
            data['session']=session.dt.strftime('%Y-%m-%d').values
            data['minute']=m.to_numpy()
            data['rth']=rth.loc[keep].to_numpy()
            # Filtering by session / contract does not open future data; it also
            # prevents adjacent-quarter overlaps from contaminating the signal.
            data=data[data.session.str.slice(0,4).isin(('2020','2021','2022','2023','2024'))]
            eligible={d for d in data.session.unique() if roll_contract(date.fromisoformat(d))==contract}
            data=data[data.session.isin(eligible)]
            if data.empty:continue
            a=data[data.rth]
            if not a.empty:rth_parts.append(a[['session','minute','open','high','low','close','volume']])
            b=data[~data.rth]
            if not b.empty:
                overnight_parts.append(b.groupby('session').agg(on_count=('minute','size'),on_high=('high','max'),on_low=('low','min')))
            if idx%5==4:print('Read allowed NQ DEV partition:',idx+1,'/25',flush=True)
    if not rth_parts:raise ValueError('No RTH records in development')
    rth=pd.concat(rth_parts,ignore_index=True)
    ov=pd.concat(overnight_parts) if overnight_parts else pd.DataFrame()
    if not ov.empty and ov.index.duplicated().any():raise ValueError('Overlapping overnight contracts')
    grouped=rth.groupby('session',sort=True)
    d=grouped.agg(n=('minute','size'),n_unique=('minute','nunique'),first=('minute','min'),last=('minute','max'))
    full=d.index[(d.n==390)&(d.n_unique==390)&(d['first']==571)&(d['last']==960)]
    dates=[];arr=[]
    for day,grp in rth[rth.session.isin(full)].groupby('session',sort=True):
        g=grp.sort_values('minute')
        if not np.array_equal(g.minute.to_numpy(),np.arange(571,961)):
            raise ValueError('Incomplete RTH: '+day)
        a=g[['open','high','low','close','volume']].to_numpy(float)
        if a.shape!=(390,5):raise ValueError('Bad RTH shape')
        dates.append(day);arr.append(a)
    if len(dates)<1100:raise ValueError('Unexpectedly short RTH history')
    return dates,np.stack(arr),ov,{'total_full_rth_sessions':len(dates),
                    'original_development_nq_partitions':len(members),
                    'holdouts_opened':False,'excluded_partial_rth_sessions':len(d)-len(full)}


def choose_h05(bar:np.ndarray,prior_hi:float,prior_lo:float):
    _,hi,lo,close,_=bar
    up=hi>=prior_hi+TICK and close<prior_hi
    down=lo<=prior_lo-TICK and close>prior_lo
    if up and down:return 0  # ambig => consumed, no outcome
    return -1 if up else (1 if down else None)


def choose_h06(a:np.ndarray,i:int,prior_hi:float,prior_lo:float,volume_median:float):
    if a[i,4]<1.25*volume_median:return None
    up=(a[i-1,3]>prior_hi and a[i,3]>prior_hi)
    down=(a[i-1,3]<prior_lo and a[i,3]<prior_lo)
    return 1 if up else (-1 if down else None)


def choose_h07(a:np.ndarray,on_high:float,on_low:float):
    # First overnight extreme break from 09:31 onward consumes this session.
    for i in range(0,90):
        up=a[i,1]>=on_high+TICK
        down=a[i,2]<=on_low-TICK
        if not (up or down):continue
        if (up and down) or i<15 or i>86:return None
        for j in range(i,min(i+4,90)):
            if up and a[j,3]<on_high:return (j,-1)
            if down and a[j,3]>on_low:return (j,1)
        return None
    return None


def signals(dates:list[str],rth:np.ndarray,overnight:pd.DataFrame):
    rows=[]; exclusions={'H05_missing_or_stale_prior':0,'H07_insufficient_overnight':0}
    for k in range(20,len(dates)):
        day=dates[k];g=rth[k];previous=rth[k-1]
        age=(date.fromisoformat(day)-date.fromisoformat(dates[k-1])).days
        prior_ok=age<=5
        prior_hi=float(previous[:,1].max());prior_lo=float(previous[:,2].min())
        h05=None;h06=None;h07=None
        if prior_ok:
            for i in range(15,90):
                answer=choose_h05(g[i],prior_hi,prior_lo)
                if answer is not None:
                    h05=(i,answer) if answer else None
                    break
            historical_vol=np.median(rth[k-20:k,:,4],axis=0)
            for i in range(16,90):
                answer=choose_h06(g,i,prior_hi,prior_lo,historical_vol[i])
                if answer is not None:
                    h06=(i,answer);break
        else:
            exclusions['H05_missing_or_stale_prior']+=1
        if day in overnight.index:
            ov=overnight.loc[day]
            if int(ov.on_count)>=800:
                h07=choose_h07(g,float(ov.on_high),float(ov.on_low))
            else: exclusions['H07_insufficient_overnight']+=1
        else: exclusions['H07_insufficient_overnight']+=1
        for hyp,event in (('NQ-H05',h05),('NQ-H06',h06),('NQ-H07',h07)):
            if event is None:continue
            i,side=event
            if i+31>=390:continue
            entry=float(g[i+1,0]);close15=float(g[i+16,0]);close30=float(g[i+31,0])
            pnl30=(close30-entry)*side*NQ_POINT_VALUE-FRICTION
            pnl15=(close15-entry)*side*NQ_POINT_VALUE-FRICTION
            rows.append({'session':day,'year':int(day[:4]),'hypothesis':hyp,
                         'signal_time_et':f'{(571+i)//60:02d}:{(571+i)%60:02d}',
                         'side':'LONG' if side==1 else 'SHORT','entry_open':entry,
                         'exit_30m_open':close30,'net_30m_usd':round(pnl30,2),
                         'net_15m_usd':round(pnl15,2),
                         'gross_30m_points':round((close30-entry)*side,4),
                         'week':str(pd.Timestamp(day).to_period('W-SUN'))})
    return pd.DataFrame(rows,columns=['session','year','hypothesis','signal_time_et','side','entry_open','exit_30m_open',
                                      'net_30m_usd','net_15m_usd','gross_30m_points','week']),exclusions


def bh(pvals:dict[str,float]):
    ordered=sorted(pvals,key=pvals.get);out={};m=len(ordered);q=1.
    for rank,key in reversed(list(enumerate(ordered,start=1))):
        q=min(q,m*pvals[key]/rank);out[key]=round(q,6)
    return out


def stats(events:pd.DataFrame):
    rng=np.random.default_rng(SEED)
    out={};pvals={}
    for h in ('NQ-H05','NQ-H06','NQ-H07'):
        x=events[events.hypothesis==h].copy()
        if x.empty:
            out[h]={'n':0,'decision':'INSUFFICIENT_EVIDENCE','p_one_sided':1.,'q_h05_h07':None};pvals[h]=1.;continue
        pnl=x.net_30m_usd.to_numpy(float)
        grouped=x.groupby('week').net_30m_usd.agg(['sum','count']);w=grouped[['sum','count']].to_numpy(float)
        B=ITER;null_exceed=0;boot=[];seen=float(pnl.sum())
        for j in range(0,B,200):
            chunk=min(200,B-j)
            sign=rng.choice((-1.,1.),size=(chunk,len(w)))
            null_exceed+=int(np.count_nonzero((sign*w[:,0]).sum(axis=1)>=seen))
            ix=rng.integers(0,len(w),size=(chunk,len(w)))
            sampled=w[ix]
            boot.extend((sampled[:,:,0].sum(axis=1)/sampled[:,:,1].sum(axis=1)).tolist())
        p=(1+null_exceed)/(1+B);pvals[h]=p
        ci90=np.quantile(boot,[.05,.95]);ci95=np.quantile(boot,[.025,.975])
        yearly={str(y):{'events':int((x.year==y).sum()),
                        'net_usd':round(float(x.loc[x.year==y,'net_30m_usd'].sum()),2),
                        'mean_net_usd':round(float(x.loc[x.year==y,'net_30m_usd'].mean()),2) if (x.year==y).any() else None}
                for y in range(2020,2025)}
        years_pos=sum(v['mean_net_usd'] is not None and v['mean_net_usd']>0 for v in yearly.values())
        winning=pnl[pnl>0].sum();losing=-pnl[pnl<0].sum()
        days=pd.to_datetime(x.session.drop_duplicates().sort_values())
        gaps=days.diff().dt.days.dropna()
        out[h]={'n':len(x),'net_30m_usd':round(float(seen),2),
          'mean_30m_net_usd':round(float(pnl.mean()),2),
          'pf_30m':round(float(winning/losing),3) if losing>0 else None,
          'win_rate':round(float((pnl>0).mean()),4),
          'net_15m_usd':round(float(x.net_15m_usd.sum()),2),
          'net_stress_1_tick_extra_each_side_usd':round(float(seen-10*len(x)),2),
          'p_one_sided':round(float(p),6),
          'ci90_mean_net_usd':list(map(lambda z:round(float(z),2),ci90)),
          'ci95_mean_net_usd':list(map(lambda z:round(float(z),2),ci95)),
          'annual_positive_years':years_pos,'yearly':yearly,
          'gaps_gt_7_days':int((gaps>7).sum()),
          'max_gap_days':int(gaps.max()) if len(gaps) else 0,
          'weeks_for_inference':len(w)}
    adj=bh(pvals)
    prior={'NQ-H01':0.44831,'NQ-H02':0.20016,'NQ-H03':0.97640,'NQ-H04':1.0}
    historical=bh({**prior,**pvals})
    for h,v in out.items():
        v['q_h05_h07']=adj[h]
        v['q_accumulated_h01_h07_exploratory']=historical[h]
        if v['n']==0:continue
        v['gate1']={'N_gt_150':v['n']>150,'net_expectancy_positive':v['mean_30m_net_usd']>0,
         'CI90_above_zero':v['ci90_mean_net_usd'][0]>0,
         'BH_q_le_010':v['q_h05_h07']<=.10,
         'positive_years_ge_3_of_5':v['annual_positive_years']>=3,
         'no_post_hoc_rescue':True}
        v['decision']='PROMISING_EXPLORATORY' if all(v['gate1'].values()) else ('INSUFFICIENT_EVIDENCE' if v['n']<=150 else 'NOT_SUPPORTED_EXPLORATORY')
    return out,adj,historical


def main():
    cli=argparse.ArgumentParser(description='NQ-H05–H07 2020–24 DEV exploratory study ONLY')
    cli.add_argument('--zip',type=Path,required=True)
    cli.add_argument('--out',type=Path,default=Path('results/nq_h05_h07'))
    a=cli.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    dates,rth,ov,source=load_development(a.zip)
    events,exclusions=signals(dates,rth,ov)
    results,adj,historical=stats(events)
    report={'stage':'DEVELOPMENT_EXPLORATORY_2020_2024',
     'loaded_years':[2020,2021,2022,2023,2024],
     'holdout_2025_loaded':False,'holdout_2026_loaded':False,
     'source':source,'warmup_complete_sessions':20,
     'calendar_days_scored':len(dates)-20,
     'all_hypotheses_preregistered':True,
     'preregistration':'research/nq/NQ_PRICE_LEVEL_VOLUME_FAMILY_H05_H07_PREREG_2026_10_09.md',
     'account':'NinjaTrader Free; fee $5.74 RT plus $20 fixed modelled slippage; no stops/targets',
     'feature_exclusions':exclusions,
     'exploratory_fdr_H05_H07':adj,
     'exploratory_accumulated_fdr_H01_H07':historical,
     'results':results,
     'status':'DESCRIPTIVE_REUSED_DEVELOPMENT_ONLY_NO_OOS_CONFIRMATION',
     'limitations':['No stop loss or take profit and no tick-level fills',
       'No news filters', 'One NQ contract may exceed funded-account loss limit',
       'Calendar-week inference cannot remove accumulated development data reuse',
       'NQ/MNQ are correlated same-underlying contracts, not independent tests',
       '2025 and 2026 holdout prices never opened']}
    events.to_csv(a.out/'NQ_H05_H07_DEV_EVENTS_2020_2024.csv',index=False)
    (a.out/'NQ_H05_H07_DEV_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()