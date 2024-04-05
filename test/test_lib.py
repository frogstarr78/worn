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
    time = str(datetime.now().timestamp()).replace('.', '')
    self.assertTrue(istimestamp_id(f'{time[:10]:0<13}-*'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:11]:0<13}-*'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:12]:0<13}-*'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:13]:0<13}-*'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:10]:0<13}-0'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:11]:0<13}-0'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:12]:0<13}-0'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:13]:0<13}-0'), msg=f'"{time[:10]:0<13}-*" was not considered a valid timestamp id.')
    self.assertTrue(istimestamp_id(f'{time[:13]:0<13}-11111111111'), msg=f'"{time[:10]:0<13}-11111111111" was not considered a valid timestamp id.')

    self.assertFalse(istimestamp_id(f'{time[:13]:0<13}0-0'), msg=f'"{time[:13]:0<13}0-0" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(f'{time[:13]:0<13}0-*'), msg=f'"{time[:13]:0<13}0-*" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(f'{time[:13]:0<13}0-r'), msg=f'"{time[:13]:0<13}0-r" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(f'{time[:13]:0<13}0-1o1'), msg=f'"{time[:13]:0<13}0-1o1" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(f'{time[:13]:0<13}0-o1o'), msg=f'"{time[:13]:0<13}0-o1o" was considered a valid timestamp id when it should not have been.')

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
    from lib import parse_timestamp

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
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2, 1234), ts)

    ts = parse_timestamp('1711729682.1234')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 29, 9, 28, 2, 123400), ts)

    ts = parse_timestamp('1711154701553-1')
    self.assertIsInstance(ts, datetime)
    self.assertEqual(datetime(2024, 3, 22, 17, 45, 1, 553), ts)

    with self.assertRaises(Exception):
      parse_timestamp('abcdefghij.k')

    with self.assertRaises(Exception):
      parse_timestamp('1234567890.k')

    with self.assertRaises(Exception):
      parse_timestamp('abcdefghij.12')

    with self.assertRaises(Exception):
      parse_timestamp('1711729682.1234.1')

    with self.assertRaises(Exception):
      parse_timestamp('123')

    with self.assertRaises(Exception):
      parse_timestamp(range(0, 4))

  def test_explain_dates(self):
    from lib import explain_dates
    self.assertGreater(len(explain_dates()), 0)
    self.assertIn('now', explain_dates())
    self.assertIn('yesterday', explain_dates())
    self.assertIn('redis stream timestamp', explain_dates())
    self.assertIn('examples: "10:31", "22:22", etc', explain_dates())
    self.assertIn('examples: "2024-03-14"', explain_dates())

if __name__ == '__main__':
  unittest.main(buffer=True)
