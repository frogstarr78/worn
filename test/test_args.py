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

#  @patch(f'{lib.__name__}.now', wraps=datetime)
#  def test_something(self, mock_datetime):
#      mock_datetime.datetime.now.return_value = datetime(1999, 12, 31, 23, 59, 59, 999)
#      self.assertEqual(_datetime('now'), mock_datetime.datetime.now())

  def test_datetime_now(self):
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = _datetime('now')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 31, 23, 59, 59, 999))

  def test_datetime_today(self):
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = _datetime('today')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 31, 0, 0, 0))

  def test_datetime_yesterday(self):
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = _datetime('yesterday')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 30, 0, 0, 0))

  def test_datetime_days_ago(self):
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = _datetime('5 days ago')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 26, 0, 0, 0))

  def test_datetime_weekdays(self):
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = _datetime('thu')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 30, 23, 59, 59, 999))

      r = _datetime('wednesday')
      self.assertEqual(not_now.call_count, 2)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 29, 23, 59, 59, 999))

      r = _datetime('Tuesday')
      self.assertEqual(not_now.call_count, 3)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 28, 23, 59, 59, 999))

      r = _datetime('Mon')
      self.assertEqual(not_now.call_count, 4)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 27, 23, 59, 59, 999))

      r = _datetime('sunday')
      self.assertEqual(not_now.call_count, 5)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 26, 23, 59, 59, 999))

      r = _datetime('Sat')
      self.assertEqual(not_now.call_count, 6)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 25, 23, 59, 59, 999))

      r = _datetime('Friday')
      self.assertEqual(not_now.call_count, 7)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 24, 23, 59, 59, 999))

  def test_datetime_datetime(self):
    _n = datetime.now()
    r = _datetime(_n)
    self.assertIsInstance(r, datetime)
    self.assertEqual(r, _n)

  def test_datetime_times(self):
    with self.assertRaises(Exception):
      r = _datetime('13:01:01:34')

    _known_date = datetime(2001, 12, 31, 23, 59, 59, 999)
    with patch('lib.now', return_value=_known_date) as not_now:
      _hour_min = '13:01'
      with patch('datetime.datetime.strptime', return_value=datetime.strptime(f'{_known_date:%F} {_hour_min}', '%Y-%m-%d %H:%M')) as m:
        r = _datetime(_hour_min)

        self.assertEqual(not_now.call_count, 1)
        self.assertEqual(m.call_count, 1)
        self.assertIsInstance(r, datetime)
        self.assertEqual(r, datetime(2001, 12, 31, 13, 1))

    _known_date = datetime(2001, 12, 31, 23, 59, 59, 999)
    with patch('lib.now', return_value=_known_date) as not_now:
      _hour_min = '13:01:57'
      with patch('datetime.datetime.strptime', return_value=datetime.strptime(f'{_known_date:%F} {_hour_min}', '%Y-%m-%d %H:%M:%S')) as m:
        r = _datetime(_hour_min)

        self.assertEqual(not_now.call_count, 1)
        self.assertEqual(m.call_count, 1)
        self.assertIsInstance(r, datetime)
        self.assertEqual(r, datetime(2001, 12, 31, 13, 1, 57))

  def test_datetime_dates(self):
    _known_date = datetime(2024, 3, 31)
    with patch('datetime.datetime.strptime', return_value=_known_date) as m:
      r = _datetime('2024-03-31')
      self.assertEqual(m.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, _known_date)

  def test_datetime_digits_and_stream_ids(self):
    with patch('lib.parse_timestamp', return_value=datetime.now()) as mock_ts:
      r = _datetime('1234567890')
      self.assertEqual(mock_ts.call_count, 1)
      self.assertIsInstance(r, datetime)

    with patch('lib.parse_timestamp', return_value=datetime.now()) as mock_ts:
      r = _datetime('1234567890123-1')
      self.assertEqual(mock_ts.call_count, 1)
      self.assertIsInstance(r, datetime)

  def test_datetime_invalid_input(self):
    with self.assertRaises(Exception):
      _datetime(['i', 'am', 'a', 'list'])

    with self.assertRaises(Exception):
      _datetime(('i', 'am', 'a', 'tuple'))

    with self.assertRaises(Exception):
      _datetime({'i': 'am', 'a': 'dict'})

    with self.assertRaises(Exception):
      _datetime(5)

  def test_parse_args(self): pass
#    from lib.args import parse_args
#    from argparse import Namespace
#    with patch('builtins.print', new_callable=StringIO) as mock_debug:
#      r = parse_args(['-h'])
#      self.assertEqual(len(r), 5)
#      self.assertIsInstance(r[-1], Namespace)
      

if __name__ == '__main__':
  unittest.main(buffer=True)
