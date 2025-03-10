from __future__ import annotations
import sys
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re, io
from typing import *

class BaseException(Exception): pass
class InvalidTimeE(BaseException): pass
class InvalidTypeE(BaseException): pass

def debug(*msgs) -> None:
  for m in msgs:
    print(m, file=sys.stderr)

def now():
  return datetime.now()

def isuuid(s:Any) -> bool:
    if isinstance(s, UUID):                           return True
    elif isinstance(s, str):                          return re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s) is not None
    elif isinstance(s, tuple | list) and len(s) == 1: return all(isuuid(_) for _ in s)
    else:                                             return False

def stream_id(ts, seq='*'):
  if isinstance(ts, int | float):   return stream_id(datetime.fromtimestamp(float(ts)), seq)
  elif isinstance(ts, str | bytes): return stream_id(parse_timestamp(ts), seq)
  elif isinstance(ts, datetime):    return f'{ts:%s}-{seq}'
  else:                             raise InvalidTypeE(f'Unknown timestamp {ts!r} type {type(ts)!r}.')

def istimestamp_id(s:str) -> bool:
  return isinstance(s, str) and re.search(r'^\d+-(\d+|\*)$', s) is not None

def isfloat(s:str) -> bool:
  match s:
    case float(): return True
    case bytes(): return s.count(b'.') == 1 and all(_.isdigit() for _ in s.split(b'.'))
    case str():   return s.count('.')  == 1 and all(_.isdigit() for _ in s.split('.'))
    case _:       return False

