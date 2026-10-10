#!/usr/bin/env python3
"""Strict developmental source QC from user-supplied NQ/MNQ ZIP. NEVER extracts/opens 2025/2026 holds."""
from __future__ import annotations
import zipfile, re, io, json, hashlib, time, collections
from pathlib import Path
import numpy as np
import pandas as pd

import argparse
cli=argparse.ArgumentParser(description='NQ/MNQ 2020-2024 structural source QC (holdouts unopened)')
cli.add_argument('--zip',required=True,type=Path);cli.add_argument('--out',type=Path,default=Path('results/nq_qc_2020_2024'))
args=cli.parse_args();INPUT=args.zip;OUT=args.out
OUT.mkdir(exist_ok=True)
REGEX=re.compile(r'^(NQ|MNQ)_(03|06|09|12)-(20|21|22|23|24|25)_(2020|2021|2022|2023|2024)_Minute_Last\.txt$')
FILE_COLUMNS=['time_utc','open','high','low','close','volume']
results=[]
bySymbol={s:{'rth_per_day':collections.defaultdict(set),'rth_contract_days':collections.Counter(),'session_times':collections.defaultdict(set),'per_year_rows':collections.Counter(),'per_year_rth':collections.Counter(),'prices':[]} for s in ['NQ','MNQ']}

