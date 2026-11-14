"""Integration tests against the pinned official CTF artifacts in data/."""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solve_challenges import solve_blue, solve_sleepy  # noqa: E402

BLUE_PATH = ROOT / "data" / "blue3" / "blue.png"
SLEEPY_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
REFERENCE_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"

BLUE_FLAG = "byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}"
SLEEPY_FLAG = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"

EXPECTED_HASHES = {
    BLUE_PATH: "009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e",
    SLEEPY_PATH: "bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2",
    REFERENCE_PATH: "d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad",
}


class OfficialArtifactIntegrationTests(unittest.TestCase):
    def test_official_artifact_sha256(self):
        for path, expected_hash in EXPECTED_HASHES.items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(path.is_file(), f"missing official artifact: {path}")
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash)

    def test_blue3_official_artifact_exact_flag(self):
        candidate, attempts = solve_blue(BLUE_PATH)
        self.assertEqual(candidate, BLUE_FLAG)
        self.assertTrue(any(length == len(BLUE_FLAG) for length, _ in attempts))

    def test_sleepy_alarm_official_artifact_exact_flag_with_reference(self):
        result = solve_sleepy(
            SLEEPY_PATH,
            reference=REFERENCE_PATH,
            expected_text=SLEEPY_FLAG,
        )
        self.assertTrue(result["format_valid"], result["errors"])
        self.assertTrue(result["ground_truth_match"])
        self.assertTrue(result["success"])
        self.assertEqual(result["expected_symbol_count"], 350)
        self.assertEqual(result["measured_symbol_count"], 350)
        self.assertEqual(result["symbol_counts"]["separator"], 38)
        self.assertEqual(result["byte_count"], 39)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
