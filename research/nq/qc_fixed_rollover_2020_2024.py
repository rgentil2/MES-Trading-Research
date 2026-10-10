"""Select NQ/MNQ development RTH contract via FIXED rollover calendar, no market outcome peek."""
import zipfile,re,json,collections,calendar
from datetime import date,timedelta
from pathlib import Path
import pandas as pd, numpy as np
import argparse
cli=argparse.ArgumentParser(description='NQ/MNQ 2020-2024 fixed rollover RTH QA')
cli.add_argument('--zip',required=True,type=Path);cli.add_argument('--out',type=Path,default=Path('results/nq_qc_2020_2024'))
args=cli.parse_args();P=args.zip;O=args.out;O.mkdir(parents=True,exist_ok=True)
PAT=re.compile(r'^(NQ|MNQ)_(03|06|09|12)-(\d\d)_20(20|21|22|23|24)_Minute_Last[.]txt$')

def third_friday(year,month):
    d=date(year,month,1); shift=(4-d.weekday())%7
    return d+timedelta(days=shift+14)

def chosen_contract(local_day):
    y=local_day.year
    for m in (3,6,9,12):
        roll=third_friday(y,m)-timedelta(days=8) # Thursday prior week, fixed before data
        if local_day<roll: return (m,y)
    return (3,y+1)

frames=[];reports=[]
with zipfile.ZipFile(P) as z:
  names=sorted(f for f in z.namelist() if '/development_2020_2024/' in f and f.endswith('.txt'))
  for j,path in enumerate(names,1):
    m=PAT.fullmatch(path.split('/')[-1]); assert m,(path,m)
    sym,expiry_m,expiry_y,bar_y=m.groups();expiry_m=int(expiry_m);expiry_y=2000+int(expiry_y)
    with z.open(path) as src:
      df=pd.read_csv(src,header=None,sep=';',names=['time','open','high','low','close','volume'],dtype={'time':'str'})
    timestamp=pd.to_datetime(df.time,utc=True,format='%Y%m%d %H%M%S').dt.tz_convert('America/New_York')
    minute=timestamp.dt.hour*60+timestamp.dt.minute
    x=df.loc[(minute>=571)&(minute<=960)&(timestamp.dt.dayofweek<5)].copy()
    if x.empty:continue
    x['dt']=timestamp.loc[x.index].to_numpy() # prefer UTC explicit after below
    x['ts_et']=timestamp.loc[x.index].dt.strftime('%Y-%m-%d %H:%M:%S').values
    x['session']=timestamp.loc[x.index].dt.strftime('%Y-%m-%d').values
    x['minute']=minute.loc[x.index].values
    # date -> deterministic contract under expiry-roll policy; includes weekends as none
    keepdates=[s for s in x.session.unique() if chosen_contract(date.fromisoformat(s))==(expiry_m,expiry_y)]
    y=x[x.session.isin(keepdates)].copy()
    if len(y):
      y['symbol']=sym;y['contract']=f'{sym}_{expiry_m:02d}-{expiry_y%100:02d}'
      frames.append(y[['symbol','contract','session','ts_et','minute','open','high','low','close','volume']])
    reports.append({'file':path.split('/')[-1],'rows_rth':len(x),'selected_rth':len(y),'selected_sessions':len(keepdates)})
    if j%15==0: print('ACTIVE',j,'/',len(names),flush=True)
all_rth=pd.concat(frames,ignore_index=True)
all_rth=all_rth.sort_values(['symbol','session','minute'])
results={}
for sym,g in all_rth.groupby('symbol'):
  group=g.groupby('session');agg=group.agg(rows=('minute','size'),distinct_min=('minute','nunique'),min_min=('minute','min'),max_min=('minute','max'),contracts=('contract','nunique'))
  agg['full']=(agg.rows==390)&(agg.distinct_min==390)&(agg.min_min==571)&(agg.max_min==960)&(agg.contracts==1)
  rejects=agg[~agg.full];full=agg[agg.full]
  results[sym]={'selected_RTH_days':int(len(agg)),'complete_selected_days':int(full.shape[0]),'partial_selected_days':int(rejects.shape[0]),
                'duplicate_minute_occurrences':int((g.duplicated(['session','minute']).sum())),
                'partial_days':[{**{'date':k},**{col:int(row[col]) for col in ['rows','distinct_min','min_min','max_min','contracts']}} for k,row in rejects.iterrows()],
                'yearly':{str(y):{'session_days':int((agg.index.str[:4]==str(y)).sum()),'full_days':int((full.index.str[:4]==str(y)).sum()),'partial_days':int((rejects.index.str[:4]==str(y)).sum())} for y in range(2020,2025)}}
  ok=g[g.session.isin(set(full.index))].copy()
  # No raw data export in QC-only pass
  print(sym,'selected',len(agg),'full',len(full),'partial',len(rejects),'sample',results[sym]['partial_days'][:8],flush=True)
( O/'active_contract_rollover_qc.json').write_text(json.dumps({'rule':'Fixed on Thu 8 calendar days before third Friday of each quarterly expiry; deterministic, not selected from PnL','holdouts':'2025 and 2026 never opened; only 2020-2024 development partitions','symbols':results,'per_file':reports},indent=2),encoding='utf-8')