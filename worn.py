#!/usr/bin/python3

import sys
from tkinter import *
from tkinter import ttk
from uuid import uuid4, UUID
import redis
import argparse
import datetime
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

class Project(object):
  def __init__(self, id:UUID, name:str, state:str='stopped'):
    self.id = id
    self.name = name
    self.state = state

  @classmethod
  def make(gaudy, thing) -> object:
    id, project = None, None
    try:
      id, project = UUID(thing), db('hget', 'projects', str(id))
    except ValueError:
      id, project = UUID(db('hget', 'ids', thing.casefold())), thing
    finally:
      return Project(id, project)

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

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

  _projects = sorted(db('hvals', 'projects'), key=str.casefold)
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
  db('hsetnx', 'ids', project.casefold(), str(id))
  db('xadd', 'logs', dict(project=str(id), action=state), id=f'{_ts}-*')
  db('hset', 'last', mapping=dict(action=state, project=str(id), when=_ts))
  db('save')

def load_project(project:Union[None, str, UUID]) -> Tuple[UUID, str]:
  if project is None:
    debug(f"Project {project!r} was empty.")
    return (None, None)
  elif isinstance(project, Sequence) and len(project) == 0:
    debug(f"Project {project!r} was empty.")
    return (None, None)

#  debug(f'project {project!r} type {type(project)} {isinstance(project, UUID)}')
  if isinstance(project, UUID):
    if db_exists('hexists', 'projects', str(project)):
      return (project, db('hget', 'projects', str(project)))
  elif isinstance(project, str):
    if re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', project) and db_exists('hexists', 'projects', project):
      return (UUID(project), db('hget', 'projects', project))
    elif db_exists('hexists', 'ids', project.casefold()):
      return (UUID(db('hget', 'ids', project.casefold())), project)
    else:
      id = uuid4()
      db('hsetnx', 'ids', project.casefold(), str(id))
      return (id, project)
  else:
    debug(f'Unable to find or create a new project {project} of type {type(project)}.')
    raise Exception(f'Unable to find or create a new project {project} of type {type(project)}.')

def last_project() -> tuple:
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

def remove(project:Union[UUID, str]) -> None:
  project_id, project_name = load_project(project)
  debug(f'project {project_id} project {project_name}')
  for timeid, log in db('xrange', 'logs', '-', '+'):
    if UUID(log.get('project')) == project_id:
      db('xdel', 'logs', timeid)

  db('hdel', 'ids', project_name)
  db('hdel', 'projects', str(project_id))
  db('save')

def show_projects() -> None:
  for pid, project in sorted(db('hgetall', 'projects').items(), key=lambda kv: (kv[0].casefold(), kv[1])):
    print(f'{pid}: {project}')

def stream_time(stream_id:str) -> str:
  unix_time_mills, seq = stream_id.split('-')
  timestamp_mills = float('.'.join([unix_time_mills[:10], unix_time_mills[10:]]))
  return fromtimestamp(timestamp_mills).isoformat(' ', timespec='seconds')

def show_logs(project:Union[None, UUID]=None) -> None:
  for tid, log in db('xrange', 'logs', '-', '+'):
    log_id, log_project = load_project(log.get('project'))
    if project is None or log_id == project:
      print(f"{stream_time(tid)} action {log.get('action')!r} project {log_project!r}")

def show_id(id:UUID) -> None:
  print(db('hget', 'projects', str(id)))

def last() -> None:
  if not db('exists', 'last'):
    debug('There is not current last project.')
  else:
    last_id, last_name, last_state, last_when = last_project()
    print(f"Last project: {last_name!r}; action: {last_state!r}; at: {last_when}.")

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