with zipfile.ZipFile(INPUT) as z:
    metadata=[]
    for obj in z.infolist():
        if obj.is_dir(): continue
        parts=obj.filename.replace('\\','/').split('/')
        stage=next((s for s in parts if s in ('development_2020_2024','validation_holdout_2025','pseudo_forward_holdout_2026')),None)
        if stage in ('validation_holdout_2025','pseudo_forward_holdout_2026'):
            # Only metadata; never z.open() or read() this member.
            metadata.append({'stage':stage,'file':parts[-1],'bytes':obj.file_size,'compressed_bytes':obj.compress_size})
    files=[x for x in z.infolist() if 'development_2020_2024' in x.filename.split('/') and x.filename.endswith('.txt')]
    print('DEV files',len(files),'HOLDOUT files metadata',len(metadata),flush=True)
    for index,obj in enumerate(sorted(files,key=lambda q:q.filename),start=1):
        name=obj.filename.split('/')[-1];m=REGEX.fullmatch(name)
        if not m:raise ValueError('Unexpected DEV file '+name)
        symbol,mon,yy,bar_year=m.groups();bar_year=int(bar_year)
        with z.open(obj) as stream:
            df=pd.read_csv(stream,sep=';',header=None,names=FILE_COLUMNS, dtype={'time_utc':'str'},on_bad_lines='error')
        total=len(df)
        bad_times=0
        dt=pd.to_datetime(df.time_utc,format='%Y%m%d %H%M%S',errors='coerce',utc=True)
        bad_times=int(dt.isna().sum())
        if bad_times: raise ValueError(f'{name}: invalid timestamps {bad_times}')
        outsideYear=int((dt.dt.year!=bar_year).sum())
        duplicates=int(dt.duplicated().sum())
        outoforder=int((dt.diff().dropna()<pd.Timedelta(0)).sum())
        griderr=0;bad_price=0;negative_vol=0
        values=df[['open','high','low','close']].to_numpy(dtype='float64')
        griderr=int((np.max(abs(values/.25-np.rint(values/.25)),axis=1)>1e-6).sum())
        bad_price=int((~np.isfinite(values).all(axis=1) | (df.high<df[['open','close']].max(axis=1)).to_numpy() | (df.low>df[['open','close']].min(axis=1)).to_numpy() | (df.low>df.high).to_numpy() | (values<=0).any(axis=1)).sum())
        negative_vol=int(((df.volume<=0)|df.volume.isna()).sum())
        tz=dt.dt.tz_convert('America/New_York')
        clock=tz.dt.hour*60+tz.dt.minute
        weekday=tz.dt.dayofweek
        mask=((clock>=571)&(clock<=960)&(weekday<5)).to_numpy()
        localdate=tz.dt.strftime('%Y-%m-%d').to_numpy()[mask]
        minutes=clock.to_numpy()[mask]
        bs=bySymbol[symbol]
        bs['per_year_rows'][bar_year]+=total
        bs['per_year_rth'][bar_year]+=int(mask.sum())
        for d,mins in pd.DataFrame({'date':localdate,'minute':minutes}).groupby('date'):
            minuteSet=set(mins.minute.tolist())
            bs['rth_per_day'][d].update(minuteSet)
            bs['rth_contract_days'][(name,d)]=len(minuteSet)
        row={'file':name,'symbol':symbol,'expiry_month':int(mon),'expiry_year':2000+int(yy),'bar_year':bar_year,
             'rows':total,'first_utc':dt.iloc[0].isoformat() if total else None,'last_utc':dt.iloc[-1].isoformat() if total else None,
             'raw_bytes':obj.file_size,'crc32_zip':f'{obj.CRC:08x}','invalid_times':bad_times,'wrong_bar_year':outsideYear,
             'duplicates':duplicates,'out_of_order':outoforder,'off_tick_grid':griderr,'invalid_prices':bad_price,
             'nonpositive_volume':negative_vol,'rth_rows':int(mask.sum()),'rth_distinct_days':len(set(localdate))}
        results.append(row)
        if index%10==0:print('QC processed',index,'/50 files',flush=True)
    expected={f'{s}_{m}-{yy}_20{yy}_Minute_Last.txt' for s in ['NQ','MNQ'] for yy in range(20,25) for m in ['03','06','09','12']}
    expected|={f'{s}_03-{yy+1}_20{yy}_Minute_Last.txt' for s in ['NQ','MNQ'] for yy in range(20,25)}
    names={r['file'] for r in results}
    sessionStats={}
    for sym,bs in bySymbol.items():
        days=bs['rth_per_day']
        observed=sorted(days)
        distribution=collections.Counter(len(days[d]) for d in observed)
        full=[d for d in observed if days[d]==set(range(571,961))]
        partial=[{'date':d,'distinct_rth_minutes':len(days[d]),'missing':390-len(days[d])} for d in observed if len(days[d])!=390]
        severe=[p for p in partial if p['missing']>=30]
        byYear={y:{'observed_days':sum(d.startswith(str(y)+'-') for d in observed),
                   'full_390_day_count':sum(d.startswith(str(y)+'-') for d in full),
                   'partial_days':sum(p['date'].startswith(str(y)+'-') for p in partial),
                   'total_rows_all_overlapping_contracts':bs['per_year_rows'][y]} for y in range(2020,2025)}
        sessionStats[sym]={'dates_with_any_RTH_minute':len(observed),'full_390_RTH_days_union_of_contracts':len(full),
                           'partial_RTH_days_union_of_contracts':len(partial),
                           'severe_partial_gt_30_missing_minutes':len(severe),
                           'partial_example_first_15':partial[:15],
                           'partial_example_last_15':partial[-15:],
                           'most_missing_RTH_days':sorted(partial,key=lambda q:-q['missing'])[:15],
                           'yearly':byYear}
    import csv
    with (OUT/'file_quality.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    summary={'scope':'NQ/MNQ DEVELOPMENT ONLY: 2020-2024; sealed 2025/2026 content NOT ACCESSED',
             'archive_name':INPUT.name,'archive_size_bytes':INPUT.stat().st_size,
             'dev_file_count':len(results),'dev_expected_partitions':len(expected),
             'dev_missing_files':sorted(expected-names),'dev_unexpected_files':sorted(names-expected),
             'dev_file_format_problems':{k:sum(row[k] for row in results) for k in ['invalid_times','wrong_bar_year','duplicates','out_of_order','off_tick_grid','invalid_prices','nonpositive_volume']},
             'dev_total_rows':sum(x['rows'] for x in results),'dev_total_rows_per_symbol':{sym:sum(x['rows'] for x in results if x['symbol']==sym) for sym in ['NQ','MNQ']},
             'dev_date_range_by_symbol':{sym:{'first_utc':min(r['first_utc'] for r in results if r['symbol']==sym),'last_utc':max(r['last_utc'] for r in results if r['symbol']==sym)} for sym in ['NQ','MNQ']},
             'holdout_inventory_only':{'validation_holdout_2025':sum(x['stage']=='validation_holdout_2025' for x in metadata),
                                        'pseudo_forward_holdout_2026':sum(x['stage']=='pseudo_forward_holdout_2026' for x in metadata)},
             'holdout_file_metadata_only':metadata,
             'rth_session_coverage_union_not_single_contract':sessionStats,
             'next_steps':['Calculate per-contract non-lookahead rollover selection, not union of contracts','Identify market holidays and true missing active-contract 1m session bars','Implement preregistered NQ-H01..H04 causal features before evaluating price outcomes','Preserve 2025 and 2026 sealed for validation and pseudo-forward']}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print('SUMMARY '+json.dumps({k:summary[k] for k in ['dev_file_count','dev_expected_partitions','dev_missing_files','dev_file_format_problems','dev_total_rows','dev_total_rows_per_symbol','holdout_inventory_only']},ensure_ascii=False),flush=True)
    print('SESSIONS '+json.dumps({s:{k:sessionStats[s][k] for k in ['dates_with_any_RTH_minute','full_390_RTH_days_union_of_contracts','partial_RTH_days_union_of_contracts','severe_partial_gt_30_missing_minutes','most_missing_RTH_days']} for s in sessionStats},ensure_ascii=False)[:2300],flush=True)