
from test import *

class TestLib(TestWornBase):
  def test_email(self):
    from lib.args import email
    with self.assertRaises(TypeError) as cm:
      email('me')

    with self.assertRaises(TypeError) as cm:
      email('me@')

    with self.assertRaises(TypeError) as cm:
      email('me@or.am.i@you')

    self.assertEqual(email('me@example.com'), 'me@example.com')

  def test_datetime(self):
    self.fail('Implement me') 

  def test_parse_args(self):
    self.fail('Implement me') 

if __name__ == '__main__':
  unittest.main(buffer=True)
