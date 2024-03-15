from . import *

def _db(cmd, key='', *args, **kw) -> Any:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if int(conn.info('default').get('redis_version', '0')[0]) < 7:
      raise Exception('This software requires version 7+ of Redis.')

    if cmd.casefold() == 'shutdown':
      return None

    if hasattr(conn, cmd.casefold()) and callable(f := getattr(conn, cmd.casefold())):
      if cmd in ['save', 'bgsave', 'ping']:
        return f()
      else:
        return f(key, *args, **kw)
    else:
      return None

def exists(key:str) -> bool:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.exists(key) == 1

def xadd(key:str, ts:Union[int, str, None]=None, **record) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if ts is None:
      conn.xadd(key, record)
    elif ts.count('-') == 1:
      conn.xadd(key, record, id=ts)
    else:
      conn.xadd(key, record, id=f'{ts[:13]:0<13}-*')
    conn.save()

def xrange(key:str, start:str='-', end:str='+', count:Union[int, None]=None, reverse:bool=False) -> list:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if reverse:
      return conn.xrevrange(key, end, start, count=count)
    else:
      return conn.xrange(key, start, end, count=count)

def xinfo(key:str, kind:str='stream') -> dict:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.xinfo_stream(key)

def hexists(key:str, hkey:str) -> bool:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.exists(key) and conn.hexists(key, hkey)

def hkeys(key:str) -> list:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.hkeys(key)

def hget(key:str, hkey:Any=None) -> dict:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hkey is None:
      return conn.hgetall(key)
    else:
      return {hkey: conn.hget(key, hkey)}

def hdel(key:str, hkey:str) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    conn.hdel(key, hkey)
    conn.save()

def set(key:str, val:Union[str, int, dict], expire:Union[int, None]=None, nx:bool=False) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if isinstance(val, dict):
      conn.hset(key, mapping=val)
    else:
      conn.set(key, str(val))
    if expire is not None:
      conn.expire(key, expire)
    conn.save()

def save(bg=False) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if bg:
      conn.bgsave()
    else:
      conn.save()
