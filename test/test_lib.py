from test import *

class TestLib(TestWornBase):
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
    import lib
    self.assertEqual(lib.MINUTE, 60)
    self.assertEqual(lib.HOUR, 3600)
    self.assertEqual(lib.DAY, 86400)
    self.assertEqual(lib.WEEK, 604800)

if __name__ == '__main__':
  unittest.main(buffer=True)
