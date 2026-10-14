"""Strategy Builder V2: bounded causal rule grammar for NQ 1m, development 2020-24.

Independent of T05/T186/T215 NinjaTrader transfer. Historical 2025 sealed,
2026 forbidden. No discretionary outcome-based mutation; no actual broker fills.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
import math
from typing import Any

import numpy as np
import pandas as pd

from engine import (FAMILIES, SEED, TICK, POINT_MNQ, FEE_MNQ_RT,
                    SLIP_TICKS_SIDE, MAX_CONTRACTS, RISK_PER_TRADE,
                    indicators, directional_signal, round_to_grid_up,
                    _exit, metrics, _weekly_test, _bh)

# No code execution, eval, arbitrary expressions, or access to later bars.
LEAVES = frozenset(("ema_align", "ema_oppose", "macd_align", "vwap_align",
                    "vwap_oppose", "volume_active", "rsi_align", "adx_trend",
                    "adx_quiet", "atr_active", "atr_quiet", "squeeze",
                    "candle_align", "obv_align", "mfi_align"))


def leaf(name: str) -> dict:
    if name not in LEAVES:
        raise ValueError('INVALID_LEAF')
    return {'op':'LEAF','name':name}


def AND(*items:dict) -> dict:
    return {'op':'AND','args':list(items)}


def OR(*items:dict) -> dict:
    return {'op':'OR','args':list(items)}


# Six fixed, economically interpretable logical contexts. Six distinct contexts
# are *not* six statistically independent ideas if the same base signal recurs.
CONTEXTS = (
    ("trend_volume", AND(leaf("ema_align"), OR(leaf("macd_align"), leaf("volume_active"))), 1.0, 1.5, 20),
    ("quiet_reversal", AND(leaf("adx_quiet"), OR(leaf("vwap_oppose"), leaf("ema_oppose"))), 1.0, 1.5, 20),
    ("volume_direction", AND(leaf("volume_active"), OR(leaf("vwap_align"), leaf("candle_align"))), 1.5, 2.0, 30),
    ("momentum_confirm", AND(leaf("macd_align"), OR(leaf("rsi_align"), leaf("obv_align"))), 1.0, 2.0, 30),
    ("squeeze_release", AND(leaf("squeeze"), OR(leaf("atr_active"), leaf("volume_active"))), 1.5, 1.5, 20),
    ("vwap_moneyflow", AND(OR(leaf("vwap_align"), leaf("vwap_oppose")), leaf("mfi_align")), 2.0, 1.5, 30),
)


@dataclass(frozen=True)
class Combo:
    id:str
    mechanism:str
    context:str
    expression:dict
    stop_atr_mult:float
    reward_r:float
    hold_min:int
    side_mode:str='BOTH'

    def digest(self):
        return sha256(json.dumps(asdict(self),sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16]


def validate_ast(node:dict,depth=0) -> int:
    if not isinstance(node,dict) or depth>3:raise ValueError('RULE_AST_INVALID_DEPTH_OR_TYPE')
    op=node.get('op')
    if op=='LEAF':
        if set(node)!={'op','name'} or node['name'] not in LEAVES:raise ValueError('RULE_AST_UNKNOWN_LEAF')
        return 1
    if op not in ('AND','OR') or set(node)!={'op','args'}:raise ValueError('RULE_AST_UNKNOWN_OPERATION')
    args=node['args']
    if not isinstance(args,list) or not 2<=len(args)<=3:raise ValueError('RULE_AST_ARITY')
    n=sum(validate_ast(child,depth+1) for child in args)
    if n>4:raise ValueError('RULE_AST_EXCESS_COMPLEXITY')
    return n


def build_registry_v2():
    specs=[]
    for fi,fam in enumerate(FAMILIES,1):
        for ci,(context,expr,stop,reward,hold) in enumerate(CONTEXTS,1):
            validate_ast(expr)
            # JSON copy avoids mutable expression aliasing between specifications.
            specs.append(Combo(f'SB2-{fi:02d}-{ci}',fam,context,
                               json.loads(json.dumps(expr)),stop,reward,hold))
    if len(specs)!=96 or len({x.id for x in specs})!=96:
        raise ValueError('REGISTRY_NOT_96_UNIQUE_RULES')
    return specs


def registry_manifest(specs):
    docs=[asdict(s) for s in specs]
    hashed=sha256(json.dumps(docs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'project':'NQ-Strategy-Builder-50K','cohort':'V2-96',
            'created_utc_date':'2026-10-14',
            'status':'RULES_FROZEN_BEFORE_ANY_NEW_OHLCV_READ',
            'data_scope':'ONLY_NQ_1M_2020_2024_REUSED_DEV',
            'training':'2020-2022','internal':'2023-2024',
            'validation_2025':'SEALED_NO_CONTENT_READ',
            'year_2026':'EXCLUDED_NO_CONTENT_READ',
            'existing_v1_tests':48,'this_family_tests':len(specs),
            'total_builder_v1_v2_tests':48+len(specs),
            'legacy_NQ_families_additional_and_uncorrected':True,
            'avoid_tuning_or_mutation_to_results':True,
            'registry_sha256':hashed,'candidates':docs}


def _base_leaf_masks(d:pd.DataFrame,side:int):
    if side not in (-1,1):raise ValueError('SIDE_MUST_BE_LONG_OR_SHORT')
    # Each leaf is a causal condition at the *close* of the corresponding bar.
    c=d.close
    bb_width=(d.bb_hi-d.bb_lo)/d.close
    width_past=bb_width.shift(1).rolling(30,min_periods=30).median()
    candle=(c-d.open)*side
    raw={
        'ema_align':(d.ema_fast-d.ema_slow)*side>0,
        'ema_oppose':(d.ema_fast-d.ema_slow)*side<0,
        'macd_align':(d.macd-d.macd_sig)*side>0,
        'vwap_align':(c-d.vwap)*side>0,
        'vwap_oppose':(c-d.vwap)*side<0,
        'volume_active':d.volume_z>.4,
        'rsi_align':(d.rsi-50)*side>0,
        'adx_trend':d.adx>22,
        'adx_quiet':d.adx<18,
        'atr_active':d.atr_pct>d.atr_pct_med,
        'atr_quiet':d.atr_pct<d.atr_pct_med,
        'squeeze':bb_width<.85*width_past,
        'candle_align':candle>0,
        'obv_align':(d.obv-d.obv_ma)*side>0,
        'mfi_align':(d.mfi-50)*side>0,
    }
    # No filling indicator warm-up with future or crossing values.
    return {k:v.fillna(False).to_numpy(dtype=bool) for k,v in raw.items()}


def evaluate_ast(node:dict,leaf_masks:dict[str,np.ndarray]):
    validate_ast(node)
    def visit(n):
        if n['op']=='LEAF':
            if n['name'] not in leaf_masks:raise ValueError('LEAF_MISSING_IN_FEATURE_SET')
            return leaf_masks[n['name']]
        parts=[visit(v) for v in n['args']]
        if n['op']=='AND':return np.logical_and.reduce(parts)
        return np.logical_or.reduce(parts)
    return visit(node)


def _trades_for_day(day:np.ndarray,day_label:str,context_rules:list[Combo]):
    f=indicators(day)
    families={c.mechanism for c in context_rules}
    sig={fam:directional_signal(f,fam) for fam in families}
    masks={side:_base_leaf_masks(f,side) for side in (-1,1)}
    unique_contexts={c.context:c.expression for c in context_rules}
    ctx={name:(evaluate_ast(expr,masks[1]),evaluate_ast(expr,masks[-1]))
         for name,expr in unique_contexts.items()}
    daily={}
    for spec in context_rules:
        s=sig[spec.mechanism]
        longmask,shortmask=ctx[spec.context]
        valid=((s==1)&longmask)|((s==-1)&shortmask)
        # bar end 09:31 ... bar index 118 end 11:29; entry OPEN of next minute.
        idxs=np.flatnonzero(valid[4:119])+4
        for i in idxs:
            atr=float(f.atr.iat[i]);side=int(s[i]);
            if not np.isfinite(atr) or side not in (-1,1):continue
            stop=round_to_grid_up(min(60.,max(8.,atr*spec.stop_atr_mult)))
            target=round_to_grid_up(stop*spec.reward_r)
            entry=float(day[i+1,0]+side*SLIP_TICKS_SIDE*TICK)
            unit_risk=(stop+SLIP_TICKS_SIDE*TICK)*POINT_MNQ+FEE_MNQ_RT
            q=min(MAX_CONTRACTS,int(RISK_PER_TRADE//unit_risk))
            if q<=0:continue
            ex,ex_i,reason,mae=_exit(day,i+1,side,entry,stop,target,spec.hold_min)
            pnl=round((ex-entry)*side*POINT_MNQ*q-FEE_MNQ_RT*q,2)
            daily[spec.id]={'candidate':spec.id,'day':day_label,'year':int(day_label[:4]),
                'signal_i':int(i),'entry_i':int(i+1),'exit_i':int(ex_i),'side':side,
                'instrument':'MNQ_PROXY','qty':q,'entry':round(entry,2),
                'exit':round(ex,2),'sl_pts':stop,'tp_pts':target,
                'reason':reason,'net':pnl,
                'floating_mae_proxy_usd':round((-mae*POINT_MNQ-FEE_MNQ_RT)*q,2)}
            break # one trade / session / candidate; not portfolio account routing
    return daily


def analyze_v2(days:np.ndarray,dates:list[str],registry:list[Combo],replications=1000):
    if days.ndim!=3 or days.shape[1:]!=(390,5) or len(days)!=len(dates):
        raise ValueError('SOURCE_MUST_BE_COMPLETE_390_RTH_NQ_1MIN')
    # Never inspect market data before validating all input dates and roster.
    if any(not ('2020-01-01'<=str(d)<='2024-12-31') for d in dates):
        raise ValueError('SEALED_2025_2026_DATA_BLOCKED_NO_PRICE_READ')
    if dates!=sorted(dates) or len(set(dates))!=len(dates):raise ValueError('BAD_SESSION_ORDER')
    expected=build_registry_v2()
    if [asdict(c) for c in registry]!=[asdict(c) for c in expected]:
        raise ValueError('V2_REGISTRY_MUTATION_NOT_ALLOWED_AFTER_PRECOMMIT')
    if not 100<=replications<=10000:raise ValueError('BAD_REPLICATIONS')
    work={c.id:[] for c in registry}
    for k,(day,dd) in enumerate(zip(days,dates)):
        if k%250==0:print(f'V2 causal 1m sessions: {k}/{len(dates)}',flush=True)
        new=_trades_for_day(day,dd,registry)
        for cid,tr in new.items():work[cid].append(tr)
    rng=np.random.default_rng(SEED+2)
    preliminary=[];pvals={}
    for s in registry:
        x=work[s.id]
        train=[y for y in x if y['year']<=2022]
        p,ci=_weekly_test(train,rng,replications=replications)
        pvals[s.id]=p
        preliminary.append({'id':s.id,'mechanism':s.mechanism,'context':s.context,
            'spec_hash':s.digest(),'train_2020_22':metrics(x,(2020,2021,2022)),
            'internal_2023_24':metrics(x,(2023,2024)),
            'all_reused_dev_2020_24':metrics(x,(2020,2021,2022,2023,2024)),
            'p_train_one_sided':p,'ci90_train':ci,
            'stress_extra_one_tick_each_side_dev_net_usd':round(
                sum(y['net']-2*TICK*POINT_MNQ*y['qty'] for y in x),2)})
    qvals=_bh(pvals)
    for r in preliminary:
        a=r['train_2020_22'];b=r['internal_2023_24'];c=r['all_reused_dev_2020_24']
        r['bh_q_v2_family_96_only']=qvals[r['id']]
        reasons=[]
        if a['n']<90:reasons.append('TRAIN_N_LT_90')
        if a['pf'] is None or a['pf']<1.25:reasons.append('TRAIN_PF_LT_1_25')
        if r['ci90_train'][0] is None or r['ci90_train'][0]<=0:reasons.append('TRAIN_CI90_NOT_POSITIVE')
        if r['bh_q_v2_family_96_only']>.10:reasons.append('TRAIN_Q_GT_0_10')
        if b['n']<60:reasons.append('INTERNAL_N_LT_60')
        if b['pf'] is None or b['pf']<1.25:reasons.append('INTERNAL_PF_LT_1_25')
        if b['positive_years']<2:reasons.append('INTERNAL_NOT_POSITIVE_BOTH_YEARS')
        if a['floating_dd_proxy_usd']>=1600 or b['floating_dd_proxy_usd']>=1600:
            reasons.append('FLOATING_DD_PROXY_GTE_1600')
        if c['trades_per_month']<5:reasons.append('LOW_MONTHLY_FREQUENCY')
        if r['stress_extra_one_tick_each_side_dev_net_usd']<=0:reasons.append('STRESS_NET_NONPOSITIVE')
        r['gate']='EXPLORATORY_SURVIVOR_NOT_VALIDATED' if not reasons else 'EXPLORATORY_SCREEN_FAIL'
        r['fail_reasons']=reasons
    return {'status':'V2_REUSED_DEV_EXPLORATION_NOT_VALIDATED',
            'registered_tests_v1_v2':144,
            'legacy_search_tests_not_included_in_Q':True,
            'loaded_dates_2025':False,'loaded_dates_2026':False,
            'split':{'train':'2020-2022','internal':'2023-2024','holdout_2025':'SEALED','exclude_2026':True},
            'registry_sha256':registry_manifest(registry)['registry_sha256'],
            'test_family':96,'n_sessions':len(dates),
            'fill_model':'NQ 1m OHLC -> MNQ price proxy; stop first on ties; 2 ticks adverse each side as relevant; NOT ticks/broker',
            'account_reference_usd':50000,
            'independent_account_portfolio_simulation':False,
            'candidate_results':preliminary}, work