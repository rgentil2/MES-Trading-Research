"""MES-MS1: causal daily feature map, separate from frozen R063.

No entry, forward return, trade label, outcome-based selection or live approval.
Episode end dates belong to diagnostics, never to the causal feature table.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import numpy as np
import pandas as pd

VERSION = 'MES-MS1-20261003'
STATES = ['R0', 'R1', 'R2', 'R3', 'R4']


@dataclass(frozen=True)
class Config:
    window: int = 252
    minimum_valid: int = 126
    atr_sessions: int = 14
    trend_sessions: int = 10
    overnight_min_bars: int = 800
    q_low: float = 1 / 3
    q_high: float = 2 / 3
    trend_neutral_atr: float = 1.0
    overnight_flat_atr: float = 0.1
    cusum_k: float = 0.5
    cusum_h: float = 5.0
    transition_sessions: int = 5

    def __post_init__(self):
        if not 2 <= self.minimum_valid <= self.window:
            raise ValueError('invalid warm-up')
        if self.atr_sessions < self.trend_sessions + 1:
            raise ValueError('ATR history must contain all trend closes')
        if not 0 < self.q_low < self.q_high < 1:
            raise ValueError('invalid quantiles')


def hysteresis(value, low, high, previous):
    if not np.isfinite([value, low, high]).all() or low >= high:
        return None
    if value < low:
        return 'LOW'
    if value > high:
        return 'HIGH'
    return previous


def _bands(history, field, cfg):
    values = np.asarray([r.get(field, np.nan) for r in history[-cfg.window:]], float)
    values = values[np.isfinite(values)]
    if len(history) < cfg.window or len(values) < cfg.minimum_valid:
        return np.nan, np.nan, len(values)
    lo, hi = np.quantile(values, [cfg.q_low, cfg.q_high], method='linear')
    return float(lo), float(hi), len(values)


def _bucket(value, low, high, labels):
    if not np.isfinite([value, low, high]).all() or low >= high:
        return 'UNKNOWN'
    return labels[0] if value < low else labels[2] if value > high else labels[1]


def causal_inputs(bars: pd.DataFrame, cfg=Config()):
    """Aggregate only completed prior RTH and current overnight observations.

