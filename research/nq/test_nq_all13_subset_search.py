#!/usr/bin/env python3
"""All13 topology/selection fail-closed tests; no trading-market inputs."""
import unittest
from itertools import combinations
from nq_all13_subset_search import (
    IDS,H,T,load_frozen,topology,classify_subset,closed_metrics,
    choose_candidates,pareto
)

class FullThirteen(unittest.TestCase):
    def test_all_13_and_original_order(self):
        self.assertEqual(len(IDS),13)
        self.assertEqual(len(H),5)
        self.assertEqual(len(T),8)
        self.assertEqual(len(set(IDS)),13)
        self.assertEqual(sum(1 for i in range(1,14) for x in combinations(IDS,i)),8191)
        self.assertEqual(load_frozen()["enumeration"]["H_T_mixed_raw"],7905)
    def test_exact_complete_topology_counts(self):
        z=topology()
        c=z["coverage"]
        self.assertEqual(c["CROSS_SAMPLE_NO_JOINT_EQUITY"],7905)
        self.assertEqual(c["H_PARENT_ROUTER_DUPLICATION_OR_EQUIVALENT"],26)
        self.assertEqual(c["H_EXCLUSIVE_PARENT_OR_ROUTER_ALTERNATIVE"],5)
        self.assertEqual(c["T_SAME_CALENDAR_NEEDS_EIGHT_PARENT_EXPOSURE_LEDGER"],255)
        self.assertIsNone(z["T_best_subset"])
        self.assertFalse(z["holdouts_opened"])
    def test_overlap_and_parent_router_not_independent(self):
        self.assertEqual(classify_subset(("H09","H69")),
                         "H_PARENT_ROUTER_DUPLICATION_OR_EQUIVALENT")
        self.assertEqual(classify_subset(("H09","H56")),
                         "H_PARENT_ROUTER_DUPLICATION_OR_EQUIVALENT")
        self.assertEqual(classify_subset(("H09","T224")),
                         "CROSS_SAMPLE_NO_JOINT_EQUITY")
        self.assertEqual(classify_subset(("T05-377","T147","T210")),
                         "T_SAME_CALENDAR_NEEDS_EIGHT_PARENT_EXPOSURE_LEDGER")
    def test_closed_drawdown_not_float(self):
        z=closed_metrics([100,-80,20,-90,60],{"2025-10":40,"2025-11":-10})
        self.assertEqual(z["N"],5)
        self.assertEqual(z["net_usd"],10)
        self.assertEqual(z["DD_closed_usd"],150)
        self.assertEqual(z["positive_months"],1)
    def test_selective_five_t_only_fails(self):
        with self.assertRaisesRegex(AssertionError,"255"):
            choose_candidates([{"members":("T05-377",),"status":"ESTIMABLE"}])
    def test_nondominated_filter(self):
        x=[{"ID":"A","net_plus10":200,"DD_plus10_closed":80,
             "expectancy_R":.2,"net_DD_plus10":2.5},
           {"ID":"B","net_plus10":100,"DD_plus10_closed":100,
             "expectancy_R":.1,"net_DD_plus10":1},
           {"ID":"C","net_plus10":250,"DD_plus10_closed":125,
             "expectancy_R":.1,"net_DD_plus10":2}]
        self.assertEqual({z["ID"] for z in pareto(x)},{"A","C"})
    def test_pareto_portfolios_have_member_tuples_without_id(self):
        x=[{"members":("T05-377",),"net_plus10":500,"DD_plus10_closed":200,
            "expectancy_R":.4,"net_DD_plus10":2.5},
           {"members":("T224",),"net_plus10":300,"DD_plus10_closed":150,
            "expectancy_R":.2,"net_DD_plus10":2.0}]
        z=pareto(x)
        self.assertEqual(len(z),2)
        self.assertEqual(z[0]["members"],("T05-377",))

    def test_malformed_mask_fails(self):
        with self.assertRaisesRegex(ValueError,"INVALID"):
            classify_subset(("T05-377","UNKNOWN"))
        with self.assertRaisesRegex(ValueError,"INVALID"):
            classify_subset(())

if __name__=="__main__": unittest.main()
