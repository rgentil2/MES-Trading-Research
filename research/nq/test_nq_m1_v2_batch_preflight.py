"""Two-track 132-block structural catalogue remains intact; no market data."""
import unittest
from research.nq import nq_m1_v2_batch_preflight as b
from research.nq import nq_m1_v2_orders as orders
from research.nq import nq_m1_v2_generator as g


class TestNQM1V2TwoTrack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = b.make_manifest(broad_count=70, compatible_target=20, seed=27)

    def test_full_132_not_restricted(self):
        x = self.a
        self.assertEqual(x["search_universe_blocks"], 132)
        self.assertEqual(x["available_scalar_implementations"], 38)
        self.assertEqual(x["blocks_certified_against_independent_reference"], 0)
        self.assertEqual(x["generation"]["broad_n"], 70)
        self.assertEqual(x["generation"]["compatible_n"], 20)
        self.assertEqual(len(x["broad"]), 70)
        self.assertEqual(len(x["compatible"]), 20)

    def test_broad_records_all_retained_even_if_unsupported(self):
        data = self.a["broad"]
        x = self.a["generation"]
        self.assertEqual(x["broad_pending_implementation_n"] +
                         x["broad_synthetically_compatible_n"], len(data))
        self.assertTrue(all(e["classification"] in {b.LABEL_COMPATIBLE, b.LABEL_PENDING}
                            for e in data))
        self.assertGreater(x["broad_pending_implementation_n"], 0)

    def test_compatible_track_is_only_technical_not_economic(self):
        for s in self.a["compatible"]:
            orders.validate_supported(s)
            self.assertNotIn("net_usd", s)
            self.assertNotIn("profit_factor", s)
            self.assertNotIn("score", s)
        self.assertEqual(self.a["status"], "S0_STRUCTURAL_ONLY_NO_MARKET_OUTCOMES")
        self.assertEqual(self.a["holdouts"], "H2025_H2026_T_SEALED")

    def test_deterministic_seeds_hashes(self):
        other = b.make_manifest(broad_count=70, compatible_target=20, seed=27)
        self.assertEqual(self.a, other)
        self.assertEqual(len({g.fingerprint(s) for s in self.a["compatible"]}), 20)
        changed = b.make_manifest(broad_count=70, compatible_target=20, seed=28)
        self.assertNotEqual(self.a["compatible_manifest_sha256"],
                            changed["compatible_manifest_sha256"])

    def test_invalid_batch_rejected(self):
        for broad, deep in ((0, 10), (10, 0), (100001, 10), (10, 100001)):
            with self.assertRaises(ValueError):
                b.make_manifest(broad, deep)


if __name__ == "__main__":
    unittest.main()
