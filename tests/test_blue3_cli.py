import contextlib
import io
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from solve_challenges import main


class Blue3CliTests(unittest.TestCase):
    def test_cli_black_box_mode_does_not_require_base_color(self):
        flag = "byuctf{cli_42}"
        image = Image.new("RGB", (512, 512), (64, 77, 205))
        pixels = image.load()
        rng = random.Random(19)
        cell = 512 // len(flag)
        for index, character in enumerate(flag):
            for _ in range(ord(character)):
                x = index * cell + rng.randrange(cell)
                y = index * cell + rng.randrange(cell)
                channel = rng.randrange(3)
                value = list(pixels[x, y])
                value[channel] += 1
                pixels[x, y] = tuple(value)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cli.png"
            image.save(path)
            output = io.StringIO()
            with patch.object(sys, "argv", ["solve_challenges.py", "blue3", str(path)]):
                with contextlib.redirect_stdout(output):
                    exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertIn(flag, output.getvalue())
        self.assertIn("Format validated: True", output.getvalue())


if __name__ == "__main__":
    unittest.main()
