import lib
from test import *
from lib.args import _datetime

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

  def test_datetime_last(self):
    _when = datetime.now()
    _proj = lib.project.Project(uuid4(), 'I was last', state='stopped', when=_when)
    with patch.object(lib.project.Project, 'last', return_value=_proj) as mock:
      r = _datetime('last')
      self.assertEqual(mock.call_count, 1)
      self.assertEqual(r, _when)

  def test_datetime_datetime(self):
    _when = datetime.now()
    self.assertEqual(_when, _datetime(_when))
    self.assertEqual(datetime.strptime(_when.strftime('%F %T'), '%Y-%m-%d %H:%M:%S'), _datetime(_when.strftime('%F %T')))

  def test_parse_args(self):
    from lib.args import parse_args
    from argparse import Namespace
    with patch('builtins.print') as mock_debug:
      r = parse_args(['show', 'last'])
      self.assertEqual(len(r), 5)
      self.assertIsInstance(r[-1], Namespace)
      self.assertEqual(mock_debug.call_count, 1)
      
      r = parse_args(['start', 'last'])
      self.assertEqual(len(r), 5)
      self.assertIsInstance(r[-1], Namespace)
      self.assertEqual(mock_debug.call_count, 2)

    with patch('builtins.print') as mock_debug:
      r = parse_args(['start', ' this', 'and', 'that '])
      self.assertEqual(r[-1].project, 'this and that')

    _uuid = uuid4()
    with patch('builtins.print') as mock_debug:
      r = parse_args(['start', str(_uuid)])
      self.assertEqual(r[-1].project, _uuid)
      self.assertEqual(mock_debug.call_count, 1)

      with self.assertRaises(Exception):
        r = parse_args(['start', [str(_uuid)]])
      
    with patch('builtins.print') as mock_debug:
      r = parse_args(['report', '--comment', 'that', 'and', 'this'])
      self.assertEqual(mock_debug.call_count, 1)
      self.assertEqual(r[-1].comment, 'that and this')

if __name__ == '__main__':
  unittest.main(buffer=True)
