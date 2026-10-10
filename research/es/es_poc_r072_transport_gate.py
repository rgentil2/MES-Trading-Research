#!/usr/bin/env python3
"""ES 2020-2024 exploratory fixed-rule transport of POC (H15/0.45ATR), R072 (H30/0.70ATR).

NO 2025/2026, NO news filter, no tick queue fill proof.  Not MES parity or funded-ready.
No retrospective parameter search. Non-backadjusted quarterly ES DoNotMerge RTH data.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from research.es.es_pdc_transport_gate import required_manifest,read_contract,complete_rth_sessions
from research.mes_pdc_small_gap_reconstruction import daily_context
from research.mes_poc_breakdown_reconstruction import build_levels,build_events
from research.mes_parameter_walkforward_p1 import build_signal_trades
from research.archive.B13.b13_high_directional_triggers import block_features
from research.archive.B12.b12_strategy_architecture import prepare_rth

# Prespecified frozen ES port; absolute ES and MES monetary risks differ 10x per point.
SPEC={"POC":{"stop_atr":0.45,"horizon":15,"entry_cutoff":690},
      "R072":{"stop_atr":0.70,"horizon":30,"entry_cutoff":660}}
POINT={"ES":50.0,"MES":5.0}
FEE={"ES":4.68,"MES":1.90}  # Original MFFU comparison, unchanged
_FREE_TABLE=json.loads((ROOT/"research/costs/NINJATRADER_FREE_ALL_IN_124_SYMBOLS_2026_10_09.json").read_text(encoding="utf-8"))["rates"]
FREE_FEE={asset:float(_FREE_TABLE[asset]["all_in_free_round_trip_usd"]) for asset in ("ES","MES")}
# FREE_FEE ES=$5.74/MES=$1.88 round trip. Slippage is separate.
TICK=0.25
SLIPPAGE_TICKS=2
SLIP=TICK*SLIPPAGE_TICKS
YEARS=range(2020,2025)
OUT=ROOT/"results/es_poc_r072_transport"


def load_raw_dev():
    records=required_manifest()
    # Strictly load ONLY 20 quarterly 2020-2024 contracts; do not touch heldouts.
    chunks=[];last=None;discarded=0;total=0
    for rec in records:
        x=read_contract(rec)
        total+=len(x)
        end=x.timestamp.iloc[-1]
        if last is not None:
            original=len(x)
            x=x[x.timestamp>last].copy()
            discarded+=original-len(x)
        if x.empty:raise ValueError('Contract contributed no rows: '+rec['contract'])
        chunks.append(x)
        last=end
    d=pd.concat(chunks,ignore_index=True)
    if not d.timestamp.is_monotonic_increasing or d.timestamp.duplicated().any():
        raise ValueError('Bad rollover/timestamp integrity')
    if (d.timestamp>=pd.Timestamp('2025-01-01',tz='UTC')).any():
        raise ValueError('STOP: ES holdout leak detected')
    d=d.rename(columns={'timestamp':'timestamp_utc'})
    d['timestamp_et']=d.timestamp_utc.dt.tz_convert('America/New_York')
    d['session_date']=d.timestamp_et.dt.strftime('%Y-%m-%d')
    d['year']=d.timestamp_et.dt.year
    d=d[d.year.between(2020,2024)].copy()
    # Note: retain overnight for causal H017 regime engine (R072), unlike PDC-only screening.
    return d,{'dev_quarterly_contracts':len(records),'stitched_rows':len(d),'raw_rows':total,'overlaps_removed':discarded,'2025_2026_opened':False}


def full_rth_groups(raw):
    _,groups=prepare_rth(raw)
    groups={k:g for k,g in groups.items() if int(g.year.iloc[0])<=2024
            and g.minute.diff().iloc[1:].eq(1).all()}
    if not groups:raise ValueError('No full contiguous RTH sessions')
    return groups


def find_signal_index(g, clock):
    matched=np.flatnonzero(g.timestamp_et.eq(clock).to_numpy())
    if len(matched)!=1:return None
    return int(matched[0])


def execute(g,signal_pos,side,atr,strategy):
    """Stop first, fill at stop/gap worse by 2 ticks, time order next open after H close.

    Original NinjaTrader exported Entry time corresponds to EOB signal label, i.e.
    next candle OPEN. Time-exit market order sent at signal+H close and filled
    next candle OPEN (signal index +H+1).
    """
    spec=SPEC[strategy];h=spec['horizon']
    entry_pos=signal_pos+1
    time_exit_pos=signal_pos+h+1
    if time_exit_pos>=len(g) or signal_pos<0 or atr<=0:return None
    if any(g.timestamp_et.iloc[i]-g.timestamp_et.iloc[i-1]!=pd.Timedelta(minutes=1)
           for i in range(signal_pos+1,time_exit_pos+1)):
        return None
    sig=g.iloc[signal_pos];bar=g.iloc[entry_pos]
    direction=1 if side=='LONG' else -1
    entry=float(bar.open)+direction*SLIP
    st_ticks=max(1,int(np.ceil(spec['stop_atr']*float(atr)/TICK-1e-12)))
    stop=entry-direction*st_ticks*TICK
    chosen=None
    for i in range(entry_pos,time_exit_pos):
        b=g.iloc[i]
        hit=(float(b.low)<=stop) if direction>0 else (float(b.high)>=stop)
        if hit:
            base=min(float(b.open),stop) if direction>0 else max(float(b.open),stop)
            chosen=(base-direction*SLIP,g.timestamp_et.iloc[i],"STOP")
            break
    if chosen is None:
        b=g.iloc[time_exit_pos]
        chosen=(float(b.open)-direction*SLIP,b.timestamp_et,"TIME")
    exit_px,exit_ts,exit_type=chosen
    gross_pts=(exit_px-entry)*direction
    row=dict(strategy=strategy,signal_et=str(sig.timestamp_et),entry_et=str(sig.timestamp_et),
             exit_et=str(exit_ts),date=str(sig.session_date),year=int(sig.year),
             side=side,contract=str(sig.contract),entry_price=entry,
             exit_price=exit_px,sl_ticks=st_ticks,atr_prev=float(atr),stop_price=stop,
             exit_type=exit_type,gross_points=gross_pts)
    for asset in ('ES','MES'):
        row['net_'+asset.lower()]=round(gross_pts*POINT[asset]-FEE[asset],2)
        row['stop_risk_'+asset.lower()]=round((st_ticks*TICK+SLIP)*POINT[asset]+FEE[asset],2)
        row['net_'+asset.lower()+'_free']=round(gross_pts*POINT[asset]-FREE_FEE[asset],2)
        row['stop_risk_'+asset.lower()+'_free']=round((st_ticks*TICK+SLIP)*POINT[asset]+FREE_FEE[asset],2)
    return row


def stats(df,asset='ES',account='mffu'):
    if df.empty:
        return {'trades':0,'net':0,'pf':None,'dd':None}
    suffix='_free' if account=='ninjatrader_free' else ''
    pnl=df['net_'+asset.lower()+suffix].to_numpy(float)
    s=pnl.cumsum(); dd=np.maximum.accumulate(np.r_[0,s])[1:]-s
    wins=float(pnl[pnl>0].sum());loss=float(-pnl[pnl<0].sum())
    return {'trades':len(df),'net':round(float(pnl.sum()),2),
            'expectancy':round(float(pnl.mean()),2),'pf':round(wins/loss,3) if loss>0 else None,
            'closed_trade_dd':round(float(dd.max()),2),
            'yearly':{str(int(y)):round(float(g['net_'+asset.lower()+suffix].sum()),2)
                      for y,g in df.groupby('year')},
            'stop_risk_median':round(float(df['stop_risk_'+asset.lower()+suffix].median()),2),
            'stop_risk_p95':round(float(df['stop_risk_'+asset.lower()+suffix].quantile(.95)),2),
            'stop_risk_max':round(float(df['stop_risk_'+asset.lower()+suffix].max()),2),
            'stop_risk_gt_500':int((df['stop_risk_'+asset.lower()+suffix]>500).sum()),
            'stop_risk_gt_2000':int((df['stop_risk_'+asset.lower()+suffix]>2000).sum())}


def report_gap(df):
    days=pd.to_datetime(df['date'].drop_duplicates().sort_values())
    diff=days.diff().dt.days.dropna()
    return {'gaps_gt_7':int((diff>7).sum()),'max_gap_days':int(diff.max()) if len(diff) else 0,
            'days':len(days),'months_active':int(df['date'].str.slice(0,7).nunique())}


def build():
    raw,qc=load_raw_dev()
    groups=full_rth_groups(raw)
    # POC previous-session HLC3 volume profile and ATR14 are computed from ES (past-only).
    atr_table=daily_context(groups)
    atr_by_key=atr_table.set_index('group_key')['atr14_prev'].to_dict()
    level_table=build_levels(groups)
    poc_base=build_events(groups,level_table)
    # Original engine: prior 60 complete 15-min blocks / dynamic HIGH state and H017 filter.
    # Crucial: raw includes overnight data, as in the historical MES regime implementation.
    feats=block_features(raw,groups)
    r072_base=build_signal_trades(feats,groups,0.50,660)
    outputs=[]
    candidate_counts={'POC':len(poc_base),'R072':len(r072_base)}
    dropped={}
    for strat,base in [('POC',poc_base),('R072',r072_base)]:
        skipped={'bad_or_missing_signal_index':0,'atr_missing':0,'missing_exit_bars':0}
        for tr in base.itertuples(index=False):
            if int(tr.year)>2024:raise ValueError('HOLDOUT SIGNAL')
            g=groups.get(tr.group_key)
            if g is None:continue
            signal_ts=tr.contact_ts if strat=='POC' else tr.entry_clock_et
            ix=find_signal_index(g,signal_ts)
            if ix is None:
                skipped['bad_or_missing_signal_index']+=1;continue
            atr=atr_by_key.get(tr.group_key,float('nan'))
            if not np.isfinite(atr) or atr<=0:
                skipped['atr_missing']+=1;continue
            side='SHORT' if strat=='POC' else ('LONG' if int(tr.direction)>0 else 'SHORT')
            ev=execute(g,ix,side,atr,strat)
            if ev is None:
                skipped['missing_exit_bars']+=1;continue
            outputs.append(ev)
        dropped[strat]=skipped
    trades=pd.DataFrame(outputs).sort_values(['entry_et','strategy']).reset_index(drop=True)
    if trades.empty:raise ValueError('NO ES POC/R072 TRADES')
    summary={'status':'DEVELOPMENT_DIAGNOSTIC_ONLY_NEWS_DISABLED',
      'holdouts_read':{'ES_2025':False,'ES_2026':False,'MES_2026':False},
      'source':qc,'full_sessions':len(groups),'signal_candidates':candidate_counts,
      'exclusions':dropped,'assumptions':{'slippage_each_market_order_ticks':2,
      'poc_horizon':15,'poc_stop_atr':0.45,'r072_horizon':30,'r072_stop_atr':0.70,
      'news':'NOT APPLIED (cannot claim NinjaTrader parity)',
      'costs_ES_RT':4.68,'costs_MES_RT':1.90,
      'ninjatrader_free_all_in_round_trip_usd':FREE_FEE},
      'strategies':{k:{'ES':stats(z,'ES'),'MES_same_ES_signal':stats(z,'MES'),
                        'activity':report_gap(z)} for k,z in trades.groupby('strategy')},
      'combined_ES_two_independent_orders':stats(trades,'ES'),
      'ninjatrader_free_accounting':{
        'cost_scope':'Free brokerage plan all-in fees from supplied operator screenshot, NOT MFFU fees',
        'strategies':{k:{'ES':stats(z,'ES','ninjatrader_free'),
                          'MES_same_ES_signal':stats(z,'MES','ninjatrader_free')}
                      for k,z in trades.groupby('strategy')},
        'combined_ES_two_independent_orders':stats(trades,'ES','ninjatrader_free')
      },
      'combined_activity':report_gap(trades),
      'limitations':['No news blackouts or forced exits','ES 2020-2024 development tested with previously MES-selected strategy parameters',
       'Tick sequence, stop gaps and limit fills not NinjaTrader verified','2025/2026 holdouts SEALED',
       'Combined ES POC/R072 may conflict/overlap, not risk-routed','ES is same underlying as existing MES PDC']}
    OUT.mkdir(parents=True,exist_ok=True)
    trades.to_csv(OUT/'es_poc_r072_trades_2020_2024_NO_NEWS.csv',index=False)
    (OUT/'es_poc_r072_transport_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':build()