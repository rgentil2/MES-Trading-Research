from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone, timedelta
import math
import re
import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score

START_YEAR = 2023
END_YEAR = 2024
TARGET_YEAR = 2024
COST_DOLLARS_RT = 4.38
MES_POINT_VALUE = 5.0
COST_POINTS = COST_DOLLARS_RT / MES_POINT_VALUE
TICK_SIZE = 0.25
RTH_START_LABEL = 571
RTH_END_LABEL = 960
OR_BARS = 15
LAST_EVENT_MINUTE = 11 * 60 + 30

MICRO_FEATURES = [
    'aligned_delta_ratio_signal',
    'aligned_delta_ratio_prev',
    'delta_acceleration',
    'trades_per_second_signal',
    'trades_rate_ratio',
    'volume_per_second_signal',
    'volume_rate_ratio',
    'avg_trade_size_signal',
    'median_spread_ticks',
    'p95_spread_ticks',
    'aligned_es_price_change_ticks_signal',
    'price_impact_per_1000',
    'absorption_ratio',
    'aggression_persistence',
    'max_5s_aligned_delta_share',
    'classified_volume_fraction',
]

BASE_FEATURES = [
    'or_width_atr',
    'breakout_displacement_atr',
    'signal_body_eff',
    'signal_close_location_aligned',
    'mes_rvol',
    'es_rvol',
    'es_same_side_or',
]


