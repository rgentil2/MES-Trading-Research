#!/usr/bin/env python3
"""MFFU MES 2020-2025 *diagnostic* intraday floating-equity replay.

DOES NOT READ 2026 rows. Historical bar data only; not a certified tick-level
stop, news or risk-manager replay. Avoids treating MAE from disjoint trades as
simultaneous market movement. All times from NT export are interpreted ET.
"""
from __future__ import annotations
import argparse, csv, json, math, re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
CUTOFF_UTC = datetime(2026, 1, 1, tzinfo=timezone.utc)
MFFU_FEE = 1.90
POINT_USD = 5.0
TRADING_END = '2025-12-31'
FILES = [
    ('PDC', 'PDC_NT_2tick_106trades.csv', 106, 591.97),
    ('POC', 'POC_NT_2tick_108trades.csv', 108, 314.46),
    ('R072', 'R072_NT_2tick_149trades.csv', 149, 998.63),
]
R072_EXTRA = ('2021-11-26','2022-05-23','2024-08-02','2025-04-04')

@dataclass(frozen=True)
class Trade:
    id: str
    source: str
    side: int  # 1 long, -1 short
    entry: datetime  # naive local America/New_York wall time, sourced from NinjaTrader export
    exit: datetime
    entry_px: float
    exit_px: float
    pnl_net: float  # NT Profit already net fee; account for +0.02 to MFFU fee
    mae: float

@dataclass(frozen=True)
class Bar:
    time: datetime  # NY end-of-bar local naive time
    o: float
    h: float
    l: float
    c: float
    contract: str


def parse_money(s: str) -> float:
    v = str(s).replace('\u00a0','').replace('\u202f','').replace(' ','').replace('$','').replace('−','-')
    return float(v.replace('.','').replace(',','.')) if ',' in v else float(v)


def parse_nt_time(s: str) -> datetime:
    s = str(s).replace('\u00a0',' ').replace('\u202f',' ').strip()
    m = re.fullmatch(r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}:\d{2})\s+([ap])\s*\.?\s*m\.?', s, re.I)
    if not m:
        raise ValueError(f'Unknown NinjaTrader datetime: {s!r}')
    d = datetime.strptime(m.group(1)+' '+m.group(2), '%d/%m/%Y %I:%M:%S')
    return d.replace(hour=d.hour%12+(12 if m.group(3).lower()=='p' else 0))


def load_trades(directory: Path) -> list[Trade]:
    all_trades = []
    for source, fname, n_expected, expected_net in FILES:
        with (directory/fname).open('r', encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f, delimiter=';'))
        if len(rows) != n_expected:
            raise ValueError(f'{source}: wrong count {len(rows)}, expected {n_expected}')
        gross_net = round(sum(parse_money(r['Profit']) for r in rows),2)
        if not math.isclose(gross_net, expected_net, abs_tol=.021):
            raise ValueError(f'{source}: historical net {gross_net} != {expected_net}')
        for row in rows:
            en, ex = parse_nt_time(row['Entry time']), parse_nt_time(row['Exit time'])
            if en.year>2025 or ex.year>2025:
                raise ValueError('HOLDOUT LOCK: 2026 trade requested')
            if en.date()!=ex.date():
                raise ValueError(f'Unexpected overnight trade, cannot run intraday audit: {row}')
            if ex<en:
                raise ValueError(f'Invalid chronology {row}')
            if int(row['Qty'])!=1:
                raise ValueError('Expected single MES contract')
            all_trades.append(Trade(
                id=source+':'+row['Trade number'],source=source,
                side=(1 if 'long' in row['Market pos.'].lower() else -1),
                entry=en,exit=ex,entry_px=parse_money(row['Entry price']),
                exit_px=parse_money(row['Exit price']),
                pnl_net=round(parse_money(row['Profit']) - (MFFU_FEE-1.88), 2),
                mae=parse_money(row['MAE'])
            ))
    return sorted(all_trades,key=lambda t:(t.entry, ['PDC','POC','R072'].index(t.source)))


