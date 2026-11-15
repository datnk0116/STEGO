import unittest
from pathlib import Path
from stego.audio import decode_sleepy_alarm
ROOT=Path(__file__).resolve().parents[1]
class TestSleepyAlarm(unittest.TestCase):
 def test_official_reference_assisted_flag(self):
  result=decode_sleepy_alarm(ROOT/'data/sleepy_alarm/morning_n_breakfast.mp3',ROOT/'data/sleepy_alarm/morning_n_breakfast_original.mp3')
  self.assertTrue(result['reference_assisted'])
  self.assertTrue(result['format_valid'])
  self.assertEqual(result['decoded_text'],'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}')
