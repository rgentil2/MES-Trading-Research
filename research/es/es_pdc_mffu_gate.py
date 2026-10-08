"""Strictly descriptive MFFU Rapid EOD replay of ES PDC research trades, 2020-2024 only."""
from __future__ import annotations
import csv, json
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timedelta

ROOT=Path(__file__).resolve().parents[2]
TRADES=ROOT/'results/es_pdc_transport/ES_PDC_TRANSPORT_TRADES_2020_2024.csv'
OUTPUT=ROOT/'results/es_pdc_transport/ES_PDC_MFFU_RAPID_EOD_REPLAY_2020_2024.json'

def replay(entries, instrument='ES', enforce_inactivity=True):
    pnlkey='net_es_usd' if instrument=='ES' else 'net_mes_usd'
    pnl_by_date=defaultdict(float); stop_by_date=defaultdict(list)
    for t in entries:
        d=datetime.strptime(t['date'],'%Y-%m-%d').date()
        pnl_by_date[d]+=float(t[pnlkey]);stop_by_date[d].append(float(t['stop_risk_ES_usd' if instrument=='ES' else 'stop_risk_MES_usd']))
    balance=0.0; peak=0.0; floor=-2000.0; highest=0.0; n_days=0; largest_daily_gain=0.0
    prev=None; first_loss=None; max_floor_gap=None; target_date=None; first_inactivity=None
    for day in sorted(pnl_by_date):
        pnl=pnl_by_date[day]
        if prev is not None and (day-prev).days>7 and first_inactivity is None:
            first_inactivity=(prev+timedelta(days=7)).isoformat()
        if first_inactivity is not None and enforce_inactivity:
            return dict(outcome='FAIL_INACTIVITY',first_violation_date=first_inactivity,balance_at_breach=round(balance,2),trading_days=n_days)
        n_days+=1
        after=balance+pnl
        if after < floor-1e-8 and first_loss is None:
            first_loss=dict(date=day.isoformat(),balance_after=round(after,2),floor_prior=round(floor,2),pnl=round(pnl,2))
        if first_loss is not None:
            return dict(outcome='FAIL_EOD_CLOSED_LOSS',first_violation=first_loss,trading_days=n_days,earlier_inactivity_breach=first_inactivity)
        balance=after;peak=max(peak,balance);highest=max(highest,balance)
        floor=max(floor,min(peak-2000.0,100.0))
        largest_daily_gain=max(largest_daily_gain,pnl)
        if balance>=3000 and n_days>=4 and largest_daily_gain<=.30*balance and target_date is None:
            target_date=day.isoformat()
            return dict(outcome='PASS_DIAGNOSTIC_EOD_ONLY',date=target_date,balance=round(balance,2),trading_days=n_days,earlier_inactivity_breach=first_inactivity)
        prev=day
    return dict(outcome='NOT_PASSED_WITHIN_5Y_DEV',balance=round(balance,2),highest_closed_balance=round(highest,2),trading_days=n_days,first_inactivity_violation_without_enforcement=first_inactivity)

with TRADES.open(newline='') as f:
    entries=list(csv.DictReader(f))
assert len(entries)==94
out={
 'authority':'2020_2024_DEV_EOD_TRADE_ONLY_NO_NEWS_FILTER_EXPLORATORY',
 'ES_one_contract':replay(entries,'ES',True),
 'ES_counterfactual_inactivity_disabled':replay(entries,'ES',False),
 'MES_same_ES_derived_signals':replay(entries,'MES',True),
 'MES_counterfactual_inactivity_disabled':replay(entries,'MES',False),
 'important_caveat':'Excludes unrealized drawdown, news, execution at ticks, alternative routing, 2025/26 holdouts; not a prop-firm eligibility certificate'
}
OUTPUT.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))