"""One shared model-account router for manually frozen candidate IDs.

Proxy-only; minute bar OHLC and floating MAE proxies do NOT reproduce intraday
trailing loss, broker liquidation, news, payout or real fills. No orders.
"""
from __future__ import annotations


def route_single_account(trades_by_candidate:dict[str,list[dict]],
                         priority:list[str], max_entries_per_day:int=2,
                         loss_reference_usd:float=2000., target_reference_usd:float=3000.):
    """Deterministic chronology, tie break by fixed priority; rejects overlap.

    `priority` is externally frozen BEFORE examining portfolio performance;
    this function NEVER selects profitable candidates or optimizes weights.
    Stop reference is a post-hoc diagnostic, NOT a real broker order.
    """
    if not priority or len(set(priority))!=len(priority):
        raise ValueError('INVALID_PRIORITY')
    if not 1<=max_entries_per_day<=2:raise ValueError('INVALID_SESSION_ENTRY_CAP')
    if not 0<loss_reference_usd<=2000 or target_reference_usd<=0:
        raise ValueError('INVALID_RISK_REFERENCE')
    indexed={p:i for i,p in enumerate(priority)}
    missing=set(priority)-set(trades_by_candidate)
    if missing:raise ValueError('UNKNOWN_CANDIDATE: '+str(sorted(missing)))
    events=[]
    for cid in priority:
        for t in trades_by_candidate[cid]:
            if t.get('candidate')!=cid:raise ValueError('CANDIDATE_ID_MISMATCH')
            if not '2020-01-01'<=str(t['day'])<='2024-12-31':
                raise ValueError('SEALED_2025_2026_ROUTER_INPUT')
            if not 0<=t['signal_i']<t['entry_i']<=t['exit_i']<390:
                raise ValueError('INVALID_TRADE_CHRONOLOGY')
            events.append(t)
    events.sort(key=lambda x:(x['day'],x['entry_i'],indexed[x['candidate']]))
    selected=[];last_day=None;occupied_until=-1;today=0;balance=0.;peak=0.;
    max_closed_dd=0.;max_floating_dd=0.;first_reference_breach=None;reached_target=None
    skipped={'overlap':0,'daily_entry_cap':0,'after_loss_reference_breach':0}
    stopped=False
    for x in events:
        day=x['day']
        if day!=last_day:
            last_day=day;today=0;occupied_until=-1
        if stopped:
            skipped['after_loss_reference_breach']+=1
            continue
        if today>=max_entries_per_day:
            skipped['daily_entry_cap']+=1
            continue
        if x['entry_i']<=occupied_until:
            skipped['overlap']+=1
            continue
        occupied_until=x['exit_i']
        today+=1
        risk=float(x['floating_mae_proxy_usd'])
        if risk>0:raise ValueError('FLOATING_MAE_PROXY_SHOULD_BE_NONPOSITIVE')
        max_floating_dd=max(max_floating_dd,peak-(balance+risk))
        selected.append(dict(x))
        if first_reference_breach is None and max_floating_dd>=loss_reference_usd:
            first_reference_breach=day
            stopped=True
        balance+=float(x['net'])
        peak=max(peak,balance)
        max_closed_dd=max(max_closed_dd,peak-balance)
        if first_reference_breach is None and max_closed_dd>=loss_reference_usd:
            first_reference_breach=day
            stopped=True
        if reached_target is None and balance>=target_reference_usd:
            reached_target=day
    return dict(status='EXPLORATORY_SHARED_ACCOUNT_PROXY_NOT_FUNDING_SIM',
                priority_precommitted_by_caller=priority,
                max_entries_per_day=max_entries_per_day,
                selected_trades=selected,
                trades=len(selected),net_usd=round(balance,2),
                max_closed_dd_usd=round(max_closed_dd,2),
                floating_dd_proxy_usd=round(max_floating_dd,2),
                risk_reference_breach=first_reference_breach,
                reached_profit_reference=reached_target,
                stopped_after_proxy_breach=stopped,
                skipped=skipped,
                assumptions={'one_open_position':True,
                             'no_price_tick_execution':True,
                             'no_live_funding_rules':True,
                             'no_stacked_candidate_pnl':True,
                             'opening_equity_and_intratrade_peaks_approximate':True})