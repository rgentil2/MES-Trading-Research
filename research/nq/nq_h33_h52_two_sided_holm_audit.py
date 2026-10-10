#!/usr/bin/env python3
"""H33-H52 reporting correction: exact absolute weekly signflip 2-sided p-values.

Uses *only already frozen development signal events*, not raw/tick or 2025/26.
Reproduces the same fixed-seed signflip RNG draws and bootstrap RNG consumption
of the original primary stats routine, so no scientific rule or path is optimized.
"""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd

SEED=20261009; B=10000; IDS=[f'NQ-H{k:02}' for k in range(33,53)]

def audit(events):
    rng=np.random.default_rng(SEED);out={}
    for h in IDS:
        sub=events.loc[events.hypothesis==h]
        if sub.empty:out[h]=1.0;continue
        grouped=sub.groupby('week').pnl30.agg(['sum','count']).to_numpy(float)
        target=abs(float(sub.pnl30.sum()));n=len(grouped);exceed=0
        for offset in range(0,B,200):
            m=min(200,B-offset)
            flips=rng.choice((-1.,1.),size=(m,n))
            null=(flips*grouped[:,0]).sum(axis=1)
            exceed+=int((np.abs(null)>=target-1e-9).sum())
            _=rng.integers(0,n,size=(m,n)) # advance exactly as frozen bootstrap did
        out[h]=(1+exceed)/(B+1)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--events',type=Path,required=True);p.add_argument('--original-family',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();e=pd.read_csv(a.events)
    if e.year.min()<2020 or e.year.max()>2024 or any(not str(s).startswith(('2020','2021','2022','2023','2024')) for s in e.session):raise ValueError('Unexpected OOS year')
    if len(e)!=2125:raise ValueError('Unexpected event count')
    metrics=json.loads(a.original_family.read_text());pvals=audit(e)
    if set(metrics['family_metrics'])!=set(IDS):raise ValueError('Family mismatch')
    for k,p_two in pvals.items():metrics['family_metrics'][k]['p_value_two_sided']=p_two
    metrics['two_sided_p_correction']={'reason':'Prior min(2p,2(1-p)) is not a valid exact two-sided randomization p-value at endpoints; N=1 had p=0 spuriously', 'calculation':'absolute calendar-week signflip statistic abs(sum grouped signed pnl) with 10,000 permutations and plus-one Monte Carlo correction; original signflip/bootstrap RNG stream matched', 'source':'NQ_H33_H52_EVENTS_2020_2024.csv', 'signal_rules_changed':False,'other_primary_metrics_changed':False, 'holdouts_opened':False}
    a.out.write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'TWO_SIDED_EXACT_SIGNFLIP_FIXED','pvalues':pvals},indent=2))