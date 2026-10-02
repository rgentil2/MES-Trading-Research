from datetime import date, timedelta
import math
import numpy as np
import pytest
import statsmodels.api as sm
from tools.audit_research_robustness import audit_events, calendar_bootstrap, day_offset, mean_inference, validated_events, regression_audit


def events(values, days=None, instrument='MES'):
    days = days or [(date(2021,1,1)+timedelta(days=i)).isoformat() for i in range(len(values))]
    return [{'date':d, 'contract':instrument+' JUN21', 'instrument':instrument,
             'gross_pnl_usd':float(v)+4.38,'cost_round_trip_usd':4.38} for d,v in zip(days,values)]


def test_best_day_removal_removes_every_trade_on_that_day():
    rows = events([100,100,-4,-4], ['2021-01-01','2021-01-01','2021-01-02','2021-01-03'])
    report = audit_events(rows, 'MES', draws=100)
    assert report['baseline']['net_expectancy_usd'] == 48
    removed = report['remove_best_1_days']['remaining']
    assert removed['trades'] == 2 and removed['net_expectancy_usd'] == -4
    assert report['strategy_authorized'] is False


def test_session_cluster_and_hc3_match_independent_statsmodels_reference():
    values = np.array([1,3,-2,4,7,-1], float)
    days = ['2021-01-01','2021-01-01','2021-01-02','2021-01-02','2021-01-03','2021-01-03']
    actual = mean_inference(events(values,days), 'MES')
    model = sm.OLS(values,np.ones((len(values),1)))
    cluster = model.fit(cov_type='cluster',cov_kwds={'groups':days},use_t=True)
    hc3 = model.fit(cov_type='HC3',use_t=True)
    assert actual['SESSION_CLUSTER_T']['se'] == pytest.approx(cluster.bse[0])
    assert actual['SESSION_CLUSTER_T']['p_two_sided'] == pytest.approx(cluster.pvalues[0])
    assert actual['HC3_EVENT_DIAGNOSTIC']['se'] == pytest.approx(hc3.bse[0])


def test_calendar_hac_does_not_treat_months_apart_as_adjacent():
    values = [2,4,-1,-3]
    rows = events(values,['2021-01-01','2021-03-01','2021-05-01','2021-07-01'])
    actual = mean_inference(rows,'MES')['CALENDAR_HAC20_T_APPROX']['se']
    residual = np.array(values)-np.mean(values)
    expected = math.sqrt(4/3*np.sum(residual**2)/16)
    assert actual == pytest.approx(expected)


def test_bootstrap_reproducibility_cost_and_event_weighting():
    rows = events([10,10,-4],['2021-01-01','2021-01-01','2021-01-02'])
    a = calendar_bootstrap(rows,'MES',draws=100,block_days=1827)
    b = calendar_bootstrap(rows,'MES',draws=100,block_days=1827)
    assert a == b
    assert a['ci95_net_expectancy_usd'] == pytest.approx([16/3,16/3])


def test_sparse_bootstrap_is_marked_unavailable():
    result = calendar_bootstrap(events([10]),'MES',draws=500,block_days=20)
    assert result['ci95_net_expectancy_usd'] is None


def test_holdout_and_cross_instrument_events_are_rejected():
    with pytest.raises(ValueError):
        day_offset('2025-01-01')
    with pytest.raises(ValueError):
        day_offset('2026-01-01')
    with pytest.raises(ValueError,match='instrument'):
        validated_events(events([1],instrument='ES'),'MES')


def test_explicit_es_cost_profile_and_leave_year_out():
    rows = events([10,-5], ['2020-01-01','2021-01-01'], instrument='ES')
    rows = [{**r,'gross_pnl_usd':r['gross_pnl_usd']-4.38+8,'cost_round_trip_usd':8} for r in rows]
    actual = audit_events(rows,'ES',draws=100)
    assert actual['baseline']['net_expectancy_usd'] == pytest.approx(2.5)
    assert actual['leave_one_year_out']['2020']['net_expectancy_usd'] == pytest.approx(-5)
    assert actual['stress_1_5x_costs']['net_expectancy_usd'] == pytest.approx(-1.5)


def test_daily_regression_covariances_match_statsmodels():
    rng = np.random.default_rng(17)
    x = rng.normal(size=90)
    y = 2*x + rng.normal(size=90)*(1+abs(x))
    rows = [{'date':(date(2022,1,1)+timedelta(days=i)).isoformat(),'x':float(a),'y':float(b)}
            for i,(a,b) in enumerate(zip(x,y))]
    actual = regression_audit(rows)
    model = sm.OLS(y, sm.add_constant(x))
    hc3 = model.fit(cov_type='HC3',use_t=True)
    hac = model.fit(cov_type='HAC',cov_kwds={'maxlags':20,'use_correction':True},use_t=True)
    assert actual['methods']['HC3']['standard_error'] == pytest.approx(hc3.bse[1])
    assert actual['methods']['CALENDAR_HAC20']['standard_error'] == pytest.approx(hac.bse[1])
