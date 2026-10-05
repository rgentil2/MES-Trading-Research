from __future__ import annotations

from pathlib import Path
import re
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

MES_POINT_VALUE=5.0
COST_POINTS=4.38/MES_POINT_VALUE
TICK_SIZE=0.25
WINDOWS=(10,30,60,120)
RTH_START_LABEL=571
RTH_END_LABEL=960
OR_BARS=15
LAST_EVENT_MINUTE=11*60+24
RNG=np.random.default_rng(42)


def read_nt_minute(path, contract):
    x=pd.read_csv(path,sep=';',header=None,names=['timestamp_utc','open','high','low','close','volume'])
    x['timestamp_utc']=pd.to_datetime(x['timestamp_utc'],format='%Y%m%d %H%M%S',errors='raise',utc=True)
    for c in ['open','high','low','close','volume']:
        x[c]=pd.to_numeric(x[c],errors='coerce')
    x=x.dropna().copy()
    x['contract']=contract
    x['timestamp_et']=x['timestamp_utc'].dt.tz_convert('America/New_York')
    x['date']=x['timestamp_et'].dt.date.astype(str)
    x['minute']=x['timestamp_et'].dt.hour*60+x['timestamp_et'].dt.minute
    return x


def stitch_mes_2024():
    files=[]
    for p in Path('data/raw').glob('MES *.Last.txt'):
        m=re.search(r'MES (\d{2})-(\d{2})',p.name)
        if not m: continue
        mm,yy=int(m.group(1)),2000+int(m.group(2))
        if yy==2024: files.append((yy,mm,p))
    files.sort()
    parts=[]; prev_end=None
    for yy,mm,p in files:
        raw=read_nt_minute(p,f'MES_{mm:02d}-{yy%100:02d}')
        raw_end=raw['timestamp_utc'].max()
        if prev_end is not None:
            raw=raw[raw['timestamp_utc']>prev_end].copy()
        parts.append(raw); prev_end=raw_end
    return pd.concat(parts,ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc',keep='last')


def strict_sessions(x):
    r=x[(x['minute']>=RTH_START_LABEL)&(x['minute']<=RTH_END_LABEL)].sort_values('timestamp_utc')
    prov=[]
    for d,g in r.groupby('date',sort=True):
        if len(g)<390: continue
        g=g.iloc[:390].reset_index(drop=True)
        if g['contract'].nunique()!=1: continue
        prov.append((d,g,g['contract'].iloc[0]))
    out={}; prev=None
    for d,g,c in prov:
        if prev is not None and c!=prev:
            prev=c
            continue
        out[d]=g; prev=c
    return out


def build_events(sessions):
    rows=[]
    for d,g in sessions.items():
        org=g.iloc[:OR_BARS]
        if len(org)<OR_BARS: continue
        orh=float(org.high.max()); orl=float(org.low.min())
        hit=None
        for i in range(OR_BARS,len(g)):
            row=g.iloc[i]
            if int(row.minute)>LAST_EVENT_MINUTE: break
            if row.close>orh: hit=(i,1); break
            if row.close<orl: hit=(i,-1); break
        if hit is None: continue
        i,direction=hit
        if i+60>=len(g): continue
        entry=float(g.iloc[i+1].open)
        ex15=float(g.iloc[i+15].close)
        ex30=float(g.iloc[i+30].close)
        ex60=float(g.iloc[i+60].close)
        rows.append({
            'date':d,'event_ts_utc':g.iloc[i].timestamp_utc,'event_ts_et':g.iloc[i].timestamp_et,
            'direction':direction,'entry':entry,
            'gross15_points':direction*(ex15-entry),
            'gross30_points':direction*(ex30-entry),
            'gross60_points':direction*(ex60-entry),
            'net30_points':direction*(ex30-entry)-COST_POINTS,
            'gross30_bps':direction*(ex30/entry-1)*10000,
            'profitable30':int(direction*(ex30-entry)-COST_POINTS>0),
        })
    return pd.DataFrame(rows)


def parse_tick_timestamp(s: pd.Series) -> pd.Series:
    # NinjaTrader formats observed in exports are YYYYMMDD HHMMSS plus optional
    # fractional digits separated by whitespace or punctuation.
    s=s.astype(str).str.strip()
    base=pd.to_datetime(s.str.slice(0,15),format='%Y%m%d %H%M%S',errors='coerce',utc=True)
    frac=s.str.slice(15).str.replace(r'\D','',regex=True).str.slice(0,9)
    frac=frac.str.pad(9,side='right',fillchar='0').replace('', '0')
    ns=pd.to_numeric(frac,errors='coerce').fillna(0).astype('int64')
    return base+pd.to_timedelta(ns,unit='ns')


def file_edge_lines(path: Path):
    with open(path,'rb') as f:
        first=f.readline().decode('utf-8-sig','replace').strip()
        f.seek(0,2); size=f.tell()
        pos=max(size-65536,0); f.seek(pos)
        tail=f.read().decode('utf-8','replace').splitlines()
        last=tail[-1].strip() if tail else ''
    return first,last


def extract_event_ticks(path: Path, events: pd.DataFrame):
    starts=(events.event_ts_utc-pd.to_timedelta(120,unit='s')).astype('int64').to_numpy()
    ends=events.event_ts_utc.astype('int64').to_numpy()
    buckets=[[] for _ in range(len(events))]
    names=['timestamp','last','bid','ask','volume']
    total_rows=0
    for chunk in pd.read_csv(path,sep=';',header=None,names=names,usecols=[0,1,2,3,4],
                             dtype={'timestamp':'string','last':'float64','bid':'float64','ask':'float64','volume':'float64'},
                             chunksize=1_000_000,engine='c'):
        total_rows+=len(chunk)
        ts=parse_tick_timestamp(chunk['timestamp'])
        valid=ts.notna()
        if not valid.any(): continue
        chunk=chunk.loc[valid].copy()
        ts=ts.loc[valid]
        ns=ts.astype('int64').to_numpy()
        if len(ns)==0: continue
        cmin,cmax=int(ns.min()),int(ns.max())
        chunk['_ts']=ts
        # File is expected sorted; numpy search on sorted timestamp vector.
        order=np.argsort(ns,kind='stable')
        if not np.all(order==np.arange(len(order))):
            chunk=chunk.iloc[order].reset_index(drop=True)
            ns=ns[order]
        for j,(st,en) in enumerate(zip(starts,ends)):
            if en<cmin or st>cmax: continue
            lo=np.searchsorted(ns,st,side='left')
            hi=np.searchsorted(ns,en,side='right')
            if hi>lo:
                buckets[j].append(chunk.iloc[lo:hi][['_ts','last','bid','ask','volume']].copy())
    out=[]
    for pieces in buckets:
        out.append(pd.concat(pieces,ignore_index=True) if pieces else pd.DataFrame(columns=['_ts','last','bid','ask','volume']))
    return out,total_rows


def window_features(t: pd.DataFrame, direction: int, seconds: int, end_ts: pd.Timestamp):
    start=end_ts-pd.Timedelta(seconds=seconds)
    z=t[(t['_ts']>start)&(t['_ts']<=end_ts)].copy()
    p=f'w{seconds}_'
    if z.empty:
        return {p+k:np.nan for k in ['volume','trades','trades_per_sec','volume_per_sec','buy_volume','sell_volume',
            'delta','norm_delta','aligned_norm_delta','mean_size','max_size','spread_mean_ticks','spread_p90_ticks',
            'displacement_ticks','aligned_displacement_ticks','path_ticks','path_eff','price_impact','delta_impact_mismatch']}
    last=z['last'].to_numpy(float); bid=z['bid'].to_numpy(float); ask=z['ask'].to_numpy(float); vol=z['volume'].to_numpy(float)
    valid_quote=np.isfinite(bid)&np.isfinite(ask)&(ask>=bid)&(ask>0)
    buy=valid_quote&(last>=ask)
    sell=valid_quote&(last<=bid)&~buy
    buyv=float(vol[buy].sum()); sellv=float(vol[sell].sum()); classified=buyv+sellv
    delta=buyv-sellv
    norm=delta/classified if classified>0 else np.nan
    aligned_norm=direction*norm if np.isfinite(norm) else np.nan
    spread=(ask[valid_quote]-bid[valid_quote])/TICK_SIZE
    disp=(last[-1]-last[0])/TICK_SIZE if len(last)>=2 else 0.0
    path=float(np.abs(np.diff(last)).sum()/TICK_SIZE) if len(last)>=2 else 0.0
    aligned_disp=direction*disp
    return {
        p+'volume':float(np.nansum(vol)),
        p+'trades':len(z),
        p+'trades_per_sec':len(z)/seconds,
        p+'volume_per_sec':float(np.nansum(vol))/seconds,
        p+'buy_volume':buyv,p+'sell_volume':sellv,p+'delta':delta,p+'norm_delta':norm,
        p+'aligned_norm_delta':aligned_norm,p+'mean_size':float(np.nanmean(vol)),p+'max_size':float(np.nanmax(vol)),
        p+'spread_mean_ticks':float(np.nanmean(spread)) if len(spread) else np.nan,
        p+'spread_p90_ticks':float(np.nanpercentile(spread,90)) if len(spread) else np.nan,
        p+'displacement_ticks':disp,p+'aligned_displacement_ticks':aligned_disp,p+'path_ticks':path,
        p+'path_eff':abs(disp)/path if path>0 else 0.0,
        p+'price_impact':aligned_disp/max(classified,1.0),
        p+'delta_impact_mismatch':aligned_norm/max(abs(aligned_disp),1.0) if np.isfinite(aligned_norm) else np.nan,
    }


def cross_features(t, direction, end_ts, feats):
    out={}
    a=feats.get('w10_trades_per_sec',np.nan); b=feats.get('w60_trades_per_sec',np.nan)
    out['accel_trades_10_60']=a/b if np.isfinite(a) and np.isfinite(b) and b>0 else np.nan
    a=feats.get('w10_volume_per_sec',np.nan); b=feats.get('w60_volume_per_sec',np.nan)
    out['accel_volume_10_60']=a/b if np.isfinite(a) and np.isfinite(b) and b>0 else np.nan
    z=t[(t['_ts']>end_ts-pd.Timedelta(seconds=60))&(t['_ts']<=end_ts)].copy()
    persist=[]
    for k in range(6):
        hi=end_ts-pd.Timedelta(seconds=k*10)
        lo=hi-pd.Timedelta(seconds=10)
        q=z[(z['_ts']>lo)&(z['_ts']<=hi)]
        if q.empty: continue
        last=q['last'].to_numpy(float); bid=q['bid'].to_numpy(float); ask=q['ask'].to_numpy(float); vol=q['volume'].to_numpy(float)
        valid=np.isfinite(bid)&np.isfinite(ask)&(ask>=bid)&(ask>0)
        buy=valid&(last>=ask); sell=valid&(last<=bid)&~buy
        delta=float(vol[buy].sum()-vol[sell].sum())
        persist.append(direction*delta>0)
    out['delta_persistence_60']=float(np.mean(persist)) if persist else np.nan
    if not z.empty:
        last=z['last'].to_numpy(float); bid=z['bid'].to_numpy(float); ask=z['ask'].to_numpy(float)
        valid=np.isfinite(bid)&np.isfinite(ask)&(ask>=bid)&(ask>0)
        buy=valid&(last>=ask); sell=valid&(last<=bid)&~buy
        denom=int(buy.sum()+sell.sum())
        raw=(buy.sum()-sell.sum())/denom if denom>0 else np.nan
        out['quote_pressure_aligned_60']=direction*raw if np.isfinite(raw) else np.nan
    else: out['quote_pressure_aligned_60']=np.nan
    z120=t[(t['_ts']>end_ts-pd.Timedelta(seconds=120))&(t['_ts']<=end_ts)]
    if len(z120):
        sizes=z120['volume'].to_numpy(float)
        thr=np.nanpercentile(sizes,90)
        tot=np.nansum(sizes)
        out['large_trade_share_120']=float(np.nansum(sizes[sizes>=thr])/tot) if tot>0 else np.nan
    else: out['large_trade_share_120']=np.nan
    return out


def bootstrap_median_diff(xw,xl,B=3000):
    xw=np.asarray(xw,float); xl=np.asarray(xl,float)
    xw=xw[np.isfinite(xw)]; xl=xl[np.isfinite(xl)]
    if len(xw)<5 or len(xl)<5: return np.nan,np.nan,np.nan
    obs=float(np.median(xw)-np.median(xl))
    vals=np.empty(B)
    for i in range(B):
        vals[i]=np.median(RNG.choice(xw,len(xw),replace=True))-np.median(RNG.choice(xl,len(xl),replace=True))
    return obs,float(np.percentile(vals,2.5)),float(np.percentile(vals,97.5))


def loo_logistic_auc(df, features):
    X=df[features].replace([np.inf,-np.inf],np.nan)
    y=df['profitable30'].astype(int).to_numpy()
    preds=np.full(len(df),np.nan)
    for i in range(len(df)):
        train=np.arange(len(df))!=i
        if len(np.unique(y[train]))<2: continue
        pipe=Pipeline([
            ('imp',SimpleImputer(strategy='median')),
            ('sc',StandardScaler()),
            ('lr',LogisticRegression(C=1.0,max_iter=5000,random_state=42))
        ])
        pipe.fit(X.iloc[train],y[train])
        preds[i]=pipe.predict_proba(X.iloc[[i]])[0,1]
    ok=np.isfinite(preds)
    return float(roc_auc_score(y[ok],preds[ok])) if ok.sum()>=10 and len(np.unique(y[ok]))==2 else np.nan


def main():
    mes=stitch_mes_2024()
    events=build_events(strict_sessions(mes))
    tick_path=Path('data_es_staging/raw_lfs/ES_MAR24/ES_MAR24_Tick_Last.txt')
    first,last=file_edge_lines(tick_path)
    print('FIRST_LINE',first)
    print('LAST_LINE',last)
    # Determine file coverage from edge lines.
    first_ts=parse_tick_timestamp(pd.Series([first.split(';')[0]])).iloc[0]
    last_ts=parse_tick_timestamp(pd.Series([last.split(';')[0]])).iloc[0]
    print('TICK_COVERAGE_UTC',first_ts,last_ts)
    eligible=events[(events.event_ts_utc>=first_ts+pd.Timedelta(seconds=120))&(events.event_ts_utc<=last_ts)].copy().reset_index(drop=True)
    print('MES_EVENTS_IN_TICK_COVERAGE',len(eligible))
    ticks,total_rows=extract_event_ticks(tick_path,eligible)
    print('TICK_ROWS_SCANNED',total_rows)

    feature_rows=[]
    for i,row in eligible.iterrows():
        t=ticks[i]
        f={}
        for w in WINDOWS:
            f.update(window_features(t,int(row.direction),w,row.event_ts_utc))
        f.update(cross_features(t,int(row.direction),row.event_ts_utc,f))
        f['tick_count_120']=len(t)
        feature_rows.append(f)
    feat=pd.DataFrame(feature_rows)
    data=pd.concat([eligible,feat],axis=1)
    data=data[data['tick_count_120']>0].reset_index(drop=True)
    feature_cols=[c for c in feat.columns if c!='tick_count_120']

    rows=[]
    y=data.profitable30.astype(int)
    for c in feature_cols:
        x=pd.to_numeric(data[c],errors='coerce')
        ok=x.notna()
        if ok.sum()<10 or y[ok].nunique()<2:
            continue
        auc=float(roc_auc_score(y[ok],x[ok]))
        auc_abs=max(auc,1-auc)
        obs,lo,hi=bootstrap_median_diff(x[(y==1)&ok],x[(y==0)&ok])
        rows.append({
            'feature':c,'n':int(ok.sum()),'auc_raw':auc,'auc_abs':auc_abs,
            'winner_median':float(x[(y==1)&ok].median()),'loser_median':float(x[(y==0)&ok].median()),
            'winner_minus_loser_median':obs,'boot95_lo':lo,'boot95_hi':hi,
            'ci_excludes_zero':bool(np.isfinite(lo) and np.isfinite(hi) and (lo>0 or hi<0))
        })
    uni=pd.DataFrame(rows).sort_values('auc_abs',ascending=False)
    auc_loo=loo_logistic_auc(data,feature_cols) if len(data)>=20 else np.nan
    strong=uni[uni.auc_abs>=0.60]
    strong_ci=strong[strong.ci_excludes_zero]
    top=uni.iloc[0] if len(uni) else None
    gate={
        'n_events_ge_35':len(data)>=35,
        'two_features_auc_ge_060':len(strong)>=2,
        'one_strong_feature_ci_excludes_zero':len(strong_ci)>=1,
        'loo_logistic_auc_ge_060':bool(np.isfinite(auc_loo) and auc_loo>=0.60),
    }
    # <=3-event domination guard: top feature must retain AUC >=.58 after dropping
    # the three most extreme absolute observations.
    robust=False
    if top is not None:
        c=top.feature
        z=data[[c,'profitable30']].dropna().copy()
        if len(z)>=15:
            center=z[c].median()
            z=z.assign(dev=(z[c]-center).abs()).sort_values('dev',ascending=False).iloc[3:]
            if z.profitable30.nunique()==2:
                a=roc_auc_score(z.profitable30,z[c])
                robust=max(a,1-a)>=0.58
    gate['strongest_not_driven_by_3_extremes']=robust
    passes=all(gate.values())

    summary=pd.DataFrame([{
        'tick_first_utc':first_ts,'tick_last_utc':last_ts,
        'eligible_events':len(data),'winners':int(data.profitable30.sum()),'losers':int((1-data.profitable30).sum()),
        'base_net30_mean_points':float(data.net30_points.mean()) if len(data) else np.nan,
        'base_gross30_bps':float(data.gross30_bps.mean()) if len(data) else np.nan,
        'loo_logistic_auc':auc_loo,
        'n_features_auc_ge_060':len(strong),
        'n_strong_features_ci_excludes_zero':len(strong_ci),
        'top_feature':top.feature if top is not None else None,
        'top_feature_auc_abs':top.auc_abs if top is not None else np.nan,
        **gate,'passes_feasibility_gate':passes
    }])

    out=Path('results/mes_v2_tick_2024')
    out.mkdir(parents=True,exist_ok=True)
    data.to_csv(out/'events_tick_features.csv',index=False)
    uni.to_csv(out/'univariate_features.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)

    print('\n=== SUMMARY ===')
    print(summary.T.to_string(header=False))
    print('\n=== TOP 15 FEATURES ===')
    print(uni.head(15).round(5).to_string(index=False))
    print('\n=== STRONG AUC>=0.60 ===')
    print(strong.round(5).to_string(index=False) if len(strong) else 'NONE')
    print('\nFEASIBILITY GATE:', 'PASS' if passes else 'FAIL')

if __name__=='__main__':
    main()

# trigger tick feasibility run
