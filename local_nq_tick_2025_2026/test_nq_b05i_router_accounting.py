import unittest
from nq_b05i_router_accounting import decompose_month

class TestB05I(unittest.TestCase):
    def test_router_conservation_with_profitable_displaced_T05(self):
        a={'month':'2025-10','trades':5,'net_usd':100.}
        h={'month':'2025-10','trades':3,'net_usd':-40.}
        r={'month':'2025-10','trades':7,'net_usd':50.}
        owner={'month':'2025-10','n':3,'net':-20.}
        z=decompose_month(a,h,r,owner)
        self.assertEqual(z['t05_retained_trades'],4)
        self.assertEqual(z['t05_displaced_trades'],1)
        self.assertEqual(z['t05_retained_usd'],70.)
        self.assertEqual(z['t05_displaced_usd'],30.)
        self.assertEqual(z['router_increment_usd'],-50.)
    def test_negative_displacement_net_cannot_create_filter(self):
        a={'month':'2025-11','trades':2,'net_usd':-100.}
        h={'month':'2025-11','trades':1,'net_usd':-20.}
        r={'month':'2025-11','trades':2,'net_usd':25.}
        owner={'month':'2025-11','n':1,'net':-25.}
        z=decompose_month(a,h,r,owner)
        self.assertEqual(z['t05_displaced_usd'],-150.)
        self.assertEqual(z['router_increment_usd'],125.)
        # This is post-hoc diagnostic; no strategy rules are emitted.
    def test_invalid_negative_counts_fail_closed(self):
        a={'month':'2025-10','trades':1,'net_usd':100.}
        h={'month':'2025-10','trades':1,'net_usd':50.}
        r={'month':'2025-10','trades':3,'net_usd':50.}
        owner={'month':'2025-10','n':1,'net':-20.}
        with self.assertRaises(ValueError):
            decompose_month(a,h,r,owner)
if __name__=='__main__':unittest.main()
