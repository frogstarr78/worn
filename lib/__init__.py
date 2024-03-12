from __future__ import annotations
import sys
from uuid import uuid4, UUID
import redis
import argparse
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re
import io
from typing import *

def isuuid(s:str):
  if isinstance(s, UUID): return True
  elif isinstance(s, str): return re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s)
  elif isinstance(s, (tuple, list)) and len(s) == 1: return isuuid(s[0])
  else: return False

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

now = datetime.now

def istimestamp_id(s:str):
  return isinstance(s, str) and re.search(r'^\d{13}-(\d+|\*)$', s)

def parse_timestamp(tsin):
  if isinstance(tsin, (int, float)):
    return datetime.fromtimestamp(tsin)
  elif isinstance(tsin, datetime):
    return tsin
  elif isinstance(tsin, list):
    return parse_timestamp(' '.join(tsin))
  elif isinstance(tsin, str):
    if '-' in tsin:
      if len(time_parts := tsin.split('-')) == 2:
        tsin = time_parts[0]
      else:
        try:
          return datetime.strptime(tsin, '%Y-%m-%d %H:%M:%S')
        except:
          return datetime.strptime(tsin, '%a %Y-%m-%d %H:%M:%S')

    if len(tsin) >= 13:
      if '.' in tsin[:13]:
        return datetime.fromtimestamp(float(tsin[:13]))
      else:
        return datetime.fromtimestamp(float('.'.join([tsin[:10], tsin[10:13]])))
    elif len(tsin) > 10:
      _tsin = f'{tsin:0<13}'
      return datetime.fromtimestamp(float('.'.join([_tsin[:10], _tsin[10:13]])))
    else:
      raise Exception(f'Invalid timestamp {tsin!r} supplied.')
  else:
    raise Exception(f'Unknown input type {type(tsin)} for timestamp {tsin!r}.')

