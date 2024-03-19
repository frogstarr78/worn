from . import *
import redis

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

def has(key:str, hkey:str=None) -> bool:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hkey is None:
      return conn.exists(str(key)) == 1
    else:
      return has(key) and conn.hexists(str(key), str(hkey))

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

def rename(key:str, newkey:str) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    conn.rename(str(key), str(newkey))
    save()

def rm(key:str, sub:Union[int, str, None]=None) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if sub is None:
      conn.delete(str(key))
    elif conn.type(str(key)) == 'hash':
      conn.hdel(str(key), str(sub))
    elif conn.type(str(key)) == 'stream':
      conn.xdel(key, str(sub))
    save()

def add(key:str, val:Union[str, int, dict]=None, expire:Union[int, None]=None, nx:bool=False, **record) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if (_type := conn.type(str(key))) == 'hash':
      if nx:
        for _k, _v in val.items():
          conn.hsetnx(str(key), str(_k), str(_v))
      else:
        conn.hset(str(key), mapping=dict([(str(_k), str(_v)) for _k, _v in val.items()]))
    elif _type == 'stream':
      if val is None:
        conn.xadd(str(key), record)
      elif istimestamp_id(val):
        conn.xadd(str(key), record, id=val)
      elif isinstance(val, int) or 9 < len(val) < 14:
        conn.xadd(str(key), record, id=f'{str(val)[:13]:0<13}-*')
    else:
      conn.set(str(key), str(val), nx=nx)

    if expire is not None:
      conn.expire(str(key), expire)
    save()

def save(bg=False) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if bg:
      conn.bgsave()
    else:
      conn.save()
