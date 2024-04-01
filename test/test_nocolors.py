from test import *
from lib.nocolors import colors

class TestNoColor(TestWornBase):
  def test_mods(self):
    self.assertEqual(colors.underline, '')

  def test_fg(self):
    self.assertEqual(colors.fg.black, '')

  def test_bg(self):
    self.assertEqual(colors.bg.black, '')

  def test_reset(self):
    self.assertEqual(colors.reset, '\033[0m')

if __name__ == '__main__':
  unittest.main(buffer=True)
