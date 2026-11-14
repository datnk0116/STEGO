import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audio_alignment import align_reference


class AudioAlignmentTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.sample_rate = 44100
        self.reference = rng.normal(0.0, 0.05, (self.sample_rate * 2, 2))

    def test_aligns_integer_offset_and_returns_equal_overlap(self):
        lag = 127
        target = np.concatenate(
            [np.zeros((lag, 2)), self.reference, np.zeros((200, 2))], axis=0
        )
        target[lag:lag + len(self.reference), 0] += (
            0.002 * np.sin(
                2 * np.pi * 8000
                * np.arange(len(self.reference)) / self.sample_rate
            )
        )
        aligned_target, aligned_reference, info = align_reference(
            target, self.sample_rate, self.reference, self.sample_rate
        )
        self.assertEqual(info["alignment_lag_samples"], lag)
        self.assertEqual(aligned_target.shape, aligned_reference.shape)
        self.assertEqual(aligned_target.shape[0], len(self.reference))
        self.assertGreater(info["normalized_abs_correlation"], 0.99)

    def test_resamples_reference_before_alignment(self):
        reference_32k = resample_poly(self.reference, 32000, self.sample_rate, axis=0)
        lag = 1000
        target = np.concatenate(
            [np.zeros((lag, 2)), self.reference, np.zeros((80, 2))], axis=0
        )
        aligned_target, aligned_reference, info = align_reference(
            target, self.sample_rate, reference_32k, 32000
        )
        self.assertEqual(info["alignment_lag_samples"], lag)
        self.assertIsNotNone(info["reference_resampling"])
        self.assertEqual(aligned_target.shape, aligned_reference.shape)
        self.assertGreater(info["normalized_abs_correlation"], 0.70)

    def test_channel_mismatch_is_downmixed(self):
        reference_mono = self.reference.mean(axis=1, keepdims=True)
        target = np.concatenate(
            [np.zeros((64, 2)), self.reference, np.zeros((32, 2))], axis=0
        )
        aligned_target, aligned_reference, info = align_reference(
            target, self.sample_rate, reference_mono, self.sample_rate
        )
        self.assertEqual(info["alignment_lag_samples"], 64)
        self.assertEqual(info["channel_handling"], "downmixed_to_mono")
        self.assertEqual(aligned_target.shape[1], 1)
        self.assertEqual(aligned_target.shape, aligned_reference.shape)


if __name__ == "__main__":
    unittest.main()
