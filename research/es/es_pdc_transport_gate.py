#!/usr/bin/env python3
"""Fixed MES PDC -> ES 2020-24 structural transport / MFFU sizing diagnostic.

NOT a production backtest: archived high/medium USD news filter is not applied and
OHLC cannot order touch events inside the same bar; choose STOP first.
2025 and 2026 are not read or materialized by this script.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'data_es_staging/manifests/ES_MINUTE_LAST_MANIFEST.csv'
STAGING = ROOT / 'data_es_staging/raw_lfs'
OUTPUT = ROOT / 'results/es_pdc_transport'
POINT_ES = 50.0
POINT_MES = 5.0
TICK = 0.25
SLIPPAGE_TICKS = 2
SLIP = TICK * SLIPPAGE_TICKS
ATR_N = 14
GAP_LOW = 0.10
GAP_HIGH = 0.20
STOP_MULT = 0.30
CUTOFF = 690   # ET 11:30
FEE_ES_RT = 4.68  # Original MFFU comparison: preserved unchanged
FEE_MES_RT = 1.90
_FREE_TABLE = json.loads((ROOT/'research/costs/NINJATRADER_FREE_ALL_IN_124_SYMBOLS_2026_10_09.json').read_text(encoding='utf-8'))['rates']
FREE_FEE_ES_RT = float(_FREE_TABLE['ES']['all_in_free_round_trip_usd'])  # 5.74
FREE_FEE_MES_RT = float(_FREE_TABLE['MES']['all_in_free_round_trip_usd'])  # 1.88
MONTHS = 60


def required_manifest(path: Path = MANIFEST) -> list[dict]:
    with path.open(newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    selected = [x for x in rows if x['stage'] == 'DEVELOPMENT']
    expected = {f'ES_{m}{y:02d}_Minute_Last.txt' for y in range(20, 25) for m in ('MAR','JUN','SEP','DEC')}
    names = {r['repo_filename'] for r in selected}
    if len(selected) != 20 or names != expected:
        raise ValueError('Expected precisely 20 ES development contracts (2020-2024)')
    if any('25' in r['contract'][-2:] or '26' in r['contract'][-2:] for r in selected):
        raise ValueError('Holdout entry in development manifest')
    order={'MAR':3,'JUN':6,'SEP':9,'DEC':12}
    selected.sort(key=lambda r: (int(r['repo_filename'].split('_')[1][-2:]),order[r['repo_filename'].split('_')[1][:3]]))
    return selected


def raw_contract_file(record: dict) -> Path:
    stem = record['repo_filename'].split('_')[1]
    return STAGING / f'ES_{stem}' / record['repo_filename']


def read_contract(record: dict) -> pd.DataFrame:
    path = raw_contract_file(record)
    if not path.exists() or path.stat().st_size < 1000:
        raise FileNotFoundError(f'ES LFS data not materialized: {path}')
    data=path.read_bytes()
    if len(data)!=int(record['size_bytes']) or hashlib.sha256(data).hexdigest()!=record['sha256']:
        raise ValueError('Manifest checksum/size mismatch for '+path.name)
    df=pd.read_csv(path,sep=';',header=None,names=['timestamp','open','high','low','close','volume'],dtype={'timestamp':'string'})
    if len(df)!=int(record['rows']):
        raise ValueError('Row-count mismatch for '+path.name)
    df['timestamp']=pd.to_datetime(df.timestamp,format='%Y%m%d %H%M%S',utc=True,errors='raise')
    if not df.timestamp.is_monotonic_increasing or df.timestamp.duplicated().any():
        raise ValueError('Non-monotonic or duplicate raw timestamps in '+path.name)
    for k in ('open','high','low','close','volume'):
        df[k]=pd.to_numeric(df[k],errors='raise')
    a=df[['open','high','low','close']].to_numpy(float)
    if not np.isfinite(a).all() or not np.allclose(a/TICK,np.round(a/TICK),atol=1e-10):
        raise ValueError('Invalid prices/tick size in '+path.name)
    if (df.volume<=0).any() or (df.high<df[['open','close']].max(axis=1)).any() or (df.low>df[['open','close']].min(axis=1)).any():
        raise ValueError('Invalid OHLC/volume in '+path.name)
    df['contract']=record['contract']
    return df


def load_es_development(records: list[dict]) -> tuple[pd.DataFrame,dict]:
    batches=[];prev_end=None;kept=0;removed=0
    for record in records:
        df=read_contract(record)
        end=df.timestamp.iloc[-1]
        original=len(df)
        if prev_end is not None:
            df=df[df.timestamp>prev_end].copy()
        if len(df)==0:
            raise ValueError(f'Rollover invalid: {record["contract"]} contributes no rows')
        removed+=original-len(df);kept+=len(df)
        batches.append(df);prev_end=end
    result=pd.concat(batches,ignore_index=True)
    if result.timestamp.duplicated().any() or not result.timestamp.is_monotonic_increasing:
        raise ValueError('Continuous ES data has duplicate or reversed timestamps')
    if (result.timestamp>=pd.Timestamp('2025-01-01',tz='UTC')).any():
        # MAR25 starts in DEC24; its data are excluded altogether until an explicit gate.
        raise ValueError('Unexpected >=2025 record in development contracts')
    result['timestamp_et']=result.timestamp.dt.tz_convert('America/New_York')
    result['date_et']=result.timestamp_et.dt.strftime('%Y-%m-%d')
    result['minute_et']=result.timestamp_et.dt.hour*60+result.timestamp_et.dt.minute
    result=result[(result.minute_et>=571)&(result.minute_et<=960)].copy()
    result=result[(result.timestamp_et.dt.year>=2020)&(result.timestamp_et.dt.year<=2024)].copy()
    return result,{'development_contracts':len(records),'raw_rows_used':kept,'overlapping_raw_rows_discarded':removed,'rth_rows':len(result)}


def complete_rth_sessions(data:pd.DataFrame)->tuple[list[tuple[str,pd.DataFrame]],dict]:
    complete=[];excluded=[]
    for date,g in data.groupby('date_et',sort=True):
        g=g.sort_values('timestamp_et').reset_index(drop=True)
        if len(g)==390 and int(g.minute_et.iloc[0])==571 and int(g.minute_et.iloc[-1])==960 and g.minute_et.diff().iloc[1:].eq(1).all() and g.contract.nunique()==1:
            complete.append((date,g))
        else:
            excluded.append({'date':date,'rows':int(len(g)),'contracts':int(g.contract.nunique())})
    return complete,{'complete_rth_sessions':len(complete),'excluded_sessions':len(excluded),'excluded_samples':excluded[:12]}


def wilder_update(previous:float|None,seed:list[float],true_range:float)->float|None:
    if previous is not None:
        return ((ATR_N-1)*previous+true_range)/ATR_N
    seed.append(true_range)
    return float(np.mean(seed)) if len(seed)==ATR_N else None


def new_candidate(g:pd.DataFrame,previous_close:float|None,atr:float|None,rollover:bool)->dict|None:
    if previous_close is None or atr is None or atr<=0 or rollover:
        return None
    op=float(g.iloc[0].open)
    gap=op-previous_close
    ratio=abs(gap)/atr
    if not (GAP_LOW<=ratio<GAP_HIGH) or gap==0:
        return None
    direction=-1 if gap>0 else 1
    first5=g.iloc[:5]
    if direction==-1 and float(first5.low.min())<=previous_close:return None
    if direction==1 and float(first5.high.max())>=previous_close:return None
    if direction==-1 and float(first5.iloc[-1].close)>=op:return None
    if direction==1 and float(first5.iloc[-1].close)<=op:return None
    enter=g.iloc[5]
    price=float(enter.open)+direction*SLIP
    if (direction==-1 and price<=previous_close) or (direction==1 and price>=previous_close):
        return None
    ticks=max(1,int(np.ceil((STOP_MULT*atr)/TICK-1e-12)))
    stop=price-direction*ticks*TICK
    return {'dir':direction,'entry':price,'stop':stop,'target':previous_close,'stop_ticks':ticks,
            'entry_clock':enter.timestamp_et.isoformat(),'gap_ratio':ratio,'atr_prev':atr}


def execute_candidate(g:pd.DataFrame,candidate:dict)->dict|None:
    direction=candidate['dir'];entry=candidate['entry'];stop=candidate['stop'];target=candidate['target']
    # Next-bar open after 09:35 decision is 09:36 EOB bar open.
    event=None
    for i in range(5,len(g)):
        row=g.iloc[i];minute=int(row.minute_et)
        if minute>690:break
        low=float(row.low);high=float(row.high);op=float(row.open)
        hit_stop=low<=stop if direction==1 else high>=stop
        hit_target=high>=target if direction==1 else low<=target
        if hit_stop:
            # Order-path ambiguity resolved to stop first; gap through stops conservatively priced.
            fill_base=min(op,stop) if direction==1 else max(op,stop)
            event=(fill_base-direction*SLIP,str(row.timestamp_et), 'STOP_AMBIGUOUS_FIRST' if hit_target else 'STOP')
            break
        if hit_target:
            event=(target,str(row.timestamp_et),'PDC_LIMIT_TOUCH')
            break
    if event is None:
        next_bar=g[g.minute_et==691]
        if len(next_bar)!=1: return None
        event=(float(next_bar.iloc[0].open)-direction*SLIP,str(next_bar.iloc[0].timestamp_et),'TIME_EXIT')
    fill,clock,reason=event
    gross_points=direction*(fill-entry)
    slippage_adverse_risk=(candidate['stop_ticks']*TICK+SLIP)*POINT_ES+FEE_ES_RT
    risk_mes=(candidate['stop_ticks']*TICK+SLIP)*POINT_MES+FEE_MES_RT
    return {'entry_clock':candidate['entry_clock'],'exit_clock':clock,'direction':'LONG' if direction==1 else 'SHORT',
      'entry_price':entry,'exit_price':fill,'target':target,'stop':stop,'stop_ticks':candidate['stop_ticks'],
      'stop_risk_ES_usd':round(slippage_adverse_risk,2),'stop_risk_MES_usd':round(risk_mes,2),
      'gap_atr':round(candidate['gap_ratio'],5),'atr_prev':round(candidate['atr_prev'],5),
      'reason':reason,'gross_points':gross_points,
      'net_es_usd':round(gross_points*POINT_ES-FEE_ES_RT,2),
      'net_mes_usd':round(gross_points*POINT_MES-FEE_MES_RT,2),
      'net_es_free_usd':round(gross_points*POINT_ES-FREE_FEE_ES_RT,2),
      'net_mes_free_usd':round(gross_points*POINT_MES-FREE_FEE_MES_RT,2),
      'stop_risk_ES_free_usd':round((candidate['stop_ticks']*TICK+SLIP)*POINT_ES+FREE_FEE_ES_RT,2),
      'stop_risk_MES_free_usd':round((candidate['stop_ticks']*TICK+SLIP)*POINT_MES+FREE_FEE_MES_RT,2)}


def generate_trades(sessions:list[tuple[str,pd.DataFrame]])->list[dict]:
    rows=[];atr=None;seed=[];prev_close=None;prev_contract=None; prev_date=None
    for date,g in sessions:
        contract=str(g.iloc[0].contract)
        rollover=prev_contract is not None and contract!=prev_contract
        cand=new_candidate(g,prev_close,atr,rollover)
        if cand is not None:
            tr=execute_candidate(g,cand)
            if tr is None:raise ValueError('Missing time-exit 11:31 bar on '+date)
            tr.update(date=date,contract=contract)
            rows.append(tr)
        today_high=float(g.high.max());today_low=float(g.low.min());close=float(g.iloc[-1].close)
        tr=max(today_high-today_low,abs(today_high-prev_close),abs(today_low-prev_close)) if prev_close is not None and not rollover else today_high-today_low
        atr=wilder_update(atr,seed,tr)
        prev_close=close;prev_contract=contract;prev_date=date
    return rows


def summarize(trades:list[dict],diag:dict)->dict:
    df=pd.DataFrame(trades)
    if df.empty:raise RuntimeError('No ES PDC signals')
    df['year']=pd.to_datetime(df.date).dt.year
    df['month']=df.date.str.slice(0,7)
    if set(df.year)-set(range(2020,2025)):
        raise ValueError('ES holdout leakage')
    def money_metrics(col):
        vals=df[col].to_numpy(float);pos=vals[vals>0].sum();neg=-vals[vals<0].sum()
        eq=np.cumsum(vals); running_peak=np.maximum.accumulate(np.r_[0,eq])[1:]
        return {'n':len(vals),'net':round(float(vals.sum()),2),'expectancy':round(float(vals.mean()),2),
                'profit_factor':round(float(pos/neg),3) if neg>0 else None,
                'max_closed_trade_drawdown':round(float(np.max(running_peak-eq)),2)}
    risk=df.stop_risk_ES_usd.to_numpy(float)
    days=pd.to_datetime(df.date.drop_duplicates().sort_values()).to_numpy()
    gaps=np.diff(days).astype('timedelta64[D]').astype(int)
    per_year=df.groupby('year',sort=True).agg(trades=('net_es_usd','size'),es_net=('net_es_usd','sum'),mes_net=('net_mes_usd','sum')).round(2)
    result={
        'authority':'EXPLORATORY_DEVELOPMENT_TRANSPORT_ONLY_NEWS_MISSING_NO_OOS',
        'holdouts_read':{'ES_2025':False,'ES_2026':False,'MES_2026':False},
        'data':diag,
        'news_filter':'NOT_AVAILABLE__NO_NEWS_ENTRY_OR_EXIT_FILTER__NOT_FROZEN_PDC_PARITY',
        'fills':'2 ticks adverse entry and stop/time market exits; touch-fill PDC limit, stop-first ambiguity',
        'ES_1_CONTRACT':money_metrics('net_es_usd'),
        'MES_1_CONTRACT_SAME_ES_DERIVED_SIGNALS':money_metrics('net_mes_usd'),
        'NINJATRADER_FREE_FEE_SCENARIO':{
            'source':'Operator supplied all-in Free per side * 2; do not conflate with MFFU',
            'ES_fee_round_trip_usd':FREE_FEE_ES_RT,'MES_fee_round_trip_usd':FREE_FEE_MES_RT,
            'ES':money_metrics('net_es_free_usd'),
            'MES_same_ES_derived_signals':money_metrics('net_mes_free_usd'),
            'ES_stop_risk_median':round(float(df.stop_risk_ES_free_usd.median()),2),
            'ES_stop_risk_p95':round(float(df.stop_risk_ES_free_usd.quantile(.95)),2),
            'ES_stop_risk_max':round(float(df.stop_risk_ES_free_usd.max()),2),
            'ES_stop_risk_gt_2000':int((df.stop_risk_ES_free_usd>2000).sum())
        },
        'ES_risk':{'median':round(float(np.median(risk)),2),'p95':round(float(np.quantile(risk,.95)),2),'max':round(float(risk.max()),2),
                   'n_gt_200':int((risk>200).sum()),'n_gt_500':int((risk>500).sum()),'n_gt_1000':int((risk>1000).sum()),'n_gt_2000':int((risk>2000).sum()),
                   'veto_ES_single_contract':bool((risk>2000).any())},
        'activity':{'trade_days':len(days),'months_with_trades':int(df.month.nunique()),'months_total':60,
                    'gaps_above_7_days':int((gaps>7).sum()),'longest_gap_days':int(gaps.max()) if gaps.size else None},
        'es_years':[{"year":int(year),**{k:round(float(v),2) for k,v in row.items()}} for year,row in per_year.to_dict('index').items()],
        'exit_types':{str(k):int(v) for k,v in df.reason.value_counts().items()},
        'stress_es_usd':{
            'baseline':round(float(df.net_es_usd.sum()),2),
            'plus_1_extra_tick_per_side':round(float(df.net_es_usd.sum()-df.shape[0]*2*TICK*POINT_ES),2),
            'plus_2_extra_ticks_per_side':round(float(df.net_es_usd.sum()-df.shape[0]*4*TICK*POINT_ES),2)
        },
        'limitations':['Historical ES 1m only, selected MES thresholds carry selection bias',
                       'No USD high/medium news blackout; no live approval',
                       'No tick sequencing or target fill queue validation','No 2025/2026 outcomes used']
    }
    return result


def main()->None:
    manifests=required_manifest()
    es,ingestion=load_es_development(manifests)
    sessions,sessions_info=complete_rth_sessions(es)
    rows=generate_trades(sessions)
    report=summarize(rows,{**ingestion,**sessions_info})
    OUTPUT.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT/'ES_PDC_TRANSPORT_TRADES_2020_2024.csv',index=False)
    (OUTPUT/'ES_PDC_TRANSPORT_REPORT_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=='__main__':main()