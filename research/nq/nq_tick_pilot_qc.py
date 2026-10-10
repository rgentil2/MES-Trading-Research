#!/usr/bin/env python3
"""Source-only NinjaTrader NQ tick-data availability QC, no strategy/outcome reads.

Only accepts specifically named NQ 2020-2024 contracts under a development_2020_2024
folder. Refuses any 2025/2026 path before opening data. Does not publish raw rows.

Usage:
  python research/nq/nq_tick_pilot_qc.py --last \
    private/development_2020_2024/'NQ 03-24.Last.txt' \
    --bid private/development_2020_2024/'NQ 03-24.Bid.txt' \
    --ask private/development_2020_2024/'NQ 03-24.Ask.txt' \
    --from-date 2024-02-05 --to-date 2024-02-16 \
    --out /tmp/nq_tick_pilot_qc_summary.json

NinjaTrader tick text: YYYYMMDD HHMMSS[ fffffff];price;volume.
Times are UTC. For quote rows 'volume' is not presumed to be displayed depth.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
import json
import re
from zoneinfo import ZoneInfo

ET = ZoneInfo('America/New_York')
GOOD_YEARS = set(range(2020, 2025))
FILE_RE = re.compile(r'^NQ (?P<month>03|06|09|12)-(?P<yy>20|21|22|23|24)\.(?P<kind>Last|Bid|Ask)\.txt$')
UTCSTAMP = re.compile(r'^(\d{8}) (\d{6})(?: (\d{1,7}))?$')
START_MINUTE, END_MINUTE = 8*60+30, 11*60+30


def check_safe_path(path: Path, kind: str, expected_contract: str | None = None) -> str:
    """Validate path, contract and role BEFORE any file operations or row reads."""
    parts = set(path.parts)
    if 'development_2020_2024' not in parts:
        raise ValueError('Source must reside inside a development_2020_2024 directory')
    if any(re.search(r'(?:^|[_/\\.-])20(?:25|26)(?:$|[_/\\.-])', part) for part in path.parts):
        raise ValueError('Holdout-like 2025/2026 path rejected')
    m = FILE_RE.fullmatch(path.name)
    if not m or m['kind'] != kind:
        raise ValueError('Expected development NQ quarterly tick filename with matching Last/Bid/Ask suffix')
    contract = f'NQ {m["month"]}-{m["yy"]}'
    if expected_contract is not None and contract != expected_contract:
        raise ValueError(f'Mismatched contract: {contract} versus {expected_contract}')
    return contract


def parse_nt_tick_row(row: str) -> tuple[int, float, float]:
    """Return UTC 100-ns count, price and volume, preserving 7-digit fraction."""
    parts = row.rstrip('\r\n').split(';')
    if len(parts) != 3:
        raise ValueError('Tick line needs timestamp;price;volume')
    m = UTCSTAMP.fullmatch(parts[0])
    if m is None:
        raise ValueError('Invalid UTC tick timestamp')
    dt = datetime.strptime(m[1]+m[2], '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
    if dt.year not in GOOD_YEARS:
        raise ValueError('Unexpected year outside research development 2020-2024')
    tick_time_100ns = int(dt.timestamp()) * 10_000_000 + int((m[3] or '0').ljust(7, '0'))
    price = float(parts[1]); volume = float(parts[2])
    import math
    if not math.isfinite(price) or price <= 0 or not math.isfinite(volume) or volume < 0:
        raise ValueError('Invalid price/volume')
    return tick_time_100ns, price, volume


def inspect(path: Path, kind: str, start: date, end: date, expected_contract: str | None = None) -> dict:
    contract = check_safe_path(path, kind, expected_contract)
    if not path.is_file():
        raise FileNotFoundError(f'Tick source not found: {path}')
    out = {'contract':contract, 'type':kind, 'file':path.name, 'bytes':path.stat().st_size,
           'rows_total':0, 'rows_in_pilot':0, 'out_of_order':0, 'same_timestamp':0,
           'non_quarter_tick':0, 'nonpositive_trade_volume':0,
           'daily_events':{}, 'daily_active_minute_counts':{},
           'invalid_row_count':0, 'date_range_et':[start.isoformat(), end.isoformat()],
           'pilot_window_et':'08:30-11:30', 'has_subsecond_timestamp':False,
           'preserves_100ns_fraction':True}
    last_ns = None
    day_counts = Counter(); daily_minutes = {}
    with path.open('r',encoding='utf-8-sig') as f:
        for line in f:
            if not line.strip():
                continue
            out['rows_total'] += 1
            try:
                t, price, vol = parse_nt_tick_row(line)
            except (ValueError, OverflowError):
                out['invalid_row_count'] += 1
                continue
            if last_ns is not None:
                if t < last_ns:
                    out['out_of_order'] += 1
                elif t == last_ns:
                    out['same_timestamp'] += 1
            last_ns = t
            if t % 10_000_000:
                out['has_subsecond_timestamp'] = True
            et = datetime.fromtimestamp(t // 10_000_000, timezone.utc).astimezone(ET)
            d = et.date()
            minute = et.hour*60+et.minute
            if not (start <= d <= end and START_MINUTE <= minute < END_MINUTE):
                continue
            out['rows_in_pilot'] += 1
            day_counts[str(d)] += 1
            daily_minutes.setdefault(str(d),set()).add(minute)
            if abs(price / .25 - round(price / .25)) > 1e-6:
                out['non_quarter_tick'] += 1
            if kind == 'Last' and vol <= 0:
                out['nonpositive_trade_volume'] += 1
    out['daily_events'] = dict(sorted(day_counts.items()))
    out['daily_active_minute_counts'] = {d:len(m) for d,m in sorted(daily_minutes.items())}
    out['observed_pilot_dates'] = len(day_counts)
    out['quality_status'] = ('REJECT' if out['rows_in_pilot']==0 or out['invalid_row_count']>0
        or out['out_of_order']>0 or out['non_quarter_tick']>0 or out['nonpositive_trade_volume']>0
        else 'PRELIMINARY_PASS')
    return out


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--last', type=Path,required=True)
    ap.add_argument('--bid',type=Path)
    ap.add_argument('--ask',type=Path)
    ap.add_argument('--from-date',dest='start',default='2024-02-05')
    ap.add_argument('--to-date',dest='end',default='2024-02-16')
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    start=date.fromisoformat(args.start);end=date.fromisoformat(args.end)
    if start.year not in GOOD_YEARS or end.year not in GOOD_YEARS or end<start:
        raise SystemExit('Only valid development-period 2020-2024 pilot dates are permitted')
    contract=check_safe_path(args.last,'Last')
    for kind in ('Bid','Ask'):
        p=getattr(args,kind.lower())
        if p is not None:
            check_safe_path(p,kind,contract)
    reports={kind:inspect(path,kind,start,end,contract)
         for kind,path in [('Last',args.last),('Bid',args.bid),('Ask',args.ask)] if path is not None}
    result={'stage':'DEVELOPMENT_TICK_DATA_QC_ONLY','tested_market_outcomes':False,
            'holdout_2025_loaded':False,'holdout_2026_loaded':False,
            'contract':contract,'all_types_present':len(reports)==3,
            'quote_trade_asof_match_performed':False,'spread_execution_validated':False,
            'no_real_fills_claimed':True,'types':reports}
    text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(text,encoding='utf-8')
    else:
        print(text)

if __name__=='__main__':
    main()