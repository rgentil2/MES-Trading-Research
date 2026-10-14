#!/usr/bin/env python3
"""V2 frozen-registry builder: --freeze-only without historical market ZIP.

Reads only NQ development_2020_2024 members using the repository audited loader.
2025 stays sealed and all 2026 excluded; never calls NinjaTrader.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:sys.path.insert(0,str(REPO))
from dataclasses import asdict
from engine import build_registry, analyze, _bh
from v2_engine import build_registry_v2, registry_manifest, analyze_v2

FROZEN_FILE=Path(__file__).with_name('CANDIDATES_V2_FROZEN.json')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--freeze-only',action='store_true',help='No market data read; print frozen registry SHA/count and exit')
    p.add_argument('--zip',type=Path,help='Private historical zip; 2020-24 development only')
    p.add_argument('--out',type=Path,help='New private results directory; must not exist')
    p.add_argument('--approve-reused-dev',action='store_true')
    p.add_argument('--bootstrap',type=int,default=1000)
    a=p.parse_args(argv)
    specs=build_registry_v2(); frozen=registry_manifest(specs)
    v1_file=Path(__file__).with_name('CANDIDATES_V1_FROZEN.json')
    if not v1_file.is_file():p.error('PRECOMMITTED_V1_48_REGISTRY_FILE_MISSING')
    v1_reg=build_registry()
    if json.loads(v1_file.read_text(encoding='utf8')).get('candidates') != [asdict(x) for x in v1_reg]:
        p.error('V1_REGISTRY_DIVERGED; no market reads')
    if not FROZEN_FILE.is_file():p.error('PRECOMMITTED_REGISTRY_FILE_MISSING; no market reads')
    if json.loads(FROZEN_FILE.read_text(encoding='utf8'))!=frozen:
        p.error('PRECOMMITTED_REGISTRY_CHANGED; no market reads')
    print('V2 FROZEN',len(specs),'candidates','SHA256:',frozen['registry_sha256'])
    if a.freeze_only:
        if a.zip or a.out:p.error('FREEZE_ONLY must not have zip/output paths')
        print('NO HISTORICAL DATA READ')
        return
    if not a.approve_reused_dev:p.error('Explicit --approve-reused-dev is required')
    if not a.zip or not a.out or not a.zip.is_file():p.error('--zip and --out required')
    if a.out.exists():p.error('Refusing overwrite of existing output folder')
    if any(t in str(a.out.resolve()).lower() for t in ('mes-trading-research','github')):
        p.error('Derived private market outputs must stay outside GitHub')
    if not 100<=a.bootstrap<=10000:p.error('Invalid --bootstrap')
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'registry_locked_before_data.json').write_text(json.dumps(frozen,indent=2)+'\n')
    from research.nq.nq_h05_h07_level_volume_screen import load_development
    dates,days,overnight,qc=load_development(a.zip)
    if len(dates)!=1221:raise ValueError('SOURCE_QC_EXPECTED_1221_COMPLETE_RTH_SESSIONS')
    # Both frozen Builder cohorts are counted in one BH denominator (144),
    # rather than reporting V2-only p-values as if V1 never happened.
    v1_report,_=analyze(days,dates,v1_reg,replications=a.bootstrap)
    report,work=analyze_v2(days,dates,specs,replications=a.bootstrap)
    combined={r['id']:r['weekly_p_train'] for r in v1_report['candidates']}
    combined.update({r['id']:r['p_train_one_sided'] for r in report['candidate_results']})
    if len(combined)!=144:raise RuntimeError('MULTIPLE_TEST_REGISTER_COUNT_NOT_144')
    adjusted=_bh(combined)
    for r in report['candidate_results']:
        r['bh_q_builder_v1_v2_144']=adjusted[r['id']]
        if adjusted[r['id']]>0.10 and r['gate']=='EXPLORATORY_SURVIVOR_NOT_VALIDATED':
            r['gate']='EXPLORATORY_SCREEN_FAIL'
            r['fail_reasons'].append('BUILDER_COMBINED_BH_Q_144_GT_0_10')
    report['combined_builder_multiplicity_scope']='48_V1_PLUS_96_V2 = 144; earlier H/T hypothesis searches excluded (hence still exploratory)'
    report['v1_replayed_for_multiplicity_registry_hash']=v1_report['registry_sha256']
    report['source_qc']=qc
    (a.out/'report_V2_2020_2024.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    with (a.out/'summary_V2_96.csv').open('w',newline='',encoding='utf8') as f:
        cols=['id','mechanism','context','n_train','net_train','pf_train','n_internal',
              'net_internal','pf_internal','n_all','net_all','pf_all','monthly_all',
              'q_v2_only','q_builder_144','ci90_low','ci90_high','gate','fail_reasons']
        writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
        for r in report['candidate_results']:
            tr=r['train_2020_22'];it=r['internal_2023_24'];al=r['all_reused_dev_2020_24']
            writer.writerow(dict(id=r['id'],mechanism=r['mechanism'],context=r['context'],
                n_train=tr['n'],net_train=tr['net_usd'],pf_train=tr['pf'],
                n_internal=it['n'],net_internal=it['net_usd'],pf_internal=it['pf'],
                n_all=al['n'],net_all=al['net_usd'],pf_all=al['pf'],
                monthly_all=al['trades_per_month'],q_v2_only=r['bh_q_v2_family_96_only'],
                q_builder_144=r['bh_q_builder_v1_v2_144'],
                ci90_low=r['ci90_train'][0],ci90_high=r['ci90_train'][1],
                gate=r['gate'],fail_reasons=';'.join(r['fail_reasons'])))
    # Do not write internal OHLC or market data into the public repository.
    print('V2 DEV 2020-24 COMPLETE; no 2025/2026 bar contents accessed. Outputs:',a.out)

if __name__=='__main__':main()