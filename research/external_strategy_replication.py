from __future__ import annotations

from pathlib import Path
import re, math
import numpy as np
import pandas as pd

START_YEAR, END_YEAR = 2020, 2024
COST_DOLLARS_RT = 4.38
MES_POINT_VALUE = 5.0
COST_POINTS = COST_DOLLARS_RT / MES_POINT_VALUE
TICK = 0.25
MONTHS = 60.0

def read_nt(p: Path, contract: str) -> pd.DataFrame:
    df = pd.read_csv(p, sep=';', header=None,
                     names=['timestamp_utc','open','high','low','close','volume'])
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], format='%Y%m%d %H%M%S')
    for c in ['open','high','low','close','volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().copy()
    df['contract'] = contract
    return df

def stitch_mes() -> pd.DataFrame:
    files=[]
    for p in Path('data/raw').glob('MES *.Last.txt'):
        m=re.search(r'MES (\d{2})-(\d{2})',p.name)
        if not m: continue
        mm, yy=int(m.group(1)), 2000+int(m.group(2))
        if START_YEAR <= yy <= END_YEAR:
            files.append((yy,mm,p))
    files.sort()
    parts=[]; prev_end=None
    for yy,mm,p in files:
        raw=read_nt(p,f'MES_{mm:02d}-{yy%100:02d}')
        raw_end=raw['timestamp_utc'].max()
        if prev_end is not None:
            raw=raw[raw['timestamp_utc']>prev_end].copy()
        parts.append(raw); prev_end=raw_end
    x=pd.concat(parts,ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc',keep='last')
    x['timestamp_utc']=x['timestamp_utc'].dt.tz_localize('UTC')
    x['timestamp_et']=x['timestamp_utc'].dt.tz_convert('America/New_York')
    x['date']=x['timestamp_et'].dt.date.astype(str)
    x['minute']=x['timestamp_et'].dt.hour*60+x['timestamp_et'].dt.minute
    return x

def rth_sessions(x: pd.DataFrame) -> dict[str,pd.DataFrame]:
    r=x[(x['minute']>570)&(x['minute']<=960)].copy().sort_values('timestamp_et')
    sessions={}
    for d,g in r.groupby('date',sort=True):
        g=g.sort_values('timestamp_et').copy()
        # Strict full RTH session only; avoids holidays/incomplete sessions.
        if len(g) < 390: continue
        g=g.iloc[:390].copy().reset_index(drop=True)
        sessions[d]=g
    return sessions

def tpo_value_area(g: pd.DataFrame, pct: float=0.70):
    # Prior-session 30-min TPO profile: 13 periods; each period contributes
    # one TPO to every 0.25-point price touched by its high-low range.
    counts={}
    for k in range(13):
        b=g.iloc[k*30:(k+1)*30]
        lo=math.floor(float(b['low'].min())/TICK)*TICK
        hi=math.ceil(float(b['high'].max())/TICK)*TICK
        n=int(round((hi-lo)/TICK))
        for i in range(n+1):
            p=round(lo+i*TICK,2)
            counts[p]=counts.get(p,0)+1
    if not counts: return np.nan,np.nan,np.nan
    prices=sorted(counts)
    vals=np.array([counts[p] for p in prices],dtype=float)
    mx=vals.max()
    tied=[i for i,v in enumerate(vals) if v==mx]
    midpoint=(float(g['high'].max())+float(g['low'].min()))/2
    poc_i=min(tied,key=lambda i: abs(prices[i]-midpoint))
    target=pct*vals.sum()
    included={poc_i}; total=vals[poc_i]
    lo_i=hi_i=poc_i
    while total < target and (lo_i>0 or hi_i<len(prices)-1):
        down=vals[lo_i-1] if lo_i>0 else -1
        up=vals[hi_i+1] if hi_i<len(prices)-1 else -1
        if up>=down:
            hi_i+=1; included.add(hi_i); total+=vals[hi_i]
        else:
            lo_i-=1; included.add(lo_i); total+=vals[lo_i]
    return prices[poc_i],prices[hi_i],prices[lo_i]

def path_exit(g, start_idx, direction, entry, stop, target, eod_idx=389):
    # Conservative ambiguity rule: if stop and target touch in same 1m bar,
    # count the stop first.
    for i in range(start_idx, min(eod_idx,len(g)-1)+1):
        b=g.iloc[i]
        if direction==1:
            if b['low']<=stop: return stop,i,'SL'
            if b['high']>=target: return target,i,'TP'
        else:
            if b['high']>=stop: return stop,i,'SL'
            if b['low']<=target: return target,i,'TP'
    return float(g.iloc[min(eod_idx,len(g)-1)]['close']),min(eod_idx,len(g)-1),'EOD'

def record(strategy,date,direction,entry,exit_price,exit_reason,extra=None):
    gross=direction*(exit_price-entry)
    net=gross-COST_POINTS
    row=dict(strategy=strategy,date=date,year=int(date[:4]),direction=direction,
             entry=entry,exit=exit_price,exit_reason=exit_reason,
             gross_points=gross,net_points=net,net_dollars=net*MES_POINT_VALUE)
    if extra: row.update(extra)
    return row

def test_overnight_reversal(sessions):
    # Academic relation: prior RTH close -> current RTH open return predicts
    # first 30m negatively. Literal sign strategy: fade overnight return,
    # enter 09:30 open, exit 10:00 close.
    rows=[]; dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]; pg=sessions[prev]
        prev_close=float(pg.iloc[-1]['close'])
        open_px=float(g.iloc[0]['open'])
        ov=open_px/prev_close-1
        if ov==0: continue
        direction=-1 if ov>0 else 1
        exit_px=float(g.iloc[29]['close']) # 09:30-10:00
        rows.append(record('Academic overnight reversal 09:30-10:00',d,direction,open_px,exit_px,'TIME',
                           {'signal':ov}))
    return rows

def test_intraday_momentum(sessions):
    # Gao et al. sign timing: first-half-hour return measured from prior close
    # predicts last half-hour. Enter 15:30, exit 16:00 in signal direction.
    rows=[]; dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]; pg=sessions[prev]
        prev_close=float(pg.iloc[-1]['close'])
        close_1000=float(g.iloc[29]['close'])
        sig=close_1000/prev_close-1
        if sig==0: continue
        direction=1 if sig>0 else -1
        entry=float(g.iloc[360]['open'])  # 15:30 open
        exit_px=float(g.iloc[-1]['close'])
        rows.append(record('Academic intraday momentum 15:30-16:00',d,direction,entry,exit_px,'TIME',
                           {'signal':sig}))
    return rows

