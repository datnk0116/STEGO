from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_submission_manifest import ARTIFACT_PATHS, MANIFEST, validate_submission_manifest


class SubmissionManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Submission tests")
        self.git("config", "user.email", "submission@example.invalid")
        (self.root / "report").mkdir()
        (self.root / "report/REPORT.md").write_text("input report\n", encoding="utf-8")
        self.commit("build inputs")
        self.build_input_commit = self.git("rev-parse", "HEAD")
        self.make_package()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                              text=True, check=True).stdout.strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def make_package(self):
        records = {}
        for key, rel in ARTIFACT_PATHS.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if key == "zip":
                with zipfile.ZipFile(path, "w") as archive:
                    for name in (
                        "README.md", "requirements.txt", "report/REPORT.md",
                        "data/artifact.bin", "src/solver.py", "tests/test_solver.py",
                        "scripts/run.py", "references/REFERENCES.md",
                        "docs/GUIDE.md", "results/run.json",
                    ):
                        archive.writestr(name, "fixture\n")
            elif key == "docx":
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("[Content_Types].xml", "<Types/>")
                    archive.writestr("word/document.xml", "<document/>")
            else:
                path.write_bytes((key + " fixture\n").encode("ascii"))
            records[key] = {
                "path": rel, "bytes": path.stat().st_size, "sha256": self.digest(path),
                "page_count": 19 if key == "pdf" else None,
            }
        manifest = {
            "schema_version": 1, "status": "VERIFIED",
            "build_input_commit": self.build_input_commit,
            "built_at_utc": "2026-11-14T00:00:00+00:00",
            "pdf_visual_inspection_confirmed_at_utc": "2026-11-14T01:00:00+00:00",
            "build_command": ["python", "scripts/build_submission.py", "--max-main-pages", "20"],
            "tool_versions": {
                "python": "Python fixture", "pandoc": "pandoc fixture",
                "libreoffice": "LibreOffice fixture", "pdfinfo": "pdfinfo fixture",
                "pdftotext": "pdftotext fixture", "unzip": "unzip fixture",
                "platform": "platform fixture", "python-docx": "python-docx fixture",
            },
            "max_main_pages": 20, "artifacts": records,
            "checks": {
                "docx_integrity": "PASS", "pdf_page_check": "PASS",
                "pdf_visual_inspection": "PASS",
                "zip_integrity": "PASS", "zip_contents": "PASS",
            },
        }
        path = self.root / MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        self.commit("store package artifacts")

    def validate(self):
        with patch("check_submission_manifest.pdf_check",
                   return_value=(True, 19, 17, "fixture PDF check PASS")):
            return validate_submission_manifest(self.root)

    def test_valid_committed_manifest_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["derived"]["freshness"], "FRESH")

    def test_missing_artifact_fails(self):
        (self.root / ARTIFACT_PATHS["docx"]).unlink()
        result = self.validate()
        self.assertFalse(result["passed"])
        self.assertTrue(any("artifact missing" in item for item in result["errors"]))

    def test_wrong_sha256_fails(self):
        path = self.root / MANIFEST
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["artifacts"]["pdf"]["sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["passed"])
        self.assertTrue(any("SHA-256 mismatch" in item for item in result["errors"]))

    def test_build_revision_must_exist_and_be_ancestor(self):
        path = self.root / MANIFEST
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["build_input_commit"] = "0" * 40
        path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["passed"])
        self.assertTrue(any("does not exist" in item for item in result["errors"]))

    def test_input_change_after_build_marks_package_stale(self):
        (self.root / "report/REPORT.md").write_text("changed after build\n", encoding="utf-8")
        self.commit("change report after package build")
        result = self.validate()
        self.assertFalse(result["passed"])
        self.assertEqual(result["derived"]["freshness"], "STALE")
        self.assertTrue(any("build inputs changed" in item for item in result["errors"]))

    def test_visual_inspection_pass_requires_confirmation_timestamp(self):
        path = self.root / MANIFEST
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.pop("pdf_visual_inspection_confirmed_at_utc")
        path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["passed"])
        self.assertTrue(any("confirmation timestamp" in item for item in result["errors"]))

    def test_uncommitted_input_change_is_rejected(self):
        (self.root / "report/REPORT.md").write_text("uncommitted report edit\\n", encoding="utf-8")
        result = self.validate()
        self.assertFalse(result["passed"])
        self.assertEqual(result["derived"]["freshness"], "STALE")
        self.assertTrue(any("uncommitted package input changes" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
