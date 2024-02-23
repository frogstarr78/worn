#!/usr/bin/python3

import sys
from tkinter import *
from tkinter import ttk
from uuid import uuid4, UUID
import redis
import argparse
import datetime
import functools
from urllib.parse import urlparse
from typing import *
import re

def db(cmd, key='', *args, **kw):
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hasattr(conn, cmd.casefold()) and callable(f := getattr(conn, cmd.casefold())):
      if cmd in ['save', 'bgsave', 'ping']:
        return f()
      else:
        return f(key, *args, **kw)
    else:
      return None
now = datetime.datetime.now
fromtimestamp = datetime.datetime.fromtimestamp

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

def isuuid(s:str):
  return re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s)

def gui_action(action:str, project:StringVar='') -> None:
  project_id, project_name = load_project(project.get())
  if 'Start' in action:
    start_project(project_id)
  elif action == 'Stop':
    stop_project(project_id)
  else:
    debug(f"Unknown action {action!r}")

def gui() -> None:
  root = Tk()
  root.title('Worn')

  proj = StringVar()

  frm = ttk.LabelFrame(root, text='Project', underline=0, padding=11)
  frm.grid()

  _projects = [project for (pid, project) in all_projects().items()]
  c = ttk.Combobox(frm, values=_projects, textvariable=proj, width=len(max(_projects, key=len))-10)
  last_id, last_name, last_state, last_when = last_project()
  debug(last_name)
  if last_state == 'started':
    c.set(last_name)
  c.grid(row=0, column=0, pady=7, columnspan=3)

  s = ttk.Button(frm, text="(Re-)Start", underline=5)
  s.bind('<ButtonPress>',    lambda e: gui_action(s['text'], proj))
  s.bind('<KeyPress-space>', lambda e: gui_action(s['text'], proj))

  t = ttk.Button(frm, text="Stop", underline=1)
  t.bind('<ButtonPress>',    lambda e: gui_action(t['text'], proj))
  t.bind('<KeyPress-space>', lambda e: gui_action(t['text'], proj))

  c = ttk.Button(frm, text="Quit", underline=0, command=root.destroy)

  s.grid(row=1, column=0)
  t.grid(row=1, column=1)
  c.grid(row=1, column=2)

  root.bind('<Alt-p>', lambda *e: c.focus_set())
  root.bind('<Alt-s>', lambda *e: s.focus_set())
  root.bind('<Alt-t>', lambda *e: t.focus_set())
  root.bind('<Alt-q>', lambda *e: root.destroy())

#  root.columnconfigure(2, weight=2)
#  root.rowconfigure(0, weight=2)
#  frm.columnconfigure(0, weight=2)
#  frm.rowconfigure(0, weight=2)

  root.mainloop()

def db_exists(cmd, key, *rest):
  if not db('exists', key):
    raise Exception(f"Key {key!r} doesn't exist")

  return db(cmd, key, *rest)

def log(id, project, state, at=now()):
  _ts = str(at.timestamp()).replace('.', '')[:13]
  db('hsetnx', 'projects', str(id), project)
  db('hsetnx', 'projects', project.casefold(), str(id))
  db('xadd', 'logs', dict(project=str(id), action=state), id=f'{_ts:0<13}-*')
  db('hset', 'last', mapping=dict(action=state, project=str(id), when=_ts))
  db('save')

@functools.cache
def load_project(project:Union[None, str, UUID]) -> Tuple[UUID, str]:
  if project is None:
    debug(f"Project {project!r} was empty.")
    return (None, None)
  elif isinstance(project, Sequence) and len(project) == 0:
    debug(f"Project {project!r} was empty.")
    return (None, None)

  if isinstance(project, UUID):
    if db_exists('hexists', 'projects', str(project)):
      return (project, db('hget', 'projects', str(project)))
  elif isinstance(project, str):
    if isuuid(project) and db_exists('hexists', 'projects', project):
      return (UUID(project), db('hget', 'projects', project))
    elif db_exists('hexists', 'projects', project.casefold()):
      return (UUID(db('hget', 'projects', project.casefold())), project)
    elif project.casefold() == 'last':
      last_id, last_name, last_state, last_when = last_project()
      return (last_id, last_name)
    else:
      id = uuid4()
      db('hsetnx', 'projects', project.casefold(), str(id))
      db('hsetnx', 'projects', str(id), project)
      return (id, project)
  else:
    debug(f'Unable to find or create a new project {project} of type {type(project)}.')
    raise Exception(f'Unable to find or create a new project {project} of type {type(project)}.')

