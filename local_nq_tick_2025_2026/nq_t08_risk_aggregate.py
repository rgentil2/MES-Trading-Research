#!/usr/bin/env python3
"""T08 aggregate seven DEV risk segments; no raw ticks, no holdout access."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from nq_t08_risk_audit import MONTHS,FAMILIES,SCENARIOS

REFERENCE_DD_USD=2000.0  # historical reference; firm rules NOT VERIFIED
EXPECTED_BASELINE={
    'T02_PARENT':(190,8420.0),
    'T05_377':(115,6220.0),
    'T05_233_AND_377':(59,5395.0)}
EXPECTED_STRESS={
    'T02_PARENT':(190,6860.0),
    'T05_377':(115,5102.5),
    'T05_233_AND_377':(59,4657.5)}

def aggregate(month_data):
    if sorted(month_data)!=sorted(MONTHS):
        raise ValueError('Must have all and only seven DEV months; no holdouts')
    for month,r in month_data.items():
        if (r['month']!=month or r['status']!='T08_DEV_RISK_DIAGNOSTIC_NOT_BROKER_OR_OOS'
            or r['holdouts_opened'] is not False or r['funded_rules_verified'] is not False
            or r['costs_verified'] is not False):
            raise ValueError('Incomplete/untrusted audit month')
    result={}
    for fam in FAMILIES:
        result[fam]={}
        for sc in SCENARIOS:
            net=0.0;hi=0.0;dd=0.0;closed_peak=0.0;closed_dd=0.0
            trades=0;pos=neg=0.0;ambiguity=abort=0;min_month=None
            monthly=[]
            for month in MONTHS:
                row=month_data[month]['families'][fam][sc]
                seg=row['last_envelope_segment']
                if abs(seg['equity']-row['net_usd'])>0.01:
                    raise ValueError('Segment equity != net PnL')
                if seg['low']>seg['high'] or seg['closed_low']>seg['closed_high']:
                    raise ValueError('Invalid envelope extrema')
                # Local segment has its own 0-based equity. The global high-water
                # continues through boundaries instead of resetting every month.
                dd=max(dd,seg['max_dd'],hi-(net+seg['low']))
                closed_dd=max(closed_dd,seg['closed_dd'],
                              closed_peak-(net+seg['closed_low']))
                hi=max(hi,net+seg['high'])
                closed_peak=max(closed_peak,net+seg['closed_high'])
                net=round(net+row['net_usd'],2)
                trades+=row['trades']
                pos+=row['gross_positive_net_usd']
                neg+=row['gross_negative_net_usd']
                ambiguity+=row['ambiguous_or_unknown']
                abort+=row['aborted_days']
                monthly.append({'month':month,'trades':row['trades'],
                    'net_usd':row['net_usd'],
                    'last_month_segment_dd_usd':seg['max_dd']})
            baseline=EXPECTED_BASELINE if sc=='baseline' else EXPECTED_STRESS
            exp_trades,exp_net=baseline[fam]
            if trades!=exp_trades or abs(net-exp_net)>0.02:
                raise AssertionError(f'Previous DEV T04/T05 totals changed: {fam}/{sc}'
                                     f' got {trades}/{net}, expect {exp_trades}/{exp_net}')
            pf=round(pos/neg,5) if neg else None
            minimum=min(x['trades'] for x in monthly)
            gate={
                'positive_net_after_costs':net>0,
                'profit_factor_stress_at_least_1p25':
                    (pf>=1.25 if sc!='baseline' and pf is not None else None),
                'at_least_5_trades_each_month':minimum>=5,
                'zero_unresolved_execution_ambiguity':ambiguity==0 and abort==0,
                'last_envelope_dd_below_unverified_2000_usd_reference':
                    dd<REFERENCE_DD_USD}
            result[fam][sc]={
                'trades':trades,'net_usd':round(net,2),'profit_factor_net':pf,
                'last_envelope_max_dd_usd':round(dd,2),
                'last_closed_trade_max_dd_usd':round(closed_dd,2),
                'minimum_monthly_trade_count':minimum,
                'unknown_entry_or_exit':ambiguity,'aborted_days':abort,
                'monthly':monthly,'preliminary_gates':gate,
                'status':'RESEARCH_RISK_REVIEW_ONLY_NOT_OOS_NOT_LIVE'}
    for fam in FAMILIES:
        base=result[fam]['baseline']
        stress=result[fam]['stress_1p5_fee_2ticks_each_side']
        base['risk_gate_preliminary_pass']=(
            all(x is True for x in base['preliminary_gates'].values() if x is not None)
            and all(x is True for x in stress['preliminary_gates'].values() if x is not None))
        base['decision']=('CONDITIONAL_ONLY_NOT_APPROVED' if
            base['risk_gate_preliminary_pass'] else 'GATE_FAIL_OR_REVIEW_REQUIRED')
    return {'status':'T08_EXPLORATORY_ONLY_FUNDED_NOT_APPROVED',
        'source_months':list(MONTHS),
        'eligible_days':sum(month_data[x]['eligible_days'] for x in MONTHS),
        'source_days':sum(month_data[x]['source_days'] for x in MONTHS),
        'holdouts_opened':False,'firm_terms_verified':False,'actual_fills':False,
        'etf_cagr_comparison_completed':False,'candidates':result}

def load_months(directory):
    r={}
    for path in directory.rglob('nq_t08_*.json'):
        item=json.loads(path.read_text(encoding='utf8'))
        month=item['month']
        if month in r:raise ValueError('Duplicate month artifact')
        r[month]=item
    return r

def markdown(out):
    lines=[
        '# NQ T08 — auditoría de riesgo preliminar (Last-only, DEV)',
        '',
        '**NO VALIDADA PARA FONDEO.** No se abrieron mayo–septiembre 2026.',
        'T08 es evaluación retrospectiva post-selección; P&L anterior es simulado.',
        'Todos los números representan portafolios **ALTERNATIVOS**, nunca sumables.',
        'El drawdown Last-envelope es una envolvente adversa hipotética, no broker equity.',
        '',
        '| Cartera | Trades | Neto base USD | Neto estrés USD | PF estrés |',
        'DD continuo Last envolvente base USD | DD estrés USD |',
    ]
    # combine header into a single markdown row
    lines[-2]=lines[-2]+' '+lines.pop()
    lines+=['|---|---:|---:|---:|---:|---:|---:|']
    for fam in FAMILIES:
        b=out['candidates'][fam]['baseline']
        s=out['candidates'][fam]['stress_1p5_fee_2ticks_each_side']
        lines.append('| '+fam+' | '+str(b['trades'])+' | '+str(b['net_usd'])+
            ' | '+str(s['net_usd'])+' | '+str(s['profit_factor_net'])+
            ' | '+str(b['last_envelope_max_dd_usd'])+
            ' | '+str(s['last_envelope_max_dd_usd'])+' |')
    lines+=['','## Controles y decisión','']
    for fam in FAMILIES:
        b=out['candidates'][fam]['baseline']
        s=out['candidates'][fam]['stress_1p5_fee_2ticks_each_side']
        lines.append('### '+fam)
        lines.append('- Estado: **'+b['decision']+'** (no aprobación para operar)')
        lines.append('- Frecuencia mínima mensual: '+str(b['minimum_monthly_trade_count'])+
            ' (umbral orientativo 5)')
        lines.append('- DD Last-envolvente baseline/estrés: '+
            str(b['last_envelope_max_dd_usd'])+' / '+
            str(s['last_envelope_max_dd_usd'])+' USD; referencia histórica **NO VERIFICADA** $2.000.')
        lines.append('- PF estrés: '+str(s['profit_factor_net'])+
                     '; ambiguos base/estrés: '+str(b['unknown_entry_or_exit'])+
                     ' / '+str(s['unknown_entry_or_exit']))
        lines.append('- Trades por mes: '+', '.join(x['month']+':'+str(x['trades'])
                     for x in b['monthly']))
        lines.append('')
    lines+=['## Limitaciones / siguiente puerta','',
        '- Una marca Last no representa oferta ejecutable Bid/Ask ni stop o slippage real.',
        '- El orden de prints compartiendo timestamp es desconocido; el método asume orden adverso.',
        '- Costes $5+$1 tick/side y $7,50+2 ticks/side son supuestos, no comprobados.',
        '- Las reglas específicas vigentes de fondeo (trailing intraday/EOD, daily limits, payout) no se verificaron.',
        '- Se requiere auditoría de fuente Minute vs Tick y revisión de coste y reglas para NQ/MNQ.',
        '- PF, estabilidad, pruebas Holm/BH de la familia estratégica y superar max(15%, VOO-TR, QQQM-TR) siguen siendo gates separados.',
        '- Mantener mayo–junio como validación interna; julio–septiembre pseudo-forward sellado.',
        '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    r=aggregate(load_months(a.inputs))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf8')
    a.report.write_text(markdown(r),encoding='utf8')
    print('T08_SUMMARY='+json.dumps({f:{
        s:{k:v for k,v in row.items() if k in ('trades','net_usd','profit_factor_net',
        'last_envelope_max_dd_usd','minimum_monthly_trade_count','decision')}
        for s,row in fs.items()} for f,fs in r['candidates'].items()},sort_keys=True))
