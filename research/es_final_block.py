from __future__ import annotations

from pathlib import Path
import re
import numpy as np
import pandas as pd

START_YEAR = 2020
END_YEAR = 2024
RTH_START = 9 * 60 + 30
OR_END = 9 * 60 + 45
EVENT_END = 11 * 60 + 30
MONTHS = 60.0


def read_nt(path: Path, contract: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';', header=None,
                     names=['timestamp_utc','open','high','low','close','volume'])
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], format='%Y%m%d %H%M%S', errors='raise')
    for c in ['open','high','low','close','volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().copy()
    df['contract'] = contract
    return df


def stitch_mes() -> pd.DataFrame:
    files = []
    for p in Path('data/raw').glob('MES *.Last.txt'):
        m = re.search(r'MES (\d{2})-(\d{2})', p.name)
        if not m:
            continue
        month, yy = int(m.group(1)), int(m.group(2))
        year = 2000 + yy
        if START_YEAR <= year <= END_YEAR:
            files.append((year, month, p))
    files.sort()
    parts, previous_end = [], None
    for year, month, p in files:
        raw = read_nt(p, f'MES_{month:02d}-{year%100:02d}')
        raw_end = raw['timestamp_utc'].max()
        if previous_end is not None:
            raw = raw[raw['timestamp_utc'] > previous_end].copy()
        parts.append(raw)
        previous_end = raw_end
    out = pd.concat(parts, ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc', keep='last')
    return add_et(out)


MONTH_MAP = {'MAR':3,'JUN':6,'SEP':9,'DEC':12}


def stitch_es() -> pd.DataFrame:
    files = []
    root = Path('data_es_staging/raw_lfs')
    for p in root.glob('ES_*/*_Minute_Last.txt'):
        m = re.search(r'ES_(MAR|JUN|SEP|DEC)(\d{2})', str(p.parent.name))
        if not m:
            continue
        month, year = MONTH_MAP[m.group(1)], 2000 + int(m.group(2))
        if START_YEAR <= year <= END_YEAR:
            files.append((year, month, p))
    files.sort()
    parts, previous_end = [], None
    for year, month, p in files:
        raw = read_nt(p, f'ES_{month:02d}-{year%100:02d}')
        raw_end = raw['timestamp_utc'].max()
        if previous_end is not None:
            raw = raw[raw['timestamp_utc'] > previous_end].copy()
        parts.append(raw)
        previous_end = raw_end
    if not parts:
        raise RuntimeError('No ES Minute Last files found; Git LFS data were not materialized.')
    out = pd.concat(parts, ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc', keep='last')
    return add_et(out)


def add_et(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['timestamp_utc'] = out['timestamp_utc'].dt.tz_localize('UTC')
    out['timestamp_et'] = out['timestamp_utc'].dt.tz_convert('America/New_York')
    out['session_date'] = out['timestamp_et'].dt.date.astype(str)
    out['minute'] = out['timestamp_et'].dt.hour * 60 + out['timestamp_et'].dt.minute
    return out


def rth(df: pd.DataFrame) -> pd.DataFrame:
    x = df[(df['minute'] > RTH_START) & (df['minute'] <= 16*60)].copy()
    x = x[x['timestamp_et'].dt.year.between(START_YEAR, END_YEAR)].copy()
    return x


def add_daily_features(df: pd.DataFrame, prefix: str) -> tuple[pd.DataFrame,pd.DataFrame]:
    x = rth(df).sort_values('timestamp_et').copy()
    g = x.groupby('session_date', sort=True, observed=True)
    x['bar_index'] = g.cumcount()
    x['cum_volume'] = g['volume'].cumsum()

    daily = g.agg(open=('open','first'), high=('high','max'), low=('low','min'), close=('close','last'),
                  volume=('volume','sum'), bars=('close','size')).reset_index()
    daily['date'] = pd.to_datetime(daily['session_date'])
    daily = daily.sort_values('date').reset_index(drop=True)
    prev_close = daily['close'].shift(1)
    tr = pd.concat([
        daily['high']-daily['low'],
        (daily['high']-prev_close).abs(),
        (daily['low']-prev_close).abs()
    ], axis=1).max(axis=1)
    daily['atr14'] = tr.shift(1).rolling(14, min_periods=14).mean()
    daily['atr_pct'] = daily['atr14'] / daily['close'].shift(1)

    p33 = daily['atr_pct'].shift(1).rolling(252, min_periods=60).quantile(1/3)
    p67 = daily['atr_pct'].shift(1).rolling(252, min_periods=60).quantile(2/3)
    daily['vol_state'] = np.select(
        [daily['atr_pct'] < p33, daily['atr_pct'] > p67],
        ['LOW','HIGH'], default='MID'
    )
    daily.loc[p33.isna() | p67.isna(), 'vol_state'] = 'UNKNOWN'
    return x, daily.add_prefix(prefix)


def causal_same_minute_median(x: pd.DataFrame, value_col: str, out_col: str) -> pd.DataFrame:
    x = x.sort_values(['minute','timestamp_et']).copy()
    x[out_col] = x.groupby('minute', observed=True)[value_col].transform(
        lambda s: s.shift(1).rolling(20, min_periods=10).median()
    )
    return x.sort_values('timestamp_et')


def prepare_es_features(es: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame]:
    x, daily_pref = add_daily_features(es, 'es_')
    x = causal_same_minute_median(x, 'volume', 'vol_med20')
    x['rvol'] = x['volume'] / x['vol_med20']
    x = causal_same_minute_median(x, 'cum_volume', 'cumvol_med20')
    x['cum_rvol'] = x['cum_volume'] / x['cumvol_med20']

    ors = []
    for d, g in x.groupby('session_date', sort=True, observed=True):
        org = g[(g['minute'] > RTH_START) & (g['minute'] <= OR_END)]
        if len(org) < 15:
            continue
        orh, orl = org['high'].max(), org['low'].min()
        after = g[(g['minute'] > OR_END) & (g['minute'] <= EVENT_END)]
        up = after.loc[after['close'] > orh, 'timestamp_et']
        dn = after.loc[after['close'] < orl, 'timestamp_et']
        ors.append({
            'session_date': d, 'es_orh':orh, 'es_orl':orl,
            'es_first_up': up.iloc[0] if len(up) else pd.NaT,
            'es_first_dn': dn.iloc[0] if len(dn) else pd.NaT,
            'es_or_open': org.iloc[0]['open'],
            'es_or_close': org.iloc[-1]['close'],
        })
    ors = pd.DataFrame(ors)
    daily = daily_pref.merge(ors, left_on='es_session_date', right_on='session_date', how='left')
    daily['es_open_impulse'] = daily['es_or_close'] - daily['es_or_open']
    daily['es_open_impulse_atr'] = daily['es_open_impulse'] / daily['es_atr14']
    return x, daily


def build_mes_events(mes: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame]:
    x, daily = add_daily_features(mes, 'mes_')
    g = x.groupby('session_date', sort=False, observed=True)
    for h in [15,30,60]:
        x[f'fwd_close_{h}'] = g['close'].shift(-h)

    rows=[]
    for d, gd in x.groupby('session_date', sort=True, observed=True):
        org=gd[(gd['minute'] > RTH_START) & (gd['minute'] <= OR_END)]
        if len(org)<15:
            continue
        orh,orl=org['high'].max(),org['low'].min()
        after=gd[(gd['minute'] > OR_END) & (gd['minute'] <= EVENT_END)]
        hits=after[(after['close']>orh)|(after['close']<orl)]
        if hits.empty:
            continue
        ev=hits.iloc[0]
        direction=1 if ev['close']>orh else -1
        row={
            'session_date':d,'timestamp_et':ev['timestamp_et'],'minute':int(ev['minute']),
            'direction':direction,'mes_event_close':float(ev['close']),'mes_orh':orh,'mes_orl':orl,
            'year':int(ev['timestamp_et'].year),
        }
        for h in [15,30,60]:
            fc=ev[f'fwd_close_{h}']
            row[f'mes_dir_{h}m_bps'] = np.nan if pd.isna(fc) else direction*(fc/ev['close']-1.0)*10000
        rows.append(row)
    return pd.DataFrame(rows),daily


def attach_features(events: pd.DataFrame, esx: pd.DataFrame, esdaily: pd.DataFrame, mesdaily: pd.DataFrame) -> pd.DataFrame:
    es_cols=['timestamp_et','open','high','low','close','volume','rvol','cum_rvol']
    z=events.merge(esx[es_cols], on='timestamp_et', how='left', suffixes=('','_es'))
    z=z.merge(esdaily[[
        'es_session_date','es_atr14','es_open_impulse_atr','es_orh','es_orl','es_first_up','es_first_dn'
    ]], left_on='session_date', right_on='es_session_date', how='left')
    z=z.merge(mesdaily[['mes_session_date','mes_vol_state']], left_on='session_date', right_on='mes_session_date', how='left')
    rng=(z['high']-z['low']).replace(0,np.nan)
    z['es_eff_abs']=(z['close']-z['open']).abs()/rng
    z['es_eff_aligned']=z['direction']*(z['close']-z['open'])/rng
    z['es_same_side_now']=np.where(z['direction']>0,z['close']>z['es_orh'],z['close']<z['es_orl'])
    z['es_lead_same_side']=np.where(
        z['direction']>0,
        z['es_first_up'].notna() & (z['es_first_up']<z['timestamp_et']),
        z['es_first_dn'].notna() & (z['es_first_dn']<z['timestamp_et'])
    )
    z['es_open_impulse_aligned']=z['direction']*z['es_open_impulse_atr']
    return z


def summarize_filter(base: pd.DataFrame, name: str, mask: pd.Series, pred_mult: int=1) -> dict:
    m=mask.fillna(False)
    g=base[m].copy()
    c=base[~m].copy()
    out={'hypothesis':name,'n':len(g),'signals_per_month':len(g)/MONTHS}
    for h in [15,30,60]:
        col=f'mes_dir_{h}m_bps'
        yg=pred_mult*g[col]
        yc=pred_mult*c[col]
        out[f'mean_{h}m_bps']=yg.mean()
        out[f'median_{h}m_bps']=yg.median()
        out[f'win_{h}m']=(yg>0).mean()
        out[f'control_mean_{h}m_bps']=yc.mean()
        out[f'delta_vs_control_{h}m_bps']=yg.mean()-yc.mean()
    years=[]
    for y, gy in g.groupby('year'):
        val=(pred_mult*gy['mes_dir_30m_bps']).mean()
        out[f'y{y}_n']=len(gy)
        out[f'y{y}_mean30']=val
        if pd.notna(val): years.append(val>0)
    out['positive_years']=sum(years)
    out['gate_frequency']=len(g)>=300
    out['gate_effect']=out['mean_30m_bps']>=3.0
    out['gate_incremental']=out['delta_vs_control_30m_bps']>=3.0
    out['gate_stability']=out['positive_years']>=4
    out['passes_signal_gate']=all([out['gate_frequency'],out['gate_effect'],out['gate_incremental'],out['gate_stability']])
    return out


def main():
    print('Loading MES 2020-2024...')
    mes=stitch_mes()
    print('Loading ES Minute Last 2020-2024 from Git LFS...')
    es=stitch_es()
    events, mesdaily=build_mes_events(mes)
    esx, esdaily=prepare_es_features(es)
    base=attach_features(events, esx, esdaily, mesdaily)
    base=base.dropna(subset=['mes_dir_30m_bps']).copy()

    print(f'BASE EVENTS: {len(base)} | {len(base)/MONTHS:.2f}/month')
    print('BASE continuation mean30 bps:', round(base['mes_dir_30m_bps'].mean(),3))
    print('BASE by year:', base.groupby('year')['mes_dir_30m_bps'].agg(['count','mean']).round(3).to_dict('index'))

    tests=[]
    tests.append(summarize_filter(base,'H-ES01 RVOL>=1.0 continuation',base['rvol']>=1.0,1))
    tests.append(summarize_filter(base,'H-ES02 RVOL>=1.5 continuation',base['rvol']>=1.5,1))
    tests.append(summarize_filter(base,'H-ES03 RVOL>=1.25 + aligned_eff>=0.60 continuation',(base['rvol']>=1.25)&(base['es_eff_aligned']>=0.60),1))
    tests.append(summarize_filter(base,'H-ES04 RVOL>=1.5 + abs_eff<=0.25 REVERSAL',(base['rvol']>=1.5)&(base['es_eff_abs']<=0.25),-1))
    tests.append(summarize_filter(base,'H-ES05 aligned_eff>=0.60 continuation',base['es_eff_aligned']>=0.60,1))
    tests.append(summarize_filter(base,'H-ES06 ES led same-side OR15 continuation',base['es_lead_same_side'],1))
    tests.append(summarize_filter(base,'H-ES07 ES non-confirmation REVERSAL',~base['es_same_side_now'].fillna(False),-1))
    tests.append(summarize_filter(base,'H-ES08 cumulative RVOL>=1.25 continuation',base['cum_rvol']>=1.25,1))
    tests.append(summarize_filter(base,'H-ES09 opening impulse aligned>=0.10 ATR continuation',base['es_open_impulse_aligned']>=0.10,1))
    tests.append(summarize_filter(base,'H-ES10 ES same-side now + RVOL>=1 continuation',base['es_same_side_now'].fillna(False)&(base['rvol']>=1.0),1))
    summary=pd.DataFrame(tests)

    regime_rows=[]
    for state in ['LOW','MID','HIGH']:
        b=base[base['mes_vol_state']==state]
        if b.empty: continue
        m=(b['es_same_side_now'].fillna(False)&(b['rvol']>=1.0))
        regime_rows.append({
            'mes_vol_state':state,'base_n':len(b),'h10_n':int(m.sum()),
            'base_mean30':b['mes_dir_30m_bps'].mean(),
            'h10_mean30':b.loc[m,'mes_dir_30m_bps'].mean(),
            'delta':b.loc[m,'mes_dir_30m_bps'].mean()-b.loc[~m,'mes_dir_30m_bps'].mean() if (~m).any() and m.any() else np.nan
        })
    regimes=pd.DataFrame(regime_rows)

    out=Path('results/es_final_block')
    out.mkdir(parents=True,exist_ok=True)
    base.to_csv(out/'events_with_es_features.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    regimes.to_csv(out/'h10_by_mes_vol_state.csv',index=False)

    cols=['hypothesis','n','signals_per_month','mean_30m_bps','control_mean_30m_bps','delta_vs_control_30m_bps','positive_years','passes_signal_gate']
    print('\n=== ES FINAL BLOCK SUMMARY ===')
    print(summary[cols].round(3).to_string(index=False))
    print('\n=== BY YEAR 30M ===')
    ycols=['hypothesis']+[c for c in summary.columns if re.match(r'y202[0-4]_(n|mean30)$',c)]
    print(summary[ycols].round(3).to_string(index=False))
    print('\n=== H-ES10 BY MES VOL STATE ===')
    print(regimes.round(3).to_string(index=False))
    print('\nPASSED:', summary.loc[summary['passes_signal_gate'],'hypothesis'].tolist())

if __name__=='__main__':
    main()

# workflow trigger: preregistered ES block