def test_orb15_15m(sessions):
    # Public reproducible ORB spec:
    # 09:30-09:45 range; wait for a 15m candle close beyond range;
    # enter next 15m candle open if entry <12:00; SL opposite OR edge; TP 1.5R.
    rows=[]
    for d,g in sessions.items():
        orbar=g.iloc[:15]
        orh=float(orbar['high'].max()); orl=float(orbar['low'].min())
        # 15m groups after opening range: group 1 starts index15.
        chosen=None
        for group in range(1,10): # enough through noon
            s=group*15; e=s+15
            if e>len(g): break
            candle=g.iloc[s:e]
            c=float(candle.iloc[-1]['close'])
            direction=1 if c>orh else (-1 if c<orl else 0)
            if direction==0: continue
            entry_idx=e
            if entry_idx>=len(g): break
            # entry open time = 09:30 + entry_idx minutes; must be before noon
            entry_clock=570+entry_idx
            if entry_clock>=720: break
            chosen=(direction,entry_idx); break
        if chosen is None: continue
        direction,entry_idx=chosen
        entry=float(g.iloc[entry_idx]['open'])
        stop=orl if direction==1 else orh
        risk=abs(entry-stop)
        if risk<=0: continue
        target=entry+direction*1.5*risk
        exit_px,exit_idx,reason=path_exit(g,entry_idx,direction,entry,stop,target,389)
        rows.append(record('Public ORB15 SL=opposite edge TP=1.5R',d,direction,entry,exit_px,reason,
                           {'orh':orh,'orl':orl,'risk_points':risk,'target':target,'stop':stop}))
    return rows

