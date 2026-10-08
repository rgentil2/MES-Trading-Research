#!/usr/bin/env python3
"""Validate NT8 NQ/MNQ individual 2020-24 Minute Last (no outcome/2025/26 reads)."""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

PATTERN=re.compile(r'^(NQ|MNQ)_(03|06|09|12)-(20|21|22|23|24)_Minute_Last[.]txt$')
OHLC_TICK=.25

def file_qc(path:Path):
    m=PATTERN.fullmatch(path.name)
    if not m: raise ValueError('Not a 2020-24 named contract: '+path.name)
    symbol,mm,yy=m.groups()
    length=0;last_ts=None;first_ts=None;outoforder=0;duplicate=0;bad=0;min_v=None;max_v=None;hash=hashlib.sha256()
    # Stream through 3+ million rows without loading them all into RAM.
    with path.open('rb') as f:
        for data in f:
            hash.update(data)
            line=data.decode('utf-8-sig').strip()
            if not line: continue
            length+=1
            try:
                ts,op,hi,lo,cl,vol=line.split(';')
                dt=datetime.strptime(ts,'%Y%m%d %H%M%S')
                p=[float(v) for v in (op,hi,lo,cl)];v=int(float(vol))
                if not (min(p)<=max(p) and p[2]<=min(p[0],p[3]) and p[1]>=max(p[0],p[3]) and v>0):bad+=1
                if any(abs(q/OHLC_TICK-round(q/OHLC_TICK))>1e-7 for q in p):bad+=1
                if last_ts is not None:
                    if dt<last_ts:outoforder+=1
                    if dt==last_ts:duplicate+=1
                if first_ts is None:first_ts=dt
                last_ts=dt
                min_v=v if min_v is None else min(min_v,v)
                max_v=v if max_v is None else max(max_v,v)
            except Exception:
                bad+=1
                if bad>100:break
    status='QC_PASS_CANDIDATE' if length>=20000 and bad==0 and outoforder==0 and duplicate==0 else 'QC_REVIEW_REQUIRED'
    return {'symbol':symbol,'quarter':mm+'-'+yy,'file':path.name,'bytes':path.stat().st_size,'sha256':hash.hexdigest(),
            'rows':length,'first_utc':first_ts.isoformat() if first_ts else None,'last_utc':last_ts.isoformat() if last_ts else None,
            'bad_rows':bad,'outoforder':outoforder,'duplicates':duplicate,'status':status,
            'reason':'Initial structural QC only; check session completeness/rollover/available provider history before first hypotheses'}

def audit(root:Path):
    found=[]
    for p in sorted(root.glob('*.txt')):
        # Fail closed: never inspect heldout files if added by mistake.
        if not PATTERN.fullmatch(p.name):raise ValueError('Reject unexpected file; heldout 2025/26 must stay sealed: '+p.name)
        found.append(file_qc(p))
    expected={f'{s}_{m}-{y}_Minute_Last.txt' for s in ('NQ','MNQ') for m in ('03','06','09','12') for y in ('20','21','22','23','24')}
    missing=sorted(expected-set(x['file'] for x in found))
    return {'scope':'NO 2025/26 outcomes: filenames restricted to 2020-2024',
            'expected_contracts':40,'received':len(found),'missing':missing,'files':found,
            'status':'ALL_FILES_QC_PASS_CANDIDATE' if not missing and all(x['status']=='QC_PASS_CANDIDATE' for x in found) else 'SOURCE_INCOMPLETE'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--folder',required=True,type=Path);a.add_argument('--output',type=Path,default=None)
    args=a.parse_args()
    report=audit(args.folder)
    output=args.output or args.folder/'nq_mnq_structural_qc.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'scope':report['scope'],'status':report['status'],'expected':40,'received':report['received'],
                      'missing_count':len(report['missing']),'bad':[(f['file'],f['status']) for f in report['files'] if f['status']!='QC_PASS_CANDIDATE']},indent=2))

if __name__=='__main__':main()