#!/usr/bin/env python3
"""NQ-H04 preregistered overnight+opening compression, DEV 2020-2024 only.

The loader explicitly opens ZIP members containing /development_2020_2024/;
2025 and 2026 contents are NEVER opened. No direction / trade P&L is inferred.
"""
from __future__ import annotations
import argparse
import json
import re
import zipfile
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import pandas as pd

EXACT = re.compile(r'NQ_(03|06|09|12)-(20|21|22|23|24|25)_20(20|21|22|23|24)_Minute_Last[.]txt$')
SEED=20261009
BOOTSTRAPS=10000


def roll_contract(d:date) -> str:
    for expiry_month in (3,6,9,12):
        first=date(d.year,expiry_month,1)
        third_friday=first+timedelta(days=(4-first.weekday())%7+14)
        if d < third_friday-timedelta(days=8):
            return f'NQ_{expiry_month:02d}-{d.year%100:02d}'
    return f'NQ_03-{(d.year+1)%100:02d}'


def read_selected(zip_path:Path):
    rth_frames=[]; overnight_summaries=[]
    with zipfile.ZipFile(zip_path) as z:
        members=[x for x in z.namelist()
                 if '/development_2020_2024/' in x and EXACT.fullmatch(x.rsplit('/',1)[-1])]
        if len(members)!=25:raise ValueError(f'Expected 25 NQ development contract partitions, got {len(members)}')
        for ix,member in enumerate(sorted(members)):
            match=EXACT.fullmatch(member.rsplit('/',1)[-1]);mm,yy,bar_year=match.groups()
            contract=f'NQ_{mm}-{yy}'
            # Only explicitly allowed zip members are read. NO 2025 or 2026 prices.
            with z.open(member) as f:
                raw=pd.read_csv(f,sep=';',header=None,
                    names=['timestamp','open','high','low','close','volume'],dtype={'timestamp':'string'})
            ts=pd.to_datetime(raw.timestamp,format='%Y%m%d %H%M%S',utc=True,errors='raise')
            if not bool((ts.dt.year==int('20'+bar_year)).all()):
                raise ValueError('Unexpected bar year within development: '+member)
            et=ts.dt.tz_convert('America/New_York')
            minutes=et.dt.hour*60+et.dt.minute
            is_rth=minutes.between(571,960)
            is_on=(minutes>=1081)|(minutes<=570)
            selected=is_rth|is_on
            if not bool(selected.any()):continue
            raw=raw.loc[selected,['high','low','close']].copy()
            et=et.loc[selected];mins=minutes.loc[selected]
            local_day=et.dt.tz_localize(None).dt.normalize()
            session_day=local_day+pd.to_timedelta((mins>=1081).astype('int8'),unit='D')
            raw['session']=session_day.dt.strftime('%Y-%m-%d').to_numpy()
            raw['minute']=mins.to_numpy()
            raw['rth']=is_rth.loc[selected].to_numpy()
            valid_years=raw.session.str[:4].isin(['2020','2021','2022','2023','2024'])
            raw=raw.loc[valid_years]
            # Single selected contract per session, preventing contract overlap.
            days=raw.session.unique()
            qualifying={d for d in days if roll_contract(date.fromisoformat(d))==contract}
            raw=raw[raw.session.isin(qualifying)]
            if len(raw)==0:continue
            rth=raw[raw.rth]
            on=raw[~raw.rth]
            if len(rth):rth_frames.append(rth[['session','minute','high','low','close']])
            if len(on):
                overnight_summaries.append(on.groupby('session',sort=False).agg(
                    on_bars=('minute','size'),on_high=('high','max'),on_low=('low','min')))
            if ix%5==4:print('Development files opened:',ix+1,'/25',flush=True)

    if not rth_frames or not overnight_summaries:raise ValueError('No permitted data')
    rth=pd.concat(rth_frames,ignore_index=True)
    ov=pd.concat(overnight_summaries)
    # A local session should appear in exactly one contract because of fixed roll.
    if ov.index.duplicated().any():raise ValueError('Overlapping overnight selected contracts')
    count=rth.groupby('session',sort=True).agg(
        n=('minute','size'), unique=('minute','nunique'),start=('minute','min'),end=('minute','max'))
    full=count.index[(count.n==390)&(count.unique==390)&(count.start==571)&(count.end==960)]
    rows=[]
    for session,g in rth[rth.session.isin(full)].groupby('session',sort=True):
        # Minute labels must be precisely contiguous 09:31..16:00.
        ordered=g.sort_values('minute')
        mins=ordered.minute.to_numpy()
        if not np.array_equal(mins,np.arange(571,961)):raise ValueError('RTH gap on '+session)
        if session not in ov.index:continue
        on=ov.loc[session]
        if int(on.on_bars)<800:continue
        r=ordered[['high','low','close']].to_numpy(float)
        signal_close=r[14,2] # EOB 09:45, is known at signal decision
        or_range=(float(r[:15,0].max())-float(r[:15,1].min()))*10000/signal_close
        ov_range=(float(on.on_high)-float(on.on_low))*10000/signal_close
        # Future 09:46..10:15; never participates in compression features.
        fut_range=(float(r[15:45,0].max())-float(r[15:45,1].min()))*10000/signal_close
        if not all(np.isfinite(x) and x>0 for x in (or_range,ov_range,fut_range)):
            continue
        rows.append({'session':session,'year':int(session[:4]),
                     'overnight_bars':int(on.on_bars),'overnight_range_bps':ov_range,
                     'opening_15m_range_bps':or_range,'future_30m_range_bps':fut_range})
    d=pd.DataFrame(rows).sort_values('session').reset_index(drop=True)
    if len(d)<1000:raise ValueError(f'Unexpectedly few complete NQ RTH+overnight sessions: {len(d)}')
    return d,{'nq_rth_full':len(full),'nq_overnight_and_rth_eligible':len(d),
              'ineligible_overnight_or_nonpositive_range':len(full)-len(d),
              'zip_development_partitions':25,'holdout_2025_or_2026_bar_content_opened':False}