@functools.cache
def last_project() -> tuple[UUID, str, str, datetime.datetime]:
  if not db('exists', 'last'):
    raise Exception('No previous projects logged')

  r = db('hgetall', 'last')
  last_id = UUID(r.get('project'))
  last_name = db('hget', 'projects', str(last_id))
  last_state = r.get('action')
  if (last_when := r.get('when')).isdigit():
    last_when = datetime.datetime.fromtimestamp(float('.'.join([last_when[:10], last_when[10:13]])))
  else:
    last_when = datetime.datetime.strptime(last_when, '%Y-%m-%d %H:%M:%S')

  return (last_id, last_name, last_state, last_when)

def start_project(project:Union[str, UUID, None], at:datetime=now()) -> None:
  project_id, project_name = load_project(project)
  if db('exists', 'last'):
    last_id, last_name, last_state, last_when = last_project()
    if last_state == 'started':
      stop_project(last_id, at=at)
  log(project_id, project_name, 'started', at)

def stop_project(project:Union[str, UUID, None], at:datetime=now()) -> None:
  last_id, last_name, last_state, last_when = last_project()
  current_project_id, current_project_name = load_project(project)

  if current_project_id is None or current_project_name is None:
    log(last_id, last_name, 'stopped', at)
  elif project == 'last':
    log(last_id, last_name, 'stopped', at)
  elif last_id != current_project_id:
    debug(f"The previous project {last_name!r} was not the same project specified.")
  elif last_state != 'started':
    debug(f"The previous project {last_name!r} has not started.")
  else:
    log(current_project_id, current_project_name, 'stopped', at)

def rename(old:Union[str, UUID], new:str) -> None:
  id, old_project = load_project(old)
  db('hset', 'projects', str(id), new)
  db('hset', 'projects', new.casefold(), str(id))
  db('save')

def remove(project:Union[UUID, str]) -> None:
  project_id, project_name = load_project(project)
  for timeid, log in db('xrange', 'logs', '-', '+'):
    if UUID(log.get('project')) == project_id:
      db('xdel', 'logs', timeid)

  db('hdel', 'projects', project_name)
  db('hdel', 'projects', str(project_id))
  db('save')

@functools.cache
def all_projects() -> dict[UUID, str]:
  return dict([(UUID(pid), project) for pid, project in sorted(db('hgetall', 'projects').items(), key=lambda kv: kv[1].casefold()) if isuuid(pid)])

def stream_time(stream_id:str) -> str:
  unix_time_mills, seq = stream_id.split('-')
  timestamp_mills = float('.'.join([unix_time_mills[:10], unix_time_mills[10:]]))
  return fromtimestamp(timestamp_mills).isoformat(' ', timespec='seconds')

def weeks_long(ts:int) -> int:
  return int(ts/(3600*24*7))

def days_long(ts:int) -> int:
  return int(ts/(3600*24))

def hours_long(ts:int) -> int:
  return int(ts/3600)

def minutes_long(ts:int) -> int:
  return int(ts%3600/60)

def seconds_long(ts:int) -> int:
  return int(ts%60)

