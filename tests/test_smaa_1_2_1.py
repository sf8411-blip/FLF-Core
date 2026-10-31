import json
import tempfile
import unittest
from pathlib import Path

from smaa.blind_harness import (
    TrialResult, TrialSpec, append_result, balanced_assignments,
    make_trial_specs, write_manifest,
)


class HarnessTests(unittest.TestCase):
    def test_balanced_deterministic_assignment(self):
        a = balanced_assignments(101, 12)
        self.assertEqual(a, balanced_assignments(101, 12))
        counts = {}
        for _, architecture in a:
            counts[architecture] = counts.get(architecture, 0) + 1
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_specs_reproducible_and_valid(self):
        a = make_trial_specs(20, 99, ["env-a", "env-b"])
        self.assertEqual(a, make_trial_specs(20, 99, ["env-a", "env-b"]))
        self.assertEqual(len({x.trial_id for x in a}), 20)
        self.assertTrue(all(x.environment_id in {"env-a", "env-b"} for x in a))

    def test_manifest_hash_and_contents(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "manifest.json"
            specs = make_trial_specs(8, 3, ["hidden-1"])
            digest = write_manifest(path, specs, {"protocol": "pilot"})
            data = json.loads(path.read_text())
            self.assertEqual(data["sha256"], digest)
            self.assertEqual(len(data["manifest"]["trials"]), 8)

    def test_result_jsonl_append(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "results.jsonl"
            result = TrialResult("t", "log_only", 1, "ok", 0.2, 0.3, 0.8, 0.1, 1024)
            append_result(path, result)
            self.assertEqual(json.loads(path.read_text())["trial_id"], "t")

    def test_reject_invalid_spec(self):
        with self.assertRaises(ValueError):
            TrialSpec("x", 1, "unknown", "env", 2)


if __name__ == "__main__":
    unittest.main()
