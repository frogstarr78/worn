from __future__ import annotations
import sys
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re, io
from typing import *

def debug(*msgs) -> None:
  for m in msgs:
    print(m, file=sys.stderr)

def now():
  return datetime.now()

def isuuid(s:str) -> bool:
  if isinstance(s, UUID): return True
  elif isinstance(s, str): return re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s)
  elif isinstance(s, (tuple, list)) and len(s) == 1: return isuuid(s[0])
  else: return False

def istimestamp_id(s:str) -> bool:
  return isinstance(s, str) and re.search(r'^\d{10,13}-(\d+|\*)$', s)

def isfloat(s:str) -> bool:
  if isinstance(s, float): return True
  if isinstance(s, bytes): return s.count(b'.') == 1 and all(_.isdigit() for _ in s.split(b'.'))
  if isinstance(s, str):   return s.count('.')  == 1 and all(_.isdigit() for _ in s.split('.'))
  return False

def parse_timestamp(tsin):
  if isinstance(tsin, (int, float)):
    return datetime.fromtimestamp(tsin)
  elif isinstance(tsin, datetime):
    return tsin
  elif isinstance(tsin, list):
    return parse_timestamp(' '.join(tsin))
  elif isinstance(tsin, str):
    if '-' in tsin:
      '''Do we have something that looks like a redis stream id or date?'''

      if tsin.count('-') == 1:
        '''This is intended to extract the timestamp out of a redis stream id'''
        return parse_timestamp(tsin[:tsin.index('-')])
      else:
        try:
          return datetime.strptime(tsin, '%Y-%m-%d %H:%M:%S')
        except:
          return datetime.strptime(tsin, '%a %Y-%m-%d %H:%M:%S')

    elif tsin.count('.') > 1:
      raise Exception('Invalid timestamp {tsin!r} supplied.')

    elif len(tsin) >= 13:
      if '.' in tsin[:11]:
        '''Possible truncation happening here'''
        ts, mils = tsin.split('.')
        if ts.isdigit() and mils.isdigit():
          return parse_timestamp(float('.'.join([ts[:10], mils])))
        else:
          raise Exception(f'Invalid timestamp {tsin!r} supplied.')
      else:
        return parse_timestamp(float('.'.join([tsin[:10], f'{tsin[10:]:>06}'])))
    elif 10 <= len(tsin) < 13:
      return parse_timestamp(float('.'.join([tsin[:10], f'{tsin[10:]:>06}'])))
    else:
      raise Exception(f'Invalid timestamp {tsin!r} supplied.')
  else:
    raise Exception(f'Unknown input type {type(tsin)} for timestamp {tsin!r}.')

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
