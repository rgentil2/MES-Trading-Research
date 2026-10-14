#!/usr/bin/env python3
"""Research only: deterministic first batch on existing NQ 2020-24 DEV ZIP.

Do not use with the active NinjaTrader strategy transfer. Does not inspect holdout ZIP
members: the existing audited loader accepts 2020-24 development members ONLY.
"""
import argparse
from dataclasses import asdict
import csv
import hashlib
import json
from pathlib import Path
import sys

# The command is run as a file from the repository root. Python sets
# sys.path[0] to this file's folder; add the repo root to find research.nq.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from engine import build_registry, analyze, SEED


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zip',type=Path,required=True,help='Existing private operator export ZIP; no web download')
    p.add_argument('--out',type=Path,required=True,help='NEW private output directory; do not place in public Git repo')
    p.add_argument('--approve-reused-dev',action='store_true',help='Acknowledge 2020-24 heavily reused; no independent statistical proof')
    p.add_argument('--bootstrap',type=int,default=1000)
    args=p.parse_args()
    if not args.approve_reused_dev:p.error('Mandatory: --approve-reused-dev (2020-24 already exhaustively researched)')
    if args.bootstrap<100 or args.bootstrap>10000:p.error('--bootstrap must be 100..10000')
    if not args.zip.is_file():p.error('Source ZIP unavailable; do not substitute market data')
    if args.out.exists():p.error('Refusing overwrite existing output directory')
    if any(x in str(args.out.resolve()).lower() for x in ['mes-trading-research','github']):
        p.error('Private results must be outside GitHub working copy')
    reg=build_registry()
    args.out.mkdir(parents=True)
    manifest={'status':'LOCKED_BEFORE_DATA_READ','seed':SEED,'n_candidates':len(reg),
              'date_policy':'DEV 2020-2024 ONLY; 2025 sealed; 2026 excluded',
              'candidates':[asdict(c) for c in reg]}
    (args.out/'registry_frozen_before_prices.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Registered',len(reg),'candidate specifications BEFORE data read.')
    # Import audit-approved loader from main GitHub research tree, not a new/unverified parser.
    try:
        from research.nq.nq_h05_h07_level_volume_screen import load_development
    except ImportError as exc:
        raise RuntimeError('Run from repository root: python research/strategy_builder_50k/run_builder.py ...') from exc
    dates,days,overnight,qc=load_development(args.zip)
    if len(dates)!=1221:raise ValueError(f'SOURCE_QC_EXPECTED_1221_RTH_SESSIONS_GOT_{len(dates)}')
    report,trades=analyze(days,dates,reg,args.bootstrap)
    report['data_source_qc']=qc
    report['run_started_with_registry_locked']=True
    report['files_2025_opened']=False
    report['files_2026_opened']=False
    (args.out/'report_DEV_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    with (args.out/'candidate_summary_DEV.csv').open('w',newline='',encoding='utf8') as f:
        keys=['id','mechanism','filter','n_train','net_train','pf_train','dd_floating_train','n_internal','net_internal','pf_internal','n_all','net_all','pf_all','monthly_all','q_train','CI90_low','CI90_high','gate','reasons']
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in report['candidates']:
            a,b,z=r['train_2020_22'],r['internal_2023_24'],r['dev_2020_24']
            w.writerow(dict(id=r['id'],mechanism=r['mechanism'],filter=r['filter'],
                n_train=a['n'],net_train=a['net_usd'],pf_train=a['pf'],dd_floating_train=a['floating_dd_proxy_usd'],
                n_internal=b['n'],net_internal=b['net_usd'],pf_internal=b['pf'],
                n_all=z['n'],net_all=z['net_usd'],pf_all=z['pf'],monthly_all=z['trades_per_month'],
                q_train=r['bh_q_train_family_48'],CI90_low=r['ci90_mean_usd_train'][0],
                CI90_high=r['ci90_mean_usd_train'][1],gate=r['gate'],reasons=';'.join(r['reasons'])))
    for k,rows in trades.items():
        if rows:
            with (args.out/f'trades_{k}.csv').open('w',newline='',encoding='utf8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('FINISHED EXPLORATORY DEV ONLY; no 2025/2026 prices read; results are NOT independently validated.')
    print('OUTPUT',args.out)

if __name__=='__main__':main()
