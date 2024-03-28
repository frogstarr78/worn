from test import *
#import redis
from lib import db

class TestLib(TestWornBase):
  def test_xrange(self):
    with patch.multiple('redis.StrictRedis', xrevrange=DEFAULT, xrange=DEFAULT) as neone:
      db.xrange('skooter')
      self.assertTrue(neone['xrange'].called)
      self.assertEqual(neone['xrange'].call_count, 1)
      self.assertEqual(neone['xrange'].call_args.args, ('skooter', '-', '+'))
      self.assertEqual(neone['xrange'].call_args.kwargs, dict(count=None))

      self.assertFalse(neone['xrevrange'].called)
      self.assertEqual(neone['xrevrange'].call_count, 0)

      _uuid = self.random_uuid
      db.xrange(_uuid)
      self.assertEqual(neone['xrange'].call_count, 2)
      self.assertEqual(neone['xrange'].call_args.args, (str(_uuid), '-', '+'))


    with patch.multiple('redis.StrictRedis', xrevrange=DEFAULT, xrange=DEFAULT) as neone:
      db.xrange('man-hole', reverse=True)
      self.assertFalse(neone['xrange'].called)
      self.assertEqual(neone['xrange'].call_count, 0)

      self.assertTrue(neone['xrevrange'].called)
      self.assertEqual(neone['xrevrange'].call_count, 1)
      self.assertEqual(neone['xrevrange'].call_args.args, ('man-hole', '+', '-'))
      self.assertEqual(neone['xrevrange'].call_args.kwargs, dict(count=None))

    with patch('redis.StrictRedis.xrange') as kirk:
      db.xrange('some', start='123', end='124', count=4)
      self.assertTrue(kirk.called)
      self.assertEqual(kirk.call_count, 1)
      self.assertEqual(kirk.call_args.args, ('some', '123', '124'))
      self.assertEqual(kirk.call_args.kwargs, dict(count=4))

    with patch('redis.StrictRedis.xrevrange') as kirk:
      '''Kirk mocked Khan(conn)'''
      db.xrange('what was that', start='9', end='3', count=7, reverse=True)
      self.assertTrue(kirk.called)
      self.assertEqual(kirk.call_count, 1)
      self.assertEqual(kirk.call_args.args, ('what was that', '9', '3'))
      self.assertEqual(kirk.call_args.kwargs, dict(count=7))

  def test_xinfo(self):
    with patch('redis.StrictRedis.xinfo_stream', return_value={'a': 'b'}) as babbling_brook:
      '''A brook is a pall in comparison to a stream'''
      ret = db.xinfo('periwinkle')
      self.assertTrue(babbling_brook.called)
      self.assertEqual(babbling_brook.call_count, 1)
      self.assertEqual(babbling_brook.call_args.args, ('periwinkle',))
      self.assertDictEqual({'a': 'b'}, ret)

      ret = db.xinfo('periwinkle', 'a')
      self.assertEqual(babbling_brook.call_count, 2)
      self.assertEqual(babbling_brook.call_args.args, ('periwinkle',))
      self.assertEqual('b', ret)

      ret = db.xinfo('periwinkle', 'leg', default='brown')
      self.assertEqual(babbling_brook.call_count, 3)
      self.assertEqual(babbling_brook.call_args.args, ('periwinkle',))
      self.assertEqual('brown', ret)

      with self.assertRaises(Exception):
        db.xinfo('periwinkle', 'a', kind='river')

  def test_has(self):
    with patch('redis.StrictRedis.exists', return_value=1) as philosopher:
      '''The philosopher mock's whether or not we exist'''
      r = db.has('an idea')
      self.assertTrue(philosopher.called)
      self.assertEqual(philosopher.call_count, 1)
      self.assertEqual(philosopher.call_args.args, ('an idea',))
      self.assertTrue(r)

      r = db.has('figero')
      self.assertEqual(philosopher.call_count, 2)
      self.assertEqual(philosopher.call_args.args, ('figero',))
      self.assertTrue(r)

    with patch('redis.StrictRedis.exists', return_value=1) as philosopher:
      '''The philosopher mock's whether or not we exist'''
      with patch('redis.StrictRedis.hexists', return_value=True) as comedian:
        '''The hairy comedian makes fun of our existance'''
        r = db.has('cosmos', 'cat mug')

        self.assertTrue(philosopher.called)
        self.assertEqual(philosopher.call_count, 1)
        self.assertEqual(philosopher.call_args.args, ('cosmos',))

        self.assertTrue(comedian.called)
        self.assertEqual(comedian.call_count, 1)
        self.assertEqual(comedian.call_args.args, ('cosmos','cat mug'))
        self.assertTrue(r)

  def test_keys(self):
    with patch('redis.StrictRedis.hkeys', return_value=True) as kirk:
      '''Kirk mocked Khan(conn)'''
      ret = db.keys('something')
      self.assertTrue(ret)
      self.assertTrue(kirk.called)
      self.assertEqual(kirk.call_count, 1)
      self.assertEqual(kirk.call_args.args, ('something',))

      ret = db.keys(123)
      self.assertTrue(ret)
      self.assertEqual(kirk.call_count, 2)
      self.assertEqual(kirk.call_args.args, ('123',))
    
  def test_get(self):
    with patch('redis.StrictRedis.hget', return_value='carrot') as sleight_of_hand:
      '''A magician doesn't act like they get anything, they control where it goes the whole time.'''
      ret = db.get('hat', 'rabbit')
      self.assertEqual(sleight_of_hand.call_count, 1)
      self.assertEqual(sleight_of_hand.call_args.args, ('hat','rabbit'))
      self.assertEqual(ret, 'carrot')

    with patch('redis.StrictRedis.hgetall', return_value={'pretty':'assistant'}) as sleight_of_hand:
      '''A magician doesn't act like they get anything, they control where it goes the whole time.'''
      with patch('redis.StrictRedis.type', return_value='hash') as candy:
        '''Candy is a poor substitute for a meal.'''
        ret = db.get('cabinet')

        self.assertTrue(candy.called)
        self.assertEqual(candy.call_count, 1)

        self.assertEqual(sleight_of_hand.call_count, 1)
        self.assertEqual(sleight_of_hand.call_args.args, ('cabinet',))
        self.assertDictEqual(ret, {'pretty': 'assistant'})

    with patch('redis.StrictRedis.get', return_value='ribbon') as sleight_of_hand:
      '''A magician doesn't act like they get anything, they control where it goes the whole time.'''
      with patch('redis.StrictRedis.type', return_value='string') as meal:
        ret = db.get('sleeve')

        self.assertTrue(candy.called)
        self.assertEqual(candy.call_count, 1)

        self.assertEqual(sleight_of_hand.call_count, 1)
        self.assertEqual(sleight_of_hand.call_args.args, ('sleeve',))
        self.assertEqual(ret, 'ribbon')

  def test_rename(self):
    with patch.multiple('redis.StrictRedis', rename=DEFAULT, save=DEFAULT) as neone:
      db.rename('this', 'that')
      self.assertTrue(neone['rename'].called)
      self.assertEqual(neone['rename'].call_count, 1)
      self.assertEqual(neone['rename'].call_args.args, ('this', 'that'))

      self.assertTrue(neone['save'].called)
      self.assertEqual(neone['save'].call_count, 1)

  def test_rm(self):
    with patch.multiple('redis.StrictRedis', delete=DEFAULT, save=DEFAULT) as archive:
      '''We don't remove things, we archive them FOREVER.'''
      db.rm('iron')
      self.assertEqual(archive['delete'].call_count, 1)
      self.assertEqual(archive['delete'].call_args.args, ('iron',))

      self.assertEqual(archive['save'].call_count, 1)

    with patch.multiple('redis.StrictRedis', hdel=DEFAULT, save=DEFAULT) as archive:
      '''We don't remove things, we archive them FOREVER.'''
      with patch('redis.StrictRedis.type', return_value='hash') as candy:
        '''Candy is a poor substitute for a meal.'''
        db.rm('body', 'brain')
        self.assertEqual(candy.call_count, 1)
        self.assertEqual(candy.call_args.args, ('body',))

        self.assertEqual(archive['hdel'].call_count, 1)
        self.assertEqual(archive['hdel'].call_args.args, ('body', 'brain'))

        self.assertEqual(archive['save'].call_count, 1)

    with patch.multiple('redis.StrictRedis', xdel=DEFAULT, save=DEFAULT) as archive:
      with patch('redis.StrictRedis.type', return_value='stream') as brook:
        '''A brook is a pall in comparison to a stream'''
        db.rm('forest', 'tree')
        self.assertEqual(brook.call_count, 1)
        self.assertEqual(brook.call_args.args, ('forest',))

        self.assertEqual(archive['xdel'].call_count, 1)
        self.assertEqual(archive['xdel'].call_args.args, ('forest', 'tree'))

        self.assertEqual(archive['save'].call_count, 1)

      with patch('redis.StrictRedis.type', return_value='set') as toy:
        '''A toy is a made up version of things in real life'''
        with self.assertRaises(Exception):
          db.rm('forest', 'tree')

  def test_add(self):
    with patch.multiple('redis.StrictRedis', hsetnx=DEFAULT, save=DEFAULT) as mockarena:
      '''Do a little dance, make a little love, get down tonight'''
      with patch('redis.StrictRedis.type', return_value='hash') as atom:
        '''Strings don't make up the world, atoms do.'''
        db.add('dance_floor', {'disco': 'ball', 'strobe': 'lights', 'party': 1}, nx=True)
        self.assertEqual(atom.call_args.args, ('dance_floor',))
        self.assertEqual(atom.call_count, 1)

        self.assertEqual(mockarena['hsetnx'].call_args_list, [('dance_floor','disco', 'ball'), ('dance_floor', 'strobe', 'lights'), ('dance_floor', 'party', '1')])
        self.assertEqual(mockarena['hsetnx'].call_count, 3)

        self.assertEqual(mockarena['save'].call_count, 1)

    self.fail('Implement me')

  def test_save(self):
    with patch.multiple('redis.StrictRedis', save=DEFAULT, bgsave=DEFAULT) as neone:
      db.save()
      self.assertTrue(neone['save'].called)
      self.assertEqual(neone['save'].call_count, 1)

      self.assertFalse(neone['bgsave'].called)
      self.assertEqual(neone['bgsave'].call_count, 0)

    with patch.multiple('redis.StrictRedis', save=DEFAULT, bgsave=DEFAULT) as neone:
      db.save(bg=True)
      self.assertFalse(neone['save'].called)
      self.assertEqual(neone['save'].call_count, 0)

      self.assertTrue(neone['bgsave'].called)
      self.assertEqual(neone['bgsave'].call_count, 1)

if __name__ == '__main__':
  unittest.main(buffer=True)