def test_return_to_value(sessions):
    # NexusFi-style Open Outside Value -> Return to Value:
    # prior 70% TPO VA; open outside; first 30m remains fully outside;
    # second 30m closes inside; enter next minute open; target opposite VA edge;
    # stop 6 ticks beyond re-entry edge (midpoint of published 5-7 tick range).
    rows=[]; dates=sorted(sessions)
    levels={}
    for d,g in sessions.items():
        poc,vah,val=tpo_value_area(g)
        levels[d]=(poc,vah,val)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]
        _,vah,val=levels[prev]
        if not np.isfinite(vah): continue
        op=float(g.iloc[0]['open'])
        first=g.iloc[:30]; second=g.iloc[30:60]
        close2=float(second.iloc[-1]['close'])
        direction=0; edge=None; target=None
        if op>vah and float(first['low'].min())>vah and val<=close2<=vah:
            direction=-1; edge=vah; target=val
        elif op<val and float(first['high'].max())<val and val<=close2<=vah:
            direction=1; edge=val; target=vah
        if direction==0: continue
        entry_idx=60
        entry=float(g.iloc[entry_idx]['open'])
        stop=edge + (1.5 if direction==-1 else -1.5) # 6 ticks
        # Ensure stop lies on wrong side and target on favorable side.
        if direction==1 and not (stop<entry<target): continue
        if direction==-1 and not (target<entry<stop): continue
        exit_px,exit_idx,reason=path_exit(g,entry_idx,direction,entry,stop,target,389)
        rows.append(record('Market Profile return-to-value 6tick stop',d,direction,entry,exit_px,reason,
                           {'prev_vah':vah,'prev_val':val,'stop':stop,'target':target}))
    return rows

def metrics(df):
    if df.empty: return {}
    pos=df[df.net_points>0].net_points.sum()
    neg=-df[df.net_points<0].net_points.sum()
    pf=pos/neg if neg>0 else np.inf
    eq=df.sort_values('date').net_points.cumsum()
    dd=(eq-eq.cummax()).min()
    years=df.groupby('year').net_points.agg(['count','mean','sum'])
    return {
        'trades':len(df),'trades_per_month':len(df)/MONTHS,
        'gross_pts_trade':df.gross_points.mean(),'net_pts_trade':df.net_points.mean(),
        'net_dollars_trade':df.net_dollars.mean(),'win_rate':(df.net_points>0).mean(),
        'profit_factor_net':pf,'max_dd_points':dd,
        'positive_years':int((years['sum']>0).sum()),
        'year_detail':'; '.join(f"{y}:N{int(r['count'])},avg{r['mean']:.3f},sum{r['sum']:.1f}" for y,r in years.iterrows())
    }

def main():
    x=stitch_mes()
    sessions=rth_sessions(x)
    print('Full RTH sessions:',len(sessions))
    rows=[]
    rows += test_overnight_reversal(sessions)
    rows += test_intraday_momentum(sessions)
    rows += test_orb15_15m(sessions)
    rows += test_return_to_value(sessions)
    trades=pd.DataFrame(rows).sort_values(['strategy','date'])
    summary=[]
    for s,g in trades.groupby('strategy',sort=False):
        m=metrics(g)
        summary.append({'strategy':s,**m})
    summary=pd.DataFrame(summary)
    out=Path('results/external_strategy_replication')
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/'trades.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    pd.set_option('display.max_colwidth',120)
    print('\n=== EXTERNAL STRATEGY REPLICATION 2020-2024 ===')
    cols=['strategy','trades','trades_per_month','gross_pts_trade','net_pts_trade','net_dollars_trade','win_rate','profit_factor_net','max_dd_points','positive_years']
    print(summary[cols].round(3).to_string(index=False))
    print('\n=== YEAR DETAIL ===')
    for _,r in summary.iterrows():
        print(r['strategy'])
        print(' ',r['year_detail'])
    print('\nORB exits:', trades[trades.strategy.str.contains('ORB15')].exit_reason.value_counts().to_dict())
    print('Return-to-value exits:', trades[trades.strategy.str.contains('return-to-value')].exit_reason.value_counts().to_dict())

if __name__=='__main__':
    main()
