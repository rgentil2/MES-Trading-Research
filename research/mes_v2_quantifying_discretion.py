from __future__ import annotations

from pathlib import Path
import math
import re
import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score

START_YEAR = 2020
END_YEAR = 2024
DISCOVERY_END = 2022
VALIDATION_START = 2023
COST_DOLLARS_RT = 4.38
MES_POINT_VALUE = 5.0
COST_POINTS = COST_DOLLARS_RT / MES_POINT_VALUE
RTH_START_LABEL = 571      # NinjaTrader EOB label: 09:31 represents 09:30-09:31
RTH_END_LABEL = 960
OR_BARS = 15
LAST_EVENT_MINUTE = 11 * 60 + 24  # label 11:24; leaves 5 complete confirmation bars + next open
CONFIRM_BARS = 5
MONTHS_VALIDATION = 24.0

FEATURES = [
    'or_width_atr',
    'breakout_displacement_atr',
    'signal_body_eff',
    'signal_close_location_aligned',
    'mes_rvol',
    'mes_cum_rvol',
    'mes_speed3_atr',
    'mes_path_eff5',
    'mes_vwap_dist_atr',
    'es_rvol',
    'es_cum_rvol',
    'es_signal_eff_aligned',
    'es_same_side_or',
    'es_led_same_side',
    'es_minus_mes_move3_bps',
    'es_move3_atr_aligned',
    'accept_close_frac_5',
    'accept_volume_frac_5',
    'reentry_depth_atr_5',
    'continuation_5_atr',
    'mfe_5_atr',
    'mae_5_atr',
    'confirm_mean_mes_rvol',
    'es_accept_close_frac_5',
    'es_continuation_5_atr',
]


