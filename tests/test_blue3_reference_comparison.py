import random
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blue3.reference_comparison import compare_solvers


class Blue3ReferenceComparisonTests(unittest.TestCase):
    def test_cross_check_output_matches_on_deterministic_synthetic_fixture(self):
        flag = "byuctf{ref_42}"
        image = Image.new("RGB", (512, 512), (64, 77, 205))
        pixels = image.load()
        rng = random.Random(20261114)
        width = image.width // len(flag)
        height = image.height // len(flag)
        for index, character in enumerate(flag):
            for _ in range(ord(character)):
                x = rng.randint(0, width - 1) + width * index
                y = rng.randint(0, height - 1) + height * index
                channel = rng.randint(0, 2)
                color = list(pixels[x, y])
                color[channel] += 1
                pixels[x, y] = tuple(color)
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "blue3-synthetic.png"
            image.save(artifact)
            # Independent, minimal reference implementation for an offline regression.
            # The real benchmark fetches the untouched upstream script at its pinned commit.
            reference_code = """\
from collections import Counter
from PIL import Image
import re

image = Image.open('blue.png').convert('RGB')
pixels = image.load()
base = Counter(pixels[x, y] for x in range(image.size[0]) for y in range(image.size[1])).most_common(1)[0][0]
for length in range(2, image.size[0] + 1):
    width = image.size[0] // length
    height = image.size[1] // length
    candidate = ''
    for index in range(length):
        total = 0
        for x in range(width * index, width * (index + 1)):
            for y in range(height * index, height * (index + 1)):
                total += sum(pixels[x, y][channel] - base[channel] for channel in range(3))
        candidate += chr(total)
    if re.match(r'byuctf\\{[0-9A-Za-z_]*\\}', candidate):
        print(candidate)
        break
"""
            result = compare_solvers(artifact, upstream_source=reference_code)

        comparison = result["comparison"]
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(len(result["input"]["sha256"]), 64)
        self.assertEqual(comparison["upstream_candidate"], flag)
        self.assertEqual(comparison["local_candidate"], flag)
        self.assertTrue(comparison["exact_candidate_match"])
        self.assertEqual(len(comparison["upstream_source_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
