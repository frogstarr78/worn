import redis
from typing import Any
from uuid import uuid4, UUID
from . import istimestamp_id

def _valid_key(key:Any) -> str:
  assert isinstance(key, str | int | UUID), f"{key=} should be an instance of {','.join(types)}, but isn't."
  if not isinstance(key, str):
    key = str(key)
  assert len(key) > 0, f"{key=} should not be an empty string."

  return key

def xrange(key:str, *, start:str=None, end:str=None, count:int=None, reverse:bool=False) -> list:
  key = _valid_key(key)
  if start is not None:
    assert isinstance(start, str), f"{start=} should be an instance of str, but isn't."
  if end is not None:
    assert isinstance(end, str), f"{end=} should be an instance of str, but isn't."
  if count is not None:
    assert isinstance(count, int), f"{end=} should be an instance of int, but isn't."
  assert isinstance(reverse, bool), f"{reverse=} should be an instance of bool, but isn't."

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    if reverse: return conn.xrevrange(key, start or '+', end or '-', count=count)
    else:       return conn.xrange(   key, start or '-', end or '+', count=count)

def xinfo(key:str, hkey:str=None, *, default:Any=None, kind:str='stream') -> dict | str:
  key = _valid_key(key)

  if hkey is not None:
    hkey = _valid_key(hkey)
  assert isinstance(kind, str), f"{kind=} should be an instance of str, but isn't."
  assert len(kind) > 0, f"{key=} should not be an empty string."

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    if kind != 'stream': raise Exception(f'Unkown kind {kind}.')

    info = conn.xinfo_stream(key)
    if hkey is None: return info
    else:            return info.get(str(hkey), default)

def has(key:str, hkey:str=None) -> bool:
  key = _valid_key(key)

  if hkey is not None:
    hkey = _valid_key(hkey)

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    if hkey is None:
      return conn.exists(key) == 1
    else:
      return has(key) and conn.hexists(key, str(hkey))

def keys(key:str | int) -> list:
  key = _valid_key(key)

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    return conn.hkeys(str(key))

def get(key:str, hkey:Any=None) -> str | dict:
  key = _valid_key(key)

  if hkey is not None:
    hkey = _valid_key(hkey)

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    match conn.type(key):
      case 'hash' if hkey is None:   return conn.hgetall(key)
      case 'stream':                 raise Exception('Use xrange method instead.')
      case _ if hkey is None:        return conn.get(key)
      case _:                        return conn.hget(key, str(hkey))

def rename(key:str, newkey:str) -> None:
  key = _valid_key(key)
  newkey = _valid_key(newkey)

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    conn.rename(str(key), str(newkey))
    save()

def rm(key:str, sub:int | str=None) -> None:
  key = _valid_key(key)

  if sub is not None:
    assert isinstance(sub, int | str), f"{sub=} should be an instance of int or str, but isn't."

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    if sub is None:
      conn.delete(key)
    else:
      match conn.type(key):
        case 'hash': conn.hdel(key, str(sub))
        case 'stream': conn.xdel(key, str(sub))
        case kind: raise Exception('Unhandled database kind {kind}.')
    save()

def add(key:str, val:str | int | dict, *, expire:int=None, nx:bool=False) -> None:
  key = _valid_key(key)
  assert val is not None, f"{val=} should have a value, but doesn't."
  assert isinstance(nx, bool), f"{nx=} should be an instance of bool, but isn't."

  if isinstance(val, dict):
    _val = dict([(str(_k), str(_v)) for _k, _v in val.items()])
  else:
    _val = val

  if expire is not None:
    assert isinstance(expire, int), f"{expire=} should be an instance of int, but isn't."

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    match conn.type(key):
      case 'hash' if nx:
        for _k, _v in _val.items():
          conn.hsetnx(key, _k, _v)
      case 'hash':   conn.hset(key, mapping=_val)
      case 'stream':
        if istimestamp_id(stream_id := conn.xadd(key, _val, id=_val.pop('id', '*'))):
          for group in set(['display:console', 'display:tickets', 'display:email']).difference(set([_.get('name') for _ in conn.xinfo_groups(key)])):
            conn.xgroup_create(key, group, entries_read=0)
      case 'string': conn.set(key, str(_val), nx=nx, ex=expire)
      case _:
        if isinstance(_val, dict):
          if nx:
            for _k, _v in _val.items():
              conn.hsetnx(key, _k, _v)
          elif 'id' in _val:
            conn.xadd(key, _val, id=_val.pop('id', '*'))
          else:
            conn.hset(key, mapping=_val)
        elif isinstance(_val, str):
          conn.set(key, str(_val), nx=nx, ex=expire)
        else:
          raise Exception(f'Unable to set/add value for unhandled key kind {_val}.')

  save()

def save(*, bg:bool=False) -> None:
  assert isinstance(bg, bool), f"{bg=} should be an instance of bool, but isn't."

  with redis.StrictRedis(encoding="utf-8", decode_responses=True, db=0) as conn:
    if bg:
      conn.bgsave()
    else:
      conn.save()

def new_version(reason:str | list) -> UUID:
  assert isinstance(reason, str | list), f"{reason=} should be an instance of str or list, but isn't."
  version_id = uuid4()
  add('versions', dict(reason=reason, version=version_id, id='*'))
  rename('logs', f'logs-{version_id:s}')
  return version_id
