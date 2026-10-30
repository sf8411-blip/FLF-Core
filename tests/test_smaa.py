import unittest
from smaa import (
    Capability, EventLedger, IsolatedCellProcess, KnowledgeClaim, Prediction,
    SMAAEngine, brier_score, expected_calibration_error,
)

class SMAATests(unittest.TestCase):
    def test_membership_and_identity_continuity(self):
        e = SMAAEngine("net-1")
        e.register_cell("a")
        e.register_cell("b")
        e.deactivate_cell("b")
        self.assertEqual(e.identity_report()["active_cells"], ["a"])
        self.assertEqual(e.identity_report()["inactive_cells"], ["b"])
        self.assertEqual(e.identity_report()["network_id"], "net-1")
    def test_private_fields_rejected(self):
        e = SMAAEngine("n"); e.register_cell("c")
        with self.assertRaises(ValueError):
            e.receive_public_summary("c", {"raw_observations": ["secret"]})
    def test_unknown_summary_fields_rejected(self):
        e = SMAAEngine("n"); e.register_cell("c")
        with self.assertRaises(ValueError):
            e.receive_public_summary("c", {"arbitrary": "payload"})
    def test_public_summary_allowlist(self):
        e = SMAAEngine("n"); e.register_cell("c")
        e.receive_public_summary("c", {"resource_cpu": 0.4, "reported_unknowns": ["new-domain"]})
        self.assertEqual(e.model.resources["c.resource_cpu"], 0.4)
        self.assertIn("new-domain", e.model.unknowns)
    def test_hash_chain_detects_payload_tampering(self):
        ledger = EventLedger(); ledger.append("test", "actor", 0, {"x": 1})
        self.assertTrue(ledger.verify())
        ledger.events[0].payload["x"] = 2
        self.assertFalse(ledger.verify())
    def test_action_policy_uses_self_model(self):
        e = SMAAEngine("n")
        self.assertEqual(e.choose_action("geometry"), "abstain")
        e.add_capability(Capability("geometry", 0.9, 20, ("blind-eval-1",)))
        self.assertEqual(e.choose_action("geometry"), "attempt")
        e.model.capabilities.pop("geometry")
        self.assertEqual(e.choose_action("geometry"), "abstain")
    def test_prediction_calibration_metrics(self):
        self.assertAlmostEqual(brier_score([0.8, 0.2], [1, 0]), 0.04)
        self.assertGreaterEqual(expected_calibration_error([0.8, 0.2], [1, 0]), 0.0)
    def test_prediction_resolution_and_replayable_event(self):
        e = SMAAEngine("n"); e.record_prediction(Prediction("p", "success", 0.8))
        self.assertAlmostEqual(e.resolve_prediction("p", 1), 0.04)
        self.assertTrue(e.ledger.verify())
    def test_social_knowledge_provenance(self):
        e = SMAAEngine("n"); e.register_cell("a"); e.register_cell("b")
        e.add_claim(KnowledgeClaim("k", "candidate relation", "b"), "b")
        self.assertEqual(e.social_knowledge_view("a")["other_unverified"], ["k"])
    def test_revision_requires_reason_and_versions_model(self):
        e = SMAAEngine("n")
        with self.assertRaises(ValueError): e.revise_self_model("", [])
        e.revise_self_model("observed prediction failure", ["membership can change"])
        self.assertEqual(e.model.version, 2)
    def test_isolated_cell_exports_only_allowlisted_summary(self):
        with IsolatedCellProcess("c-private", ("geometry",)) as cell:
            cell.observe({"raw_sensor": "secret", "label": "hidden"})
            cell.report_unknown("unknown-shape")
            summary = cell.public_summary()
            self.assertEqual(summary["cell_id"], "c-private")
            self.assertEqual(summary["capability_names"], ["geometry"])
            self.assertEqual(summary["reported_unknowns"], ["unknown-shape"])
            self.assertNotIn("raw_sensor", summary)
            self.assertNotIn("label", summary)
    def test_capability_validation(self):
        with self.assertRaises(ValueError): Capability("bad", 1.2, 3)
    def test_prediction_validation(self):
        with self.assertRaises(ValueError): Prediction("p", "x", 1.2)
    def test_claim_requires_registered_owner(self):
        with self.assertRaises(ValueError):
            SMAAEngine("n").add_claim(KnowledgeClaim("k", "x", "missing"), "missing")

if __name__ == "__main__":
    unittest.main()
