#!/usr/bin/env python3
"""Exploratory ES 1min -> MES proxy transport of FROZEN NQ Strategy Builder V1+V2.

NEVER reads 2025/2026 OHLCV. Only ES development 2020..24 manifest rows.
This is cross-instrument transport, not a clean 144-test discovery or funded evaluation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
SELF=Path(__file__).resolve().parent
for x in (str(ROOT),str(SELF)):
    if x not in sys.path:sys.path.insert(0,x)

import engine
import v2_engine
from v2_engine import build_registry_v2,registry_manifest,analyze_v2
from engine import build_registry,analyze,_bh

MES_POINT_USD=5.0
MES_ROUNDTRIP_FEE_USD=1.90
SEED=20261014


def check_precommit():
    p1=SELF/'CANDIDATES_V1_FROZEN.json'
    p2=SELF/'CANDIDATES_V2_FROZEN.json'
    v1=build_registry(); v2=build_registry_v2()
    if json.loads(p1.read_text(encoding='utf8'))['candidates']!=[asdict(x) for x in v1]:
        raise ValueError('FROZEN_V1_REGISTRY_MISMATCH')
    if json.loads(p2.read_text(encoding='utf8'))!=registry_manifest(v2):
        raise ValueError('FROZEN_V2_REGISTRY_MISMATCH')
    if len(v1)!=48 or len(v2)!=96:
        raise ValueError('WRONG_MULTIPLICITY_UNIVERSE')
    return v1,v2


def holdout_guard():
    root=ROOT/'data_es_staging/raw_lfs'
    if not root.exists():raise FileNotFoundError('ES_LFS_DIRECTORY_MISSING')
    for suffix in ('25','26'):
        for p in root.glob(f'ES_*{suffix}/*_Minute_Last.txt'):
            if p.stat().st_size>1000:
                raise RuntimeError('STOP_SEALED_ES_HOLDOUT_LFS_MATERIALIZED '+str(p))


def load_dev_es():
    # Independently audited ES source loader: manifest strictly 20 DEVELOPMENT,
    # checks rows, byte length, SHA256, tick grid, timestamps, completeness.
    from research.es.es_pdc_transport_gate import (required_manifest,load_es_development,
                                                      complete_rth_sessions)
    holdout_guard()
    records=required_manifest()
    raw,qc=load_es_development(records)
    sessions,selection=complete_rth_sessions(raw)
    holdout_guard()
    if len(sessions)<900 or len(sessions)>1300:
        raise ValueError('UNEXPECTED_ES_RTH_COMPLETE_SESSION_COUNT_'+str(len(sessions)))
    import numpy as np
    dates=[d for d,g in sessions]
    if any(not '2020-01-01'<=d<='2024-12-31' for d in dates):
        raise ValueError('HOLDOUT_DATE_IN_DEV')
    bars=np.stack([g[['open','high','low','close','volume']].to_numpy(dtype=float) for _,g in sessions])
    if bars.shape!=(len(dates),390,5):raise ValueError('BAD_ES_BARS_SHAPE')
    return dates,bars,dict(source='ES_1m_GitLFS_DEVELOPMENT_ONLY',**qc,**selection,
                           LFS_holdouts_2025_2026_not_opened=True)


def set_mes_policy():
    # Instrument-dependent business parameters are intentionally factored from
    # the frozen SIGNALS. NO signal, stop, target, indicator or timing mutation.
    # v2_engine imported values BY VALUE, hence both references are changed.
    engine.POINT_MNQ=MES_POINT_USD
    engine.FEE_MNQ_RT=MES_ROUNDTRIP_FEE_USD
    v2_engine.POINT_MNQ=MES_POINT_USD
    v2_engine.FEE_MNQ_RT=MES_ROUNDTRIP_FEE_USD
    assert engine.POINT_MNQ==v2_engine.POINT_MNQ==5.0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--bootstrap',type=int,default=1000)
    p.add_argument('--allow-existing-dev-reuse',action='store_true')
    p.add_argument('--registry-only',action='store_true')
    a=p.parse_args(argv)
    v1,v2=check_precommit()
    if a.registry_only:
        if a.allow_existing_dev_reuse:p.error('REGISTRY_ONLY_NO_ANALYSIS_ALLOWED')
        print('LOCKED',len(v1)+len(v2),'ES-transport frozen-rule candidates; NO DATA READ')
        return
    if not a.allow_existing_dev_reuse:p.error('Explicit consent flag for heavily reused ES development required')
    if not 100<=a.bootstrap<=10000:p.error('BOOTSTRAP_RANGE')
    out=a.output.resolve()
    if out.exists():p.error('NEVER_OVERWRITE_EXISTING_RESULTS')
    if str(ROOT.resolve()) in str(out):p.error('PRIVATE_RESULT_DIR_MUST_BE_OUTSIDE_REPOSITORY')
    # Check all source/holdout paths before any outcomes are calculated.
    holdout_guard()
    out.mkdir(parents=True)
    (out/'ES_TRANSPORT_PRECOMMIT.json').write_text(json.dumps({
        'status':'REGISTERED_BEFORE_ANY_NEW_ES_OHLCV_READ',
        'v1_count':len(v1),'v2_count':len(v2),
        'v2_hash':registry_manifest(v2)['registry_sha256'],
        'training':'2020-2022','internal':'2023-2024',
        '2025':'SEALED','2026':'EXCLUDED',
        'signal_source':'ES 1m','economic_proxy':'MES 1m',
        'mes_point_usd':MES_POINT_USD,'mes_rt_fee_usd':MES_ROUNDTRIP_FEE_USD,
        'max_contracts':5,'risk_usd_per_trade_ref':250,
        'important':'ES cross-instrument transport of already-researched NQ grammar, NOT OOS'},indent=2)+'\n')
    dates,days,qc=load_dev_es()
    set_mes_policy()
    print('ES SOURCE PASSED',qc['complete_rth_sessions'],'complete RTH sessions. TRAIN + INTERNAL (reused).',flush=True)
    v1_report,v1_trades=analyze(days,dates,v1,replications=a.bootstrap)
    v2_report,v2_trades=analyze_v2(days,dates,v2,replications=a.bootstrap)
    combined={x['id']:x['weekly_p_train'] for x in v1_report['candidates']}
    combined.update({x['id']:x['p_train_one_sided'] for x in v2_report['candidate_results']})
    if len(combined)!=144:raise ValueError('MISSING_OR_DUPLICATED_144_CONTRASTS')
    all_q=_bh(combined)
    candidates=[]
    for x in v1_report['candidates']:
        row=dict(x)
        row['q_144']=all_q[x['id']]
        row['original_gate']=x['gate']
        row['transport_criteria_pass']=(x['gate']=='EXPLORATORY_PASS_NOT_VALIDATED' and row['q_144']<=.10)
        candidates.append(row)
    for x in v2_report['candidate_results']:
        row=dict(x)
        row['q_144']=all_q[x['id']]
        row['original_gate']=x['gate']
        row['transport_criteria_pass']=(x['gate']=='EXPLORATORY_SURVIVOR_NOT_VALIDATED' and row['q_144']<=.10)
        candidates.append(row)
    candidates.sort(key=lambda x:x['id'])
    summary={'status':'ES_1MIN_TO_MES_PROXY_EXPLORATORY_REUSED_DEV_NO_OOS',
             'data_audit':qc,'funding_program_not_verified':True,
             'frozen_rules_v1':48,'frozen_rules_v2':96,'family_tests':144,
             'historical_prior_tests_not_in_q':True,
             'train':'2020-2022','internal':'2023-2024','holdout_2025':'SEALED','2026':'EXCLUDED',
             'instrument_signal':'ES','instrument_pnl':'MES_PROXIED_FROM_ES_BARS',
             'fixed_mes_point_value':MES_POINT_USD,'fee_rt_mes':MES_ROUNDTRIP_FEE_USD,
             'max_micros':5,'slip_ticks_each_side':2,
             'execution_warning':'No independent MES tape, no true tick order of intrabar extremes; historical OHLC stop-first proxy',
             'n_criteria_pass':sum(v['transport_criteria_pass'] for v in candidates),
             'candidates':candidates}
    (out/'ES_BUILDER_REPORT.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    csvfile=out/'ES_BUILDER_ALL144.csv'
    with csvfile.open('w',newline='',encoding='utf8') as f:
        fields=['id','source','n_train','net_train_usd','pf_train','n_internal','net_internal_usd','pf_internal','n_all','net_all_usd','pf_all','trades_per_month','q_144','gate','transport_criteria_pass']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for x in candidates:
            ta=x['train_2020_22']; it=x['internal_2023_24'];all_=x.get('dev_2020_24') or x['all_reused_dev_2020_24']
            writer.writerow(dict(id=x['id'],source='V1' if x['id'].startswith('SB-') else 'V2',n_train=ta['n'],net_train_usd=ta['net_usd'],pf_train=ta['pf'],n_internal=it['n'],net_internal_usd=it['net_usd'],pf_internal=it['pf'],n_all=all_['n'],net_all_usd=all_['net_usd'],pf_all=all_['pf'],trades_per_month=all_['trades_per_month'],q_144=x['q_144'],gate=x['original_gate'],transport_criteria_pass=x['transport_criteria_pass']))
    print('ES BUILDER COMPLETE',len(candidates),'tests, gate-pass',summary['n_criteria_pass'],'no 2025/2026 opened.',flush=True)
    print('RESULTS',out,flush=True)

if __name__=='__main__':main()