def read_nt_minute(path: Path, contract: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';', header=None,
                     names=['timestamp_utc','open','high','low','close','volume'])
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], format='%Y%m%d %H%M%S', errors='raise')
    for c in ['open','high','low','close','volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().copy()
    df['contract'] = contract
    df['timestamp_utc'] = df['timestamp_utc'].dt.tz_localize('UTC')
    df['timestamp_et'] = df['timestamp_utc'].dt.tz_convert('America/New_York')
    df['date'] = df['timestamp_et'].dt.date.astype(str)
    df['minute'] = df['timestamp_et'].dt.hour * 60 + df['timestamp_et'].dt.minute
    return df


def stitch_mes() -> pd.DataFrame:
    files=[]
    for p in Path('data/raw').glob('MES *.Last.txt'):
        m=re.search(r'MES (\d{2})-(\d{2})', p.name)
        if not m:
            continue
        mm, yy=int(m.group(1)), 2000+int(m.group(2))
        if START_YEAR <= yy <= END_YEAR:
            files.append((yy,mm,p))
    files.sort()
    parts=[]; prev_end=None
    for yy,mm,p in files:
        raw=read_nt_minute(p,f'MES_{mm:02d}-{yy%100:02d}')
        raw_end=raw['timestamp_utc'].max()
        if prev_end is not None:
            raw=raw[raw['timestamp_utc']>prev_end].copy()
        parts.append(raw)
        prev_end=raw_end
    if not parts:
        raise RuntimeError('No MES files.')
    return pd.concat(parts,ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc',keep='last')


def strict_rth_sessions(df: pd.DataFrame) -> dict[str,pd.DataFrame]:
    r=df[(df['minute']>=RTH_START_LABEL)&(df['minute']<=RTH_END_LABEL)].copy()
    provisional=[]
    for d,g in r.groupby('date',sort=True):
        g=g.sort_values('timestamp_et')
        if len(g)<390:
            continue
        g=g.iloc[:390].copy().reset_index(drop=True)
        if g['contract'].nunique()!=1:
            continue
        provisional.append((d,g,g['contract'].iloc[0]))
    sessions={}; prev_contract=None
    for d,g,c in provisional:
        if prev_contract is not None and c!=prev_contract:
            prev_contract=c
            continue
        sessions[d]=g
        prev_contract=c
    return sessions


def daily_atr_map(sessions: dict[str,pd.DataFrame]) -> dict[str,float]:
    rows=[]
    for d,g in sessions.items():
        rows.append({'date':d,'high':g['high'].max(),'low':g['low'].min(),'close':g.iloc[-1]['close']})
    daily=pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    pc=daily['close'].shift(1)
    tr=pd.concat([
        daily['high']-daily['low'],
        (daily['high']-pc).abs(),
        (daily['low']-pc).abs()
    ],axis=1).max(axis=1)
    daily['atr14']=tr.shift(1).rolling(14,min_periods=14).mean()
    return dict(zip(daily['date'],daily['atr14']))


def add_rvol(sessions: dict[str,pd.DataFrame]) -> dict[str,pd.DataFrame]:
    all_rows=[]
    for d,g in sessions.items():
        z=g.copy()
        z['cum_volume']=z['volume'].cumsum()
        all_rows.append(z)
    x=pd.concat(all_rows,ignore_index=True)
    x=x.sort_values(['minute','timestamp_et'])
    x['vol_med20']=x.groupby('minute',observed=True)['volume'].transform(
        lambda s:s.shift(1).rolling(20,min_periods=10).median())
    x['rvol']=x['volume']/x['vol_med20']
    x=x.sort_values('timestamp_et')
    return {d:g.reset_index(drop=True) for d,g in x.groupby('date',sort=True)}


def build_events(mes_s, es_s, atr_map):
    rows=[]
    common=sorted(set(mes_s).intersection(es_s))
    for d in common:
        if int(d[:4]) != TARGET_YEAR:
            continue
        mg=mes_s[d]; eg=es_s[d]
        atr=atr_map.get(d,np.nan)
        if not np.isfinite(atr) or atr<=0:
            continue

        org=mg.iloc[:OR_BARS]
        if len(org)<OR_BARS:
            continue
        orh=float(org['high'].max()); orl=float(org['low'].min())
        hit=None
        for i in range(OR_BARS,len(mg)):
            row=mg.iloc[i]
            if int(row['minute'])>LAST_EVENT_MINUTE:
                break
            if row['close']>orh:
                hit=(i,1); break
            if row['close']<orl:
                hit=(i,-1); break
        if hit is None:
            continue
        i,direction=hit
        if i+30>=len(mg):
            continue
        signal=mg.iloc[i]
        entry=float(mg.iloc[i+1]['open'])
        exit30=float(mg.iloc[i+30]['close'])
        gross_pts=direction*(exit30-entry)
        net_pts=gross_pts-COST_POINTS
        gross_bps=direction*(exit30/entry-1.0)*10000

        ts=signal['timestamp_utc']
        esidx=eg.index[eg['timestamp_utc']==ts].tolist()
        if not esidx:
            continue
        ei=int(esidx[0])
        eorg=eg.iloc[:OR_BARS]
        if len(eorg)<OR_BARS:
            continue
        eorh=float(eorg['high'].max()); eorl=float(eorg['low'].min())
        es_same=(float(eg.iloc[ei]['close'])>eorh) if direction==1 else (float(eg.iloc[ei]['close'])<eorl)

        rng=float(signal['high']-signal['low'])
        body_eff=abs(float(signal['close']-signal['open']))/rng if rng>0 else np.nan
        close_loc=(float(signal['close']-signal['low'])/rng if direction==1
                   else float(signal['high']-signal['close'])/rng) if rng>0 else np.nan
        edge=orh if direction==1 else orl

        rows.append({
            'date':d,
            'signal_ts_utc':ts,
            'signal_ts_et':signal['timestamp_et'],
            'direction':direction,
            'profitable30':int(net_pts>0),
            'gross30_points':gross_pts,
            'net30_points':net_pts,
            'gross30_bps':gross_bps,
            'or_width_atr':(orh-orl)/atr,
            'breakout_displacement_atr':direction*(float(signal['close'])-edge)/atr,
            'signal_body_eff':body_eff,
            'signal_close_location_aligned':close_loc,
            'mes_rvol':float(signal.get('rvol',np.nan)),
            'es_rvol':float(eg.iloc[ei].get('rvol',np.nan)),
            'es_same_side_or':float(es_same),
        })
    return pd.DataFrame(rows).sort_values('signal_ts_utc').reset_index(drop=True)


def parse_tick_timestamp(raw: str) -> datetime:
    digits=''.join(ch for ch in raw if ch.isdigit())
    if len(digits)<14:
        raise ValueError(f'Bad tick timestamp: {raw!r}')
    base=digits[:14]
    frac=digits[14:]
    dt=datetime.strptime(base,'%Y%m%d%H%M%S')
    micro=int((frac+'000000')[:6]) if frac else 0
    return dt.replace(microsecond=micro,tzinfo=timezone.utc)


class Agg:
    def __init__(self, direction, start, end):
        self.direction=direction
        self.start=start
        self.end=end
        self.signal_start=end-timedelta(seconds=60)
        self.prev_start=end-timedelta(seconds=120)
        self.base_start=end-timedelta(seconds=360)
        self.sig={'n':0,'vol':0.0,'buy':0.0,'sell':0.0,'first':None,'last':None,'spreads':[],'buckets':[0.0]*12}
        self.prev={'n':0,'vol':0.0,'buy':0.0,'sell':0.0}
        self.base={'n':0,'vol':0.0}

    def add(self, ts, last, bid, ask, vol):
        if not (self.base_start <= ts < self.end):
            return
        if self.signal_start <= ts < self.end:
            seg=self.sig
            seg['n']+=1; seg['vol']+=vol
            if seg['first'] is None: seg['first']=last
            seg['last']=last
            spr=(ask-bid)/TICK_SIZE
            if np.isfinite(spr) and spr>=0 and spr<100:
                seg['spreads'].append(spr)
            sign=0
            if last>=ask:
                seg['buy']+=vol; sign=1
            elif last<=bid:
                seg['sell']+=vol; sign=-1
            bucket=int((ts-self.signal_start).total_seconds()//5)
            if 0<=bucket<12:
                seg['buckets'][bucket]+=self.direction*sign*vol
        elif self.prev_start <= ts < self.signal_start:
            seg=self.prev
            seg['n']+=1; seg['vol']+=vol
            if last>=ask: seg['buy']+=vol
            elif last<=bid: seg['sell']+=vol
        else:
            self.base['n']+=1; self.base['vol']+=vol

    def features(self):
        s,p,b=self.sig,self.prev,self.base
        class_s=s['buy']+s['sell']
        class_p=p['buy']+p['sell']
        net_s=s['buy']-s['sell']
        net_p=p['buy']-p['sell']
        adr_s=self.direction*net_s/class_s if class_s>0 else np.nan
        adr_p=self.direction*net_p/class_p if class_p>0 else np.nan
        signal_trade_rate=s['n']/60.0
        base_trade_rate=b['n']/300.0
        signal_vol_rate=s['vol']/60.0
        base_vol_rate=b['vol']/300.0
        aligned_ticks=(self.direction*(s['last']-s['first'])/TICK_SIZE
                       if s['first'] is not None and s['last'] is not None else np.nan)
        impact=(aligned_ticks/max(abs(net_s),1.0)*1000.0) if np.isfinite(aligned_ticks) else np.nan
        absorption=(max(adr_s,0.0)/max(abs(aligned_ticks),1.0)
                    if np.isfinite(adr_s) and np.isfinite(aligned_ticks) else np.nan)
        persistence=sum(1 for x in s['buckets'] if x>0)/12.0
        maxshare=(max(s['buckets'])/s['vol']) if s['vol']>0 else np.nan
        spreads=np.asarray(s['spreads'],dtype=float)
        return {
            'aligned_delta_ratio_signal':adr_s,
            'aligned_delta_ratio_prev':adr_p,
            'delta_acceleration':adr_s-adr_p if np.isfinite(adr_s) and np.isfinite(adr_p) else np.nan,
            'trades_per_second_signal':signal_trade_rate,
            'trades_rate_ratio':signal_trade_rate/base_trade_rate if base_trade_rate>0 else np.nan,
            'volume_per_second_signal':signal_vol_rate,
            'volume_rate_ratio':signal_vol_rate/base_vol_rate if base_vol_rate>0 else np.nan,
            'avg_trade_size_signal':s['vol']/s['n'] if s['n']>0 else np.nan,
            'median_spread_ticks':float(np.median(spreads)) if len(spreads) else np.nan,
            'p95_spread_ticks':float(np.quantile(spreads,0.95)) if len(spreads) else np.nan,
            'aligned_es_price_change_ticks_signal':aligned_ticks,
            'price_impact_per_1000':impact,
            'absorption_ratio':absorption,
            'aggression_persistence':persistence,
            'max_5s_aligned_delta_share':maxshare,
            'classified_volume_fraction':class_s/s['vol'] if s['vol']>0 else np.nan,
            'tick_count_signal':s['n'],
            'tick_volume_signal':s['vol'],
        }


def stream_tick_features(path: Path, events: pd.DataFrame):
    aggs=[]
    for _,r in events.iterrows():
        end=r['signal_ts_utc'].to_pydatetime()
        aggs.append(Agg(int(r['direction']),end-timedelta(seconds=360),end))
    if not aggs:
        return pd.DataFrame()

    first_start=min(a.base_start for a in aggs)
    last_end=max(a.end for a in aggs)
    active_idx=0
    nlines=0
    bad=0
    first_data_line=None

    with path.open('r',encoding='utf-8-sig',errors='ignore') as fh:
        for line in fh:
            nlines+=1
            line=line.strip()
            if not line:
                continue
            parts=line.split(';')
            if len(parts)<5:
                bad+=1
                continue
            try:
                ts=parse_tick_timestamp(parts[0])
            except Exception:
                # tolerate a header
                bad+=1
                continue
            if first_data_line is None:
                first_data_line=line[:200]
                print('First parsed tick line:',first_data_line)
            if ts<first_start:
                continue
            if ts>=last_end:
                break
            while active_idx<len(aggs) and ts>=aggs[active_idx].end:
                active_idx+=1
            # Events do not overlap materially but check neighbors safely.
            for j in range(max(0,active_idx-1),min(len(aggs),active_idx+3)):
                a=aggs[j]
                if a.base_start<=ts<a.end:
                    try:
                        last=float(parts[1]); bid=float(parts[2]); ask=float(parts[3]); vol=float(parts[4])
                    except Exception:
                        bad+=1
                        continue
                    if not all(np.isfinite([last,bid,ask,vol])) or vol<0:
                        bad+=1
                        continue
                    a.add(ts,last,bid,ask,vol)
    print('Tick lines scanned:',nlines,'bad/unparsed:',bad)
    return pd.DataFrame([a.features() for a in aggs])


def make_pipeline():
    return Pipeline([
        ('imputer',SimpleImputer(strategy='median')),
        ('scale',StandardScaler()),
        ('model',LogisticRegression(C=1.0,max_iter=5000,random_state=42)),
    ])


def cv_predict(df, features):
    X=df[features]
    y=df['profitable30'].astype(int).to_numpy()
    tscv=TimeSeriesSplit(n_splits=5)
    pred=np.full(len(df),np.nan)
    fold_rows=[]
    for fold,(tr,te) in enumerate(tscv.split(X),start=1):
        ytr=y[tr]; yte=y[te]
        if len(np.unique(ytr))<2:
            p=np.repeat(float(np.mean(ytr)),len(te))
        else:
            model=make_pipeline()
            model.fit(X.iloc[tr],ytr)
            p=model.predict_proba(X.iloc[te])[:,1]
        pred[te]=p
        auc=np.nan
        if len(np.unique(yte))==2:
            auc=float(roc_auc_score(yte,p))
        fold_rows.append({'fold':fold,'train_n':len(tr),'test_n':len(te),'auc':auc,
                          'test_start':df.iloc[te[0]]['date'],'test_end':df.iloc[te[-1]]['date']})
    mask=np.isfinite(pred)
    pooled=np.nan
    if mask.sum()>0 and len(np.unique(y[mask]))==2:
        pooled=float(roc_auc_score(y[mask],pred[mask]))
    return pred,pd.DataFrame(fold_rows),pooled


def main():
    tick_path=Path('data_es_staging/raw_lfs/ES_MAR24/ES_MAR24_Tick_Last.txt')
    minute_path=Path('data_es_staging/raw_lfs/ES_MAR24/ES_MAR24_Minute_Last.txt')
    if not tick_path.exists() or tick_path.stat().st_size<1_000_000:
        raise RuntimeError('ES MAR24 Tick Last LFS object not materialized.')
    print('Tick bytes:',tick_path.stat().st_size)

    mes=stitch_mes()
    es=read_nt_minute(minute_path,'ES_MAR24')
    mes_s=add_rvol(strict_rth_sessions(mes))
    es_s=add_rvol(strict_rth_sessions(es))
    atr=daily_atr_map(mes_s)
    events=build_events(mes_s,es_s,atr)
    print('Eligible events before tick coverage:',len(events))
    if events.empty:
        raise RuntimeError('No eligible MAR24 events.')

    micro=stream_tick_features(tick_path,events)
    full=pd.concat([events.reset_index(drop=True),micro.reset_index(drop=True)],axis=1)
    full=full.replace([np.inf,-np.inf],np.nan)

    # Require at least some signal tick data.
    eligible=full[full['tick_count_signal'].fillna(0)>0].copy().reset_index(drop=True)
    print('Events with signal Tick data:',len(eligible))

    pb,fb,auc_b=cv_predict(eligible,BASE_FEATURES)
    pm,fm,auc_m=cv_predict(eligible,MICRO_FEATURES)
    pc,fc,auc_c=cv_predict(eligible,BASE_FEATURES+MICRO_FEATURES)
    eligible['pred_baseline_oof']=pb
    eligible['pred_micro_oof']=pm
    eligible['pred_combined_oof']=pc

    valid=eligible[np.isfinite(eligible['pred_combined_oof'])].copy()
    tercile_diff=np.nan
    top_n=bottom_n=0
    if len(valid)>=3:
        ranks=valid['pred_combined_oof'].rank(method='first',pct=True)
        bot=valid[ranks<=1/3]
        top=valid[ranks>2/3]
        if len(bot) and len(top):
            tercile_diff=float(top['gross30_bps'].mean()-bot['gross30_bps'].mean())
            top_n=len(top); bottom_n=len(bot)

    fold_good=int((fc['auc']>0.50).sum())
    gate={
        'n_ge_40':len(eligible)>=40,
        'combined_auc_ge_058':bool(np.isfinite(auc_c) and auc_c>=0.58),
        'auc_lift_ge_004':bool(np.isfinite(auc_c) and np.isfinite(auc_b) and auc_c-auc_b>=0.04),
        'four_of_five_folds_gt_050':fold_good>=4,
        'top_bottom_gross_diff_ge_3bps':bool(np.isfinite(tercile_diff) and tercile_diff>=3.0),
    }
    passes=all(gate.values())

    summary=pd.DataFrame([{
        'eligible_events':len(eligible),
        'date_start':eligible['date'].min() if len(eligible) else None,
        'date_end':eligible['date'].max() if len(eligible) else None,
        'baseline_oof_auc':auc_b,
        'micro_oof_auc':auc_m,
        'combined_oof_auc':auc_c,
        'combined_auc_lift_vs_baseline':auc_c-auc_b if np.isfinite(auc_c) and np.isfinite(auc_b) else np.nan,
        'combined_folds_auc_gt_050':fold_good,
        'top_tercile_n':top_n,
        'bottom_tercile_n':bottom_n,
        'top_minus_bottom_gross30_bps':tercile_diff,
        **gate,
        'passes_import_rest_2024_gate':passes,
    }])

    # Fixed descriptive univariate statistics, no selection/tuning.
    uni=[]
    for f in MICRO_FEATURES:
        z=eligible[[f,'gross30_bps','profitable30']].dropna()
        corr=z[f].corr(z['gross30_bps'],method='spearman') if len(z)>=10 else np.nan
        uni.append({'feature':f,'n':len(z),'spearman_gross30_bps':corr,
                    'mean':z[f].mean() if len(z) else np.nan,
                    'std':z[f].std() if len(z) else np.nan})
    uni=pd.DataFrame(uni)

    folds=pd.concat([
        fb.assign(model='baseline'),
        fm.assign(model='micro'),
        fc.assign(model='combined'),
    ],ignore_index=True)

    out=Path('results/mes_v2_layer2_mar24')
    out.mkdir(parents=True,exist_ok=True)
    eligible.to_csv(out/'events_with_tick_features.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    folds.to_csv(out/'folds.csv',index=False)
    uni.to_csv(out/'micro_univariate.csv',index=False)

    print('\n=== MAR24 MICROSTRUCTURE PILOT ===')
    print(summary.T.to_string(header=False))
    print('\n=== FOLD AUC ===')
    print(folds.round(4).to_string(index=False))
    print('\n=== MICRO UNIVARIATE ===')
    print(uni.sort_values('spearman_gross30_bps',key=lambda s:s.abs(),ascending=False).round(4).to_string(index=False))
    print('\nIMPORT REST OF 2024 TICK:', 'YES' if passes else 'NO')

if __name__=='__main__':
    main()
