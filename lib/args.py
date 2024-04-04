import lib
import sys
from uuid import uuid4, UUID
from lib import debug, isuuid, istimestamp_id, parse_timestamp, SECOND, MINUTE, HOUR, DAY, WEEK
import argparse
from lib.project import Project
from datetime import datetime, timedelta

def email(s):
  if '@' not in s:
    raise TypeError("Invalid email address.")

  if '.' not in s.split('@')[1]:
    raise TypeError("Invalid email address.")

  if len(s.split('@')) > 2:
    raise TypeError("Invalid email address.")

  return str(s)

def _datetime(dtin:str | datetime) -> datetime:
  weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  abbrev_weekdays = [day[:3] for day in weekdays]
  if not isinstance(dtin, (datetime, str)):
    raise Exception(f'Input value {dtin!r} is unknown type {type(dtin)}.')

  if isinstance(dtin, datetime):
    return dtin

  dtin = dtin.strip().casefold()
  match dtin:
    case 'last':      return Project.make('last').when
    case 'now':       return lib.now()
    case 'today':     return datetime.strptime(f'{lib.now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S')
    case 'yesterday': return datetime.strptime(f'{lib.now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
    case _ if dtin.isdigit() or istimestamp_id(dtin):
      '''"parse" a timestamp or redis stream id'''
      return parse_timestamp(dtin)
    case _ if dtin.endswith('days ago'):
      '''"parse" a "yesterday"'''
      num_days = int(dtin.split(' ')[0])
      return datetime.strptime(f'{lib.now():%F} 00:00:00', '%Y-%m-%d %H:%M:%S') - timedelta(days=num_days)
    case _ if dtin in weekdays:
      '''"parse" a weekday'''
      _now = lib.now()
      current_dow = _now.weekday()
      if current_dow <= weekdays.index(dtin.casefold()):
        return _now - timedelta(days=7 - (weekdays.index(dtin.casefold()) - current_dow))
      else:
        return _now - timedelta(days=current_dow - weekdays.index(dtin.casefold()))
    case _ if dtin in abbrev_weekdays:
      '''"parse" a weekday abbreviation'''
      _now = lib.now()
      current_dow = _now.weekday()
      if current_dow <= abbrev_weekdays.index(dtin.casefold()):
        return _now - timedelta(days=7 - (abbrev_weekdays.index(dtin.casefold()) - current_dow))
      else:
        return _now - timedelta(days=current_dow - abbrev_weekdays.index(dtin.casefold()))
    case _ if dtin.count(' ') > 0:
      '''parse a datetime'''
      if dtin.count(' ') > 2 or dtin.count(':') not in (1, 2):
        raise Exception(f'Unknown datetime format for input value {dtin!r}.')

      if dtin.endswith('am') or dtin.endswith('pm'):
        return datetime.strptime(dtin, '%Y-%m-%d %I:%M:%S %p')
      elif dtin.count(':') == 1:
        return datetime.strptime(dtin, '%Y-%m-%d %H:%M')
      elif dtin.count(':') == 2:
        return datetime.strptime(dtin, '%Y-%m-%d %H:%M:%S')
    case _ if (num_sep := dtin.count(':')) > 0:
      '''parse a time'''
      if num_sep > 2:
        raise Exception(f'Unknown datetime format for input value {dtin!r}.')

      if num_sep == 1:
        return datetime.strptime(f'{lib.now():%F} {dtin}', '%Y-%m-%d %H:%M')
      elif num_sep == 2:
        return datetime.strptime(f'{lib.now():%F} {dtin}', '%Y-%m-%d %H:%M:%S')
    case _:
      '''parse a date'''
      return datetime.strptime(dtin, '%Y-%m-%d')

def parse_args(argv=sys.argv[1:]) -> argparse.Namespace:
  from .colors import colors
  p = argparse.ArgumentParser(description=f'{colors.underline}W{colors.reset}orking {colors.underline}o{colors.reset}n {colors.underline}R{colors.reset}ight {colors.underline}N{colors.reset}ow', formatter_class=argparse.ArgumentDefaultsHelpFormatter, allow_abbrev=True)

  sub = p.add_subparsers(required=True, title='commands', dest='action', help='Various sub-commands')
  p.add_argument('-C', '--no_color', action='store_true', default=False, help="Don't include color in the output.")
  ui = sub.add_parser('gui', help='Show the gui', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  beg = sub.add_parser('start', help='Start a project', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  beg.add_argument('-a', '--at', type=_datetime, default=lib.now(), metavar='DATETIME',  help='...the project at this specific time')
  beg.add_argument('project',    nargs='+',     metavar='NAME|UUID',                 help='Project name or uuid.')

  end = sub.add_parser('stop', help='Stop a project', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  end.add_argument('-a', '--at',      type=_datetime, metavar='DATETIME',  default=lib.now(),  help='...the project at this specific time')
  end.add_argument('-p', '--project', nargs='+',      metavar='NAME|UUID', default='last', help='Project name or uuid (or the last project if none provided).')

  ren = sub.add_parser('rename', help='Rename a project', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  ren.add_argument('project',    nargs='+', metavar='NAME|UUID',                help='Old project name or uuid.')
  ren.add_argument('-t', '--to', nargs='+', metavar='NAME',      required=True, help='New project name.')

  rm = sub.add_parser('rm', help='Remove a project', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  rm.add_argument('project', nargs='+', metavar='NAME|UUID', help='Project name or uuid.')

  edit = sub.add_parser('edit', help='Change the recorded time of a log entry.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  edit.add_argument('at', type=_datetime, metavar='LAST|TIMESTAMP_ID|DATETIME',     help='The original log entry time to change.')
  edit.add_argument('-s', '--state',   type=str, choices=('started', 'stopped'),    help='Change the log entry to this state.')
  edit.add_argument('-p', '--project', type=str,                                    help='Change the log entry to this project.')
  edit.add_argument('-t', '--to',      type=_datetime,      metavar='DATETIME',     help='The updated time to set.')
  edit.add_argument('-r', '--reason',  type=str, nargs='+', metavar='REASON',       help='Reason for the change in time.')

  pstat = sub.add_parser('stat', help='Show the last status.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  show = sub.add_parser('show',  help='Show some aspect of the system', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  showsub = show.add_subparsers(dest='display', required=False)

  shas = showsub.add_parser('last',     help='Show the last status.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  shor = showsub.add_parser('projects', help='Show the available projects.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  shol = showsub.add_parser('logs',     help='Show the project logs.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  shol.add_argument('-p', '--project',                       nargs='+', metavar='NAME|UUID', default=None, help='Project name or uuid.')
  shol.add_argument('-s', '--since',         type=_datetime,            metavar='DATETIME',  default=None, help='Report details since this datetime.')
  shol.add_argument('-t', '--timestamp',     action='store_true',                            default=False, help='Show the timestamp also.')

  shid = showsub.add_parser('id', help='Show the project name from the provided id.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  shid.add_argument('UUID', nargs='+', type=UUID, help='UUID(s) to display the project names of.')

  rep = sub.add_parser('report', help='Report the results of work done', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  rep.add_argument('-l', '--largest_scale', type=str,       choices='w,d,h,m,s'.split(','),                                    default='h',                            help='The largest component of time to display: w => Weeks; d => Days; h => Hours; m => Minutes; s => Seconds.')
  rep.add_argument('-f', '--format',        type=str,       choices='simple,csv,time'.split(','),                              default='simple',                       help='Output the report in this format.')
  rep.add_argument('-c', '--comment',       type=str,        nargs='+',                                                        default='Time spent on {project.name}', help='Comment to make in tickets when reporting to a ticket.')
  rep.add_argument('-H', '--no_header',     action='store_true',                                                               default=False,                          help="Don't display the header in the output.")
  rep.add_argument('-N', '--NOOP'     ,     action='store_true',                                                               default=False,                          help="Don't include color in the output.")

  prep = rep.add_mutually_exclusive_group(required=False)
  prep.add_argument('-p', '--project',                       nargs='+',                      metavar='NAME|UUID',                                                      help='Project name or uuid.')
  prep.add_argument('-a', '--include_all',                   action='store_true',                                              default=False,                          help='Display ALL projects including those without any tracked time.')

  trep = rep.add_mutually_exclusive_group(required=False)
  trep.add_argument('-s', '--since',        type=_datetime,                                 metavar='DATETIME',                                                       help='Report details since this datetime.')
#  trep.add_argument('-b', '--between',      type=_datetime, nargs=2,                        metavar=('DATETIME', 'DATETIME'),                                         help='Report details between these date and times.')

  rrep = rep.add_mutually_exclusive_group(required=False)
  rrep.add_argument('-t', '--ticket',       type=int,                                                                          default=None,                           help='Document the report to this ticket.')
  rrep.add_argument('-m', '--mailto',       type=email,                                                                        default=None,                           help='Email the report to this user.')

  hlp = sub.add_parser('help',     help='show this or other help items and exit.')
  hlpsub = hlp.add_subparsers(dest='kind', title='subcommands', required=False)
  hld = hlpsub.add_parser('dates', help='Display and explain the avilable date formats that can be used by the program.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  p.set_defaults(project=[], display=None, kind=None, comment=None, action='help')

  r = p.parse_args(argv)
  if r.project is not None and isinstance(r.project, list) and len(r.project) > 0 and all(isinstance(p, str) for p in r.project):
    r.project = ' '.join(r.project).strip().replace('\n', ' ')

  if not isinstance(r.project, UUID) and isuuid(r.project):
    r.project = UUID(r.project)

  if isinstance(r.comment, list):
    r.comment = ' '.join(r.comment).strip()
  debug(r)

  return (p, show, edit, rep, r)