def parse_timestamp(tsin) -> datetime:
  weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  abbrev_weekdays = [day[:3] for day in weekdays]

  if isinstance(tsin, int | float):
      return datetime.fromtimestamp(float(tsin))
  elif isinstance(tsin, datetime):
    return tsin
  elif isinstance(tsin, list | tuple):
    return parse_timestamp(' '.join(tsin))
  elif isinstance(tsin, str):
    if len(tsin) == 0:
      raise InvalidTimeE(f'Invalid timestamp {tsin!r} supplied.')

    if tsin.count('.') > 1:
      raise InvalidTimeE(f'Invalid timestamp {tsin!r} supplied.')

    if tsin.isdigit():
      if len(tsin) < 10:
        raise InvalidTimeE(f'Unknown input value for timestamp {tsin!r}.')

      if len(tsin) >= 10:
        return parse_timestamp(float('.'.join([tsin[:10], tsin[10:]])))
    elif istimestamp_id(tsin):
      '''A redis stream id'''
      return parse_timestamp(tsin[:tsin.index('-')])
    elif tsin.count('.') == 1:
      ts, mils = tsin.split('.')
      if len(ts) > 10:
        raise InvalidTimeE(f'Invalid timestamp {tsin!r} supplied.')

      if ts.isdigit() and mils.isdigit():
        return parse_timestamp(float('.'.join([ts, mils])))
      else:
        raise InvalidTimeE(f'Invalid timestamp {tsin!r} supplied.')
    elif (dt_num := tsin.count(' ')) > 0:
      '''parse a datetime'''
      if dt_num > 3:
        raise InvalidTimeE(f'Unknown datetime format for input value {tsin!r}.')

      if dt_num == 3 and tsin.endswith('am') or tsin.endswith('pm'):
        return datetime.strptime(tsin, '%a %Y-%m-%d %H:%M:%S %p')
      elif dt_num == 2:
        if tsin.endswith('am') or tsin.endswith('pm'):
          return datetime.strptime(tsin, '%Y-%m-%d %H:%M:%S %p')
        elif tsin.endswith(' ago'):
          '''"parse" some time ago'''
          num_time, num_scale, ago = tsin.casefold().split(' ')

          if num_scale not in ['weeks', 'days', 'hours', 'minutes', 'seconds']:
            raise InvalidTypeE(f'Provided scale {num_scale!r} is invalid.')

          if not num_time.isdigit() or isfloat(num_time):
            raise InvalidTypeE(f'The provided time {num_time!r} is invalid.')

          return now() - timedelta(**{num_scale: int(num_time)})
        else:
          return datetime.strptime(tsin, '%a %Y-%m-%d %H:%M:%S')
      elif tsin.count(':') == 1:
        return datetime.strptime(tsin, '%Y-%m-%d %H:%M')
      elif tsin.count(':') == 2:
        return datetime.strptime(tsin, '%Y-%m-%d %H:%M:%S')
      else:
        raise InvalidTimeE(f'Invalid time {tsin!r} provided.')
    elif (dat_sep := tsin.count('-')) > 1:
      '''Do we have something that looks like a redis stream id or date?'''

      if dat_sep > 3:
        raise InvalidTimeE(f"Invalid data {tsin!r} supplied.")

      if dat_sep == 2:
        '''parse a date'''
        return datetime.strptime(tsin, '%Y-%m-%d')

    elif (hour_sep := tsin.count(':')) > 0:
      '''parse a time'''
      if hour_sep > 2:
        raise InvalidTimeE(f'Unknown datetime format for input value {tsin!r}.')
      elif hour_sep == 1:
        return datetime.strptime(f'{now():%F} {tsin}', '%Y-%m-%d %H:%M')
      elif hour_sep == 2:
        return datetime.strptime(f'{now():%F} {tsin}', '%Y-%m-%d %H:%M:%S')
    elif tsin.casefold() in weekdays:
      '''"parse" a weekday'''
      _now = now()
      current_dow = _now.weekday()
      if current_dow <= weekdays.index(tsin.casefold()):
        return _now - timedelta(days=7 - (weekdays.index(tsin.casefold()) - current_dow))
      else:
        return _now - timedelta(days=current_dow - weekdays.index(tsin.casefold()))
    elif tsin.casefold() in abbrev_weekdays:
      '''"parse" a weekday abbreviation'''
      _now = now()
      current_dow = _now.weekday()
      if current_dow <= abbrev_weekdays.index(tsin.casefold()):
        return _now - timedelta(days=7 - (abbrev_weekdays.index(tsin.casefold()) - current_dow))
      else:
        return _now - timedelta(days=current_dow - abbrev_weekdays.index(tsin.casefold()))

    else:
      match tsin.casefold().strip():
        case 'now':       return now()
        case 'today':     return datetime.strptime(f'{now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S')
        case 'yesterday': return datetime.strptime(f'{now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
        case _:
          raise InvalidTypeE(f'Unknown input type {type(tsin)} for timestamp {tsin!r}.')
  else:
    raise InvalidTypeE(f'Unknown input type {type(tsin)} for timestamp {tsin!r}.')

def explain_dates():
    msg = '''The system should know how to parse these custom pseudo-values and formats.

  In all these instances, case is ignored.
  Pseudo-values "understood" by the system.

  "now"                 This means right now, to include microseconds. It utilizes datetime.datetime.now(). The default value in most cases.
  "today"               Similar to now, however, it starts at Midnight local time.
  "yesterday"           Same as today, except yeterday

  weekdays              These are understood as the last occurance of the named weekday. So if today is Tuesday and you enter Wednesday, it will be interpreted as the previous Wednesday, approximately a week ago.
                        If you enter Monday, though, it will be understood as meaning yesterday (although at current time, not midnight like "today" and "yesterday" are).
                        examples: monday, Tuesday, Sunday, etc

  abbreviated weekdays: same as weekdays
                        examples: Thur, fri, etc

  x days ago:           Understood as midnight x days ago.  If today is Friday, then this means midnight on Monday of this week.
                        examples: "5 days ago".


  Formats "understood" by the system"
  uniz timestamp:              Standard unix time stamps, which may or may not include microseconds (which is necessary for the software to understand redis stream timestamp ids).
                               examples: 17095835400, 17102610000, 1710262561568, 1710478747033

  redis stream timestamps:     See https://redis.io/docs/data-types/streams/#entry-ids
                               examples: 17095835400-0, 17102610000-2, 1710262561568-0, 1710478747033-0

  See https://docs.python.org/3/library/datetime.html#datetime.datetime.strptime

  %Y-%m-%d %I:%M:%S %p         Datetime value with trailing am/pm
                               examples: "2024-03-14 11:54:02 pm"

  %Y-%m-%d %H:%M:%S            Datetime value with 24-hour clock
                               examples: "2024-03-14 23:54:02"

  %H:%M                        Time value. These are interpreted as today at the time specified, which means, if you're not careful, you could unintentionally enter a time in the future.
  %H:%M:%S                     examples: "10:31", "22:22", etc

  %Y-%m-%d                     Date value
                             examples: "2024-03-14"'''
    return msg

SECOND = 1.0
MINUTE = SECOND*60
HOUR   = MINUTE*60
DAY    = HOUR*24
WEEK   = DAY*7

from . import project
from . import gui