def allowed_files(raw_dir:Path) -> list[Path]:
    pat=re.compile(r'^MES (03|06|09|12)-(\d\d)\.Last\.txt$')
    names=[]
    for p in raw_dir.glob('MES *.Last.txt'):
        m=pat.match(p.name)
        if not m:
            continue
        yy=int(m.group(2))
        # MAR26 has essential December 2025 bars. Stream it *only until* 2026-01-01.
        if yy>26 or (yy==26 and int(m.group(1))!=3):
            continue
        if yy>=20:
            names.append((yy,int(m.group(1)),p))
    files=[p for _,_,p in sorted(names)]
    if len(files)!=25:  # 2020-2025 quarters (24) + MAR26 for Dec 2025 only
        raise ValueError(f'Expected 25 quarters including cut-off MAR26, found {len(files)}: {[x.name for x in files]}')
    return files


def read_target_bars(raw_dir: Path, trades: list[Trade]) -> tuple[dict[datetime,Bar],dict]:
    wanted_days={t.entry.date() for t in trades}|{datetime.fromisoformat(x).date() for x in R072_EXTRA}
    files=allowed_files(raw_dir)
    bars={}
    retained_by_contract=Counter()
    ignored_overlaps=0
    prev_contract_last_utc=None
    coverage_cut_at_2026=False
    date_contracts=defaultdict(set)
    last_seen=None
    for path in files:
        this_last=None
        with path.open('r', encoding='utf-8-sig') as f:
            for line in f:
                fields=line.rstrip('\n').split(';')
                if len(fields)<6:
                    continue
                t_utc=datetime.strptime(fields[0].strip(), '%Y%m%d %H%M%S').replace(tzinfo=timezone.utc)
                if t_utc>=CUTOFF_UTC:
                    coverage_cut_at_2026=True
                    break # HARD HOLDOUT STOP - no price or future signal is read
                this_last=t_utc
                if prev_contract_last_utc is not None and t_utc<=prev_contract_last_utc:
                    ignored_overlaps+=1
                    continue
                local=t_utc.astimezone(NY).replace(tzinfo=None)
                if local.year>2025:  # hard secondary NY clock stop
                    continue
                if local.date() not in wanted_days:
                    continue
                try:
                    op, hi, lo, cl=(float(z.replace(',','.')) for z in fields[1:5])
                except (ValueError,TypeError) as exc:
                    raise ValueError(f'{path.name}: malformed OHLC {line[:200]}') from exc
                if not(lo<=op<=hi and lo<=cl<=hi):
                    raise ValueError(f'{path.name}: invalid OHLC {line[:200]}')
                if local in bars:
                    raise ValueError(f'Duplicate minute after rollover: {local}')
                bars[local]=Bar(local,op,hi,lo,cl,path.stem)
                retained_by_contract[path.stem]+=1
                date_contracts[local.date()].add(path.stem)
        if this_last is not None:
            prev_contract_last_utc=this_last
            last_seen=this_last
    return bars,{'raw_files':len(files), 'cut_before_2026':coverage_cut_at_2026,
                 'raw_last_timestamp_below_holdout_utc':str(last_seen),
                 'bar_count_targeted':len(bars), 'overlaps_discarded':ignored_overlaps,
                 'retained_targeted_by_contract':dict(retained_by_contract)}


def apply_router(trades: list[Trade], enable: bool) -> tuple[list[Trade],list[dict]]:
    if not enable: return trades,[]
    accepted=[]; skipped=[];active=[]
    for t in trades:
        active=[a for a in active if a.exit>t.entry]
        if any(a.side!=t.side for a in active):
            skipped.append({'trade_id':t.id,'timestamp':t.entry.isoformat(),'reason':'opposite MES position'})
            continue
        accepted.append(t)
        if t.exit>t.entry: active.append(t)
    return accepted,skipped


def audit_sessions(bars:dict[datetime,Bar]):
    out={}
    for day in R072_EXTRA:
        d=datetime.fromisoformat(day).date()
        found=sorted((b for b in bars.values() if b.time.date()==d and (9,31)<=(b.time.hour,b.time.minute)<=(16,0)),key=lambda x:x.time)
        # 09:31–16:00 inclusive = 390 RTH one-minute bars, except abbreviated sessions.
        times={b.time for b in found}
        missing=[]
        for minute in range(390):
            x=datetime.combine(d,datetime.min.time())+timedelta(hours=9,minutes=31+minute)
            if x not in times: missing.append(x.strftime('%H:%M'))
        out[day]={'rth_count':len(found), 'first':found[0].time.strftime('%H:%M') if found else None,
                  'last':found[-1].time.strftime('%H:%M') if found else None,
                  'missing_count_vs_full_390':len(missing), 'first_missing':missing[:8],
                  'note':'Check exchange abbreviated-session calendar and active contract before accepting this as trade-eligible. 390-bar criterion is not a valid holiday-session rule.'}
    return out


