#!/usr/bin/env python3
import unittest
from nq_all13_h5_comparable_options import H, FROZEN, evaluate

class HFive(unittest.TestCase):
    def test_five_distinct_alternative_choices(self):
        z=evaluate()
        self.assertEqual(tuple(z["H_five"]),H)
        self.assertEqual(len(set(H)),5)
        self.assertTrue(z["duplicate_H_router_parent_stacks_prohibited"])
        self.assertFalse(z["H_OOS_2025_2026_opened"])
        self.assertIsNone(z["H_T_total_net"])
        self.assertIsNone(z["H_T_combined_DD"])
    def test_reported_historical_net_DD_and_n(self):
        z=evaluate()
        for k,(n,net,dd) in FROZEN.items():
            self.assertEqual(z["H_five"][k]["N"],n)
            self.assertAlmostEqual(z["H_five"][k]["net_mnq_proxy_usd"],net)
            self.assertAlmostEqual(z["H_five"][k]["DD_closed_usd"],dd)
        self.assertEqual(z["best_historical_net_DD"],"H77")
    def test_h09_is_dominated_by_h77_same_mnq_units(self):
        z=evaluate()
        self.assertIn("H77",z["H_five"]["H09"]["dominated_by"])
        self.assertEqual(set(z["Pareto_H_options"]),set(("H56","H74","H77","H69")))
    def test_no_h_oos_or_confirmed(self):
        z=evaluate()
        self.assertIsNone(z["confirmed_H_strategy"])
        self.assertFalse(z["risk_floating_and_broker_fills_verified"])

if __name__=="__main__":unittest.main()
