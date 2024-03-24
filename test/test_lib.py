from test import *
from lib import *

class TestLib(TestWornBase):
  def test_isuuid(self):
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
    time = str(now().timestamp()).replace('.', '')
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

    time = now().timestamp()
    self.assertFalse(istimestamp_id(time),      msg=f'"{time}" was considered a valid timestamp id when it should not have been.')
    self.assertFalse(istimestamp_id(int(time)), msg=f'"{time}" was considered a valid timestamp id when it should not have been.')

  def test_debug(self):
    self.assertTrue(True)

  def test_email(self):
    with self.assertRaises(TypeError) as cm:
      email('me')

    with self.assertRaises(TypeError) as cm:
      email('me@')

    with self.assertRaises(TypeError) as cm:
      email('me@or.am.i@you')

    self.assertEqual(email('me@example.com'), 'me@example.com')

  def test_constants(self):
    self.assertEqual(lib.MINUTE, 60)
    self.assertEqual(lib.HOUR, 3600)
    self.assertEqual(lib.DAY, 86400)
    self.assertEqual(lib.WEEK, 604800)

if __name__ == '__main__':
  unittest.main(buffer=True)
