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

NEWS_CSV = Path("data_external/forexfactory/usd_high_medium_2020_2024.csv")


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
    x['bar_start_et']=x['timestamp_et']-pd.Timedelta(minutes=1)
    x['date']=x['timestamp_et'].dt.date.astype(str)
    x['minute']=x['timestamp_et'].dt.hour*60+x['timestamp_et'].dt.minute
    return x


def rth_sessions(x: pd.DataFrame) -> dict[str,pd.DataFrame]:
    r=x[(x['minute']>570)&(x['minute']<=960)].copy().sort_values('timestamp_et')
    sessions={}
    for d,g in r.groupby('date',sort=True):
        g=g.sort_values('timestamp_et').copy()
        if len(g) < 390: continue
        g=g.iloc[:390].copy().reset_index(drop=True)
        sessions[d]=g
    return sessions


def load_news():
    n=pd.read_csv(NEWS_CSV)
    n['event_et']=pd.to_datetime(n['event_et'],utc=True).dt.tz_convert('America/New_York')
    n['blackout_start_et']=pd.to_datetime(n['blackout_start_et'],utc=True).dt.tz_convert('America/New_York')
    n['blackout_end_et']=pd.to_datetime(n['blackout_end_et'],utc=True).dt.tz_convert('America/New_York')
    n['date_et']=n['event_et'].dt.date.astype(str)
    by_date={}
    for d,g in n.groupby('date_et',sort=True):
        by_date[d]=g.sort_values('event_et').reset_index(drop=True)
    return n,by_date


def entry_blocked(entry_time, news_day):
    if news_day is None or news_day.empty:
        return False, None
    m=(news_day['blackout_start_et']<=entry_time)&(entry_time<=news_day['blackout_end_et'])
    if not m.any(): return False,None
    row=news_day.loc[m].iloc[0]
    return True,row


def next_forced_exit(entry_time, news_day):
    if news_day is None or news_day.empty:
        return None
    # Position must already exist before T-5. If entry == cutoff, it would have been blocked.
    z=news_day[news_day['blackout_start_et']>entry_time]
    if z.empty: return None
    return z.iloc[0]


def price_at_cutoff(g, cutoff):
    # NinjaTrader timestamps are EOB. A bar with start == cutoff has label cutoff+1 minute.
    m=g['bar_start_et']==cutoff
    if m.any():
        idx=int(g.index[m][0])
        return float(g.loc[idx,'open']),idx
    # Fallback: first bar starting after cutoff, conservative and causal.
    z=g[g['bar_start_et']>cutoff]
    if z.empty:
        return None,None
    idx=int(z.index[0])
    return float(g.loc[idx,'open']),idx


def tpo_value_area(g: pd.DataFrame, pct: float=0.70):
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
    total=vals[poc_i]
    lo_i=hi_i=poc_i
    while total < target and (lo_i>0 or hi_i<len(prices)-1):
        down=vals[lo_i-1] if lo_i>0 else -1
        up=vals[hi_i+1] if hi_i<len(prices)-1 else -1
        if up>=down:
            hi_i+=1; total+=vals[hi_i]
        else:
            lo_i-=1; total+=vals[lo_i]
    return prices[poc_i],prices[hi_i],prices[lo_i]


def path_exit(g, start_idx, direction, entry, stop, target, news_day=None, apply_news=False, eod_idx=389):
    entry_time=g.iloc[start_idx]['bar_start_et']
    forced=next_forced_exit(entry_time,news_day) if apply_news else None
    cutoff=forced['blackout_start_et'] if forced is not None else None
    for i in range(start_idx,min(eod_idx,len(g)-1)+1):
        b=g.iloc[i]
        # Forced flat happens at bar open at T-5, before this minute's price path.
        if cutoff is not None and b['bar_start_et']>=cutoff:
            px,idx=price_at_cutoff(g,cutoff)
            if px is not None:
                return px,idx,'NEWS_EXIT',forced['event'],forced['impact']
        if direction==1:
            if b['low']<=stop: return stop,i,'SL',None,None
            if b['high']>=target: return target,i,'TP',None,None
        else:
            if b['high']>=stop: return stop,i,'SL',None,None
            if b['low']<=target: return target,i,'TP',None,None
    return float(g.iloc[min(eod_idx,len(g)-1)]['close']),min(eod_idx,len(g)-1),'EOD',None,None


def timed_exit(g, entry_idx, exit_idx, direction, entry, news_day=None, apply_news=False):
    entry_time=g.iloc[entry_idx]['bar_start_et']
    if apply_news:
        forced=next_forced_exit(entry_time,news_day)
        if forced is not None:
            cutoff=forced['blackout_start_et']
            scheduled_exit_time=g.iloc[exit_idx]['timestamp_et']  # close timestamp
            if cutoff < scheduled_exit_time:
                px,idx=price_at_cutoff(g,cutoff)
                if px is not None and idx<=exit_idx:
                    return px,idx,'NEWS_EXIT',forced['event'],forced['impact']
    return float(g.iloc[exit_idx]['close']),exit_idx,'TIME',None,None