def assess_price_alignment(trades:list[Trade],bars:dict[datetime,Bar]):
    # End-of-bar candle with label entry+1m normally opens at the filled trade's entry clock.
    diffs=[];no_entry=[];not_enough=[]
    for t in trades:
        b=bars.get(t.entry+timedelta(minutes=1))
        if b is None:
            no_entry.append(t.id); continue
        diffs.append({'id':t.id,'diff_points':round(b.o-t.entry_px,4), 'abs_points':round(abs(b.o-t.entry_px),4),
                      'raw_contract':b.contract})
    ordered=sorted(x['abs_points'] for x in diffs)
    out={'matched':len(diffs),'missing_entry_bars':len(no_entry),'missing_trade_ids':no_entry[:20],
         'median_abs_diff_points':ordered[len(ordered)//2] if ordered else None,
         'p95_abs_diff_points':ordered[int(.95*(len(ordered)-1))] if ordered else None,
         'large_diff_gt_3_points':sum(x>3 for x in ordered),
         'largest_abs_price_diff':sorted(diffs,key=lambda x:-x['abs_points'])[:10],
         'required':'Market data/open execution source must be reconciled before floating PnL is certified; expected 2-tick plus bar conventions.'}
    return out


def replay(trades:list[Trade], bars:dict[datetime,Bar], require_complete=True):
    # Model minute OHLC adverse mark, with each position's initial cost estimated as full MFFU RT fee.
    # In a single underlying, aggregate MTM PnL is affine in price, so the low/high choice is feasible
    # for the net position *in that minute*, unlike summing unrelated MAEs from different times.
    bydate=defaultdict(list)
    for t in trades:bydate[t.entry.date()].append(t)
    acct_balance=0.0
    previous_eod_peak=0.0
    eod_floor=-2000.0
    worst_margin=math.inf
    min_close_margin=math.inf
    worst_date=None
    max_intraday_peak=0.0
    peak_to_worst=0.0
    intraday_breach=[]
    missing=[]
    annotated=[]
    total_adverse_events=0
    distinct_trade_days=sorted(bydate)
    for date in distinct_trade_days:
        dt=bydate[date]
        needed=set()
        for t in dt:
            m=t.entry+timedelta(minutes=1)
            while m<=t.exit:
                needed.add(m)
                m+=timedelta(minutes=1)
        missing_minutes=sorted(needed-set(bars))
        if missing_minutes:
            missing.append({'date':date.isoformat(),'count':len(missing_minutes),
                            'examples':[m.isoformat() for m in missing_minutes[:6]]})
            if require_complete:
                continue
        times=sorted(needed & set(bars))
        day_min_margin=math.inf
        day_min_eq=math.inf
        for ts in times:
            open_at=[t for t in dt if t.entry<ts<=t.exit]
            settled_before=sum(t.pnl_net for t in dt if t.exit<ts)
            baseline=acct_balance+settled_before-len(open_at)*MFFU_FEE
            net_direction=sum(t.side for t in open_at)
            base_price=sum(-t.side*t.entry_px*POINT_USD for t in open_at)
            b=bars[ts]
            eq_close=baseline +base_price+net_direction*POINT_USD*b.c
            eq_worst=baseline+base_price+net_direction*POINT_USD*(b.l if net_direction>=0 else b.h)
            margin=eq_worst-eod_floor
            if margin<day_min_margin:
                day_min_margin=margin
            if margin<worst_margin:
                worst_margin=margin;worst_date=ts.isoformat()
            min_close_margin=min(min_close_margin,eq_close-eod_floor)
            day_min_eq=min(day_min_eq,eq_worst)
            max_intraday_peak=max(max_intraday_peak,eq_close)
            peak_to_worst=max(peak_to_worst,max_intraday_peak-eq_worst)
            if margin<=0:
                intraday_breach.append({'at':ts.isoformat(),'float_equity':round(eq_worst,2),'floor':round(eod_floor,2), 'open_trades':[t.id for t in open_at]})
                total_adverse_events+=1
        if missing_minutes and require_complete:
            # Do not advance account past an unknown day, because later floor would be wrong.
            break
        if not math.isfinite(day_min_eq):
            day_min_eq=acct_balance+sum(t.pnl_net for t in dt)
        if not math.isfinite(day_min_margin):
            day_min_margin=day_min_eq-eod_floor
        acct_balance+=sum(t.pnl_net for t in dt)
        previous_eod_peak=max(previous_eod_peak,acct_balance)
        eod_floor=max(-2000.,min(previous_eod_peak-2000.,100.))
        annotated.append({'date':date.isoformat(),'closed_profit_cumulative':round(acct_balance,2),
                          'floating_worst_equity':round(day_min_eq,2),
                          'min_margin_above_EOD_floor':round(day_min_margin,2),
                          'EOD_floor_next_day':round(eod_floor,2)})
    return {'trading_days_processed':len(annotated),'trading_days_total':len(bydate),
            'missing_path_days':missing,
            'float_min_margin_above_MFFU_floor_usd':round(worst_margin,2) if math.isfinite(worst_margin) else None,
            'when_worst_margin':worst_date,
            'min_close_margin_above_floor_usd':round(min_close_margin,2) if math.isfinite(min_close_margin) else None,
            'max_intraday_snapshot_peak_to_adverse_usd':round(peak_to_worst,2),
            'adverse_one_minute_equity_breach_count':total_adverse_events,
            'breach_examples':intraday_breach[:12],
            'final_balance_net':round(acct_balance,2),
            'accounting':'Open-trade MTM at 1-minute OHLC extrema, full round-trip fee reserved; EOD trailing floor reset after each day; NOT tick-level fill simulation.'}


def run(raw_dir:Path, input_dir:Path, output:Path):
    trades=load_trades(input_dir)
    bars,qc=read_target_bars(raw_dir,trades)
    source_validation=assess_price_alignment(trades,bars)
    if source_validation['missing_entry_bars'] or source_validation['large_diff_gt_3_points']:
        status='BLOCKED_DATA_PRICE_ALIGNMENT'
    else:
        status='HISTORICAL_1M_FLOATING_REPLAY_READY'
    observed={}
    for mode in ('all_signals','conflict_free_router'):
        selected,skipped=apply_router(trades,mode=='conflict_free_router')
        observed[mode]={'trades':len(selected),'skipped_opposing_signals':skipped,
                        'intraday':replay(selected,bars)}
    if any(x['intraday']['missing_path_days'] for x in observed.values()):
        status='BLOCKED_MISSING_MINUTE_DATA'
    result={'status':status,'holdout':'2026 DATA AND PNL NOT READ','source_fills':'NinjaTrader 2-tick, +$0.02 extra MFFU commissions/trade',
            'data_qc':qc,'entry_alignment':source_validation,'R072_four_extra_sessions':audit_sessions(bars),
            'results':observed,'caveats':[
              'Market candles include 1-minute ranges, not executable stop fill order or tick sequence.',
              'Raw input files use UTC EOB while Trades CSV uses ET clock; source/timezone price alignment is compulsory.',
              'If instrument continuous prices differ materially from NT historical fills, disregard float figures until reconciling vendor/rollover/adjustment conventions.',
              'Stops are not re-executed after adverse candle events; exceeding stop may overstate attainable loss or reveal missing fill realism.',
              'A signal router may alter subsequent trade execution; this scenario excludes only contemporaneous opposing trades.',
              'Published evaluations already fail seven-day inactivity and $3000 target with these contracts.',
              '2026 pseudo-forward remains closed until a new strategy & portfolio risk framework is frozen.'
            ]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'status':status,'data_qc':{k:v for k,v in qc.items() if k!='retained_targeted_by_contract'},
        'entry_alignment':source_validation,
        'R072_extra_sessions':result['R072_four_extra_sessions'],
        'results':{k:{'trades':v['trades'],**{z:w for z,w in v['intraday'].items() if z not in ('breach_examples','missing_path_days')}} for k,v in observed.items()}},indent=2))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw-dir',type=Path,default=Path('data/raw'))
    parser.add_argument('--input-dir',type=Path,default=Path('research/mffu/inputs'))
    parser.add_argument('--output',type=Path,default=Path('results/mffu/mes_floating_1m_audit.json'))
    args=parser.parse_args()
    result=run(args.raw_dir,args.input_dir,args.output)
    if result['status']!='HISTORICAL_1M_FLOATING_REPLAY_READY':
        print('NOTE: RISK RESULTS NOT CERTIFIED: '+result['status'])

if __name__=='__main__':main()