def read_nt(path: Path, contract: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';', header=None,
                     names=['timestamp_utc','open','high','low','close','volume'])
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], format='%Y%m%d %H%M%S', errors='raise')
    for c in ['open','high','low','close','volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().copy()
    df['contract'] = contract
    return df


def add_time(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x['timestamp_utc'] = x['timestamp_utc'].dt.tz_localize('UTC')
    x['timestamp_et'] = x['timestamp_utc'].dt.tz_convert('America/New_York')
    x['date'] = x['timestamp_et'].dt.date.astype(str)
    x['minute'] = x['timestamp_et'].dt.hour * 60 + x['timestamp_et'].dt.minute
    return x


def stitch_mes() -> pd.DataFrame:
    files=[]
    for p in Path('data/raw').glob('MES *.Last.txt'):
        m=re.search(r'MES (\d{2})-(\d{2})',p.name)
        if not m:
            continue
        mm, yy = int(m.group(1)), 2000+int(m.group(2))
        if START_YEAR <= yy <= END_YEAR:
            files.append((yy,mm,p))
    files.sort()
    parts=[]; prev_end=None
    for yy,mm,p in files:
        raw=read_nt(p,f'MES_{mm:02d}-{yy%100:02d}')
        raw_end=raw['timestamp_utc'].max()
        if prev_end is not None:
            raw=raw[raw['timestamp_utc']>prev_end].copy()
        parts.append(raw)
        prev_end=raw_end
    if not parts:
        raise RuntimeError('No MES files found.')
    out=pd.concat(parts,ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc',keep='last')
    return add_time(out)


MONTH_MAP={'MAR':3,'JUN':6,'SEP':9,'DEC':12}


def stitch_es() -> pd.DataFrame:
    files=[]
    root=Path('data_es_staging/raw_lfs')
    for p in root.glob('ES_*/*_Minute_Last.txt'):
        m=re.match(r'ES_(MAR|JUN|SEP|DEC)(\d{2})',p.parent.name)
        if not m:
            continue
        mm,yy=MONTH_MAP[m.group(1)],2000+int(m.group(2))
        if START_YEAR <= yy <= END_YEAR:
            files.append((yy,mm,p))
    files.sort()
    parts=[]; prev_end=None
    for yy,mm,p in files:
        raw=read_nt(p,f'ES_{mm:02d}-{yy%100:02d}')
        raw_end=raw['timestamp_utc'].max()
        if prev_end is not None:
            raw=raw[raw['timestamp_utc']>prev_end].copy()
        parts.append(raw)
        prev_end=raw_end
    if not parts:
        raise RuntimeError('No ES development Minute Last files materialized.')
    out=pd.concat(parts,ignore_index=True).sort_values('timestamp_utc').drop_duplicates('timestamp_utc',keep='last')
    return add_time(out)


def strict_rth_sessions(df: pd.DataFrame):
    r=df[(df['minute']>=RTH_START_LABEL)&(df['minute']<=RTH_END_LABEL)].copy()
    r=r[r['timestamp_et'].dt.year.between(START_YEAR,END_YEAR)].sort_values('timestamp_et')
    provisional=[]
    for d,g in r.groupby('date',sort=True):
        g=g.sort_values('timestamp_et')
        if len(g)<390:
            continue
        first390=g.iloc[:390].copy()
        if first390['contract'].nunique()!=1:
            continue
        provisional.append((d,first390.reset_index(drop=True),first390['contract'].iloc[0]))

    # Existing project convention: exclude the first valid RTH session whose
    # contract differs from the immediately preceding valid session.
    sessions={}
    prev_contract=None
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


def with_causal_volume_features(sessions: dict[str,pd.DataFrame]) -> dict[str,pd.DataFrame]:
    if not sessions:
        return {}
    allr=[]
    for d,g in sessions.items():
        z=g.copy()
        z['cum_volume']=z['volume'].cumsum()
        allr.append(z)
    x=pd.concat(allr,ignore_index=True).sort_values('timestamp_et')
    # Exact minute-of-day normalization using only prior observations of that minute.
    x=x.sort_values(['minute','timestamp_et'])
    x['vol_med20']=x.groupby('minute',observed=True)['volume'].transform(
        lambda s:s.shift(1).rolling(20,min_periods=10).median())
    x['cumvol_med20']=x.groupby('minute',observed=True)['cum_volume'].transform(
        lambda s:s.shift(1).rolling(20,min_periods=10).median())
    x['rvol']=x['volume']/x['vol_med20']
    x['cum_rvol']=x['cum_volume']/x['cumvol_med20']
    x=x.sort_values('timestamp_et')
    return {d:g.reset_index(drop=True) for d,g in x.groupby('date',sort=True)}


def safe_ratio(a,b):
    return np.nan if (b is None or not np.isfinite(b) or abs(b)<1e-12) else a/b


def session_vwap(g: pd.DataFrame) -> pd.Series:
    tp=(g['high']+g['low']+g['close'])/3.0
    num=(tp*g['volume']).cumsum()
    den=g['volume'].cumsum().replace(0,np.nan)
    return num/den


def first_or_break(g: pd.DataFrame, last_minute: int):
    if len(g)<OR_BARS+7:
        return None
    org=g.iloc[:OR_BARS]
    orh=float(org['high'].max()); orl=float(org['low'].min())
    after=g.iloc[OR_BARS:]
    after=after[after['minute']<=last_minute]
    for i,row in after.iterrows():
        if row['close']>orh:
            return int(i),1,orh,orl
        if row['close']<orl:
            return int(i),-1,orh,orl
    return None


def first_es_break_time(g: pd.DataFrame, direction: int):
    org=g.iloc[:OR_BARS]
    if len(org)<OR_BARS:
        return pd.NaT
    orh=float(org['high'].max()); orl=float(org['low'].min())
    after=g.iloc[OR_BARS:]
    mask=after['close']>orh if direction==1 else after['close']<orl
    if not mask.any():
        return pd.NaT
    return after.loc[mask,'timestamp_et'].iloc[0]


def build_events(mes_sessions,es_sessions,mes_atr,es_atr):
    rows=[]
    common=set(mes_sessions).intersection(es_sessions)
    for d in sorted(common):
        mg=mes_sessions[d].copy()
        eg=es_sessions[d].copy()
        atr=mes_atr.get(d,np.nan); eatr=es_atr.get(d,np.nan)
        if not np.isfinite(atr) or atr<=0 or not np.isfinite(eatr) or eatr<=0:
            continue

        br=first_or_break(mg,LAST_EVENT_MINUTE)
        if br is None:
            continue
        i,direction,orh,orl=br
        # observe 5 full bars after signal; enter on following bar
        confirm_start=i+1
        confirm_end=i+CONFIRM_BARS
        entry_idx=i+CONFIRM_BARS+1
        exit30_idx=entry_idx+29
        exit60_idx=entry_idx+59
        if exit60_idx>=len(mg):
            continue

        ts=mg.iloc[i]['timestamp_et']
        es_matches=eg.index[eg['timestamp_et']==ts].tolist()
        if not es_matches:
            continue
        ei=int(es_matches[0])
        if ei<5 or ei+CONFIRM_BARS>=len(eg):
            continue

        mbar=mg.iloc[i]
        ebar=eg.iloc[ei]
        mconf=mg.iloc[confirm_start:confirm_end+1]
        econf=eg.iloc[ei+1:ei+CONFIRM_BARS+1]
        if len(mconf)!=CONFIRM_BARS or len(econf)!=CONFIRM_BARS:
            continue

        mvwap=session_vwap(mg).iloc[i]
        morw=orh-orl
        edge=orh if direction==1 else orl
        mrng=float(mbar['high']-mbar['low'])
        signal_body_eff=safe_ratio(abs(float(mbar['close']-mbar['open'])),mrng)
        close_loc=(float(mbar['close']-mbar['low'])/mrng if direction==1
                   else float(mbar['high']-mbar['close'])/mrng) if mrng>0 else np.nan

        # MES pre-signal path metrics
        c3=float(mg.iloc[i-3]['close'])
        c5=float(mg.iloc[i-5]['close'])
        speed3=direction*(float(mbar['close'])-c3)/atr
        closes5=mg.iloc[i-5:i+1]['close'].to_numpy(dtype=float)
        pathden=np.abs(np.diff(closes5)).sum()
        path_eff=direction*(closes5[-1]-closes5[0])/pathden if pathden>0 else 0.0

        # ES OR state and lead
        eorg=eg.iloc[:OR_BARS]
        eorh=float(eorg['high'].max()); eorl=float(eorg['low'].min())
        es_same=(float(ebar['close'])>eorh) if direction==1 else (float(ebar['close'])<eorl)
        es_first=first_es_break_time(eg,direction)
        es_led=bool(pd.notna(es_first) and es_first<ts)
        erng=float(ebar['high']-ebar['low'])
        es_eff=direction*safe_ratio(float(ebar['close']-ebar['open']),erng) if erng>0 else np.nan
        e3=float(eg.iloc[ei-3]['close'])
        mes_move3=(float(mbar['close'])/c3-1.0)*10000
        es_move3=(float(ebar['close'])/e3-1.0)*10000

        # Five-minute MES acceptance/rejection
        if direction==1:
            outside_close=mconf['close']>orh
            penetration=np.maximum(orh-mconf['low'].to_numpy(dtype=float),0)
            cont= float(mconf.iloc[-1]['close'])-float(mbar['close'])
            mfe= float(mconf['high'].max())-float(mbar['close'])
            mae= float(mbar['close'])-float(mconf['low'].min())
        else:
            outside_close=mconf['close']<orl
            penetration=np.maximum(mconf['high'].to_numpy(dtype=float)-orl,0)
            cont= float(mbar['close'])-float(mconf.iloc[-1]['close'])
            mfe= float(mbar['close'])-float(mconf['low'].min())
            mae= float(mconf['high'].max())-float(mbar['close'])
        accept_close=float(outside_close.mean())
        vol_total=float(mconf['volume'].sum())
        accept_vol=float(mconf.loc[outside_close,'volume'].sum()/vol_total) if vol_total>0 else np.nan

        # Five-minute ES acceptance
        if direction==1:
            eoutside=econf['close']>eorh
            econt=float(econf.iloc[-1]['close'])-float(ebar['close'])
        else:
            eoutside=econf['close']<eorl
            econt=float(ebar['close'])-float(econf.iloc[-1]['close'])

        entry=float(mg.iloc[entry_idx]['open'])
        exit30=float(mg.iloc[exit30_idx]['close'])
        exit60=float(mg.iloc[exit60_idx]['close'])
        gross30=direction*(exit30-entry)
        gross60=direction*(exit60-entry)
        net30=gross30-COST_POINTS
        net60=gross60-COST_POINTS
        gross30_bps=direction*(exit30/entry-1.0)*10000
        gross60_bps=direction*(exit60/entry-1.0)*10000

        rows.append({
            'date':d,'year':int(d[:4]),'timestamp_et':str(ts),
            'direction':direction,'entry':entry,
            'gross30_points':gross30,'net30_points':net30,
            'gross60_points':gross60,'net60_points':net60,
            'gross30_bps':gross30_bps,'gross60_bps':gross60_bps,
            'profitable30':int(net30>0),
            'or_width_atr':morw/atr,
            'breakout_displacement_atr':direction*(float(mbar['close'])-edge)/atr,
            'signal_body_eff':signal_body_eff,
            'signal_close_location_aligned':close_loc,
            'mes_rvol':float(mbar.get('rvol',np.nan)),
            'mes_cum_rvol':float(mbar.get('cum_rvol',np.nan)),
            'mes_speed3_atr':speed3,
            'mes_path_eff5':path_eff,
            'mes_vwap_dist_atr':direction*(float(mbar['close'])-float(mvwap))/atr,
            'es_rvol':float(ebar.get('rvol',np.nan)),
            'es_cum_rvol':float(ebar.get('cum_rvol',np.nan)),
            'es_signal_eff_aligned':es_eff,
            'es_same_side_or':float(es_same),
            'es_led_same_side':float(es_led),
            'es_minus_mes_move3_bps':direction*(es_move3-mes_move3),
            'es_move3_atr_aligned':direction*(float(ebar['close'])-e3)/eatr,
            'accept_close_frac_5':accept_close,
            'accept_volume_frac_5':accept_vol,
            'reentry_depth_atr_5':float(np.max(penetration))/atr,
            'continuation_5_atr':cont/atr,
            'mfe_5_atr':max(mfe,0.0)/atr,
            'mae_5_atr':max(mae,0.0)/atr,
            'confirm_mean_mes_rvol':float(mconf['rvol'].mean()),
            'es_accept_close_frac_5':float(eoutside.mean()),
            'es_continuation_5_atr':econt/eatr,
        })
    return pd.DataFrame(rows)


def profit_factor(s: pd.Series) -> float:
    pos=s[s>0].sum()
    neg=-s[s<0].sum()
    return float(pos/neg) if neg>0 else float('inf')


def leaf_rule(tree: DecisionTreeClassifier, feature_names, xrow: np.ndarray, leaf_id: int) -> str:
    t=tree.tree_
    node_indicator=tree.decision_path(xrow.reshape(1,-1))
    nodes=node_indicator.indices[node_indicator.indptr[0]:node_indicator.indptr[1]]
    parts=[]
    for node_id in nodes:
        if node_id==leaf_id or t.children_left[node_id]==t.children_right[node_id]:
            continue
        fname=feature_names[t.feature[node_id]]
        thr=t.threshold[node_id]
        if xrow[t.feature[node_id]]<=thr:
            parts.append(f'{fname} <= {thr:.6g}')
        else:
            parts.append(f'{fname} > {thr:.6g}')
    return ' AND '.join(parts) if parts else 'ALL EVENTS'


def yearly_table(df, mask, prefix):
    z=df.loc[mask].groupby('year').agg(
        n=('net30_points','size'),
        net30_mean=('net30_points','mean'),
        gross30_bps_mean=('gross30_bps','mean'),
        net30_sum=('net30_points','sum')
    )
    z=z.reset_index()
    z['group']=prefix
    return z


def main():
    print('Loading MES 2020-2024...')
    mes=stitch_mes()
    print('Loading ES 2020-2024 Minute Last...')
    es=stitch_es()

    mes_s=strict_rth_sessions(mes)
    es_s=strict_rth_sessions(es)
    print('Strict MES sessions:',len(mes_s),'Strict ES sessions:',len(es_s))

    mes_atr=daily_atr_map(mes_s)
    es_atr=daily_atr_map(es_s)
    mes_s=with_causal_volume_features(mes_s)
    es_s=with_causal_volume_features(es_s)

    events=build_events(mes_s,es_s,mes_atr,es_atr)
    events=events.replace([np.inf,-np.inf],np.nan)
    print('Events total:',len(events))
    print('Events by year:',events.groupby('year').size().to_dict())

    disc=events[events['year']<=DISCOVERY_END].copy()
    val=events[events['year']>=VALIDATION_START].copy()
    if len(disc)==0 or len(val)==0:
        raise RuntimeError('Discovery/validation split empty.')

    Xd=disc[FEATURES]
    Xv=val[FEATURES]
    yd=disc['profitable30'].astype(int)
    yv=val['profitable30'].astype(int)

    # Logistic diagnostic
    logit=Pipeline([
        ('imputer',SimpleImputer(strategy='median')),
        ('scale',StandardScaler()),
        ('model',LogisticRegression(C=1.0,max_iter=5000,random_state=42))
    ])
    logit.fit(Xd,yd)
    pv=logit.predict_proba(Xv)[:,1]
    auc=float(roc_auc_score(yv,pv)) if yv.nunique()==2 else np.nan
    coef=logit.named_steps['model'].coef_[0]
    coef_df=pd.DataFrame({'feature':FEATURES,'standardized_coef':coef})
    coef_df['abs_coef']=coef_df['standardized_coef'].abs()
    coef_df=coef_df.sort_values('abs_coef',ascending=False)

    # Interpretable tree, imputation learned only on discovery
    imp=SimpleImputer(strategy='median')
    Xd_imp=imp.fit_transform(Xd)
    Xv_imp=imp.transform(Xv)
    tree=DecisionTreeClassifier(max_depth=2,min_samples_leaf=180,random_state=42)
    tree.fit(Xd_imp,yd)
    ld=tree.apply(Xd_imp)
    lv=tree.apply(Xv_imp)

    leaf_rows=[]
    for leaf in sorted(np.unique(ld)):
        md=ld==leaf
        mv=lv==leaf
        xexample=Xd_imp[np.where(md)[0][0]]
        rule=leaf_rule(tree,FEATURES,xexample,int(leaf))
        leaf_rows.append({
            'leaf':int(leaf),'rule':rule,
            'disc_n':int(md.sum()),
            'disc_profitable_frac':float(yd.iloc[np.where(md)[0]].mean()),
            'disc_net30_mean':float(disc.iloc[np.where(md)[0]]['net30_points'].mean()),
            'disc_gross30_bps_mean':float(disc.iloc[np.where(md)[0]]['gross30_bps'].mean()),
            'val_n':int(mv.sum()),
            'val_profitable_frac':float(yv.iloc[np.where(mv)[0]].mean()) if mv.sum() else np.nan,
            'val_net30_mean':float(val.iloc[np.where(mv)[0]]['net30_points'].mean()) if mv.sum() else np.nan,
            'val_gross30_bps_mean':float(val.iloc[np.where(mv)[0]]['gross30_bps'].mean()) if mv.sum() else np.nan,
        })
    leaf_df=pd.DataFrame(leaf_rows)
    selected=int(leaf_df.sort_values(['disc_profitable_frac','disc_net30_mean'],ascending=False).iloc[0]['leaf'])
    smd=ld==selected
    smv=lv==selected
    selected_rule=leaf_df.loc[leaf_df['leaf']==selected,'rule'].iloc[0]

    base_val_pf=profit_factor(val['net30_points'])
    sel_val=val.loc[smv].copy()
    sel_pf=profit_factor(sel_val['net30_points']) if len(sel_val) else np.nan
    base_gross_bps=float(val['gross30_bps'].mean())
    sel_gross_bps=float(sel_val['gross30_bps'].mean()) if len(sel_val) else np.nan
    lift_bps=sel_gross_bps-base_gross_bps if len(sel_val) else np.nan
    positive_years=int((sel_val.groupby('year')['net30_points'].sum()>0).sum()) if len(sel_val) else 0

    gate={
        'validation_n_ge_120':len(sel_val)>=120,
        'net_mean_gt_0':float(sel_val['net30_points'].mean())>0 if len(sel_val) else False,
        'pf_ge_1_15':sel_pf>=1.15 if np.isfinite(sel_pf) else False,
        'both_2023_2024_positive':positive_years>=2,
        'gross_lift_ge_3bps':lift_bps>=3.0 if np.isfinite(lift_bps) else False,
        'logistic_auc_ge_0_55':auc>=0.55 if np.isfinite(auc) else False,
    }
    passes=all(gate.values())

    summary=pd.DataFrame([{
        'discovery_n':len(disc),
        'validation_n':len(val),
        'base_validation_profitable_frac':float(val['profitable30'].mean()),
        'base_validation_net30_mean_points':float(val['net30_points'].mean()),
        'base_validation_pf':base_val_pf,
        'base_validation_gross30_bps':base_gross_bps,
        'logistic_validation_auc':auc,
        'selected_leaf':selected,
        'selected_rule':selected_rule,
        'selected_discovery_n':int(smd.sum()),
        'selected_discovery_profitable_frac':float(disc.loc[smd,'profitable30'].mean()),
        'selected_discovery_net30_mean_points':float(disc.loc[smd,'net30_points'].mean()),
        'selected_validation_n':len(sel_val),
        'selected_validation_signals_per_month':len(sel_val)/MONTHS_VALIDATION,
        'selected_validation_profitable_frac':float(sel_val['profitable30'].mean()) if len(sel_val) else np.nan,
        'selected_validation_net30_mean_points':float(sel_val['net30_points'].mean()) if len(sel_val) else np.nan,
        'selected_validation_pf':sel_pf,
        'selected_validation_gross30_bps':sel_gross_bps,
        'selected_validation_lift_bps':lift_bps,
        'selected_validation_positive_years':positive_years,
        **gate,
        'passes_promotion_gate':passes,
    }])

    years=pd.concat([
        yearly_table(val,np.ones(len(val),dtype=bool),'BASE_VALIDATION'),
        yearly_table(val,smv,'SELECTED_RULE_VALIDATION')
    ],ignore_index=True)

    out=Path('results/mes_v2_quantifying_discretion')
    out.mkdir(parents=True,exist_ok=True)
    events.to_csv(out/'events_features.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    leaf_df.to_csv(out/'tree_leaves.csv',index=False)
    coef_df.to_csv(out/'logistic_coefficients.csv',index=False)
    years.to_csv(out/'yearly.csv',index=False)

    print('\n=== MES V2 QUANTIFYING DISCRETION ===')
    print(summary.T.to_string(header=False))
    print('\n=== TREE LEAVES ===')
    print(leaf_df.round(4).to_string(index=False))
    print('\n=== TOP LOGISTIC COEFFICIENTS ===')
    print(coef_df.head(12).round(4).to_string(index=False))
    print('\n=== YEARLY ===')
    print(years.round(4).to_string(index=False))
    print('\nPROMOTION GATE:', 'PASS' if passes else 'FAIL')

if __name__=='__main__':
    main()

# trigger MES V2 Layer 1 workflow

# PR trigger only; preregistered logic unchanged
