#!/usr/bin/env python3
"""B05H01D fail-closed EXECUTION DIAGNOSTIC; NO P&L output or retuned signals.

Never mark invalid exposures as winning or losing. Each route/day/scenario
terminates at its first unresolvable event; other days are checked only to
count defects, not to reconstruct a profitable subset.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_right
from collections import Counter
from itertools import islice
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t04_execution import SCENARIOS,MAX_TRADES_PER_DAY,STOP_NEW_ENTRIES_AFTER_DAILY_USD
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade
from nq_b05h01_trade_expansion_month import (
    BASE,NEW,ROUTER,MODELS,STRESS,
    frozen_t05,h01_candidates,shared_router,owner_policy)

HARD=('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS','UNRESOLVED_END_OF_LAST_DATA')
SOFT=('NO_ENTRY_BEFORE_SESSION_CUTOFF','NO_ENTRY_EVENT')
ALL=HARD+SOFT

def first_blocker(day,events,old_bars,tagged,scenario):
    """Exact same frozen admission/owners/FillPolicy as H01 trace.

    No reported PnL; return first hard-fail owner/status for count only.
    """
    dev_day(day)
    times=[x[0] for x in events]
    last_exit=-1
    pnl=0.
    executed=0
    for ts,side,owner in tagged:
        if executed>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            continue
        if ts<=last_exit:continue
        r=simulate_single_trade(islice(events,bisect_right(times,ts),None),
               Signal(day,ts,side),owner_policy(owner,old_bars,scenario))
        status=r['status']
        if status in HARD:
            return {'hard_status':status,'owner':owner}
        if status in SOFT:continue
        if status!='SYNTHETIC_FILL_MODEL_ONLY':
            raise ValueError('Unexpected fill status:'+status)
        # Private state needed for next risk decision ONLY; NEVER published.
        executed+=1
        pnl=round(pnl+r['estimated_net_usd'],2)
        last_exit=r['exit_timestamp']
    return {'hard_status':'NONE','owner':'NONE'}

def run_month(root,month):
    if month not in MONTHS:
        raise ValueError('B05H01D SEALED MONTH DENIED BEFORE FS')
    days=month_days(root,month)
    flags=Counter()
    reasons=Counter()
    skipped=Counter()
    count=0
    signals=0
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        status,old_bars,t05=frozen_t05(events,day)
        skipped[status]+=1
        if status!='READY':continue
        count+=1
        new,_=h01_candidates(events,day)
        signals+=len(new)
        router,_=shared_router(t05,new)
        choices={BASE:t05, NEW:[(ts,s,NEW) for ts,s in new],ROUTER:router}
        for model,tagged in choices.items():
            for scenario in SCENARIOS:
                outcome=first_blocker(day,events,old_bars,tagged,scenario)
                if outcome['hard_status'] in HARD:
                    reasons['|'.join((model,scenario,outcome['owner'],
                                      outcome['hard_status']))]+=1
                    flags[model+'|'+scenario]+=1
    return {'status':'B05H01D_DIAGNOSTIC_ONLY_NO_PNL',
        'month':month,'source_days':len(days),'eligible_days':count,
        'excluded_days':len(days)-count,
        'skip_reasons':{k:v for k,v in skipped.items() if k!='READY'},
        'h01_candidate_opportunities':signals,
        'hard_fail_routes_by_scenario':dict(flags),
        'hard_fail_details':dict(reasons),
        'holdouts_opened':False,'new_market_history_acquired':False,
        'trading_results_calculated_or_published':False,
        'five_second_bars_used_in_new_signals':False,
        'legacy_t05_only_for_frozen_comparison':True}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED DENIED')
    x=run_month(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('B05H01D_SAFE_MONTH='+json.dumps({
      'month':x['month'],'source':x['source_days'],'eligible':x['eligible_days'],
      'hard_failed_route_scenarios':x['hard_fail_routes_by_scenario'],
      'no_pnl':True,'holdouts_closed':True},sort_keys=True))