def record(strategy,variant,date,direction,entry,exit_price,exit_reason,entry_time,
           news_event=None,news_impact=None,extra=None):
    gross=direction*(exit_price-entry)
    net=gross-COST_POINTS
    row=dict(strategy=strategy,variant=variant,date=date,year=int(date[:4]),direction=direction,
             entry_time_et=str(entry_time),entry=entry,exit=exit_price,exit_reason=exit_reason,
             news_event=news_event,news_impact=news_impact,
             gross_points=gross,net_points=net,net_dollars=net*MES_POINT_VALUE)
    if extra: row.update(extra)
    return row


def test_overnight_reversal(sessions,news_by_date,apply_news):
    rows=[]; blocked=0; dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]; pg=sessions[prev]
        prev_close=float(pg.iloc[-1]['close'])
        open_px=float(g.iloc[0]['open'])
        ov=open_px/prev_close-1
        if ov==0: continue
        entry_idx=0; entry_time=g.iloc[entry_idx]['bar_start_et']
        nd=news_by_date.get(d)
        if apply_news:
            blocked_flag,_=entry_blocked(entry_time,nd)
            if blocked_flag:
                blocked+=1; continue
        direction=-1 if ov>0 else 1
        exit_px,exit_idx,reason,nev,nimp=timed_exit(g,entry_idx,29,direction,open_px,nd,apply_news)
        rows.append(record('Academic overnight reversal 09:30-10:00','NEWS' if apply_news else 'BASE',
                           d,direction,open_px,exit_px,reason,entry_time,nev,nimp,{'signal':ov}))
    return rows,blocked


def test_intraday_momentum(sessions,news_by_date,apply_news):
    rows=[]; blocked=0; dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=sessions[d]; pg=sessions[prev]
        prev_close=float(pg.iloc[-1]['close'])
        close_1000=float(g.iloc[29]['close'])
        sig=close_1000/prev_close-1
        if sig==0: continue
        entry_idx=360; entry_time=g.iloc[entry_idx]['bar_start_et']
        nd=news_by_date.get(d)
        if apply_news:
            blocked_flag,_=entry_blocked(entry_time,nd)
            if blocked_flag:
                blocked+=1; continue
        direction=1 if sig>0 else -1
        entry=float(g.iloc[entry_idx]['open'])
        exit_px,exit_idx,reason,nev,nimp=timed_exit(g,entry_idx,389,direction,entry,nd,apply_news)
        rows.append(record('Academic intraday momentum 15:30-16:00','NEWS' if apply_news else 'BASE',
                           d,direction,entry,exit_px,reason,entry_time,nev,nimp,{'signal':sig}))
    return rows,blocked


def test_orb15(sessions,news_by_date,apply_news):
    rows=[]; blocked=0
    for d,g in sessions.items():
        orbar=g.iloc[:15]
        orh=float(orbar['high'].max()); orl=float(orbar['low'].min())
        chosen=None
        for group in range(1,10):
            s=group*15; e=s+15
            if e>len(g): break
            c=float(g.iloc[s:e].iloc[-1]['close'])
            direction=1 if c>orh else (-1 if c<orl else 0)
            if direction==0: continue
            entry_idx=e
            if entry_idx>=len(g): break
            entry_clock=570+entry_idx
            if entry_clock>=720: break
            chosen=(direction,entry_idx); break
        if chosen is None: continue
        direction,entry_idx=chosen
        entry_time=g.iloc[entry_idx]['bar_start_et']
        nd=news_by_date.get(d)
        if apply_news:
            blocked_flag,_=entry_blocked(entry_time,nd)
            if blocked_flag:
                blocked+=1; continue
        entry=float(g.iloc[entry_idx]['open'])
        stop=orl if direction==1 else orh
        risk=abs(entry-stop)
        if risk<=0: continue
        target=entry+direction*1.5*risk
        exit_px,exit_idx,reason,nev,nimp=path_exit(g,entry_idx,direction,entry,stop,target,nd,apply_news,389)
        rows.append(record('Public ORB15 SL=opposite edge TP=1.5R','NEWS' if apply_news else 'BASE',
                           d,direction,entry,exit_px,reason,entry_time,nev,nimp,
                           {'orh':orh,'orl':orl,'risk_points':risk,'target':target,'stop':stop}))
    return rows,blocked


