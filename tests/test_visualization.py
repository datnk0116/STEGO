import unittest
from pathlib import Path
from unittest.mock import patch

from visualization.utils import (
    BLUE3_PATH,
    SLEEPY_REFERENCE_PATH,
    SLEEPY_TARGET_PATH,
    audio_metadata,
    image_summary,
    read_waveform,
    run_blue3,
    run_sleepy_alarm,
)

ROOT = Path(__file__).resolve().parents[1]


class TestVisualizationDecoderCalls(unittest.TestCase):
    @patch("visualization.utils.decode_blue3")
    def test_blue3_runner_returns_decoder_data_unchanged(self, decoder):
        expected = {
            "flag": "byuctf{example}",
            "format_valid": True,
            "attempts": [{"length": 14, "candidate": "byuctf{example}"}],
        }
        decoder.return_value = expected

        run = run_blue3(BLUE3_PATH)

        decoder.assert_called_once_with(BLUE3_PATH)
        self.assertEqual(run["result"], expected)
        self.assertEqual(run["status"], "Success")

    @patch("visualization.utils.decode_sleepy_alarm")
    def test_audio_runner_passes_both_paths_and_preserves_failure_data(self, decoder):
        expected = {
            "decoded_text": "fragment}",
            "format_valid": False,
            "reference_assisted": False,
            "alignment": None,
            "symbol_count": 350,
            "separator_count": 49,
            "amplitude_centers": [0.1, 0.2, 0.3],
            "errors": [{"byte_index": 2, "bits": "101"}],
        }
        decoder.return_value = expected

        run = run_sleepy_alarm(SLEEPY_TARGET_PATH, None)

        decoder.assert_called_once_with(SLEEPY_TARGET_PATH, None)
        self.assertEqual(run["result"], expected)
        self.assertEqual(run["status"], "Failed")

    def test_missing_image_is_reported_as_failed(self):
        run = run_blue3(ROOT / "data" / "missing.png")
        self.assertEqual(run["status"], "Failed")
        self.assertIsNone(run["result"])
        self.assertIn("FileNotFoundError", run["error"])


class TestVisualizationData(unittest.TestCase):
    def test_blue3_summary_matches_decoder_baseline_and_dimensions(self):
        pixels, baseline, count = image_summary(BLUE3_PATH)
        self.assertEqual(pixels.shape, (512, 512, 3))
        self.assertEqual(baseline, (64, 77, 205))
        self.assertGreater(count, 0)

    def test_audio_metadata_and_waveform_are_bounded(self):
        info = audio_metadata(SLEEPY_TARGET_PATH)
        seconds, samples = read_waveform(SLEEPY_TARGET_PATH, max_points=1000)

        self.assertEqual(info["sample_rate"], 44100)
        self.assertEqual(info["channels"], 2)
        self.assertEqual(samples.shape[1], info["channels"])
        self.assertLessEqual(len(seconds), 1000)
        self.assertEqual(len(seconds), len(samples))
        self.assertTrue((seconds[1:] >= seconds[:-1]).all())

    def test_reference_free_decoder_failure_remains_visible(self):
        run = run_sleepy_alarm(SLEEPY_TARGET_PATH)
        self.assertEqual(run["status"], "Failed")
        self.assertIsNone(run["error"])
        self.assertFalse(run["result"]["format_valid"])
        self.assertFalse(run["result"]["reference_assisted"])
        self.assertGreater(len(run["result"]["errors"]), 0)

    def test_reference_assisted_decoder_output_is_unchanged(self):
        run = run_sleepy_alarm(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
        self.assertEqual(run["status"], "Success")
        self.assertEqual(run["result"]["decoded_text"], "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}")
        self.assertEqual(run["result"]["alignment"]["lag_samples"], 1729)
        self.assertEqual(run["result"]["alignment"]["target_start_sample"], 1729)


if __name__ == "__main__":
    unittest.main()
