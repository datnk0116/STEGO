from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_steganalysis_dataset_manifest import validate_manifest


class SteganalysisDatasetManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.samples = [
            self.add_sample("h1_host.wav", b"host-1", "benign", "h1", None, "train"),
            self.add_sample("h1_s1_stego.wav", b"stego-1", "stego", "h1", "s1", "train"),
            self.add_sample("h2_host.wav", b"host-2", "benign", "h2", None, "validation"),
            self.add_sample("h2_s2_stego.wav", b"stego-2", "stego", "h2", "s2", "validation"),
            self.add_sample("h3_host.wav", b"host-3", "benign", "h3", None, "test"),
            self.add_sample("h3_s3_stego.wav", b"stego-3", "stego", "h3", "s3", "test"),
        ]
        self.write_manifest(self.samples)

    def tearDown(self):
        self.tmp.cleanup()

    def add_sample(self, name, payload, label, host_id, secret_id, split):
        path = self.root / "corpus" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return {
            "relative_path": path.relative_to(self.root).as_posix(),
            "source_url": "https://example.invalid/dataset",
            "license": "CC BY 4.0",
            "modality": "audio",
            "label": label,
            "carrier": "speech",
            "transformation": "none" if label == "benign" else "scrambling-and-hiding",
            "host_source_id": host_id,
            "secret_source_id": secret_id,
            "bh_parameter": None if label == "benign" else 2,
            "split": split,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def write_manifest(self, samples):
        path = self.root / "manifest.json"
        path.write_text(json.dumps({
            "schema_version": 1,
            "dataset_source": {
                "url": "https://example.invalid/dataset",
                "license": "CC BY 4.0",
            },
            "samples": samples,
        }, indent=2), encoding="utf-8")
        return path

    def test_valid_manifest_passes_integrity_and_source_disjointness(self):
        result = validate_manifest(self.root, "manifest.json")
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["verified_files"], 6)
        self.assertTrue(result["checks"]["source_split_disjointness"])

    def test_wrong_hash_fails_integrity(self):
        samples = [dict(item) for item in self.samples]
        samples[0]["sha256"] = "0" * 64
        self.write_manifest(samples)
        result = validate_manifest(self.root, "manifest.json")
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["file_integrity"])

    def test_missing_file_fails_integrity(self):
        samples = [dict(item) for item in self.samples]
        samples[0]["relative_path"] = "corpus/missing.wav"
        self.write_manifest(samples)
        result = validate_manifest(self.root, "manifest.json")
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing sample file" in item for item in result["errors"]))

    def test_host_source_in_multiple_splits_fails(self):
        samples = [dict(item) for item in self.samples]
        samples.append(self.add_sample("h1_validation.wav", b"host-1-variant",
                                       "benign", "h1", None, "validation"))
        self.write_manifest(samples)
        result = validate_manifest(self.root, "manifest.json")
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["source_split_disjointness"])
        self.assertTrue(any("host_source_id=h1" in item for item in result["errors"]))

    def test_secret_source_in_multiple_splits_fails(self):
        samples = [dict(item) for item in self.samples]
        samples.append(self.add_sample("h4_s1_validation.wav", b"stego-4",
                                       "stego", "h4", "s1", "validation"))
        self.write_manifest(samples)
        result = validate_manifest(self.root, "manifest.json")
        self.assertFalse(result["passed"])
        self.assertTrue(any("secret_source_id=s1" in item for item in result["errors"]))

    def test_duplicate_hash_across_splits_fails(self):
        samples = [dict(item) for item in self.samples]
        duplicate = dict(samples[0])
        duplicate["relative_path"] = "corpus/duplicate.wav"
        duplicate["split"] = "validation"
        duplicate_path = self.root / duplicate["relative_path"]
        duplicate_path.write_bytes((self.root / samples[0]["relative_path"]).read_bytes())
        samples.append(duplicate)
        self.write_manifest(samples)
        result = validate_manifest(self.root, "manifest.json")
        self.assertFalse(result["passed"])
        self.assertTrue(any("SHA-256" in item and "appears in splits" in item
                            for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