def test_return_to_value(sessions,news_by_date,apply_news):
    rows=[]; blocked=0; dates=sorted(sessions); levels={}
    for d,g in sessions.items():
        levels[d]=tpo_value_area(g)
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
        entry_idx=60; entry_time=g.iloc[entry_idx]['bar_start_et']
        nd=news_by_date.get(d)
        if apply_news:
            blocked_flag,_=entry_blocked(entry_time,nd)
            if blocked_flag:
                blocked+=1; continue
        entry=float(g.iloc[entry_idx]['open'])
        stop=edge+(1.5 if direction==-1 else -1.5)
        if direction==1 and not (stop<entry<target): continue
        if direction==-1 and not (target<entry<stop): continue
        exit_px,exit_idx,reason,nev,nimp=path_exit(g,entry_idx,direction,entry,stop,target,nd,apply_news,389)
        rows.append(record('Market Profile return-to-value 6tick stop','NEWS' if apply_news else 'BASE',
                           d,direction,entry,exit_px,reason,entry_time,nev,nimp,
                           {'prev_vah':vah,'prev_val':val,'stop':stop,'target':target}))
    return rows,blocked


def metrics(df):
    if df.empty: return {}
    pos=df.loc[df.net_points>0,'net_points'].sum()
    neg=-df.loc[df.net_points<0,'net_points'].sum()
    pf=pos/neg if neg>0 else np.inf
    eq=df.sort_values(['date','entry_time_et']).net_points.cumsum()
    dd=(eq-eq.cummax()).min()
    years=df.groupby('year').net_points.agg(['count','mean','sum'])
    return {
        'trades':len(df),
        'trades_per_month':len(df)/MONTHS,
        'gross_pts_trade':df.gross_points.mean(),
        'net_pts_trade':df.net_points.mean(),
        'net_dollars_trade':df.net_dollars.mean(),
        'win_rate':(df.net_points>0).mean(),
        'profit_factor_net':pf,
        'max_dd_points':dd,
        'positive_years':int((years['sum']>0).sum()),
        'news_forced_exits':int((df.exit_reason=='NEWS_EXIT').sum()),
        'year_detail':'; '.join(f"{y}:N{int(r['count'])},avg{r['mean']:.3f},sum{r['sum']:.1f}" for y,r in years.iterrows())
    }


def main():
    if not NEWS_CSV.exists():
        raise RuntimeError(f'Missing {NEWS_CSV}; run calendar builder first.')
    _,news_by_date=load_news()
    x=stitch_mes(); sessions=rth_sessions(x)
    print('Full RTH sessions:',len(sessions))

    all_rows=[]; blocked_rows=[]
    tests=[
        ('overnight',test_overnight_reversal),
        ('intraday_momentum',test_intraday_momentum),
        ('orb15',test_orb15),
        ('return_to_value',test_return_to_value),
    ]
    for key,fn in tests:
        for apply in (False,True):
            rows,blocked=fn(sessions,news_by_date,apply)
            all_rows+=rows
            blocked_rows.append({'test':key,'variant':'NEWS' if apply else 'BASE','blocked_entries':blocked})
    trades=pd.DataFrame(all_rows)

    summaries=[]
    for (s,v),g in trades.groupby(['strategy','variant'],sort=True):
        summaries.append({'strategy':s,'variant':v,**metrics(g)})
    summary=pd.DataFrame(summaries)
    blocked=pd.DataFrame(blocked_rows)

    # BASE -> NEWS deltas
    wide=[]
    for s,g in summary.groupby('strategy'):
        b=g[g.variant=='BASE'].iloc[0]
        n=g[g.variant=='NEWS'].iloc[0]
        wide.append({
            'strategy':s,
            'base_trades':b.trades,'news_trades':n.trades,
            'trades_removed':int(b.trades-n.trades),
            'base_net_pts_trade':b.net_pts_trade,'news_net_pts_trade':n.net_pts_trade,
            'delta_net_pts_trade':n.net_pts_trade-b.net_pts_trade,
            'base_pf':b.profit_factor_net,'news_pf':n.profit_factor_net,
            'delta_pf':n.profit_factor_net-b.profit_factor_net,
            'base_dd':b.max_dd_points,'news_dd':n.max_dd_points,
            'base_positive_years':b.positive_years,'news_positive_years':n.positive_years,
            'news_forced_exits':n.news_forced_exits,
        })
    comparison=pd.DataFrame(wide)

    out=Path('results/news_filter_2020_2024')
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/'trades.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    comparison.to_csv(out/'comparison.csv',index=False)
    blocked.to_csv(out/'blocked_entries.csv',index=False)

    print('\n=== NEWS FILTER COMPARISON ===')
    print(comparison.round(4).to_string(index=False))
    print('\n=== YEAR DETAIL ===')
    for _,r in summary.iterrows():
        print(r['strategy'],r['variant'])
        print(' ',r['year_detail'])
    print('\n=== BLOCKED ENTRIES ===')
    print(blocked.to_string(index=False))

if __name__=='__main__':
    main()
