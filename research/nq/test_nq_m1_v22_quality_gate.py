"""S0.8 preregistration tests; NO historical market data; gate must remain BLOCKED."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from research.nq import nq_m1_v22_quality_gate as g


class TestV22ReleaseGate(unittest.TestCase):
    def setUp(self):
        self.matrix=json.loads(g.MATRIX.read_text(encoding="utf8"))

    def _with_matrix(self, obj, f):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"quality.json"
            path.write_text(json.dumps(obj),encoding="utf8")
            return f(path)

    def test_default_release_gate_blocks_economic_backtest(self):
        state=g.audit()
        self.assertEqual(state["decision"],"EXECUTION_BLOCKED")
        self.assertFalse(state["ready_for_economic_execution"])
        self.assertEqual(state["checks_total"],13)
        self.assertEqual(len(state["blocked"]),13)
        self.assertTrue(state["no_market_data_read"])
        with self.assertRaises(PermissionError):
            g.require_ready()

    def test_no_one_can_remove_mandatory_check_from_matrix(self):
        bad=copy.deepcopy(self.matrix)
        bad["criteria"].pop()
        with self.assertRaises(ValueError):
            self._with_matrix(bad,g.audit)

    def test_no_non_nq_or_mnq_switch_is_allowed(self):
        for key,value in (("asset","MNQ"),("contracts",10),("no_mnq",False)):
            bad=copy.deepcopy(self.matrix)
            bad[key]=value
            with self.assertRaises(ValueError):
                self._with_matrix(bad,g.audit)

    def test_future_year_holdouts_cannot_be_unsealed(self):
        bad=copy.deepcopy(self.matrix)
        bad["holdouts"]="2025_2026_EXPOSED"
        with self.assertRaises(ValueError):
            self._with_matrix(bad,g.audit)

    def test_self_declared_pass_without_proof_remains_blocked(self):
        bad=copy.deepcopy(self.matrix)
        for check in bad["criteria"]:
            check["state"]="PASSED_VERIFIED"
        result=self._with_matrix(bad,g.audit)
        self.assertFalse(result["ready_for_economic_execution"])
        self.assertTrue(all(x["status"]=="MISSING_IMMUTABLE_PROOF"
                            for x in result["blocked"]))

    def test_invalid_proof_hash_does_not_grant_permission(self):
        bad=copy.deepcopy(self.matrix)
        check=bad["criteria"][0]
        check["state"]="PASSED_VERIFIED"
        check["verified_evidence_ref"]={"sha256":"not-hash",
            "run_url":"https://github.com/rgentil2/MES-Trading-Research/actions/runs/1"}
        result=self._with_matrix(bad,g.audit)
        self.assertEqual(result["blocked"][0]["status"],"INVALID_EVIDENCE_REFERENCE")

    def test_no_false_economic_outcomes_in_baseline(self):
        bad=copy.deepcopy(self.matrix)
        bad["current_evidence"]["economically_evaluated"]=True
        with self.assertRaises(ValueError):
            self._with_matrix(bad,g.audit)

    def test_old_frozen_manifest_stats_unchanged(self):
        result=g.audit()
        self.assertEqual(result["registered_blocks"],132)
        self.assertEqual(result["computed_blocks"],38)
        self.assertEqual(result["external_parity_baseline"],15)


if __name__=="__main__":
    unittest.main()
