import numpy as np
import pandas as pd
import pytest

from src.mes_market_state_v1 import Config, causal_inputs, classify, diagnose, hysteresis


CFG = Config(window=8, minimum_valid=4, atr_sessions=14, trend_sessions=10)


def inputs(n=60):
    result = []
    for i, day in enumerate(pd.bdate_range('2020-01-01', periods=n)):
        vol = .01 + .003 * np.sin(i * .5)
        er = .5 + .3 * np.cos(i * .4)
        result.append(dict(date=str(day.date()), contract='MES 03-20',
                           input_status='READY', vol=vol, er=er, trend_score=.5,
                           overnight_range_atr=1.1+.3*np.sin(i), overnight_return_atr=.2,
                           overnight_volume=1000+30*i, preopen_gap_proxy_atr=.3,
                           log_vol=np.log(vol), log_on_range=np.log(1.1+.3*np.sin(i)),
                           log_on_volume=np.log(1000+30*i)))
    return result


def bars(n=25):
    parts = []
    for i, day in enumerate(pd.bdate_range('2020-01-02', periods=n)):
        cut = day.tz_localize('America/New_York') + pd.Timedelta(minutes=570)
        ts = pd.date_range(cut-pd.Timedelta(minutes=929), cut+pd.Timedelta(minutes=390), freq='min')
        p = 3000 + i * 2 + np.sin(np.arange(len(ts))/100)
        parts.append(pd.DataFrame(dict(timestamp_et=ts, open=p, high=p+.5,
                                        low=p-.5, close=p, volume=10, contract='MES 03-20')))
    return pd.concat(parts, ignore_index=True).sort_values('timestamp_et').reset_index(drop=True)


def test_hysteresis_and_equal_thresholds():
    assert hysteresis(2, 1, 3, None) is None
    assert hysteresis(2, 1, 3, 'LOW') == 'LOW'
    assert hysteresis(4, 1, 3, 'LOW') == 'HIGH'
    assert hysteresis(0, 1, 3, 'HIGH') == 'LOW'
    assert hysteresis(2, 2, 2, 'HIGH') is None


def test_prefix_invariance_and_future_mutation():
    x = inputs()
    full = classify(x, CFG)
    pd.testing.assert_frame_equal(full.iloc[:30].reset_index(drop=True),
                                  classify(x[:30], CFG).reindex(columns=full.columns))
    changed = [dict(r) for r in x]
    for r in changed[30:]:
        r.update(vol=99, er=.99, log_vol=50, overnight_volume=1_000_000_000)
    pd.testing.assert_frame_equal(full.iloc[:30], classify(changed, CFG).iloc[:30])


def test_current_value_excluded_from_reference():
    x = inputs()
    a = classify(x, CFG)
    x[20]['vol'] = 100
    b = classify(x, CFG)
    assert a.iloc[20].vol_q33 == b.iloc[20].vol_q33
    assert a.iloc[20].vol_q67 == b.iloc[20].vol_q67
    assert a.iloc[21].vol_q67 != b.iloc[21].vol_q67


def test_roll_and_missing_input_reset_memory():
    x = inputs()
    x[30]['input_status'] = 'UNKNOWN_OVERNIGHT_COVERAGE'
    x[31]['vol'] = np.median([r['vol'] for r in x[23:31]])
    a = classify(x, CFG)
    assert a.iloc[30].regime == 'R0'
    assert a.iloc[31].volatility_state == 'UNKNOWN'
    x[40]['contract'] = 'MES 06-20'
    _, _, episodes = diagnose(classify(x, CFG))
    assert not any(r.start < x[40]['date'] < r.end for r in episodes.itertuples())


def test_cusum_is_alert_not_probability_and_can_cool_down():
    x = inputs()
    x[20]['log_vol'] = 100
    cfg = Config(window=8, minimum_valid=4, cusum_h=5, transition_sessions=5)
    a = classify(x, cfg)
    assert bool(a.iloc[20].change_alert)
    assert a.iloc[20].r0_reason == 'TRANSITION_CUSUM_ALERT'
    assert a.iloc[20].transition_remaining == 5
    assert not any('probability' in c for c in a)


