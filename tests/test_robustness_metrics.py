"""Unit tests for partial-recovery metrics used by robustness experiments."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "experiments"))

from robustness_metrics import (  # noqa: E402
    blue_character_metrics,
    expected_ask_symbols,
    levenshtein_distance,
    sleepy_symbol_metrics,
)

SLEEPY_FLAG = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"


class RobustnessMetricsTests(unittest.TestCase):
    def test_blue_exact_candidate_has_full_similarity(self):
        metrics = blue_character_metrics("abcdef", "abcdef")
        self.assertEqual(metrics["edit_distance"], 0)
        self.assertEqual(metrics["position_accuracy"], 1.0)
        self.assertEqual(metrics["normalized_edit_similarity"], 1.0)

    def test_blue_partial_candidate_reports_edit_distance(self):
        metrics = blue_character_metrics("abcdef", "abXdef")
        self.assertEqual(metrics["edit_distance"], 1)
        self.assertAlmostEqual(metrics["normalized_edit_similarity"], 5 / 6)

    def test_missing_blue_candidate_is_not_reported_as_zero_edit_distance(self):
        metrics = blue_character_metrics("abcdef", None)
        self.assertFalse(metrics["candidate_available"])
        self.assertIsNone(metrics["edit_distance"])
        self.assertEqual(metrics["normalized_edit_similarity"], 0.0)

    def test_levenshtein_handles_insertions_and_deletions(self):
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("", "abc"), 3)

    def test_expected_ask_stream_has_documented_symbol_count(self):
        symbols = expected_ask_symbols(SLEEPY_FLAG)
        self.assertEqual(len(symbols), 350)
        self.assertEqual(symbols.count(" "), 38)

    def test_sleepy_perfect_symbol_stream_has_zero_error_rates(self):
        expected = expected_ask_symbols(SLEEPY_FLAG)
        metrics = sleepy_symbol_metrics(SLEEPY_FLAG, expected)
        self.assertEqual(metrics["symbol_errors"], 0)
        self.assertEqual(metrics["bit_errors"], 0)
        self.assertEqual(metrics["bit_error_rate"], 0.0)
        self.assertEqual(metrics["separator_precision"], 1.0)
        self.assertEqual(metrics["separator_recall"], 1.0)

    def test_sleepy_metrics_count_bit_and_separator_errors_separately(self):
        expected = expected_ask_symbols(SLEEPY_FLAG)
        observed = list(expected)
        first_bit = next(i for i, value in enumerate(expected) if value in "01")
        first_separator = expected.index(" ")
        observed[first_bit] = "1" if expected[first_bit] == "0" else "0"
        observed[first_separator] = "0"
        metrics = sleepy_symbol_metrics(SLEEPY_FLAG, observed)
        self.assertEqual(metrics["bit_errors"], 1)
        self.assertEqual(metrics["false_negative_separators"], 1)
        self.assertEqual(metrics["false_positive_separators"], 0)
        self.assertEqual(metrics["symbol_errors"], 2)

    def test_sleepy_metrics_reject_wrong_symbol_count(self):
        with self.assertRaises(ValueError):
            sleepy_symbol_metrics(SLEEPY_FLAG, "0101")


if __name__ == "__main__":
    unittest.main()
