import unittest

from smaa import Capability, KnowledgeClaim, SMAAEngine
from smaa.complete import ModelSnapshot, SMAAComplete
from smaa.experiments import estimate_randomized_effect, randomize_units
from smaa.recovery import restore_engine_from_snapshot


class RecoveryTests(unittest.TestCase):
    def test_restore_verified_snapshot_roundtrip(self):
        engine = SMAAEngine("net")
        engine.register_cell("cell-a", ("geometry",))
        engine.add_capability(Capability("geometry", .9, 30, ("eval-1",)))
        engine.add_claim(KnowledgeClaim("claim-1", "x", "cell-a", ("ev-1",), True), "cell-a")
        head = engine.ledger.events[-1].event_hash
        snapshot = SMAAComplete(engine).create_snapshot("snapshot-1")
        restored = restore_engine_from_snapshot(snapshot, head)
        self.assertEqual(restored.model.snapshot(), engine.model.snapshot())
        self.assertTrue(restored.ledger.verify())
        self.assertEqual(restored.ledger.events[-1].event_type, "model_restored_from_snapshot")

    def test_restore_rejects_wrong_trusted_head(self):
        engine = SMAAEngine("net")
        snapshot = SMAAComplete(engine).create_snapshot("snapshot-1")
        with self.assertRaises(ValueError):
            restore_engine_from_snapshot(snapshot, "f" * 64)

    def test_restore_rejects_tampered_snapshot(self):
        snapshot = SMAAComplete(SMAAEngine("net")).create_snapshot("snapshot-1")
        bad = ModelSnapshot(snapshot.snapshot_id, snapshot.schema_version, snapshot.network_id,
                            snapshot.model_version, snapshot.ledger_head,
                            snapshot.state_json + " ", snapshot.digest)
        with self.assertRaises(ValueError):
            restore_engine_from_snapshot(bad, snapshot.ledger_head)

    def test_restore_rejects_unknown_claim_owner(self):
        engine = SMAAEngine("net")
        snapshot = SMAAComplete(engine).create_snapshot("snapshot-1")
        import json
        state = json.loads(snapshot.state_json)
        state["claims"]["bad"] = {"claim_id":"bad","proposition":"p","owner_cell_id":"missing",
                                  "evidence_ids":[],"independently_verified":False}
        corrupted = ModelSnapshot.create("forged", state, snapshot.ledger_head)
        with self.assertRaises(ValueError):
            restore_engine_from_snapshot(corrupted, snapshot.ledger_head)


class RandomizedExperimentTests(unittest.TestCase):
    def test_assignment_is_reproducible_and_balanced(self):
        ids = [f"u{i}" for i in range(20)]
        a = randomize_units(ids, 17)
        b = randomize_units(ids, 17)
        self.assertEqual(a, b)
        self.assertEqual(sum(a.assignments.values()), 10)

    def test_randomization_rejects_duplicate_units(self):
        with self.assertRaises(ValueError):
            randomize_units(["a", "a", "b", "c"], 1)

    def test_difference_in_means_recovers_simple_effect(self):
        assignments = {"a": True, "b": True, "c": True, "d": True,
                       "e": False, "f": False, "g": False, "h": False}
        outcomes = {k: (10.0 if treated else 7.0) for k, treated in assignments.items()}
        estimate = estimate_randomized_effect(outcomes, assignments)
        self.assertAlmostEqual(estimate.difference_in_means, 3.0)
        self.assertAlmostEqual(estimate.standard_error, 0.0)
        self.assertEqual(estimate.ci95_low, 3.0)
        self.assertEqual(estimate.ci95_high, 3.0)

    def test_estimator_rejects_mismatched_ids(self):
        with self.assertRaises(ValueError):
            estimate_randomized_effect({"a": 1.0}, {"b": True})

    def test_estimator_requires_two_units_per_arm(self):
        with self.assertRaises(ValueError):
            estimate_randomized_effect({"a":1.0,"b":2.0,"c":3.0},
                                       {"a":True,"b":False,"c":False})


if __name__ == "__main__":
    unittest.main()
