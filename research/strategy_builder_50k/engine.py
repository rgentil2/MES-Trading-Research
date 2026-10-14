"""Standalone *exploratory* NQ 1m strategy builder for a modelled $50k evaluation.

ZERO dependency on NT8 execution/CSV/previous strategy logic. Data: already audited
2020-24 zip reader; 2025 and 2026 never opened. No live orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

TICK = 0.25
POINT_MNQ = 2.0
FEE_MNQ_RT = 1.90  # research assumption, must reconfirm for chosen funded provider
SLIP_TICKS_SIDE = 2
MAX_CONTRACTS = 5  # conservative internal design, not official company limit
ACCOUNT_NOMINAL = 50_000.0
EOD_LOSS_REFERENCE = 2_000.0
TARGET_REFERENCE = 3_000.0
RISK_PER_TRADE = 250.0
SEED = 20261014
FEATURES = ("EMA", "SMA", "RSI", "ATR", "ADX", "MACD", "BBANDS", "STOCH", "CCI",
            "ROC", "DONCHIAN", "KELTNER", "VWAP", "OBV", "MFI", "WILLIAMS_R", "VOLUME_Z")
FAMILIES = ("ema_trend", "sma_cross", "rsi_reversal", "bollinger_fade", "macd_cross",
            "stoch_reversal", "cci_reversal", "donchian_break", "keltner_break",
            "roc_momentum", "williams_reversal", "adx_trend", "mfi_reversal",
            "obv_momentum", "vwap_fade", "volume_break")
FILTERS = ("volume_confirm", "adx_confirm", "regime_quiet")


@dataclass(frozen=True)
class Candidate:
    id: str
    mechanism: str
    filter_name: str
    stop_atr_mult: float
    reward_r: float
    max_hold_min: int
    side_mode: str = "BOTH"

    def digest(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:16]


def build_registry() -> list[Candidate]:
    """Exactly 48 fixed tests, 16 distinct base mechanisms x 3 locked contexts.

    This is a declared small combinatorial grammar; no result-conditioned mutation.
    """
    configurations = (("volume_confirm", 1.0, 1.5, 20),
                      ("adx_confirm", 1.5, 1.5, 30),
                      ("regime_quiet", 2.0, 2.0, 30))
    return [Candidate(f"SB-{i:02d}-{k}", fam, flt, st, r, hold)
            for i, fam in enumerate(FAMILIES, 1)
            for k, (flt, st, r, hold) in enumerate(configurations, 1)]


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def indicators(day: np.ndarray) -> pd.DataFrame:
    """Only current-and-earlier COMPLETED bars. Never backward fill."""
    if day.ndim != 2 or day.shape[1] != 5:
        raise ValueError("Expected [bars, OHLCV] 5 columns")
    a = np.asarray(day, dtype=float)
    if (a[:, 1] < a[:, [0, 3]].max(axis=1)).any() or (a[:, 2] > a[:, [0, 3]].min(axis=1)).any():
        raise ValueError("Malformed OHLC source")
    if (a[:, 4] <= 0).any() or (a[:, :4] <= 0).any():
        raise ValueError("No positive prices/volume")
    d = pd.DataFrame(a, columns=["open", "high", "low", "close", "volume"])
    c, hi, lo, v = d.close, d.high, d.low, d.volume
    typical = (hi + lo + c) / 3
    prev_c = c.shift(1)
    tr = pd.concat([hi-lo, (hi-prev_c).abs(), (lo-prev_c).abs()], axis=1).max(axis=1)
    tr.iloc[0] = hi.iloc[0]-lo.iloc[0]
    d["atr"] = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    d["ema_fast"], d["ema_slow"] = _ema(c, 9), _ema(c, 21)
    d["sma_fast"], d["sma_slow"] = c.rolling(10, min_periods=10).mean(), c.rolling(30, min_periods=30).mean()
    delta = c.diff()
    ups, downs = delta.clip(lower=0), -delta.clip(upper=0)
    u = ups.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    dn = downs.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = u / dn.replace(0, np.nan)
    d["rsi"] = 100-100/(1+rs)
    d.loc[(dn == 0) & (u > 0), "rsi"] = 100
    d.loc[(dn == 0) & (u == 0), "rsi"] = 50
    plus_dm = hi.diff().where(lambda x: x > 0, 0).where(hi.diff() > -lo.diff(), 0)
    minus_dm = (-lo.diff()).where(lambda x: x > 0, 0).where(-lo.diff() > hi.diff(), 0)
    sm_tr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean()/sm_tr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean()/sm_tr.replace(0, np.nan)
    dx = 100*(plus_di-minus_di).abs()/(plus_di+minus_di).replace(0, np.nan)
    d["adx"] = dx.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    d["macd"] = _ema(c, 12)-_ema(c, 26)
    d["macd_sig"] = _ema(d.macd, 9)
    mid = c.rolling(20, min_periods=20).mean()
    dev = c.rolling(20, min_periods=20).std(ddof=0)
    d["bb_hi"], d["bb_lo"] = mid + 2*dev, mid-2*dev
    h14, l14 = hi.rolling(14,min_periods=14).max(),lo.rolling(14,min_periods=14).min()
    d["stoch"] = 100*(c-l14)/(h14-l14).replace(0,np.nan)
    d["williams"] = -100*(h14-c)/(h14-l14).replace(0,np.nan)
    tp_ma = typical.rolling(20,min_periods=20).mean()
    tp_md = (typical-tp_ma).abs().rolling(20,min_periods=20).mean()
    d["cci"] = (typical-tp_ma)/(0.015*tp_md.replace(0,np.nan))
    d["roc"] = 100*(c/c.shift(10)-1)
    d["don_hi"] = hi.shift(1).rolling(20,min_periods=20).max()
    d["don_lo"] = lo.shift(1).rolling(20,min_periods=20).min()
    d["kelt_hi"],d["kelt_lo"] = d.ema_slow + 1.5*d.atr, d.ema_slow-1.5*d.atr
    d["vwap"] = (typical*v).cumsum()/v.cumsum()
    d["obv"] = (np.sign(c.diff().fillna(0))*v).cumsum()
    d["obv_ma"] = d.obv.rolling(20,min_periods=20).mean()
    pos = typical.diff().gt(0)
    money = typical*v
    pmf = money.where(pos,0).rolling(14,min_periods=14).sum()
    nmf = money.where(~pos,0).rolling(14,min_periods=14).sum()
    d["mfi"] = 100*pmf/(pmf+nmf).replace(0,np.nan)
    d["volume_z"] = (v-v.rolling(20,min_periods=20).mean())/v.rolling(20,min_periods=20).std(ddof=0).replace(0,np.nan)
    d["atr_pct"] = d.atr/d.close
    d["atr_pct_med"] = d.atr_pct.shift(1).rolling(30,min_periods=30).median()
    return d


def _cross_above(a,b): return (a>b)&(a.shift(1)<=b.shift(1))
def _cross_below(a,b): return (a<b)&(a.shift(1)>=b.shift(1))


def directional_signal(d: pd.DataFrame, mechanism: str) -> np.ndarray:
    """+1 long, -1 short, 0 idle, signal produced at current bar CLOSE."""
    c=d.close
    lo = pd.Series(False,index=d.index)
    sh = pd.Series(False,index=d.index)
    if mechanism == 'ema_trend':
        lo = _cross_above(d.ema_fast,d.ema_slow)&(c>d.vwap)
        sh = _cross_below(d.ema_fast,d.ema_slow)&(c<d.vwap)
    elif mechanism == 'sma_cross':
        lo = _cross_above(d.sma_fast,d.sma_slow)
        sh = _cross_below(d.sma_fast,d.sma_slow)
    elif mechanism == 'rsi_reversal':
        lo = (d.rsi.shift(1)<30)&(d.rsi>=30)
        sh = (d.rsi.shift(1)>70)&(d.rsi<=70)
    elif mechanism == 'bollinger_fade':
        lo = (c.shift(1)<d.bb_lo.shift(1))&(c>=d.bb_lo)
        sh = (c.shift(1)>d.bb_hi.shift(1))&(c<=d.bb_hi)
    elif mechanism == 'macd_cross':
        lo = _cross_above(d.macd,d.macd_sig)
        sh = _cross_below(d.macd,d.macd_sig)
    elif mechanism == 'stoch_reversal':
        lo = (d.stoch.shift(1)<20)&(d.stoch>=20)
        sh = (d.stoch.shift(1)>80)&(d.stoch<=80)
    elif mechanism == 'cci_reversal':
        lo = (d.cci.shift(1)<-100)&(d.cci>=-100)
        sh = (d.cci.shift(1)>100)&(d.cci<=100)
    elif mechanism == 'donchian_break':
        lo = c>d.don_hi
        sh = c<d.don_lo
    elif mechanism == 'keltner_break':
        lo = c>d.kelt_hi
        sh = c<d.kelt_lo
    elif mechanism == 'roc_momentum':
        lo = (d.roc>0.2)&(d.roc.shift(1)<=0.2)
        sh = (d.roc<-.2)&(d.roc.shift(1)>=-.2)
    elif mechanism == 'williams_reversal':
        lo = (d.williams.shift(1)<-80)&(d.williams>=-80)
        sh = (d.williams.shift(1)>-20)&(d.williams<=-20)
    elif mechanism == 'adx_trend':
        lo = _cross_above(d.adx,pd.Series(22.,index=d.index))&(d.ema_fast>d.ema_slow)
        sh = _cross_above(d.adx,pd.Series(22.,index=d.index))&(d.ema_fast<d.ema_slow)
    elif mechanism == 'mfi_reversal':
        lo = (d.mfi.shift(1)<20)&(d.mfi>=20)
        sh = (d.mfi.shift(1)>80)&(d.mfi<=80)
    elif mechanism == 'obv_momentum':
        lo = _cross_above(d.obv,d.obv_ma)&(c>d.ema_slow)
        sh = _cross_below(d.obv,d.obv_ma)&(c<d.ema_slow)
    elif mechanism == 'vwap_fade':
        lo = (c<d.vwap-1.2*d.atr)&(c.shift(1)>=d.vwap.shift(1)-1.2*d.atr.shift(1))
        sh = (c>d.vwap+1.2*d.atr)&(c.shift(1)<=d.vwap.shift(1)+1.2*d.atr.shift(1))
    elif mechanism == 'volume_break':
        lo = (d.volume_z>1.5)&(c>d.don_hi)
        sh = (d.volume_z>1.5)&(c<d.don_lo)
    else: raise ValueError('UNKNOWN_MECHANISM: '+mechanism)
    out = np.where(lo & ~sh,1,np.where(sh & ~lo,-1,0)).astype(np.int8)
    out[~np.isfinite(d.atr.to_numpy())]=0
    return out


def filter_mask(d: pd.DataFrame, flt: str) -> np.ndarray:
    if flt=='volume_confirm': return (d.volume_z > .3).fillna(False).to_numpy()
    if flt=='adx_confirm': return (d.adx>20).fillna(False).to_numpy()
    if flt=='regime_quiet': return (d.atr_pct<d.atr_pct_med).fillna(False).to_numpy()
    raise ValueError('UNKNOWN_FILTER: '+flt)


def round_to_grid_up(points: float) -> float:
    return max(0.25,math.ceil(points/TICK-1e-12)*TICK)


def _exit(day:np.ndarray, entry_i:int, side:int, entry:float, stop_pts:float, tp_pts:float, max_hold:int):
    """OHLC conservative: entry at next open + adverse slip, stop before target on ties.

    Time-exit uses next minute OPEN after allowed holding interval. Intrabar low/high
    is NOT a verified tick sequence; worst-case drawdown is a proxy.
    """
    sl = entry - side*stop_pts
    tp = entry + side*tp_pts
    max_adverse=0.0
    last=min(entry_i+max_hold-1,len(day)-1)
    for j in range(entry_i,last+1):
        o,h,l,c,_=day[j]
        adverse = max(0.,entry-l if side==1 else h-entry)
        max_adverse = max(max_adverse,adverse)
        # Price can gap through stop/target at the bar OPEN; don't grant ideal stop fill.
        if side*(o-sl)<=0:
            return (float(o-side*SLIP_TICKS_SIDE*TICK),j,'STOP_GAP',max_adverse)
        if side*(o-tp)>=0:
            return (float(tp),j,'TARGET_GAP',max_adverse)
        hit_sl = l<=sl if side==1 else h>=sl
        hit_tp = h>=tp if side==1 else l<=tp
        if hit_sl: return (float(sl-side*SLIP_TICKS_SIDE*TICK),j,'STOP' if not hit_tp else 'AMBIGUOUS_STOP_FIRST',max_adverse)
        if hit_tp: return (float(tp),j,'TARGET',max_adverse)
    k=min(last+1,len(day)-1)
    return (float(day[k,0]-side*SLIP_TICKS_SIDE*TICK),k,'TIME' if k>last else 'SESSION_CLOSE',max_adverse)


def trade_for_day(day:np.ndarray, date_str:str, candidate:Candidate):
    f=indicators(day)
    signal=directional_signal(f,candidate.mechanism)
    signal[~filter_mask(f,candidate.filter_name)]=0
    # timestamps are END of each RTH minute: i=0 -> 09:31, i=118 -> 11:29
    # i+1 is next bar OPEN at close of current bar, never current bar OPEN.
    eligible = np.flatnonzero(signal[4:119])+4
    for i in eligible:
        side=int(signal[i]);atr=float(f.atr.iat[i])
        if not np.isfinite(atr):continue
        stop_pts=round_to_grid_up(min(60.,max(8.,atr*candidate.stop_atr_mult)))
        target_pts=round_to_grid_up(stop_pts*candidate.reward_r)
        open_next=float(day[i+1,0])
        entry=open_next+side*SLIP_TICKS_SIDE*TICK
        risk_per_mnq=(stop_pts+SLIP_TICKS_SIDE*TICK)*POINT_MNQ+FEE_MNQ_RT
        quantity=min(MAX_CONTRACTS,int(RISK_PER_TRADE//risk_per_mnq))
        if quantity<1:continue
        exit_px,exit_i,reason,mae=_exit(day,i+1,side,entry,stop_pts,target_pts,candidate.max_hold_min)
        pnl=side*(exit_px-entry)*POINT_MNQ*quantity - FEE_MNQ_RT*quantity
        floating_proxy=(-mae*POINT_MNQ - FEE_MNQ_RT)*quantity
        return dict(candidate=candidate.id,day=date_str,year=int(date_str[:4]),signal_i=int(i),
                    entry_i=int(i+1),exit_i=int(exit_i),side=side,instrument='MNQ_PROXY',qty=quantity,
                    entry=round(entry,2),exit=round(exit_px,2),sl_pts=stop_pts,tp_pts=target_pts,
                    reason=reason,net=round(pnl,2),floating_mae_proxy_usd=round(floating_proxy,2),
                    reference_cost_rt=FEE_MNQ_RT*quantity,score_source='MINUTE_LAST_PROXY')
    return None


def metrics(trades:list[dict],years:tuple[int,...]) -> dict:
    selected=[t for t in trades if t['year'] in years]
    n=len(selected); n_months=len(years)*12
    net=np.array([t['net'] for t in selected],float)
    gain=float(net[net>0].sum());loss=float(-net[net<0].sum())
    cum=0.;peak=0.;maxdd=0.;floating_dd=0.;first_target=None;first_breach=None
    for t in selected:
        floating_dd=max(floating_dd, peak-(cum+t['floating_mae_proxy_usd']))
        if first_breach is None and floating_dd>=EOD_LOSS_REFERENCE:first_breach=t['day']
        cum+=t['net']; peak=max(peak,cum)
        maxdd=max(maxdd,peak-cum)
        if first_target is None and cum>=TARGET_REFERENCE:first_target=t['day']
    by_year={str(y):round(float(sum(t['net'] for t in selected if t['year']==y)),2) for y in years}
    return dict(n=n,net_usd=round(float(net.sum()),2),mean_usd=round(float(net.mean()),2) if n else None,
                pf=round(gain/loss,3) if loss>0 else None,win_pct=round(100*float((net>0).mean()),1) if n else None,
                trades_per_month=round(n/n_months,2),closed_dd_usd=round(maxdd,2),
                floating_dd_proxy_usd=round(floating_dd,2),funded_loss_reference_breach=first_breach,
                target_reference_reached=first_target,positive_years=sum(x>0 for x in by_year.values()),yearly_net=by_year)


def _weekly_test(trades:list[dict],rng:np.random.Generator,replications:int=1000):
    if not trades:return (1.,(None,None))
    by_week={}
    for t in trades:
        year,week,_=datetime.fromisoformat(t['day']).isocalendar()
        key=f'{year}-W{week:02d}';ss=by_week.setdefault(key,[0.,0.]);ss[0]+=t['net'];ss[1]+=1
    blocks=np.array(list(by_week.values()),float)
    if len(blocks)<5:return (1.,(None,None))
    observed=blocks[:,0].sum()
    flips=rng.choice((-1.,1.),size=(replications,len(blocks)))
    p=(1+int(np.count_nonzero((flips*blocks[:,0]).sum(axis=1)>=observed)))/(replications+1)
    boot_ix=rng.integers(0,len(blocks),size=(replications,len(blocks)))
    chosen=blocks[boot_ix]
    means=chosen[:,:,0].sum(axis=1)/np.maximum(chosen[:,:,1].sum(axis=1),1)
    q=np.quantile(means,[.05,.95])
    return round(p,5),(round(float(q[0]),3),round(float(q[1]),3))


def _bh(pvalues:dict[str,float]) ->dict[str,float]:
    ordered=sorted(pvalues,key=lambda k:(pvalues[k],k))
    result={};q=1.;n=len(ordered)
    for rank,name in reversed(list(enumerate(ordered,start=1))):
        q=min(q,n*pvalues[name]/rank);result[name]=round(q,5)
    return result


def analyze(days:np.ndarray, dates:list[str], registry:list[Candidate], replications=1000):
    if days.ndim!=3 or days.shape[1:]!=(390,5) or len(days)!=len(dates):
        raise ValueError('SOURCE_MUST_BE_COMPLETE_390_RTH_NQ_1MIN')
    if any(not ('2020-01-01'<=d<='2024-12-31') for d in dates):
        raise ValueError('SEALED_2025_2026_DATA_BLOCKED_NO_PRICE_READ')
    if sorted(dates)!=dates or len(set(dates))!=len(dates):raise ValueError('BAD_SESSION_ORDER')
    registry_hash=sha256(json.dumps([asdict(x) for x in registry],sort_keys=True).encode()).hexdigest()
    # Only data-array pipeline, no NASDAQ historical PRICES stored in code or report.
    # Compute same-day features once and share cached signals/filters across
    # all 48 candidates. Never retain 1,221 big dataframes in memory.
    work={c.id:[] for c in registry}
    for di,(day,day_label) in enumerate(zip(days,dates)):
        if di%250==0:print(f'RTH loaded/scored: {di}/{len(dates)}',flush=True)
        f=indicators(day)
        signals={name:directional_signal(f,name) for name in set(c.mechanism for c in registry)}
        masks={name:filter_mask(f,name) for name in set(c.filter_name for c in registry)}
        for c in registry:
            s=signals[c.mechanism]
            allowed=masks[c.filter_name]
            idxs=np.flatnonzero((s[4:119]!=0)&allowed[4:119])+4
            for i in idxs:
                atr=float(f.atr.iat[i]);side=int(s[i])
                if not np.isfinite(atr):continue
                sl=round_to_grid_up(min(60.,max(8.,atr*c.stop_atr_mult)))
                tp=round_to_grid_up(sl*c.reward_r)
                entry=float(day[i+1,0]+side*SLIP_TICKS_SIDE*TICK)
                unit_risk=(sl+SLIP_TICKS_SIDE*TICK)*POINT_MNQ+FEE_MNQ_RT
                q=min(MAX_CONTRACTS,int(RISK_PER_TRADE//unit_risk))
                if q<1:continue
                ex,j,why,mae=_exit(day,i+1,side,entry,sl,tp,c.max_hold_min)
                pnl=round(side*(ex-entry)*POINT_MNQ*q-FEE_MNQ_RT*q,2)
                work[c.id].append(dict(candidate=c.id,day=day_label,year=int(day_label[:4]),
                     signal_i=int(i),entry_i=int(i+1),exit_i=int(j),side=side,instrument='MNQ_PROXY',
                     qty=q,entry=round(entry,2),exit=round(ex,2),sl_pts=sl,tp_pts=tp,reason=why,
                     net=pnl,floating_mae_proxy_usd=round((-mae*POINT_MNQ-FEE_MNQ_RT)*q,2)))
                break # exactly 1 / session / candidate: base research unit
    report=[];pvals={};rng=np.random.default_rng(SEED)
    for c in registry:
        tr=work[c.id]
        train=[x for x in tr if x['year']<=2022]
        dev=[x for x in tr if x['year']<=2024]
        p,ci=_weekly_test(train,rng,replications)
        pvals[c.id]=p
        report.append(dict(id=c.id,mechanism=c.mechanism,filter=c.filter_name,spec=asdict(c),
                    hash=c.digest(),train_2020_22=metrics(tr,(2020,2021,2022)),
                    internal_2023_24=metrics(tr,(2023,2024)),
                    dev_2020_24=metrics(tr,(2020,2021,2022,2023,2024)),
                    weekly_p_train=p,ci90_mean_usd_train=ci,
                    stress_extra_one_tick_both_sides_dev_usd=round(sum(t['net']-
                          POINT_MNQ*TICK*2*t['qty'] for t in dev),2),
                    signal_count_per_family=len(tr)))
    q=_bh(pvals)
    for r in report:
        r['bh_q_train_family_48']=q[r['id']]
        a,b=r['train_2020_22'],r['internal_2023_24']
        # Controls are provisional screening gates, NOT confirmatory statistical discovery.
        reasons=[]
        if a['n']<90:reasons.append('TRAIN_N_LT90')
        if a['pf'] is None or a['pf']<1.25:reasons.append('TRAIN_PF_LT1_25')
        if a['floating_dd_proxy_usd']>=1600:reasons.append('TRAIN_FLOATING_DD_GTE1600')
        if r['ci90_mean_usd_train'][0] is None or r['ci90_mean_usd_train'][0]<=0:reasons.append('TRAIN_CI90_NOT_POSITIVE')
        if r['bh_q_train_family_48']>.1:reasons.append('TRAIN_BH_Q_GT_0_1')
        if b['n']<60:reasons.append('INTERNAL_N_LT60')
        if b['pf'] is None or b['pf']<1.25:reasons.append('INTERNAL_PF_LT1_25')
        if b['floating_dd_proxy_usd']>=1600:reasons.append('INTERNAL_FLOATING_DD_GTE1600')
        if b['positive_years']<2:reasons.append('INTERNAL_POSITIVE_YEARS_LT2')
        if r['stress_extra_one_tick_both_sides_dev_usd']<=0:reasons.append('STRESS_NET_NOT_POSITIVE')
        if r['dev_2020_24']['trades_per_month']<5:reasons.append('DEV_TRADES_PER_MONTH_LT5')
        r['gate']='EXPLORATORY_PASS_NOT_VALIDATED' if not reasons else 'SCREEN_FAIL'
        r['reasons']=reasons
    return dict(status='REUSED_DEV_EXPLORATORY_NOT_INDEPENDENT_VALIDATION',
                source='NQ original NinjaTrader Minute Last 2020-2024 only',
                date_windows={'train':'2020-2022','internal':'2023-2024','validation_2025':'SEALED','year_2026':'EXCLUDED'},
                registry_sha256=registry_hash,n_candidates=len(registry),n_rth_sessions=len(dates),
                assumptions={'instrument_fills':'MNQ proxy from NQ minute bars, not MNQ tick fills',
                'commission_roundtrip_per_micro':FEE_MNQ_RT,
                'slippage_ticks_each_side':SLIP_TICKS_SIDE,'max_micro_contracts':MAX_CONTRACTS,
                'max_risk_usd':RISK_PER_TRADE,'loss_cushion_reference_usd':EOD_LOSS_REFERENCE,
                'target_reference_usd':TARGET_REFERENCE,
                'account_rule_reconfirmation_required':True,
                'entry':'NEXT_BAR_OPEN after completed signal bar',
                'both_brackets_hit':'STOP_FIRST',
                'no_2025_2026_data_read':True,
                'not_funding_account_simulation':True},
                candidates=report),work
