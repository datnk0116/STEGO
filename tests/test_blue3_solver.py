import random
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from solve_challenges import solve_blue


class Blue3SolverTests(unittest.TestCase):
    def test_decodes_generated_diagonal_region_image(self):
        flag = "byuctf{test_123}"
        image = Image.new("RGB", (512, 512), (64, 77, 205))
        pixels = image.load()
        random.seed(7)
        width = image.width // len(flag)
        height = image.height // len(flag)
        for index, character in enumerate(flag):
            for _ in range(ord(character)):
                x = random.randint(0, width - 1) + width * index
                y = random.randint(0, height - 1) + height * index
                channel = random.randint(0, 2)
                color = list(pixels[x, y])
                color[channel] += 1
                pixels[x, y] = tuple(color)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "blue.png"
            image.save(path)
            candidate, attempts = solve_blue(path)
        self.assertEqual(candidate, flag)
        self.assertTrue(attempts)


if __name__ == "__main__":
    unittest.main()