def compute_h04(d:pd.DataFrame):
    records=[]
    for i in range(20,len(d)):
        prev=d.iloc[i-20:i]
        current=d.iloc[i]
        median_on=float(prev.overnight_range_bps.median())
        median_or=float(prev.opening_15m_range_bps.median())
        median_future=float(prev.future_30m_range_bps.median())
        if median_future<=0:raise ValueError('Invalid past-only future benchmark')
        compressed=bool(current.overnight_range_bps<=median_on and current.opening_15m_range_bps<=median_or)
        outcome=float(np.log(current.future_30m_range_bps/median_future))
        records.append({'session':current.session,'year':int(current.year),
            'compressed':compressed,'overnight_range_bps':float(current.overnight_range_bps),
            'opening_15m_range_bps':float(current.opening_15m_range_bps),
            'next30_range_bps':float(current.future_30m_range_bps),
            'past20median_next30_range_bps':median_future,'z_log_future_range_ratio':outcome,
            'week':str(pd.Timestamp(current.session).to_period('W-SUN'))})
    e=pd.DataFrame(records)
    weekrows=[]
    for week,g in e.groupby('week',sort=True):
        a=g[g.compressed];b=g[~g.compressed]
        if len(a)==0 or len(b)==0:continue
        weekrows.append({'week':week,'year':int(g.year.mode().iloc[0]),
                         'compressed_days':len(a),'control_days':len(b),
                         'difference_mean_log_relative_future_vol':float(
                             a.z_log_future_range_ratio.mean()-b.z_log_future_range_ratio.mean())})
    w=pd.DataFrame(weekrows)
    if w.empty:raise ValueError('No matched weeks')
    return e,w


def bh_fdr(pvals:dict[str,float]):
    keys=sorted(pvals,key=pvals.get)
    q=1.0; out={}
    for rank,key in reversed(list(enumerate(keys,start=1))):
        q=min(q,len(keys)*pvals[key]/rank)
        out[key]=round(float(q),6)
    return out


