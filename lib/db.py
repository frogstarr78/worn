from . import *

def _db(cmd, key:str='', *args, **kw) -> Any:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if int(conn.info('default').get('redis_version', '0')[0]) < 7:
      raise Exception('This software requires version 7+ of Redis.')

    if cmd.casefold() == 'shutdown':
      return None

    if hasattr(conn, cmd.casefold()) and callable(f := getattr(conn, cmd.casefold())):
      if cmd in ['save', 'bgsave', 'ping']:
        return f()
      else:
        return f(str(key), *args, **kw)
    else:
      return None

def exists(key:str) -> bool:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.exists(str(key)) == 1

def xrange(key:str, start:str=None, end:str=None, count:Union[int, None]=None, reverse:bool=False) -> list:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if reverse:
      return conn.xrevrange(str(key), start or '+', end or '-', count=count)
    else:
      return conn.xrange(   str(key), start or '-', end or '+', count=count)

def xinfo(key:str, hkey:Union[str, None]=None, default:Any=None, kind:str='stream') -> Union[dict, str]:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    info = conn.xinfo_stream(str(key))
    if hkey is None:
      return info
    else:
      return info.get(str(hkey), default)

def hexists(key:str, hkey:str) -> bool:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return exists(str(key)) and conn.hexists(str(key), str(hkey))

def keys(key:str) -> list:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.hkeys(key)

def get(key:str, hkey:Any=None) -> Union[str, dict]:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hkey is None:
      if conn.type(str(key)) == 'hash':
        return conn.hgetall(str(key))
      else:
        return conn.get(str(key))
    else:
      return conn.hget(str(key), str(hkey))

def xdel(key:str, id:Union[int, str]) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    conn.xdel(key, str(id))
    conn.save()

def xadd(key:str, ts:Union[int, str, None]=None, **record) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if ts is None:
      conn.xadd(str(key), record)
    elif ts.count('-') == 1:
      conn.xadd(str(key), record, id=ts)
    else:
      conn.xadd(str(key), record, id=f'{ts[:13]:0<13}-*')
    conn.save()

def rename(key:str, newkey:str) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    conn.rename(str(key), str(newkey))
    conn.save()

def hdel(key:str, hkey:str) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    conn.hdel(key, hkey)
    conn.save()

def set(key:str, val:Union[str, int, dict], expire:Union[int, None]=None, nx:bool=False) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if isinstance(val, dict):
      conn.hset(str(key), mapping=val)
    else:
      conn.set(str(key), str(val))
    if expire is not None:
      conn.expire(str(key), expire)
    conn.save()

def save(bg=False) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if bg:
      conn.bgsave()
    else:
      conn.save()