def _datetime(dtin:str) -> datetime:
  weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  abbrev_weekdays = [day[:3] for day in weekdays]
  if dtin.isdigit():
    return parse_timestamp(dtin)
  elif dtin.casefold() == 'now':
    return now()
  elif dtin.casefold() == 'today':
    return datetime.strptime(f'{now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S')
  elif dtin.casefold() == 'yesterday':
    return datetime.strptime(f'{now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
  elif dtin.casefold() in weekdays:
    current_dow = now().weekday()
    if current_dow <= weekdays.index(dtin.casefold()):
      return now() - timedelta(days=7 - (weekdays.index(dtin.casefold()) - current_dow))
    else:
      return now() - timedelta(days=current_dow - weekdays.index(dtin.casefold()))
  elif dtin.casefold() in abbrev_weekdays:
    current_dow = now().weekday()
    if current_dow <= abbrev_weekdays.index(dtin.casefold()):
      return now() - timedelta(days=7 - (abbrev_weekdays.index(dtin.casefold()) - current_dow))
    else:
      return now() - timedelta(days=current_dow - abbrev_weekdays.index(dtin.casefold()))
  elif ':' in dtin and len(hrs_mins := dtin.split(':')) == 2 and all(map(str.isdigit, hrs_mins)) and 0 <= int(hrs_mins[0]) < 24 and 0 <= int(hrs_mins[1]) < 60:
    return datetime.strptime(f'{now():%F} {hrs_mins[0]}:{hrs_mins[1]}', '%Y-%m-%d %H:%M')
  elif ':' in dtin and len(hrs_mins_secs := dtin.split(':')) == 3 and all(map(str.isdigit, hrs_mins_secs)) and 0 <= int(hrs_mins[0]) < 24 and 0 <= int(hrs_mins[1]) < 60 and 0 <= int(hrs_mins[2]) < 60:
    return datetime.strptime(f'{now():%F} {hrs_mins_secs[0]}:{hrs_mins_secs[1]}:{hrs_mins_secs[2]}', '%Y-%m-%d %H:%M:%S')
  else:
    if ' ' in dtin:
      if dtin.casefold().endswith('am') or dtin.casefold().endswith('pm'):
        return datetime.strptime(dtin, '%Y-%m-%d %I:%M:%S %p')
      else:
        return datetime.strptime(dtin, '%Y-%m-%d %H:%M:%S')
    else:
      return datetime.strptime(dtin, '%Y-%m-%d')

def email(s):
  if '@' not in s:
    raise TypeError("Invalid email address.")

  if '.' not in s.split('@')[1]:
    raise TypeError("Invalid email address.")

  if len(s.split('@')) > 2:
    raise TypeError("Invalid email address.")

  return str(s)

def parse_args() -> argparse.Namespace:
  p = argparse.ArgumentParser(description='Working on Right Now', formatter_class=argparse.ArgumentDefaultsHelpFormatter, allow_abbrev=True)
  sub = p.add_subparsers(help='Various sub-commands')
  ui = sub.add_parser('gui', help='Show the gui')
  ui.set_defaults(action='gui')

  beg = sub.add_parser('start', help='Start a project')
  beg.add_argument('-a', '--at', type=_datetime, default=now(), metavar='DATETIME',  help='...the project at this specific time')
  beg.add_argument('project',    nargs='+',     metavar='NAME|UUID',                 help='Project name or uuid.')
  beg.set_defaults(action='start')

  end = sub.add_parser('stop', help='Stop a project')
  end.add_argument('-a', '--at',      type=_datetime, metavar='DATETIME',  default=now(),  help='...the project at this specific time')
  end.add_argument('-p', '--project', nargs='+',      metavar='NAME|UUID', default='last', help='Project name or uuid (or the last project if none provided).')
  end.set_defaults(action='stop')

  ren = sub.add_parser('rename', help='Rename a project')
  ren.add_argument('project',    nargs='+', metavar='NAME|UUID',                help='Old project name or uuid.')
  ren.add_argument('-t', '--to', nargs='+', metavar='NAME',      required=True, help='New project name.')
  ren.set_defaults(action='rename')

  rm = sub.add_parser('rm', help='Remove a project')
  rm.add_argument('project', nargs='+', metavar='NAME|UUID', help='Project name or uuid.')
  rm.set_defaults(action='rm')

  edit = sub.add_parser('edit', help='Change the recorded time of a log entry.')
  edit.add_argument('at', type=_datetime, metavar='TIMESTAMP_ID|DATETIME', help='The original log entry time to change.')
  edit.add_argument('to', type=_datetime, metavar='DATETIME',              help='The updated time to set.')
  edit.add_argument('reason', type=str, nargs='+', metavar='REASON',       help='Reason for the change in time.')
  edit.set_defaults(action='edit')

  pstat = sub.add_parser('stat', help='Show the last status.')
  pstat.set_defaults(action='show_last')

  show = sub.add_parser('show', help='Show some aspect of the system')
  showsub = show.add_subparsers()

  shl = showsub.add_parser('last', help='Show the last status.')
  shl.set_defaults(action='show_last')

  shp = showsub.add_parser('projects', help='Show the available projects.')
  shp.set_defaults(action='show_projects')

  sho = showsub.add_parser('logs',     help='Show the project logs.')
  sho.add_argument('-p', '--project',                       nargs='+', metavar='NAME|UUID', default=None, help='Project name or uuid.')
  sho.add_argument('-s', '--since',         type=_datetime,            metavar='DATETIME',  default=None, help='Report details since this datetime.')
  sho.add_argument('-t', '--timestamp',     action='store_true',                            default=False, help='Show the timestamp also (default: False).')
  sho.set_defaults(action='show_logs')

  shi = showsub.add_parser('id',       help='Show the project name from the provided id.')
  shi.add_argument('project', type=UUID, metavar='UUID')
  shi.set_defaults(action='show_id')

  rep = sub.add_parser('report', help='Report the results of work done')
  rep.add_argument('-l', '--largest_scale', type=str,       choices='w,d,h,m,s'.split(','),                                    default='h',                            help='The largest component of time to display (default: "h"): w => Weeks; d => Days; h => Hours; m => Minutes; s => Seconds.')
  rep.add_argument('-f', '--format',        type=str,       choices='simple,csv,time'.split(','),                              default='simple',                       help='Output the report in this format (default: simple).')
  rep.add_argument('-c', '--comment',       type=str,        nargs='+',                                                        default='Time spent on {project.name}', help='Comment to make in tickets when reporting to a ticket (default: "Time spent on {project.name}").')
  rep.add_argument('-N', '--no_header',     action='store_true',                                                               default=False,                          help="Don't display the header in the output (default: False).")
  rep.add_argument('-C', '--no_color',      action='store_false',                                                              default=True,                           help="Don't include color in the output.")
  prep = rep.add_mutually_exclusive_group(required=False)
  prep.add_argument('-p', '--project',                       nargs='+',                      metavar='NAME|UUID',                                                      help='Project name or uuid.')
  prep.add_argument('-a', '--include_all',                   action='store_true',                                              default=False,                          help='Display ALL projects including those without any tracked time.')
  trep = rep.add_mutually_exclusive_group(required=False)
  trep.add_argument('-s', '--since',         type=_datetime,                                 metavar='DATETIME',                                                       help='Report details since this datetime.')
  trep.add_argument('-b', '--between',       type=_datetime, nargs=2,                        metavar=('DATETIME', 'DATETIME'),                                         help='Report details between these date and times.')
  rrep = rep.add_mutually_exclusive_group(required=False)
  rrep.add_argument('-t', '--ticket',       type=int,                                                                          default=None,                           help='Document the report to this ticket.')
  rrep.add_argument('-m', '--mailto',       type=email,                                                                        default=None,                           help='Email the report to this user.')
  rep.set_defaults(action='report')

  hlp = sub.add_parser('help', help='show this help message and exit')
  hlp.set_defaults(action='help')

  p.set_defaults(project=[], action='help')

  r = p.parse_args()
  if r.project is not None and isinstance(r.project, list) and len(r.project) > 0:
    r.project = ' '.join(r.project).strip().replace('\n', ' ')

  if not isinstance(r.project, UUID) and isuuid(r.project):
    r.project = UUID(r.project)
  debug(r)

  if r.action == 'help':
    p.print_help()
    sys.exit(0)
  return r

from . import project
from . import colors
from . import gui
