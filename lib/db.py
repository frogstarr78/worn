from . import *
import redis

def xrange(key:str, start:str=None, end:str=None, count:int | None=None, reverse:bool=False) -> list:
  _key = str(key)
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if reverse:
      return conn.xrevrange(_key, start or '+', end or '-', count=count)
    else:
      return conn.xrange(   _key, start or '-', end or '+', count=count)

def xinfo(key:str, hkey:str | None=None, default:Any=None, kind:str='stream') -> dict | str:
  _key = str(key)
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    info = conn.xinfo_stream(_key)
    if hkey is None:
      return info
    else:
      return info.get(str(hkey), default)

def has(key:str, hkey:str=None) -> bool:
  _key = str(key)
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hkey is None:
      return conn.exists(_key) == 1
    else:
      return has(_key) and conn.hexists(_key, str(hkey))

def keys(key:str) -> list:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    return conn.hkeys(str(key))

def get(key:str, hkey:Any=None) -> str | dict:
  _key = str(key)
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hkey is None:
      if conn.type(_key) == 'hash':
        return conn.hgetall(_key)
      else:
        return conn.get(_key)
    else:
      return conn.hget(_key, str(hkey))

def rename(key:str, newkey:str) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    conn.rename(str(key), str(newkey))
    save()

def rm(key:str, sub:int | str | None=None) -> None:
  _key = str(key)

  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if sub is None:
      conn.delete(_key)
    elif conn.type(_key) == 'hash':
      conn.hdel(_key, str(sub))
    elif conn.type(_key) == 'stream':
      conn.xdel(key, str(sub))
    save()

def add(key:str, val:str | int | dict=None, expire:int | None=None, nx:bool=False) -> None:
  if isinstance(val, dict):
    _val = dict([(str(_k), str(_v)) for _k, _v in val.items()])

  _key = str(key)

  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if (_type := conn.type(_key)) == 'hash':
      if nx:
        for _k, _v in _val.items():
          conn.hsetnx(_key, _k, _v)
      else:
        conn.hset(_key, mapping=_val)
    elif _type == 'stream':
      conn.xadd(_key, _val, id=val.pop('id', '*'))
    elif isinstance(val, dict):
      conn.hset(_key, mapping=_val)
    else:
      conn.set(_key, str(val), nx=nx, ex=expire)

    save()

def save(bg=False) -> None:
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if bg:
      conn.bgsave()
    else:
      conn.save()