def csv_format(stats, largest_scale='h', still_running=None) -> None:
  print('Time spent report')
  if largest_scale == 'w':   print('weeks,days,hours,minutes,seconds', end=',')
  elif largest_scale == 'd': print('days,hours,minutes,seconds', end=',')
  elif largest_scale == 'h': print('hours,minutes,seconds', end=',')
  elif largest_scale == 'm': print('minutes,seconds', end=',')
  elif largest_scale == 's': print('seconds', end=',')

  print('total,id,project,running')
  for pid, total in stats.items():
    if largest_scale == 'w':
      print(f'{weeks_long(total):02}',   end=',')
      print(f'{days_long(total):02}',    end=',')
      print(f'{hours_long(total):02}',   end=',')
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 'd':
      print(f'{days_long(total):02}',    end=',')
      print(f'{hours_long(total):02}',   end=',')
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 'h':
      print(f'{hours_long(total):02}',   end=',')
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 'm':
      print(f'{minutes_long(total):02}', end=',')
      print(f'{seconds_long(total):02}', end=',')

    if largest_scale == 's':
      print(total, end=',')
    else:
      print(total,                       end=',')

    print(pid,                         end=',')
    print('"{0}"'.format(db('hget', 'projects', pid)), end=',')
    if still_running is not None and still_running == UUID(pid):
      print('true')
    else:
      print('false')

