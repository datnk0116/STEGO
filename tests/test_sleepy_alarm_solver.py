import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from solve_challenges import solve_sleepy


class SleepyAlarmSolverTests(unittest.TestCase):
    def test_decodes_39_byte_ask_message_from_first_stereo_channel(self):
        sample_rate = 44100
        duration = 9.0
        flag = "ictf{" + ("x" * 33) + "}"
        self.assertEqual(len(flag), 39)
        bitmap = " ".join(f"{ord(ch):08b}" for ch in flag)
        self.assertEqual(len(bitmap), 350)

        rng = np.random.default_rng(2026)
        n = int(duration * sample_rate)
        t = np.arange(n) / sample_rate
        background = np.column_stack([
            0.05 * np.sin(2 * np.pi * 440 * t)
            + 0.02 * np.sin(2 * np.pi * 1700 * t)
            + rng.normal(0, 0.0005, n),
            0.04 * np.sin(2 * np.pi * 550 * t)
            + 0.02 * np.sin(2 * np.pi * 2200 * t)
            + rng.normal(0, 0.0005, n),
        ])
        amplitudes = np.asarray([
            0.0 if bit == " " else (2e-3 if bit == "0" else 5e-3)
            for bit in bitmap
        ])
        sample_count = int(7.0 * sample_rate)
        sample_index = np.arange(sample_count)
        symbol_index = np.minimum(
            (sample_index * 50 // sample_rate).astype(int), len(amplitudes) - 1
        )
        carrier = amplitudes[symbol_index] * np.sin(
            2 * np.pi * 8000 * sample_index / sample_rate
        )

        distributed = background.copy()
        # The upstream MATLAB generator writes the ASK signal to column 1
        # (the first/left channel) only.
        distributed[:sample_count, 0] += carrier

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            reference_path = temp / "original.wav"
            distributed_path = temp / "distributed.wav"
            sf.write(reference_path, background, sample_rate, subtype="PCM_24")
            sf.write(distributed_path, distributed, sample_rate, subtype="PCM_24")
            result = solve_sleepy(
                distributed_path, reference=reference_path
            )

        self.assertTrue(result["success"], result)
        self.assertEqual(result["decoded_text"], flag)
        self.assertEqual(result["expected_symbol_count"], 350)
        self.assertEqual(result["byte_count"], 39)
        self.assertEqual(result["symbol_counts"]["separator"], 38)
        self.assertEqual(result["analysis_channel"], 0)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
