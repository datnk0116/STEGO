import unittest
from pathlib import Path
from stego.image import decode_blue3
ROOT=Path(__file__).resolve().parents[1]
class TestBlue3(unittest.TestCase):
 def test_official_flag(self):
  result=decode_blue3(ROOT/'data/blue3/blue.png')
  self.assertTrue(result['format_valid'])
  self.assertEqual(result['flag'],'byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}')