def csv_format(stats:dict[str, str], at:Union[datetime.datetime, None]=None, largest_scale:str='h', still_running:Union[UUID, None]=None, include_all:bool=False) -> None:
  print('Time spent report')
  if largest_scale == 'w':   print('weeks,days,hours,minutes,seconds', end=',')
  elif largest_scale == 'd': print('days,hours,minutes,seconds', end=',')
  elif largest_scale == 'h': print('hours,minutes,seconds', end=',')
  elif largest_scale == 'm': print('minutes,seconds', end=',')
  elif largest_scale == 's': print('seconds', end=',')

  print('total,id,project,running', end='')
  if isinstance(at, datetime.datetime):
    print(',since')
  else:
    print('')

  for pid, total in stats.items():
    if total == 0 and not include_all:
      continue

    if largest_scale == 'w':
      print(f'{weeks_long(total):02}',   end=',')
      print(f'{days_long(total):02}',    end=',')
      print(f'{hours_long(total):02}',   end=',')
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 'd':
      print(f'{days_long(total):03}',    end=',')
      print(f'{hours_long(total):02}',   end=',')
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 'h':
      print(f'{hours_long(total):03}',   end=',')
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 'm':
      print(f'{minutes_long(total):03}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 's':
      print(total, end=',')
    else:
      print(total,                       end=',')

    print(pid,                         end=',')
    print('"{0}"'.format(db('hget', 'projects', pid)), end=',')
    if isinstance(still_running, UUID) and still_running == UUID(pid):
      print('true', end='')
    else:
      print('false', end='')

    if isinstance(at, datetime.datetime):
      print(f',{at.strftime("%a %F %T")}')
    else:
      print('')

def text_format(stats:dict[str, str], at:Union[datetime.datetime, None]=None, largest_scale:str='h', still_running:Union[UUID, None]=None, include_all:bool=False) -> None:
  print('Time spent report', end='')
  if isinstance(at, datetime.datetime):
    print(f' since: {at.strftime("%a %F %T")}')
  else:
    print(f':')

  for pid, total in stats.items():
    if total == 0 and not include_all:
      continue

    if largest_scale == 'w':
      print(f'{weeks_long(total):02}w', end='')
      print(f' {days_long(total):02}d', end='')
      print(f' {hours_long(total):02}h', end='')
      print(f' {minutes_long(total):02}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 'd':
      print(f'{days_long(total):03}d', end='')
      print(f' {hours_long(total):02}h', end='')
      print(f' {minutes_long(total):02}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 'h':
      print(f'{hours_long(total):03}h', end='')
      print(f' {minutes_long(total):02}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 'm':
      print(f'{minutes_long(total):03}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 's':
      print(f'{total: >8}s', end='')
    else:
      print(f' total {total: >8}', end='')

    print(f' id {pid}', end='')
    print(f" project {db('hget', 'projects', pid)!r}", end='')
    if isinstance(still_running, UUID) and still_running == UUID(pid):
      print('...and counting')
    else:
      print('')

def get_stats(project:Union[str, UUID, None]=None, at:Union[datetime.datetime, None]=None) -> dict[str, float]:
  stats = {}
  accum = {}
  for tid, log in db('xrange', 'logs', '-', '+'):
    proj = log.get('project')
    actn = log.get('action')
    _time = int(tid[:10])
    if project is not None and len(str(project)) > 0:
      project_id, project_name = load_project(project)
      if str(project_id) != proj:
        continue

    if isinstance(at, datetime.datetime) and _time <= at.timestamp():
      continue

    stats.setdefault(proj, 0)
    if actn == 'started':
      accum = {proj: _time}
    elif actn == 'stopped':
      stats[proj] += _time-accum[proj]
      accum = {}

  last_id, last_name, last_state, last_when = last_project()
  if last_state == 'started':
    stats[str(last_id)] += int(now().timestamp()-last_when.timestamp())

  if project is None:
    for project_id in db('hkeys', 'projects'):
      if isuuid(project_id):
        stats.setdefault(project_id, 0)

  return stats

def report(args:argparse.Namespace) -> None:
  if args.since:
    when = args.since
  elif args.between:
    when = args.between
  else:
    when = None

  stats = get_stats(args.project, when)
  is_running = None
  last_id, last_name, last_state, last_when = last_project()
  if last_state == 'started':
    is_running = last_id

  if args.format == 'text':
    text_format(stats, when, args.largest_scale, is_running, args.include_all)
  elif args.format == 'csv':
    csv_format( stats, when, args.largest_scale, is_running, args.include_all)

def _datetime(dtin:str) -> datetime.datetime:
  weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  abbrev_weekdays = [day[:3] for day in weekdays]
  if dtin.isdigit():
    return datetime.datetime.fromtimestamp(int(dtin))
  elif dtin == 'today':
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S')
  elif dtin == 'yesterday':
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)
  elif dtin.casefold() in weekdays:
    current_dow = now().weekday()
    if current_dow <= weekdays.index(dtin): 
      return now() - datetime.timedelta(days=7 - (weekdays.index(dtin) - current_dow))
    else:
      return now() - datetime.timedelta(days=current_dow - weekdays.index(dtin))
  elif dtin.casefold() in abbrev_weekdays:
    current_dow = now().weekday()
    if current_dow <= abbrev_weekdays.index(dtin): 
      return now() - datetime.timedelta(days=7 - (abbrev_weekdays.index(dtin) - current_dow))
    else:
      return now() - datetime.timedelta(days=current_dow - abbrev_weekdays.index(dtin))
  elif ':' in dtin and len(hrs_mins := dtin.split(':')) == 2 and all(map(str.isdigit, hrs_mins)) and 0 <= int(hrs_mins[0]) < 24 and 0 <= int(hrs_mins[1]) < 60:
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} {hrs_mins[0]}:{hrs_mins[1]}', '%Y-%m-%d %H:%M')
  elif ':' in dtin and len(hrs_mins_secs := dtin.split(':')) == 3 and all(map(str.isdigit, hrs_mins_secs)) and 0 <= int(hrs_mins[0]) < 24 and 0 <= int(hrs_mins[1]) < 60 and 0 <= int(hrs_mins[2]) < 60:
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} {hrs_mins_secs[0]}:{hrs_mins_secs[1]}:{hrs_mins_secs[2]}', '%Y-%m-%d %H:%M:%S')
  else:
    if ' ' in dtin:
      if dtin.casefold().endswith('am') or dtin.casefold().endswith('pm'):
        return datetime.datetime.strptime(dtin, '%Y-%m-%d %I:%M:%S %p')
      else:
        return datetime.datetime.strptime(dtin, '%Y-%m-%d %H:%M:%S')
    else:
      return datetime.datetime.strptime(dtin, '%Y-%m-%d')

def email(s):
  if '@' not in s:
    raise TypeError("Invalid email address.")

  if '.' not in s.split('@')[1]:
    raise TypeError("Invalid email address.")

  if len(s.split('@')) > 2:
    raise TypeError("Invalid email address.")

  return str(s)

def pargs() -> argparse.Namespace:
  p = argparse.ArgumentParser(description='Working on Right Now')
  sub = p.add_subparsers(help='Various sub-commands')
  ui = sub.add_parser('gui', help='Show the gui')
  ui.set_defaults(action='gui')

  beg = sub.add_parser('start', help='Start a project')
  beg.add_argument('-a', '--at', type=_datetime, default=now(), metavar='DATETIME',  help='...the project at this specific time')
  beg.add_argument('project',    nargs='+',     metavar='NAME|UUID', help='Project name or uuid.')
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

  show = sub.add_parser('show', help='Modify the metadata')
  showsub = show.add_subparsers()
  shl = showsub.add_parser('last', help='Show the last project worked on and what we last did.')
  shl.set_defaults(action='show_last')

  shp = showsub.add_parser('projects', help='Show the available projects.')
  shp.set_defaults(action='show_projects')

  sho = showsub.add_parser('logs',     help='Show the project logs.')
  sho.add_argument('-p', '--project',                       nargs='+', metavar='NAME|UUID', default=None, help='Project name or uuid.')
  sho.add_argument('-s', '--since',         type=_datetime,            metavar='DATETIME',  default=None, help='Report details since this datetime.')
  sho.set_defaults(action='show_logs')

  shi = showsub.add_parser('id',       help='Show the project name from the provided id.')
  shi.add_argument('project', metavar='UUID')
  shi.set_defaults(action='show_id')

  rep = sub.add_parser('report', help='Report the results of work done')
  rep.add_argument('-p', '--project',                       nargs='+',                      metavar='NAME|UUID',                               help='Project name or uuid.')
  rep.add_argument('-s', '--since',         type=_datetime,                                 metavar='DATETIME',                                help='Report details since this datetime.')
  rep.add_argument('-b', '--between',       type=_datetime, nargs=2,                        metavar=('DATETIME', 'DATETIME'),                  help='Report details between these date and times.')
  rep.add_argument('-l', '--largest_scale', type=str,       choices='w,d,h,m,s'.split(','),                                    default='h',    help='The largest component of time to display (default: "h"): w => Weeks; d => Days; h => Hours; m => Minutes; s => Seconds.')
  rep.add_argument('-f', '--format',        type=str,       choices='text,csv'.split(','),                                     default='text', help='Output the report in this format (default: text).')
  rep.add_argument('-u', '--url',           type=urlparse,                                                                                     help='Document the report to this url.')
  rep.add_argument('-m', '--mailto',        type=email,                                                                                        help='Email the report to this user.')
  rep.add_argument('-a', '--include_all',                   action='store_true',                                               default=False,  help='Display ALL projects including those without any tracked time.')
  rep.set_defaults(action='report')

  hlp = sub.add_parser('help', help='Display help')
  hlp.set_defaults(action='help')

  p.set_defaults(project=[], action='help')

  r = p.parse_args()
  if r.project is not None and len(r.project) > 0 and isinstance(r.project, list):
    r.project = ' '.join(r.project).strip().replace('\n', ' ')

  if isinstance(r.project, str) and re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', r.project):
    r.project = UUID(r.project)
  debug(r)
  return r

def main() -> None:
  p = pargs()
  if p.action == 'show_id':
    print(db('hget', 'projects', str(id)))
  elif p.action == 'show_last':
    print('Last project: {last[1]!r}; action: {last[2]!r}; at: {last[3]}.'.format(last=last_project()))
  elif p.action == 'show_projects':
    for pid, project in all_projects().items():
      print(f'{pid}: {project}')
  elif p.action == 'show_logs':
    for tid, log in db('xrange', 'logs', '-', '+'):
      log_id, log_project = load_project(log.get('project'))
      if project is None or log_id == project:
        print(f"{stream_time(tid)} action {log.get('action')!r} project {log_project!r}")
  elif p.action == 'start':
    start_project(p.project, p.at)
  elif p.action == 'stop':
    stop_project(p.project, p.at)
  elif p.action == 'rename':
    rename(p.project, ' '.join(p.to).strip().replace('\n', ' '))
  elif p.action == 'rm':
    remove(p.project)
  elif p.action == 'gui':
    gui()
  elif p.action == 'help':
    p.print_help()
  elif p.action == 'report':
    report(p)

if __name__ == '__main__':
  main()
