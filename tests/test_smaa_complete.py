import os, tempfile, unittest
from smaa import SMAAEngine
from smaa.complete import (AgencyObservation, ModelSnapshot, RevisionProposal,
                           RevisionGate, SMAAComplete, SQLiteSnapshotStore, estimate_agency)

class SMAACompleteTests(unittest.TestCase):
    def test_snapshot_integrity(self):
        e = SMAAEngine("network-a"); e.register_cell("c")
        s = ModelSnapshot.create("snap", e.model.snapshot(), e.ledger.events[-1].event_hash)
        self.assertTrue(s.verify())
    def test_snapshot_tamper_detected(self):
        s = ModelSnapshot.create("snap", SMAAEngine("n").model.snapshot(), "0"*64)
        bad = ModelSnapshot(s.snapshot_id, s.schema_version, s.network_id, s.model_version,
                            s.ledger_head, s.state_json+" ", s.digest)
        self.assertFalse(bad.verify())
    def test_snapshot_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            store = SQLiteSnapshotStore(os.path.join(d, "s.db"))
            s = ModelSnapshot.create("snap", SMAAEngine("n").model.snapshot(), "0"*64)
            store.save(s); self.assertEqual(store.load("snap"), s)
            with self.assertRaises(KeyError): store.load("missing")
    def test_snapshot_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            store = SQLiteSnapshotStore(os.path.join(d, "s.db"))
            s = ModelSnapshot.create("snap", SMAAEngine("n").model.snapshot(), "0"*64)
            store.save(s)
            with self.assertRaises(Exception): store.save(s)
    def test_agency_uses_control_difference(self):
        r = estimate_agency(AgencyObservation("a", .5, .6, .1, "do"))
        self.assertAlmostEqual(r["estimated_causal_effect"], .5)
        self.assertTrue(r["effect_detected"]); self.assertTrue(r["prediction_consistent"])
    def test_agency_null_effect(self):
        r = estimate_agency(AgencyObservation("a", 0, .2, .18, "sham"))
        self.assertFalse(r["effect_detected"])
    def test_revision_requires_distinct_evidence(self):
        r = RevisionGate().evaluate(RevisionProposal("p", "reason", .5, .8, ("x", "x")))
        self.assertFalse(r.accepted); self.assertIn("insufficient_independent_evidence", r.reasons)
    def test_revision_rejects_counterexample(self):
        r = RevisionGate().evaluate(RevisionProposal("p", "reason", .5, .8, ("x", "y"), ("ce",)))
        self.assertFalse(r.accepted); self.assertIn("unresolved_counterexamples", r.reasons)
    def test_revision_acceptance_audited(self):
        e = SMAAEngine("n"); s = SMAAComplete(e)
        p = RevisionProposal("p", "held-out improvement", .5, .7, ("blind-a", "blind-b"))
        self.assertTrue(s.apply_accepted_revision(p, ["assumption"]))
        self.assertEqual(e.model.version, 2); self.assertTrue(e.ledger.verify())
    def test_revision_rejection_no_mutation(self):
        e = SMAAEngine("n"); s = SMAAComplete(e)
        p = RevisionProposal("p", "weak evidence", .5, .51, ("e1",))
        self.assertFalse(s.apply_accepted_revision(p, [])); self.assertEqual(e.model.version, 1)

if __name__ == "__main__": unittest.main()
