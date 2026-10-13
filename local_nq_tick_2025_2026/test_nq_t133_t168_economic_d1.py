"""No licensed market data. Synthetic regression of economic proxy and D1 gate."""
import unittest,copy
from nq_t133_t168_d1_engine import model_one,day_sim,stop_and_side
from nq_t133_t168_economic_d1_batch import gate,bh_family,aggregate,boot_mean,IDS
from nq_t133_t168_combined_D0_batch import old_registry,load_new
from test_nq_t61_t96_d0_cohort import DAY,sample

class EconomicProxy36(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=old_registry();cls.new=load_new()
    def test_all36_frozen_gate_27_diverse(self):
        a=gate()
        self.assertEqual((a['family_size'],a['D0_diverse_count'],a['D0_testable_count']),(36,27,29))
        self.assertFalse(a['D1_executed'])
        self.assertTrue(a['seed_20_masks_identical'])
    def test_BH36_must_include_all_originals(self):
        with self.assertRaises(ValueError):bh_family([.01]*27)
        self.assertAlmostEqual(bh_family([.001]+[1.]*35)[0],.036)
    def test_complete_scope_at_day(self):
        # sample() must contain enough futures; no broker-fill assertions.
        d=day_sim(sample(),DAY,self.old,self.new)
        self.assertEqual(len(d),36)
        self.assertEqual(set(d),set(IDS))
        self.assertTrue(all(x['group'] in ('CASE','CONTROL','OTHER','NOT_EVALUABLE')
                            for x in d.values()))
    def test_model_no_entry(self):
        self.assertEqual(model_one([],1,95,1.5,15,0,True)['status'],'NO_NEXT_GROUP')
    def test_adverse_stop_first_on_simultaneous_target_stop(self):
        G=[(10,100,100),(20,80,150),(30,80,180)]
        z=model_one(G,1,93,1.5,15,0,True)
        self.assertIn(z['exit_reason'],('STOP_FIRST','STOP'))
        self.assertLess(z['net_usd'],0)
        self.assertFalse(z['broker_fills_verified'] if 'broker_fills_verified' in z else False)
    def test_entry_group_stop_first_no_lucky_target(self):
        z=model_one([(10,95,120),(20,100,180)],1,96,1.5,15,0,True)
        # entry worst 120+2; stop lies far below, so proxy risk 27 ticks
        self.assertEqual(z['exit_reason'],'AMBIGUOUS_ENTRY_GROUP_STOP_FIRST')
        self.assertLess(z['net_usd'],0)
    def test_gap_adverse_execution_slippage(self):
        z=model_one([(10,100,100),(20,95,99)],1,93,1.5,15,0,True)
        self.assertEqual(z['status'],'MODELLED_EXECUTION_UNVERIFIED')
        self.assertLess(z['net_usd'],z['gross_usd'])
        self.assertLess(z['stress_1_5x_usd'],z['net_usd'])
        self.assertEqual(round(z['net_usd']-z['stress_plus_10_rt_usd'],5),10)
    def test_time_exit_requires_full_future_coverage(self):
        G=[(10,100,100),(15,100,105)]
        self.assertEqual(model_one(G,1,93,1.5,15,0,False)['status'],
                         'HORIZON_NOT_FULLY_OBSERVED')
        self.assertEqual(model_one(G,1,93,1.5,15,0,True)['exit_reason'],
                         'TIME_EXIT_ADVERSE_GROUP')
    def test_135_days_for_inference(self):
        with self.assertRaises(ValueError):boot_mean([1.]*10,'T153',5)
    def test_no_partial_months(self):
        with self.assertRaises(ValueError):
            aggregate({},self.old,self.new,gate())

if __name__=='__main__':unittest.main()