def test_current_rth_cannot_change_preopen_features():
    b = bars()
    day = pd.Timestamp('2020-02-03', tz='America/New_York')
    cutoff = day + pd.Timedelta(minutes=570)
    a = causal_inputs(b)
    modified = b.copy()
    mask = (modified.timestamp_et > cutoff) & (modified.timestamp_et < day+pd.Timedelta(days=1))
    modified.loc[mask, ['open','high','low','close']] += 1000
    c = causal_inputs(modified)
    ar = next(r for r in a if r['date'] == '2020-02-03')
    cr = next(r for r in c if r['date'] == '2020-02-03')
    assert ar == cr
    prefix = causal_inputs(b[b.timestamp_et <= cutoff])
    assert next(r for r in prefix if r['date'] == ar['date']) == ar
    assert pd.Timestamp(ar['source_max_et']) <= cutoff
    assert ar['previous_rth_date'] < ar['date']


def test_contract_basis_jump_cannot_create_trend():
    b = bars(35)
    baseline = b.copy()
    cutoff = pd.Timestamp('2020-01-28', tz='America/New_York') - pd.Timedelta(hours=6)
    mask = b.timestamp_et >= cutoff
    b.loc[mask, 'contract'] = 'MES 06-20'
    baseline.loc[mask, 'contract'] = 'MES 06-20'
    b.loc[mask, ['open','high','low','close']] += 500
    rows = causal_inputs(b)
    first = next(r for r in rows if r['contract'] == 'MES 06-20')
    assert first['input_status'] != 'READY'
    for r in rows:
        if r['input_status'] == 'READY':
            assert abs(r['trend_score']) < 30
    refs = {r['date']: r for r in causal_inputs(baseline)}
    for r in rows:
        if r['input_status'] == 'READY' and r['contract'] == 'MES 06-20':
            assert r['atr14'] == pytest.approx(refs[r['date']]['atr14'])
            assert r['trend_score'] == pytest.approx(refs[r['date']]['trend_score'])
            assert r['er'] == pytest.approx(refs[r['date']]['er'])


def test_reject_holdout_and_wrong_instrument():
    x = inputs()
    x[-1]['date'] = '2025-01-01'
    with pytest.raises(ValueError, match='scope'):
        classify(x, CFG)
    b = bars()
    b['contract'] = 'ES 03-20'
    with pytest.raises(ValueError, match='instrument'):
        causal_inputs(b)
    b['contract'] = 'MES 03-20'
    b['timestamp_et'] += pd.DateOffset(years=5)
    with pytest.raises(ValueError, match='2020-2024'):
        causal_inputs(b)


def test_diagnostic_future_duration_never_in_features():
    a = classify(inputs(), CFG)
    counts, probabilities, episodes = diagnose(a)
    assert counts.to_numpy().sum() == len(a)-1
    assert np.allclose(probabilities.loc[counts.sum(axis=1) > 0].sum(axis=1), 1)
    assert probabilities.loc[counts.sum(axis=1) == 0].isna().all().all()
    assert bool(episodes.iloc[0].left_censored)
    assert bool(episodes.iloc[-1].right_censored)
    assert not {'end', 'sessions', 'right_censored'} & set(a)
    b = a.copy()
    b.loc[20:, 'contract'] = 'MES 06-20'
    assert diagnose(b)[0].to_numpy().sum() == len(a)-2


def test_missing_overnight_endpoint_blocks_classification():
    b = bars()
    target = pd.Timestamp('2020-02-03 09:30', tz='America/New_York')
    rows = causal_inputs(b[b.timestamp_et != target])
    r = next(r for r in rows if r['date'] == '2020-02-03')
    assert r['input_status'] == 'UNKNOWN_OVERNIGHT_COVERAGE'