def test_effect(e:pd.DataFrame,w:pd.DataFrame,source:dict):
    rng=np.random.default_rng(SEED)
    x=w.difference_mean_log_relative_future_vol.to_numpy(float)
    observed=float(x.mean())
    n=len(x)
    # Weekly sign flips: the unit for inference is an independently dated calendar-week pair.
    chunk_size=250
    null=[]; boot=[]
    for start in range(0,BOOTSTRAPS,chunk_size):
        step=min(chunk_size,BOOTSTRAPS-start)
        signs=rng.choice([-1,1],size=(step,n))
        null.extend((signs*x).mean(axis=1))
        sample=rng.integers(0,n,size=(step,n))
        boot.extend(x[sample].mean(axis=1))
    p=float((1+np.sum(np.asarray(null)>=observed))/(1+BOOTSTRAPS))
    ci90=np.quantile(boot,[.05,.95]).tolist();ci95=np.quantile(boot,[.025,.975]).tolist()
    old_p={'NQ-H01':0.44831,'NQ-H02':0.20016,'NQ-H03':0.97640}
    pvals={**old_p,'NQ-H04':p};qvals=bh_fdr(pvals)
    yearly={}
    for year in range(2020,2025):
        d=e[e.year==year];g=w[w.year==year]
        yearly[str(year)]={'compressed':int(d.compressed.sum()),
                            'control':int((~d.compressed).sum()),
                            'matched_weeks':len(g),
                            'mean_matched_week_difference_log_ratio':round(float(g.difference_mean_log_relative_future_vol.mean()),6) if len(g) else None}
    years_positive=sum(val['mean_matched_week_difference_log_ratio'] is not None and val['mean_matched_week_difference_log_ratio']>0 for val in yearly.values())
    qualifies={'more_than_150_events':int(e.compressed.sum())>150,
              'predicted_positive_effect':observed>0,
              '90pct_ci_above_zero':ci90[0]>0,
              'BH_q_four_hypotheses_at_most_010':qvals['NQ-H04']<=.10,
              'yearly_consistency_at_least_3_of_5':years_positive>=3,
              'unmodified_pre_registered_rules':True}
    return {'scope':'2020-2024 DEVELOPMENT NQ ONLY; H04 NON-DIRECTIONAL exploratory magnitude prediction',
            'preregistration':'research/nq/NQ_H04_OVERNIGHT_COMPRESSION_PREREG_2026_10_09.md',
            'source':source,'trading_days_scored_after_20_day_warmup':len(e),
            'compressed_signal_days':int(e.compressed.sum()),
            'noncompressed_control_days':int((~e.compressed).sum()),
            'paired_calendar_weeks':len(w),
            'unpaired_weeks':int(e.week.nunique()-len(w)),
            'mean_z_compressed':round(float(e[e.compressed].z_log_future_range_ratio.mean()),6),
            'mean_z_controls':round(float(e[~e.compressed].z_log_future_range_ratio.mean()),6),
            'primary_equal_weight_paired_week_effect_log_ratio':round(observed,6),
            'primary_90pct_week_bootstrap_CI_log_ratio':list(map(lambda z:round(float(z),6),ci90)),
            'primary_95pct_week_bootstrap_CI_log_ratio':list(map(lambda z:round(float(z),6),ci95)),
            'one_sided_p_week_sign_flips':round(p,6),
            'exploratory_BH_four_family_p_values':pvals,
            'exploratory_BH_four_family_q_values':qvals,
            'positive_years_by_matched_week':years_positive,'yearly':yearly,
            'new_exploratory_gate1_checks':qualifies,
            'decision':'PROMISING_EXPLORATORY_VOLATILITY_ONLY' if all(qualifies.values()) else 'NOT_SUPPORTED_EXPLORATORY',
            'limitations':['No trade direction: cannot infer monetary edge or slippage/commission PnL from H04',
                           'H01-H03 were examined earlier; combined BH is an exploratory bookkeeping step, NOT confirmatory Holm',
                           'Overlap of session signal events and exposure creates dependent observations; paired-week inference approximate',
                           'Zero heldout 2025/2026 price content read; no post-hoc subgroup selection']}


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument('--zip',type=Path,required=True)
    arg.add_argument('--out',type=Path,default=Path('results/nq_h04_overnight_compression'))
    args=arg.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    d,source=read_selected(args.zip)
    e,w=compute_h04(d)
    r=test_effect(e,w,source)
    e.to_csv(args.out/'NQ_H04_DEV_EVENTS_2020_2024.csv',index=False)
    w.to_csv(args.out/'NQ_H04_DEV_MATCHED_WEEKS_2020_2024.csv',index=False)
    (args.out/'NQ_H04_DEV_REPORT_2020_2024.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r,indent=2))


if __name__=='__main__':main()