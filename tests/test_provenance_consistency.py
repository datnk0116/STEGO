from __future__ import annotations
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_provenance_consistency import (
    DOCS, GATE_JSON, GATE_LOG, HIST_END, HIST_START, PROVENANCE,
    STATUS_BODY, START, END, validate_repository,
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class ProvenanceConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "STEGO tests")
        self.git("config", "user.email", "stego@example.invalid")
        self.make_fixture()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()

    def write(self, rel, value):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes): path.write_bytes(value)
        else: path.write_text(value, encoding="utf-8")
        return path

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def readj(self, rel):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def writej(self, rel, value):
        self.write(rel, json.dumps(value, indent=2) + "\n")

    def make_fixture(self):
        block = f"{START}\n{STATUS_BODY}\n{END}\n"
        for path in DOCS: self.write(path, f"# Fixture\n\n{block}\nBody.\n")
        artifact = self.write("data/challenge.bin", b"challenge fixture bytes\n")
        manifest = [{"path": "data/challenge.bin", "bytes": artifact.stat().st_size, "sha256": digest(artifact), "source": "https://example.invalid/source"}]
        self.write("results/artifact_manifest.json", json.dumps(manifest, indent=2) + "\n")
        self.write("src/solver.py", "VALUE = 1\n")
        self.tested = self.commit("tested source")
        gate = {
            "created_at_utc": "2026-11-14T10:00:00+00:00",
            "git": {"commit": self.tested, "branch": "main", "status_short": ""},
            "unit_tests": {"exit_code": 0, "expected_test_methods": 2, "tests_run": 2, "passed": True},
            "artifact_integrity": {"one": {"path": "data/challenge.bin", "bytes": artifact.stat().st_size, "sha256": digest(artifact), "exists": True, "actual_bytes": artifact.stat().st_size, "actual_sha256": digest(artifact), "passed": True}},
            "official_decoder_verification": {"blue3": {"exact_match": True}, "sleepy_alarm_reference_assisted": {"exact_match": True}},
            "overall_passed": True,
        }
        self.writej(GATE_JSON, gate)
        self.write(GATE_LOG, "test_one ... ok\ntest_two ... ok\n\nRan 2 tests in 0.01s\n\nOK\n")
        self.make_provenance(gate, manifest, self.tested)
        self.evidence = self.commit("evidence snapshot")

    def make_provenance(self, gate, manifest, tested, working=None):
        provenance = {
            "schema_version": 1, "snapshot_type": "generated_run", "verification_id": "fixture-run-1",
            "created_at_utc": gate["created_at_utc"], "repository": "datnk0116/STEGO", "branch": "main",
            "tested_commit": tested,
            "working_tree_before_run": working or {"captured": True, "clean": True, "status_short": "", "changed_paths": []},
            "evidence_files": {
                "quality_gate_json": {"path": GATE_JSON, "sha256": digest(self.root / GATE_JSON)},
                "quality_gate_log": {"path": GATE_LOG, "sha256": digest(self.root / GATE_LOG)},
                "artifact_manifest": {"path": "results/artifact_manifest.json", "sha256": digest(self.root / "results/artifact_manifest.json")},
            },
            "artifacts": manifest,
            "quality_gate": {
                "tests_passed": True, "tests_run": 2, "tests_expected": 2, "exit_code": 0,
                "artifact_integrity_passed": True, "blue3_exact_match": True,
                "sleepy_alarm_reference_assisted_exact_match": True, "overall_passed": True,
            },
            "limitations": ["Synthetic fixture only."],
            "submission_package": {"status": "not_verified", "built_from_commit": tested},
        }
        self.writej(PROVENANCE, provenance)

    def test_valid_committed_snapshot_passes(self):
        result = validate_repository(self.root)
        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.derived["evidence_commit"], self.evidence)

    def test_missing_required_field_fails(self):
        item = self.readj(PROVENANCE); item.pop("limitations"); self.writej(PROVENANCE, item)
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Required fields" in error for error in result.errors))

    def test_nonexistent_tested_commit_fails(self):
        item = self.readj(PROVENANCE); item["tested_commit"] = "0" * 40; self.writej(PROVENANCE, item)
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Tested commit exists" in error for error in result.errors))

    def test_non_ancestor_tested_commit_fails(self):
        self.git("checkout", "--orphan", "other")
        self.git("rm", "-rf", ".")
        self.write("other.txt", "other root\n")
        orphan = self.commit("unrelated root")
        self.git("checkout", "main")
        item = self.readj(PROVENANCE); item["tested_commit"] = orphan; self.writej(PROVENANCE, item)
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("ancestor of HEAD" in error for error in result.errors))

    def test_source_change_after_run_marks_gate_stale(self):
        self.write("src/changed.py", "VALUE = 2\n"); self.commit("source changed")
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Technical gate freshness" in check[0] for check in result.checks if not check[1]))

    def test_documentation_only_commit_does_not_stale_gate(self):
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nExtra prose.\n", encoding="utf-8")
        self.commit("docs update")
        result = validate_repository(self.root)
        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.derived["submission_package_freshness"], "STALE")
        self.assertEqual(result.derived["change_classification"]["technical_gate"], [])

    def test_retrospective_provenance_can_be_committed_after_historical_evidence(self):
        gate = self.readj(GATE_JSON)
        log = (self.root / GATE_LOG).read_text(encoding="utf-8")
        item = self.readj(PROVENANCE)
        item["snapshot_type"] = "retrospective_migration"
        item["verification_id"] = None
        item["working_tree_before_run"] = {"captured": False, "clean": None, "status_short": None, "changed_paths": []}
        self.git("reset", "--hard", self.tested)
        self.writej(GATE_JSON, gate); self.write(GATE_LOG, log)
        self.evidence = self.commit("historical evidence without migration file")
        self.writej(PROVENANCE, item)
        self.commit("add retrospective migration")
        result = validate_repository(self.root)
        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.derived["evidence_commit"], self.evidence)

    def test_submission_binary_change_marks_package_stale_not_gate_stale(self):
        self.write("results/submission/mock.pdf", b"changed submission bytes\n")
        self.commit("replace package binary")
        result = validate_repository(self.root)
        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.derived["submission_package_freshness"], "STALE")
        self.assertEqual(result.derived["change_classification"]["technical_gate"], [])
        self.assertIn("results/submission/mock.pdf", result.derived["change_classification"]["submission_package"])

    def test_artifact_hash_mismatch_fails(self):
        self.write("data/challenge.bin", b"tampered\n")
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Artifact integrity" in check[0] for check in result.checks if not check[1]))

    def test_gate_summary_mismatch_fails(self):
        item = self.readj(PROVENANCE); item["quality_gate"]["tests_run"] = 99; self.writej(PROVENANCE, item)
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Canonical summary" in check[0] for check in result.checks if not check[1]))

    def test_gate_log_mismatch_fails(self):
        self.write(GATE_LOG, "Ran 1 test\nFAILED\n")
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Evidence hash quality_gate_log" in check[0] or "Gate log" in check[0] for check in result.checks if not check[1]))

    def test_outdated_document_status_block_fails(self):
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8").replace(STATUS_BODY, "outdated"), encoding="utf-8")
        result = validate_repository(self.root)
        self.assertFalse(result.passed)
        self.assertTrue(any("Documentation README.md" in check[0] for check in result.checks if not check[1]))

    def test_legacy_commit_is_allowed_inside_historical_block(self):
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8") + f"\n{HIST_START}\nOld a040e3863145038b786ba6719629e636fdf2e565\n{HIST_END}\n", encoding="utf-8")
        self.commit("label old reference")
        result = validate_repository(self.root)
        self.assertTrue(result.passed, result.errors)

    def test_precommit_snapshot_passes_before_evidence_commit(self):
        head = self.git("rev-parse", "HEAD")
        gate = self.readj(GATE_JSON); gate["git"]["commit"] = head; self.writej(GATE_JSON, gate)
        self.write(GATE_LOG, "test_one ... ok\ntest_two ... ok\n\nRan 2 tests in 0.02s\n\nOK\n")
        manifest = json.loads((self.root / "results/artifact_manifest.json").read_text(encoding="utf-8"))
        self.make_provenance(gate, manifest, head, {"captured": True, "clean": True, "status_short": "", "changed_paths": []})
        result = validate_repository(self.root, pre_commit=True)
        self.assertTrue(result.passed, result.errors)

    def test_submission_package_can_be_required_explicitly(self):
        result = validate_repository(self.root, require_submission_package=True)
        self.assertFalse(result.passed)
        self.assertTrue(any("Submission package" in check[0] for check in result.checks if not check[1]))

if __name__ == "__main__":
    unittest.main()