The historical reader contains full days. Reading a day does not make its RTH
values available to that day's feature computation: all RTH keys are strictly
earlier than the as-of date. Calendar is weekdays, not a certified CME schedule.
"""
    required = {'timestamp_et', 'open', 'high', 'low', 'close', 'volume', 'contract'}
    if not required <= set(bars):
        raise ValueError('missing bar fields')
    b = bars.copy()
    if b.empty or b.timestamp_et.dt.tz is None:
        raise ValueError('nonempty timezone-aware bars required')
    b['timestamp_et'] = b.timestamp_et.dt.tz_convert('America/New_York')
    if b.timestamp_et.duplicated().any() or not b.timestamp_et.is_monotonic_increasing:
        raise ValueError('sorted unique bars required')
    if not b.timestamp_et.dt.year.between(2020, 2024).all():
        raise ValueError('MES-MS1 accepts only calendar 2020-2024')
    if not b.contract.str.match(r'^MES (03|06|09|12)-(20|21|22|23|24)$').all():
        raise ValueError('wrong instrument or contract scope')
    b['day'] = b.timestamp_et.dt.date
    b['minute'] = b.timestamp_et.dt.hour * 60 + b.timestamp_et.dt.minute
    rth = b[(b.minute > 570) & (b.minute <= 960)]
    daily = []
    for day, g in rth.groupby('day', sort=True):
        full = (len(g) == 390 and g.minute.iloc[0] == 571 and
                g.minute.iloc[-1] == 960 and g.contract.nunique() == 1)
        daily.append({'day': day, 'contract': g.contract.iloc[-1], 'full': full,
                      'high': float(g.high.max()), 'low': float(g.low.min()),
                      'close': float(g.close.iloc[-1]), 'volume': float(g.volume.sum())})
    # TR never includes the price basis difference between two contracts.
    previous = None
    for row in daily:
        same = previous is not None and previous['contract'] == row['contract']
        reference = previous['close'] if same else row['close']
        row['tr'] = max(row['high'] - row['low'], abs(row['high'] - reference),
                        abs(row['low'] - reference))
        previous = row
    nights = b[(b.minute >= 1081) | (b.minute <= 570)].copy()
    nights['asof_day'] = nights.day
    evening = nights.minute >= 1081
    nights.loc[evening, 'asof_day'] = (nights.loc[evening, 'timestamp_et'] +
                                             pd.Timedelta(days=1)).dt.date
    overnight = {d: g for d, g in nights.groupby('asof_day', sort=True)}
    days = pd.bdate_range(b.day.min(), b.day.max())
    result = []
    for dt in days:
        day = dt.date()
        cutoff = pd.Timestamp(day).tz_localize('America/New_York') + pd.Timedelta(minutes=570)
        row = {'date': str(day), 'asof_et': cutoff.isoformat(), 'contract': '',
               'input_status': 'UNKNOWN_NO_OVERNIGHT', 'overnight_bars': 0,
               'previous_rth_date': '', 'source_max_et': '', 'roll_reset': False}
        g = overnight.get(day)
        priors = [r for r in daily if r['day'] < day]
        if priors:
            row['previous_rth_date'] = str(priors[-1]['day'])
        if g is None:
            result.append(row); continue
        row.update(contract=str(g.contract.iloc[-1]), overnight_bars=len(g),
                   source_max_et=g.timestamp_et.iloc[-1].isoformat())
        start = cutoff - pd.Timedelta(minutes=929)
        if (len(g) < cfg.overnight_min_bars or g.timestamp_et.iloc[0] != start or
                g.timestamp_et.iloc[-1] != cutoff or g.contract.nunique() != 1):
            row['input_status'] = 'UNKNOWN_OVERNIGHT_COVERAGE'
            result.append(row); continue
        if not priors or not priors[-1]['full']:
            row['input_status'] = 'UNKNOWN_PREVIOUS_RTH'
            result.append(row); continue
        p = priors[-1]
        same = p['contract'] == row['contract']
        row['roll_reset'] = not same
        eligible = [r for r in priors if r['contract'] == row['contract'] and r['full']]
        if not same or len(eligible) < cfg.atr_sessions:
            row['input_status'] = 'UNKNOWN_CONTRACT_WARMUP'
            result.append(row); continue
        h = eligible[-cfg.atr_sessions:]
        atr = float(np.mean([r['tr'] for r in h]))
        closes = np.asarray([r['close'] for r in h[-cfg.trend_sessions - 1:]])
        path = float(np.abs(np.diff(closes)).sum())
        if atr <= 0 or p['close'] <= 0 or path <= 0:
            row['input_status'] = 'UNKNOWN_DEGENERATE_HISTORY'
            result.append(row); continue
        onclose, onfirst = float(g.close.iloc[-1]), float(g.open.iloc[0])
        row.update(input_status='READY', atr14=atr, vol=atr / p['close'],
                   trend_score=(closes[-1] - closes[0]) / atr,
                   er=abs(closes[-1] - closes[0]) / path,
                   overnight_range_atr=(float(g.high.max()) - float(g.low.min())) / atr,
                   overnight_return_atr=(onclose - onfirst) / atr,
                   overnight_volume=float(g.volume.sum()),
                   preopen_gap_proxy_atr=(onclose - p['close']) / atr,
                   pdc=p['close'], pdh=p['high'], pdl=p['low'],
                   pdc_distance_atr=(onclose-p['close'])/atr,
                   pdh_distance_atr=(onclose-p['high'])/atr,
                   pdl_distance_atr=(onclose-p['low'])/atr,
                   value_location='ABOVE_PDH' if onclose > p['high'] else
                   'BELOW_PDL' if onclose < p['low'] else 'INSIDE_PREVIOUS_RANGE',
                   log_vol=float(np.log(atr / p['close'])),
                   log_on_range=float(np.log(max((g.high.max()-g.low.min()) / atr, 1e-9))),
                   log_on_volume=float(np.log(g.volume.sum())))
        result.append(row)
    return result


def classify(inputs, cfg=Config()):
    """Sequential lagged calibration: classify, then append current observation."""
    history, output = [], []
    vol_state = efficiency_state = None
    channels = ['log_vol', 'log_on_range', 'log_on_volume']
    sums = {f: [0., 0.] for f in channels}
    cooldown = 0
    last_contract = None
    previous_ready = False
    for source in inputs:
        row = dict(source)
        if history and row['date'] <= history[-1]['date']:
            raise ValueError('inputs must be sorted, unique')
        if not '2020-01-01' <= row['date'] < '2025-01-01':
            raise ValueError('input outside development scope')
        if row['contract'] and not re.fullmatch(r'MES (03|06|09|12)-(20|21|22|23|24)', row['contract']):
            raise ValueError('wrong instrument or contract scope')
        contract_changed = last_contract is not None and row['contract'] != last_contract
        ready = row['input_status'] == 'READY'
        if not ready or contract_changed or not previous_ready:
            vol_state = efficiency_state = None
            sums = {f: [0., 0.] for f in channels}
            cooldown = 0
        if row['contract']:
            last_contract = row['contract']
        row.update(engine_version=VERSION, regime='R0', r0_reason='',
                   volatility_state='UNKNOWN', efficiency_state='UNKNOWN',
                   change_alert=False, change_channels='', transition_remaining=0,
                   direction='UNKNOWN', overnight_state='UNKNOWN',
                   overnight_direction='UNKNOWN', gap_state='UNKNOWN', volume_state='UNKNOWN')
        for field in ['vol', 'er', 'overnight_range_atr', 'overnight_volume']:
            lo, hi, n = _bands(history, field, cfg)
            row[field + '_q33'], row[field + '_q67'], row[field + '_reference_n'] = lo, hi, n
        calibrated = (len(history) >= cfg.window and
                      row['vol_reference_n'] >= cfg.minimum_valid and
                      row['er_reference_n'] >= cfg.minimum_valid)
        if not ready:
            row['r0_reason'] = row['input_status']
        elif not calibrated:
            row['r0_reason'] = 'UNKNOWN_REFERENCE_WARMUP'
        else:
            alerts = []
            for f in channels:
                prior = np.asarray([r.get(f, np.nan) for r in history[-cfg.window:]], float)
                prior = prior[np.isfinite(prior)]
                if len(prior) < cfg.minimum_valid or not np.isfinite(row.get(f, np.nan)):
                    continue
                sd = float(prior.std(ddof=1))
                if sd <= 1e-12:
                    continue
                z = float(np.clip((row[f]-prior.mean()) / sd, -6, 6))
                plus, minus = sums[f]
                plus, minus = max(0., plus+z-cfg.cusum_k), max(0., minus-z-cfg.cusum_k)
                row[f + '_cusum_z'], row[f + '_cusum_plus'], row[f + '_cusum_minus'] = z, plus, minus
                sums[f] = [plus, minus]
                if max(plus, minus) >= cfg.cusum_h:
                    alerts.append(f)
            if alerts:
                cooldown = cfg.transition_sessions
                sums = {f: [0., 0.] for f in channels}
            row.update(change_alert=bool(alerts), change_channels=','.join(alerts),
                       transition_remaining=cooldown)
            vol_state = hysteresis(row['vol'], row['vol_q33'], row['vol_q67'], vol_state)
            efficiency_state = hysteresis(row['er'], row['er_q33'], row['er_q67'], efficiency_state)
            row['volatility_state'] = vol_state or 'UNKNOWN'
            row['efficiency_state'] = ('DIRECTIONAL' if efficiency_state == 'HIGH' else
                                       'CHOP' if efficiency_state == 'LOW' else 'UNKNOWN')
            if cooldown:
                row['r0_reason'] = 'TRANSITION_CUSUM_ALERT'
                cooldown -= 1
            elif vol_state is None or efficiency_state is None:
                row['r0_reason'] = 'UNKNOWN_BAND_OR_DEGENERATE_REFERENCE'
            else:
                row['regime'] = {('HIGH', 'HIGH'): 'R1', ('HIGH', 'LOW'): 'R2',
                                 ('LOW', 'HIGH'): 'R3', ('LOW', 'LOW'): 'R4'}[(vol_state, efficiency_state)]
        if ready:
            score = row['trend_score']
            row['direction'] = 'BULL' if score > cfg.trend_neutral_atr else 'BEAR' if score < -cfg.trend_neutral_atr else 'NEUTRAL'
            row['overnight_state'] = _bucket(row['overnight_range_atr'], row['overnight_range_atr_q33'], row['overnight_range_atr_q67'], ['COMPRESSED', 'NORMAL', 'EXPANDED'])
            row['volume_state'] = _bucket(row['overnight_volume'], row['overnight_volume_q33'], row['overnight_volume_q67'], ['LOW', 'NORMAL', 'HIGH'])
            onret, gap = row['overnight_return_atr'], row['preopen_gap_proxy_atr']
            row['overnight_direction'] = 'UP' if onret > cfg.overnight_flat_atr else 'DOWN' if onret < -cfg.overnight_flat_atr else 'FLAT'
            row['gap_state'] = 'UP_PROXY' if gap > cfg.overnight_flat_atr else 'DOWN_PROXY' if gap < -cfg.overnight_flat_atr else 'FLAT_PROXY'
            volumes = [r.get('overnight_volume', np.nan) for r in history[-cfg.window:]]
            volumes = np.asarray(volumes, float); volumes = volumes[np.isfinite(volumes)]
            row['overnight_volume_over_median'] = row['overnight_volume'] / np.median(volumes) if calibrated and len(volumes) >= cfg.minimum_valid else np.nan
        output.append(row)
        history.append(dict(source))
        previous_ready = ready
    # IDs and elapsed lengths are causal. Future duration/end is absent here.
    episode, elapsed, previous_key = 0, 0, None
    for row in output:
        key = (row['regime'], row['r0_reason'], row['contract'])
        if key != previous_key:
            episode += 1; elapsed = 0
        elapsed += 1
        row['episode_id'], row['episode_elapsed_sessions'] = episode, elapsed
        previous_key = key
    return pd.DataFrame(output)


def diagnose(features):
    """Retrospective descriptive objects; MUST NOT be joined as signal features."""
    counts = pd.DataFrame(0, index=STATES, columns=STATES, dtype=int)
    for a, b in zip(features.to_dict('records'), features.iloc[1:].to_dict('records')):
        # A missing business date or roll boundary is never bridged.
        adjacent = pd.bdate_range(a['date'], b['date']).size == 2
        if adjacent and a['contract'] and a['contract'] == b['contract']:
            counts.loc[a['regime'], b['regime']] += 1
    probs = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0)
    episodes = []
    for eid, g in features.groupby('episode_id', sort=True):
        episodes.append({'episode_id': int(eid), 'regime': g.regime.iloc[0],
                         'r0_reason': g.r0_reason.iloc[0], 'contract': g.contract.iloc[0],
                         'start': g.date.iloc[0], 'end': g.date.iloc[-1],
                         'sessions': len(g), 'left_censored': eid == features.episode_id.iloc[0],
                         'right_censored': eid == features.episode_id.iloc[-1]})
    return counts, probs, pd.DataFrame(episodes)


def configuration():
    return asdict(Config())
