#!/usr/bin/env python3
"""B04 aggregate of ALL 7 DEV frozen T05 temporal splits. No OOS, no fills."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from collections import Counter
from nq_tick_short_horizon_month import MONTHS
from nq_b04_temporal_month import MODELS,FROZEN_ORIGINAL_EXPECTED

EXPECTED={
    "baseline":(115,6220.0),
    "stress_1p5_fee_2ticks_each_side":(115,5102.5),
    "stress_original_plus_10usd_rt":(115,3952.5),
}
QUARTERS={
    "2025-10":"2025-Q4_PARTIAL_FROM_OCT15",
    "2025-11":"2025-Q4_PARTIAL_FROM_OCT15",
    "2025-12":"2025-Q4_PARTIAL_FROM_OCT15",
    "2026-01":"2026-Q1_FULL",
    "2026-02":"2026-Q1_FULL",
    "2026-03":"2026-Q1_FULL",
    "2026-04":"2026-Q2_APR_ONLY",
}

def totals(rows):
    c=Counter()
    for row in rows:
        for k in ("trades","win","loss","flat","net_cents","pos_cents","neg_cents"):
            c[k]+=row[k]
    return dict(c)

def view(row):
    pos=row['pos_cents']
    neg=row['neg_cents']
    n=row['trades']
    return {
        'trades':n,
        'net_usd':round(row['net_cents']/100,2),
        'pf_frozen_path':round(pos/neg,5) if neg else None,
        'win_rate_pct':round(100*row['win']/n,2) if n else None,
        'mean_net_usd_per_trade':round(row['net_cents']/100/n,2) if n else None,
        'wins':row['win'],'losses':row['loss'],'flats':row['flat']
    }

def maximum_streak(bools):
    cur=best=0
    for value in bools:
        cur=cur+1 if value else 0
        best=max(best,cur)
    return best

def summarize_weekly(byweek):
    keys=sorted(byweek)
    if not keys:raise ValueError('Empty ISO-week universe')
    active=[byweek[k] for k in keys if byweek[k]['trades']]
    plus=[x for x in active if x['net_cents']>0]
    minus=[x for x in active if x['net_cents']<0]
    flat=[x for x in active if x['net_cents']==0]
    contrib=sorted((x['net_cents'] for x in plus),reverse=True)
    total_positive=sum(contrib)
    return {
        'week_start_rule':'ISO_MONDAY_IN_ET',
        'source_weeks':len(keys),
        'active_weeks':len(active),
        'positive_weeks':len(plus),
        'negative_weeks':len(minus),
        'flat_active_weeks':len(flat),
        'weeks_without_trades':len(keys)-len(active),
        'positive_share_of_active_weeks_pct':round(100*len(plus)/len(active),2) if active else None,
        'best_week_net_usd':round(max(x['net_cents'] for x in active)/100,2) if active else None,
        'worst_week_net_usd':round(min(x['net_cents'] for x in active)/100,2) if active else None,
        'top_1_positive_week_share_of_positive_week_dollars_pct':
           round(100*sum(contrib[:1])/total_positive,2) if total_positive else None,
        'top_3_positive_weeks_share_of_positive_week_dollars_pct':
           round(100*sum(contrib[:3])/total_positive,2) if total_positive else None,
        # An inactive full week would break the streak; in this metric only
        # weeks containing at least 1 trade are evaluated in chronological order.
        'longest_streak_of_negative_active_weeks':maximum_streak(
           x['net_cents']<0 for x in active),
        'sum_all_weeks_net_usd':round(sum(byweek[k]['net_cents'] for k in keys)/100,2),
        'per_week_trade_outcomes_published':False,
    }

def aggregate(months):
    if sorted(months)!=sorted(MONTHS):
        raise ValueError('Exactly seven specified DEV months required')
    if any(months[m]['month']!=m or
           months[m]['status']!='B04_DEV_WEEK_MONTH_AGGREGATE_ONLY' or
           months[m]['chronological_et_dates'] is not True or
           months[m]['holdouts_opened'] is not False or
           months[m]['trade_level_data_exported'] is not False or
           months[m]['pnl_is_real_broker_fills'] is not False or
           months[m]['eligible_days']+months[m]['excluded_days']!=months[m]['source_days']
           for m in MONTHS):
        raise ValueError('DEV QC/holdout gate failed')
    result={}
    for sc in MODELS:
        monthly=[]
        quarter_rows={}
        weekly={}
        for m in MONTHS:
            raw=months[m]['scenarios'][sc]
            month_counter=raw['month_counter']
            week_counters=raw['iso_week_counters']
            recon=totals(week_counters.values())
            if any(recon.get(k,0)!=month_counter[k] for k in month_counter):
                raise AssertionError('Unreconciled monthly ISO weeks')
            v=view(month_counter)
            v.update({'month':m,'active_weeks_in_month':sum(x['trades']>0 for x in week_counters.values())})
            monthly.append(v)
            q=QUARTERS[m]
            quarter_rows.setdefault(q,[]).append(month_counter)
            for wk,counts in week_counters.items():
                if wk not in weekly:
                    weekly[wk]=Counter()
                weekly[wk].update(counts)
        counted=totals(months[m]['scenarios'][sc]['month_counter'] for m in MONTHS)
        total=view(counted)
        exp_n,exp_net=EXPECTED[sc]
        if total['trades']!=exp_n or abs(total['net_usd']-exp_net)>.001:
            raise AssertionError('T04/T05/B03 original trade count or net drift')
        if sc=="stress_original_plus_10usd_rt":
            base=result["stress_1p5_fee_2ticks_each_side"]["overall"]
            if round(total['net_usd']-(base['net_usd']-10*exp_n),2)!=0:
                raise AssertionError('B03 stress $10 linearity broken')
        weeks=summarize_weekly(weekly)
        if abs(weeks['sum_all_weeks_net_usd']-total['net_usd'])>.001:
            raise AssertionError('Cross-month ISO week sum mismatch')
        quarter=[]
        for q,rows in quarter_rows.items():
            v=view(totals(rows))
            v['period']=q
            v['months_in_period']=len(rows)
            v['positive_months']=sum(x['net_cents']>0 for x in rows)
            v['negative_months']=sum(x['net_cents']<0 for x in rows)
            v['share_of_all_positive_period_net_pct']=None # not used: denominator can be net-negative
            quarter.append(v)
        month_gains=[r['net_usd'] for r in monthly]
        result[sc]={
            'overall':total,
            'monthly':monthly,
            'calendar_quarter_and_partials':quarter,
            'iso_week_diagnostic':weeks,
            'negative_months':sum(x<0 for x in month_gains),
            'positive_months':sum(x>0 for x in month_gains),
            'longest_streak_negative_months':maximum_streak(x<0 for x in month_gains),
            'months_with_at_least_5_trades':sum(x['trades']>=5 for x in monthly),
            'all_7_months_positive':all(x>0 for x in month_gains),
            'all_7_months_have_5_trades':all(x['trades']>=5 for x in monthly)
        }
    n_source=sum(months[m]['source_days'] for m in MONTHS)
    n_eligible=sum(months[m]['eligible_days'] for m in MONTHS)
    if (n_source,n_eligible)!=(140,135):
        raise AssertionError(f'Unexpected T04/T05 DEV day coverage: {n_source}/{n_eligible}')
    return {
        'status':'B04_COMPLETE_DESCRIPTIVE_TEMPORAL_DIAGNOSTIC_ONLY',
        'source_months':list(MONTHS),
        'source_days':n_source,'eligible_days':n_eligible,
        'holdouts_opened':False,
        'new_parameters_optimized':False,
        'calendar_segments_are_OOS_or_independent':False,
        'actual_market_fills_verified':False,
        'broker_funded_terms_verified':False,
        'frozen_115_trades_per_model':True,
        'models':result
    }

def markdown_report(r):
    out=['# NQ-B04 — robustez temporal T05-377 (7 meses DEV exploratorios)',
         '',
         '**Simulación Last congelada y diagnóstico temporal; NO robustez anual, OOS ni fills reales.**',
         'Mayo–junio para outcomes y julio–septiembre 2026 permanecen cerrados.',
         '',
         '## Resumen de semanas y meses', '',
         '| Modelo | 115 trades P&L USD | PF | Meses positivos/7 | Semanas activas positivas/todas activas | Peor semana USD | Concentración 3 mejores semanas (%) |',
         '|---|---:|---:|---:|---:|---:|---:|']
    for name,row in r['models'].items():
        overall=row['overall'];wk=row['iso_week_diagnostic']
        out.append(f"| {name} | {overall['net_usd']} | {overall['pf_frozen_path']} | "
                   f"{row['positive_months']}/7 | {wk['positive_weeks']}/{wk['active_weeks']} | "
                   f"{wk['worst_week_net_usd']} | {wk['top_3_positive_weeks_share_of_positive_week_dollars_pct']} |")
    out+=['','## Mes por mes (todos los meses de la muestra sin selección)']
    for name,row in r['models'].items():
        out+=['',f"### {name}",'',
              '| Mes | Trades | Neto USD | PF | Aciertos % |',
              '|---|---:|---:|---:|---:|']
        for v in row['monthly']:
            out.append(f"| {v['month']} | {v['trades']} | {v['net_usd']} | "
                       f"{v['pf_frozen_path']} | {v['win_rate_pct']} |")
    out+=['','## Trimestres y períodos parciales', '',
          '2025-Q4 cubre únicamente desde **15 de octubre**. 2026-Q2 incluye **solo abril**, no abril-junio.',
          '| Modelo | Periodo | Meses | Trades | Neto USD | PF | Meses positivos |',
          '|---|---|---:|---:|---:|---:|---:|']
    for name,row in r['models'].items():
        for q in row['calendar_quarter_and_partials']:
            out.append(f"| {name} | {q['period']} | {q['months_in_period']} | "
             f"{q['trades']} | {q['net_usd']} | {q['pf_frozen_path']} | {q['positive_months']} |")
    out+=['','## Advertencias / siguiente decisión','',
          '- Las semanas ISO se agrupan en calendario ET, y las semanas que cruzan meses se fusionan antes de calcular estadísticas.',
          '- Concentración = contribución de las 3 semanas positivas mayores dividida por la suma de **ganancias netas de todas las semanas positivas**, no por el neto final.',
          '- Las semanas con pocas operaciones no constituyen muestras independientes; **no se publican resultados por trade ni una tabla individual de semanas**.',
          '- Estrés +USD10/RT es recargo contable sobre mismas entradas/salidas y se ha elegido por B03 ANTES de ver B04; no recalcula barreras.',
          '- Siete meses con dos segmentos trimestrales parciales no prueban ventaja multianual ni superar >max(15%, VOO total return, QQQM total return).',
          '- T05 sigue siendo componente de investigación NQ, no fondeo; otra estrategia debe demostrar incremento neto con el mismo router.',
          '- Próximo paso **NQ-B05**: prerregistrar un mecanismo NQ causal distinto al de T05/T09 (no filtro posterior por semana favorable).',
          '']
    return '\n'.join(out)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    args=p.parse_args()
    months={}
    for f in args.inputs.rglob('nq_b04_*.json'):
        obj=json.loads(f.read_text(encoding='utf-8'))
        if obj['month'] in months:raise ValueError('Duplicate monthly result')
        months[obj['month']]=obj
    report=aggregate(months)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    args.report.write_text(markdown_report(report),encoding='utf-8')
    print('NQ_B04_SAFE_SUMMARY='+json.dumps({
        'source_days':report['source_days'],
        'eligible_days':report['eligible_days'],
        'models':{k:{
           'pnl':v['overall']['net_usd'],
           'pf':v['overall']['pf_frozen_path'],
           'positive_months':v['positive_months'],
           'positive_weeks':v['iso_week_diagnostic']['positive_weeks'],
           'active_weeks':v['iso_week_diagnostic']['active_weeks'],
           'worst_week':v['iso_week_diagnostic']['worst_week_net_usd'],
           'top3_positive_weeks_share_pct':v['iso_week_diagnostic']['top_3_positive_weeks_share_of_positive_week_dollars_pct']}
        for k,v in report['models'].items()}},sort_keys=True))
