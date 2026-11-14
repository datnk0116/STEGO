import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from steganalysis import (image_features, audio_features, classify_image,
                          classify_audio)


class SteganalysisTests(unittest.TestCase):
    def test_uniform_image_is_flagged_by_explicit_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "uniform.png"
            Image.new("RGB", (64, 64), (64, 77, 205)).save(path)
            features = image_features(path)
        flagged, reasons = classify_image(features)
        self.assertTrue(flagged)
        self.assertEqual(len(reasons), 2)

    def test_textured_image_is_not_flagged(self):
        rng = np.random.default_rng(42)
        pixels = rng.integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "texture.png"
            Image.fromarray(pixels, "RGB").save(path)
            features = image_features(path)
        flagged, _ = classify_image(features)
        self.assertFalse(flagged)


    def test_ask_like_modulation_is_flagged(self):
        sr = 44100
        samples_per_symbol = int(sr / 50)
        amplitudes = np.tile(np.asarray([0.0, 0.002, 0.005, 0.002]), 40)
        index = np.arange(len(amplitudes) * samples_per_symbol)
        symbol = np.repeat(amplitudes, samples_per_symbol)
        carrier = symbol * np.sin(2 * np.pi * 8000 * index / sr)
        stereo = np.column_stack([carrier, np.zeros_like(carrier)])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ask.wav"
            sf.write(path, stereo, sr)
            features = audio_features(path)
        flagged, reasons = classify_audio(features)
        self.assertTrue(flagged, features)
        self.assertEqual(len(reasons), 2)

    def test_broadband_noise_is_not_flagged(self):
        sr = 44100
        rng = np.random.default_rng(7)
        noise = rng.normal(0, 0.04, sr * 2)
        stereo = np.column_stack([noise, noise * 0.9])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "noise.wav"
            sf.write(path, stereo, sr)
            features = audio_features(path)
        flagged, _ = classify_audio(features)
        self.assertFalse(flagged, features)

    def test_audio_features_are_finite(self):
        sr = 44100
        t = np.arange(sr, dtype=np.float64) / sr
        signal = 0.02 * np.sin(2 * np.pi * 8000 * t)
        stereo = np.column_stack([signal, np.zeros_like(signal)])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tone.wav"
            sf.write(path, stereo, sr)
            features = audio_features(path)
        self.assertTrue(np.isfinite(features["carrier_band_energy_ratio"]))
        self.assertGreaterEqual(features["carrier_band_energy_ratio"], 0.0)
        self.assertLessEqual(features["carrier_band_energy_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
