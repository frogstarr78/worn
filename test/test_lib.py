from test import *

class TestLib(TestWornBase):
  def test_isfloat(self):
    from lib import isfloat
    self.assertFalse(isfloat(''))
    self.assertFalse(isfloat('n'))
    self.assertFalse(isfloat('n.m'))
    self.assertFalse(isfloat('1.m'))
    self.assertFalse(isfloat('n.3'))
    self.assertFalse(isfloat('5'))
    self.assertFalse(isfloat(b'1'))
    self.assertFalse(isfloat(b'0.m'))
    self.assertFalse(isfloat(9))
    self.assertFalse(isfloat(True))
    self.assertTrue(isfloat(8384235.39434321))
    self.assertTrue(isfloat('1.1'))
    self.assertTrue(isfloat('1.0'))
    self.assertTrue(isfloat(b'1.1'))
    self.assertTrue(isfloat(b'0.1'))
    self.assertTrue(isfloat('5.3444'))
    self.assertTrue(isfloat(b'8384235.39434321'))
    self.assertTrue(isfloat(b'8384235.2'))

  def test_isuuid(self):
    from lib import isuuid
    self.assertTrue(isuuid(uuid4()))
    self.assertTrue(isuuid(UUID('2c68c577-17f6-4740-aae6-d02c9357c58e')))
    self.assertTrue(isuuid([UUID('2c68c577-17f6-4740-aae6-d02c9357c58e')]))
    self.assertTrue(isuuid((UUID('2c68c577-17f6-4740-aae6-d02c9357c58e'),)))
    self.assertTrue(isuuid('2c68c577-17f6-4740-aae6-d02c9357c58e'))
    self.assertTrue(isuuid(['2c68c577-17f6-4740-aae6-d02c9357c58e']))
    self.assertTrue(isuuid(('2c68c577-17f6-4740-aae6-d02c9357c58e',)))
    self.assertFalse(isuuid('bob'))
    self.assertFalse(isuuid(['bob']))
    self.assertFalse(isuuid(('bob',)))
    self.assertFalse(isuuid(''))
    self.assertFalse(isuuid(['']))
    self.assertFalse(isuuid([]))
    self.assertFalse(isuuid(('',)))
    self.assertFalse(isuuid(tuple()))
    self.assertFalse(isuuid({'a':'b'}))
    self.assertFalse(isuuid(dict()))
    self.assertFalse(isuuid(set()))
    self.assertFalse(isuuid(None))

  def test_istimestamp_id(self):
    from lib import istimestamp_id
    time = f'{datetime.now():%s}'
    self.assertTrue(istimestamp_id(f'{time[:10]}-*'), msg=f'"{time[:10]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:11]}-*'), msg=f'"{time[:11]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:12]}-*'), msg=f'"{time[:12]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:13]}-*'), msg=f'"{time[:13]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:10]}-0'), msg=f'"{time[:10]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:11]}-0'), msg=f'"{time[:11]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:12]}-0'), msg=f'"{time[:12]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:13]}-0'), msg=f'"{time[:13]}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:13]}-11111111111'), msg=f'"{time[:13]}-11111111111" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:14]}-0'), msg=f'"{time[:14]}-0" was considered a valid timestamp id when it should not have been.')
    self.assertTrue(istimestamp_id(f'{time[:14]}-*'), msg=f'"{time[:14]}-*" was considered a valid timestamp id when it should not have been.')

    self.assertFalse(istimestamp_id(f'{time[:10]}-r'), msg=f'"{time[:10]}-r" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(f'{time[:10]}-1o1'), msg=f'"{time[:10]}-1o1" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(f'{time[:10]}-o1o'), msg=f'"{time[:10]}-o1o" was considered a valid timestamp id when it should not have been.')

    time = datetime.now().timestamp()
    self.assertFalse(istimestamp_id(time),      msg=f'"{time}" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(int(time)), msg=f'"{time}" was considered a valid timestamp id when it should not have been.')

  def test_debug(self):
    from lib import debug
    with patch('sys.stderr', new_callable=StringIO) as mock_debug:
      debug('this', 'and', 'that')
      self.assertEqual('''this\nand\nthat\n''', mock_debug.getvalue())

  def test_constants(self):
    from lib import SECOND, MINUTE, HOUR, DAY, WEEK
    self.assertEqual(1,      SECOND)
    self.assertEqual(60,     MINUTE)
    self.assertEqual(3600,   HOUR)
    self.assertEqual(86400,  DAY)
    self.assertEqual(604800, WEEK)

  def test_parse_timestamp(self):
    from lib import parse_timestamp, InvalidTypeE, InvalidTimeE

    ts = parse_timestamp(1711729682)
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2), ts)

    ts = parse_timestamp(1711729682.1234)
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2, 123400), ts)

    ts = datetime.now()
    self.assertEqual(ts, parse_timestamp(ts))

    ts = parse_timestamp(['2024-03-29', '9:33:13'])
    self.assertEqual(ts, ts)
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 33, 13), ts)

    ts = parse_timestamp(['2024-03-29 12:33:13'])
    self.assertEqual(ts, ts)
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 12, 33, 13), ts)

    ts = parse_timestamp('Fri 2024-03-29 21:33:13')
    self.assertEqual(ts, ts)
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 21, 33, 13), ts)

    ts = parse_timestamp('1711729682')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2), ts)

    ts = parse_timestamp('17117296821234')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2, 123400), ts)

    ts = parse_timestamp('1711729682.1234')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2, 123400), ts)

    ts = parse_timestamp('1711154701.553')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 22, 17, 45, 1, 553000), ts)

    ts = parse_timestamp('1711154701553-1')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 22, 17, 45, 1, 553000), ts)

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('')

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('abcdefghij.k')

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('1234567890.k')

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('abcdefghij.12')

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('1711729682.1234.1')

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('123')

    with self.assertRaises(InvalidTypeE):
      parse_timestamp(range(0, 4))

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('17117296823.1234')

    with self.assertRaises(InvalidTypeE):
      parse_timestamp('abc')

    with self.assertRaises(InvalidTypeE):
      parse_timestamp(None)

  def test_datetime_now(self):
    from lib import parse_timestamp
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = parse_timestamp('now')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 31, 23, 59, 59, 999))

  def test_datetime_today(self):
    from lib import parse_timestamp
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = parse_timestamp('today')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 31, 0, 0, 0))

  def test_datetime_yesterday(self):
    from lib import parse_timestamp
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = parse_timestamp('yesterday')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 30, 0, 0, 0))

  def test_datetime_time_ago_exceptions(self):
    from lib import parse_timestamp, InvalidTypeE, InvalidTimeE
    with self.assertRaises(InvalidTypeE):
      parse_timestamp('7 parsecs ago')

    with self.assertRaises(InvalidTypeE):
      parse_timestamp('n minutes ago')

  def test_datetime_hours_ago(self):
    from lib import parse_timestamp
    with patch('lib.now', return_value=datetime(2000, 4, 5, 0, 38, 54, 999)) as not_now:
      r = parse_timestamp('7 hours ago')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(2000, 4, 4, 17, 38, 54, 999))

  def test_datetime_days_ago(self):
    from lib import parse_timestamp
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = parse_timestamp('3 days ago')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 28, 23, 59, 59, 999))

  def test_datetime_weekdays(self):
    from lib import parse_timestamp
    with patch('lib.now', return_value=datetime(1999, 12, 31, 23, 59, 59, 999)) as not_now:
      r = parse_timestamp('thu')
      self.assertEqual(not_now.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 30, 23, 59, 59, 999))

      r = parse_timestamp('wednesday')
      self.assertEqual(not_now.call_count, 2)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 29, 23, 59, 59, 999))

      r = parse_timestamp('Tuesday')
      self.assertEqual(not_now.call_count, 3)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 28, 23, 59, 59, 999))

      r = parse_timestamp('Mon')
      self.assertEqual(not_now.call_count, 4)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 27, 23, 59, 59, 999))

      r = parse_timestamp('sunday')
      self.assertEqual(not_now.call_count, 5)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 26, 23, 59, 59, 999))

      r = parse_timestamp('Sat')
      self.assertEqual(not_now.call_count, 6)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 25, 23, 59, 59, 999))

      r = parse_timestamp('Friday')
      self.assertEqual(not_now.call_count, 7)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, datetime(1999, 12, 24, 23, 59, 59, 999))

  def test_datetime_datetime(self):
    from lib import parse_timestamp
    _n = datetime.now()
    r = parse_timestamp(_n)
    self.assertIsInstance(r, datetime)
    self.assertEqual(r, _n)

  def test_datetime_times(self):
    from lib import parse_timestamp, InvalidTimeE
    with self.assertRaises(InvalidTimeE):
      r = parse_timestamp('13:01:01:34')

    _known_date = datetime(2001, 12, 31, 23, 59, 59, 999)
    with patch('lib.now', return_value=_known_date) as not_now:
      _hour_min = '13:01'
      with patch('datetime.datetime.strptime', return_value=datetime.strptime(f'{_known_date:%F} {_hour_min}', '%Y-%m-%d %H:%M')) as m:
        r = parse_timestamp(_hour_min)

        self.assertEqual(not_now.call_count, 1)
        self.assertEqual(m.call_count, 1)
        self.assertIsInstance(r, datetime)
        self.assertEqual(r, datetime(2001, 12, 31, 13, 1))

    _known_date = datetime(2001, 12, 31, 23, 59, 59, 999)
    with patch('lib.now', return_value=_known_date) as not_now:
      _hour_min = '13:01:57'
      with patch('datetime.datetime.strptime', return_value=datetime.strptime(f'{_known_date:%F} {_hour_min}', '%Y-%m-%d %H:%M:%S')) as m:
        r = parse_timestamp(_hour_min)

        self.assertEqual(not_now.call_count, 1)
        self.assertEqual(m.call_count, 1)
        self.assertIsInstance(r, datetime)
        self.assertEqual(r, datetime(2001, 12, 31, 13, 1, 57))

  def test_datetime_dates(self):
    from lib import parse_timestamp, InvalidTimeE
    _known_date = datetime(2024, 3, 31)
    with patch('datetime.datetime.strptime', return_value=_known_date) as m:
      r = parse_timestamp('2024-03-31')
      self.assertEqual(m.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, _known_date)

  def test_datetime_datetimes(self):
    from lib import parse_timestamp, InvalidTimeE
    with self.assertRaises(Exception):
      parse_timestamp('2024-03-31 12:45:56 08:00 am')

    with self.assertRaises(Exception):
      parse_timestamp('2024-03-31 12 45 56')

    _known_date = datetime(2024, 5, 1, 18, 22, 7)
    with patch('datetime.datetime.strptime', return_value=_known_date) as m:
      r = parse_timestamp('2024-05-01 06:22:07 pm')
      self.assertEqual(m.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, _known_date)

    _known_date = datetime(2024, 5, 1, 6, 22, 7)
    with patch('datetime.datetime.strptime', return_value=_known_date) as m:
      r = parse_timestamp('2024-05-01 06:22:07 am')
      self.assertEqual(m.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, _known_date)

    _known_date = datetime(2024, 5, 1, 18, 29)
    with patch('datetime.datetime.strptime', return_value=_known_date) as m:
      r = parse_timestamp('2024-05-01 06:29')
      self.assertEqual(m.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, _known_date)

    _known_date = datetime(2024, 5, 1, 6, 33, 29)
    with patch('datetime.datetime.strptime', return_value=_known_date) as m:
      r = parse_timestamp('2024-05-01 06:33:29')
      self.assertEqual(m.call_count, 1)
      self.assertIsInstance(r, datetime)
      self.assertEqual(r, _known_date)

  def test_datetime_digits_and_stream_ids(self):
    from lib import parse_timestamp, InvalidTimeE
    with patch('lib.parse_timestamp', return_value=datetime.now()) as mock_ts:
      r = parse_timestamp('1234567890')
      self.assertEqual(mock_ts.call_count, 1)
      self.assertIsInstance(r, datetime)

    with patch('lib.parse_timestamp', return_value=datetime.now()) as mock_ts:
      r = parse_timestamp('1234567890123-1')
      self.assertEqual(mock_ts.call_count, 1)
      self.assertIsInstance(r, datetime)

  def test_datetime_invalid_input(self):
    from lib import parse_timestamp, InvalidTypeE, InvalidTimeE
    with self.assertRaises(InvalidTimeE):
      parse_timestamp(['i', 'am', 'a', 'list'])

    with self.assertRaises(InvalidTimeE):
      parse_timestamp(('i', 'am', 'a', 'tuple'))

    with self.assertRaises(InvalidTypeE):
      parse_timestamp({'i': 'am', 'a': 'dict'})

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('i am a string with too many spaces')

    with self.assertRaises(InvalidTimeE):
      parse_timestamp('1-2-3-4-5')

  def test_explain_dates(self):
    from lib import explain_dates
    self.assertGreater(len(explain_dates()), 0)
    self.assertIn('now', explain_dates())
    self.assertIn('yesterday', explain_dates())
    self.assertIn('redis stream timestamp', explain_dates())
    self.assertIn('examples: "10:31", "22:22", etc', explain_dates())
    self.assertIn('examples: "2024-03-14"', explain_dates())

  def test_stream_id(self):
    from lib import stream_id, InvalidTypeE
    self.assertEqual(stream_id(self.known_date), f'{self.known_date:%s}-*')
    self.assertEqual(stream_id(self.known_date.timestamp()), f'{self.known_date:%s}-*')
    self.assertEqual(stream_id(str(self.known_date.timestamp())), f'{self.known_date:%s}-*')
    self.assertEqual(stream_id(int(self.known_date.timestamp())), f'{self.known_date:%s}-*')

    with self.assertRaises(InvalidTypeE):
      stream_id(['not', 'a', 'stream', 'id'])

if __name__ == '__main__':
  unittest.main(buffer=True)
