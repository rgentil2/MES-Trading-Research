"""NQ V2.1 RTH warmup tests: same contract, no lookahead, session boundaries."""
import unittest
import numpy as np
from research.nq import nq_m1_v21_warmup_context as w
from research.nq import nq_m1_v2_m1_engine as e


def series(base: float=100):
    b=np.empty((390,5),float)
    for i in range(390):
        p=base+i*.25
        b[i]=[p,p+1,p-1,p+.25,1000+i%4]
    return b


class TestV21Warmup(unittest.TestCase):
    def setUp(self):
        self.prev=w.SessionMeta("2021-01-04","NQH21")
        self.target=w.SessionMeta("2021-01-05","NQH21")
        self.prev_data=series(100)
        self.current=series(197.5)
        self.hist=[(self.prev,self.prev_data)]

    def test_long_sma_first_bar_has_real_prior_bar_context(self):
        block={"name":"SMA","parameters":{"period":200,"source":"close"}}
        self.assertIsNone(e.indicator_value(self.current,0,block))
        val=w.indicator_at(self.target,self.current,0,block,self.hist)
        self.assertIsNotNone(val)
        context=np.vstack([self.prev_data,self.current[:1]])
        self.assertAlmostEqual(val,float(np.mean(context[-200:,3])))

    def test_future_changes_do_not_modify_causal_warmup(self):
        b={"name":"RSI","parameters":{"period":50}}
        a=w.indicator_at(self.target,self.current,20,b,self.hist)
        changed=self.current.copy()
        changed[21:,:4]+=1000
        z=w.indicator_at(self.target,changed,20,b,self.hist)
        self.assertEqual(a,z)

    def test_vwap_resets_at_session_open(self):
        b={"name":"VWAP","parameters":{"anchor":"session"}}
        local=w.indicator_at(self.target,self.current,15,b,self.hist)
        direct=e.indicator_value(self.current,15,b)
        self.assertAlmostEqual(local,direct)
        changed_prev=series(10000)
        changed=w.indicator_at(self.target,self.current,15,b,[(self.prev,changed_prev)])
        self.assertAlmostEqual(changed,local)

    def test_obv_resets_at_current_session(self):
        b={"name":"OBV","parameters":{}}
        self.assertEqual(w.indicator_at(self.target,self.current,0,b,self.hist),
                         self.current[0,4])

    def test_reject_future_current_or_holdout_previous(self):
        b={"name":"SMA","parameters":{"period":20}}
        wrong=[
            (w.SessionMeta("2021-01-05","NQH21"),series(100)),
            (w.SessionMeta("2021-01-06","NQH21"),series(100)),
            (w.SessionMeta("2025-01-03","NQH25"),series(100)),
        ]
        for entry in wrong:
            with self.assertRaises(PermissionError):
                w.indicator_at(self.target,self.current,10,b,[entry])

    def test_reject_unadjusted_contract_roll(self):
        bad=w.SessionMeta("2021-01-04","NQZ20")
        with self.assertRaises(ValueError):
            w.history_for_session(self.target,self.current,[(bad,self.prev_data)])

    def test_reject_duplicate_or_unsorted_sessions(self):
        older=w.SessionMeta("2020-12-30","NQH21")
        with self.assertRaises(ValueError):
            w.history_for_session(self.target,self.current,
                                [(self.prev,self.prev_data),(older,series(100))])
        with self.assertRaises(ValueError):
            w.history_for_session(self.target,self.current,
                                [(self.prev,self.prev_data),(self.prev,series(100))])

    def test_previous_bars_truncated_to_explicit_session_budget(self):
        metas=[
            w.SessionMeta("2021-01-01","NQH21"),
            w.SessionMeta("2021-01-02","NQH21"),
            w.SessionMeta("2021-01-04","NQH21")
        ]
        b=w.history_for_session(self.target,self.current,
                                [(m,series(100+i*400)) for i,m in enumerate(metas)])
        self.assertEqual(b.shape,(780,5))
        self.assertAlmostEqual(b[0,0],500)
        self.assertAlmostEqual(b[-1,0],900+389*.25)

    def test_no_prior_history_has_no_invented_pre_market(self):
        empty=w.history_for_session(self.target,self.current,[])
        self.assertEqual(empty.shape,(0,5))
        block={"name":"EMA","parameters":{"period":350,"source":"close"}}
        self.assertIsNone(w.indicator_at(self.target,self.current,20,block,[]))

if __name__=="__main__":
    unittest.main()