def text_format(stats, largest_scale='h', still_running=None) -> None:
  print('Time spent report')
  for pid, total in stats.items():
    if largest_scale == 'w':
      print(f'{weeks_long(total):02}w', end='')
      print(f' {days_long(total):02}d', end='')
      print(f' {hours_long(total):02}h', end='')
      print(f' {minutes_long(total):02}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 'd':
      print(f'{days_long(total):02}d', end='')
      print(f' {hours_long(total):02}h', end='')
      print(f' {minutes_long(total):02}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 'h':
      print(f'{hours_long(total):02}h', end='')
      print(f' {minutes_long(total):02}d', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 'm':
      print(f'{minutes_long(total):02}m', end='')
      print(f' {seconds_long(total):02}s', end='')

    if largest_scale == 's':
      print(f'{total: >8}s', end='')
    else:
      print(f' total {total: >8}', end='')

    print(f' id {pid}', end='')
    print(f" project {db('hget', 'projects', pid)!r}", end='')
    if still_running is not None and still_running == UUID(pid):
      print('...and counting')
    else:
      print('')

def report(project:Union[str, UUID, None]=None, largest_scale='h', fmt='text') -> None:
  stats = {}
  accum = {}
  is_running = None
  for tid, log in db('xrange', 'logs', '-', '+'):
    proj = log.get('project')
    actn = log.get('action')
    _time = int(tid[:10])
    if project is None or len(str(project)) == 0:
      stats.setdefault(proj, 0)
      if actn == 'started':
        accum = {proj: _time}
      elif actn == 'stopped':
        stats[proj] += _time-accum[proj]
        accum = {}
    else:
      project_id, project_name = load_project(project)
      if str(project_id) != proj:
        continue

      stats.setdefault(proj, 0)
      if actn == 'started':
        accum = {str(project_id): _time}
      elif actn == 'stopped':
        stats[str(project_id)] += _time-accum[str(project_id)]
        accum = {}

  last_id, last_name, last_state, last_when = last_project()
  if last_state == 'started':
    is_running = last_id
    stats[str(last_id)] += int(now().timestamp()-last_when.timestamp())

  if project is None:
    for project_id in db('hkeys', 'projects'):
      stats.setdefault(project_id, 0)

  if fmt == 'text':
    text_format(stats, largest_scale, is_running)
  elif fmt == 'csv':
    csv_format(stats, largest_scale, is_running)

def rename(old:Union[str, UUID], new:str) -> None:
  id, old_project = load_project(old)
  db('hset', 'projects', str(id), new)
  db('hset', 'ids', new.casefold(), str(id))
  db('save')

def dt(dtin):
#  try:
  debug(f'dt in {dtin}')
  if dtin.isdigit(dtin):
    return datetime.datetime.fromtimestamp(int(dtin))
  elif dtin == 'today':
    debug( datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S'))
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S')
  elif dtin == 'yesterday':
    debug( datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1))
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)
  else:
    pass
#  except ValueError as e:
#    debug(f'date in {dtin}')
#    return datetime.strptime(dtin, '%Y-%m-%d %H:%M:%S')

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
  ui.set_defaults(action='gui', do=gui)

  beg = sub.add_parser('start', help='Start a project')
  beg.add_argument('-a', '--at', default=now(), metavar='DATETIME',  help='...the project at this specific time')
  beg.add_argument('project',    nargs='+',     metavar='NAME|UUID', help='Project name or uuid.')
  beg.set_defaults(action='start', do=start_project)

  end = sub.add_parser('stop', help='Stop a project')
  end.add_argument('-a', '--at',                 metavar='DATETIME',  default=now(),  help='...the project at this specific time')
  end.add_argument('-p', '--project', nargs='+', metavar='NAME|UUID', default='last', help='Project name or uuid (or the last project if none provided).')
  end.set_defaults(action='stop', do=stop_project)

  ren = sub.add_parser('rename', help='Rename a project')
  ren.add_argument('project',    nargs='+', metavar='NAME|UUID',                help='Old project name or uuid.')
  ren.add_argument('-t', '--to', nargs='+', metavar='NAME',      required=True, help='New project name.')
  ren.set_defaults(action='rename', do=rename)

  rm = sub.add_parser('rm', help='Remove a project')
  rm.add_argument('project', nargs='+', metavar='NAME|UUID', help='Project name or uuid.')
  rm.set_defaults(action='rm', do=remove)

  show = sub.add_parser('show', help='Modify the metadata')
  showsub = show.add_subparsers()
  shl = showsub.add_parser('last', help='Show the last project worked on and what we last did.')
  shl.set_defaults(action='show_last', do=last)

  shp = showsub.add_parser('projects', help='Show the available projects.')
  shp.set_defaults(action='show_projects', do=show_projects)

  sho = showsub.add_parser('logs',     help='Show the project logs.')
  sho.add_argument('-p', '--project',                       nargs='+', metavar='NAME|UUID', default=None, help='Project name or uuid.')
  sho.add_argument('-s', '--since',         type=dt,                   metavar='DATETIME',  default=None, help='Report details since this datetime.')
  sho.set_defaults(action='show_logs', do=show_logs)

  shi = showsub.add_parser('id',       help='Show the project name from the provided id.')
  shi.add_argument('project', metavar='UUID')
  shi.set_defaults(action='show_id', do=show_id)

  rep = sub.add_parser('report', help='Report the results of work done')
  rep.add_argument('-p', '--project',                       nargs='+',                      metavar='NAME|UUID',                               help='Project name or uuid.')
  rep.add_argument('-s', '--since',         type=dt,                                        metavar='DATETIME',                                help='Report details since this datetime.')
  rep.add_argument('-b', '--between',       type=dt,        nargs=2,                        metavar=('DATETIME', 'DATETIME'),                  help='Report details between these date and times.')
  rep.add_argument('-l', '--largest_scale', type=str,       choices='w,d,h,m,s'.split(','),                                    default='h',    help='The largest component of time to display (default: "h"): w => Weeks; d => Days; h => Hours; m => Minutes; s => Seconds.')
  rep.add_argument('-f', '--format',        type=str,       choices='text,csv'.split(','),                                     default='text', help='Output the report in this format (default: text).')
  rep.add_argument('-u', '--url',           type=urlparse,                                                                                     help='Document the report to this url.')
  rep.add_argument('-m', '--mailto',        type=email,                                                                                        help='Email the report to this user.')
  rep.set_defaults(action='report', do=report)

  hlp = sub.add_parser('help', help='Display help')
  hlp.set_defaults(action='help', do=p.print_help)

  p.set_defaults(project=[], action='help', do=p.print_help)

  r = p.parse_args()
  if r.project is not None and len(r.project) > 0 and isinstance(r.project, list):
    r.project = ' '.join(r.project).strip().replace('\n', '')

  if isinstance(r.project, str) and re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', r.project):
    r.project = UUID(r.project)
  debug(r)
  return r

def main() -> None:
  p = pargs()
  if p.action in ['start', 'stop']:
    p.do(p.project, p.at)
  elif p.action in ['rename']:
    p.do(p.project, p.to)
  elif p.action in ['rm', 'show_id', 'show_logs']:
    p.do(p.project)
  elif p.action in ['gui', 'show_last', 'show_projects', 'help']:
    p.do()
  elif p.action in ['report']:
    p.do(p.project, largest_scale=p.largest_scale, fmt=p.format)

if __name__ == '__main__':
  main()
