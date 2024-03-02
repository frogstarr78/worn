#!/usr/bin/python3

import sys
from tkinter import *
from tkinter import ttk
from uuid import uuid4, UUID
import redis
import argparse
import datetime
from urllib.parse import urlparse
import re
import io
from typing import *

now = datetime.datetime.now

def db(cmd, key='', *args, **kw):
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hasattr(conn, cmd.casefold()) and callable(f := getattr(conn, cmd.casefold())):
      if cmd in ['save', 'bgsave', 'ping']:
        return f()
      else:
        return f(key, *args, **kw)
    else:
      return None

def hash_exists(key, hkey):
  if db('exists', key):
    return db('hexists', key, hkey)
  else:
    raise Exception(f"Key {key!r} doesn't exist")

def parse_timestamp(tsin):
  if isinstance(tsin, (int, float)):
    return datetime.datetime.fromtimestamp(tsin)
  elif isinstance(tsin, datetime.datetime):
    return tsin
  elif isinstance(tsin, str):
    if '-' in tsin:
      tsin = tsin.split('-')[0]

    if len(tsin) >= 13:
      if '.' in tsin[:13]:
        return datetime.datetime.fromtimestamp(float(tsin[:13]))
      else:
        return datetime.datetime.fromtimestamp(float('.'.join([tsin[:10], tsin[10:13]])))
    elif len(tsin) > 10:
      _tsin = f'{tsin:0<13}'
      return datetime.datetime.fromtimestamp(float('.'.join([_tsin[:10], _tsin[10:13]])))
    else:
      raise Exception(f'Invalid timestamp {tsin!r} supplied.')
  else:
    raise Exception(f'Unknown input type {type(tsin)} for timestamp {tsin!r}.')

# https://stackoverflow.com/a/26445590
class colors:
    '''Colors class:
    Reset all colors with colors.reset
    Two subclasses fg for foreground and bg for background.
    Use as colors.subclass.colorname.
    i.e. colors.fg.red or colors.bg.green
    Also, the generic bold, disable, underline, reverse, strikethrough,
    and invisible work with the main class
    i.e. colors.bold
    '''
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    class fg:
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        orange='\033[33m'
        blue='\033[34m'
        purple='\033[35m'
        cyan='\033[36m'
        lightgrey='\033[37m'
        darkgrey='\033[90m'
        lightred='\033[91m'
        lightgreen='\033[92m'
        yellow='\033[93m'
        lightblue='\033[94m'
        pink='\033[95m'
        lightcyan='\033[96m'
    class bg:
        black='\033[40m'
        red='\033[41m'
        green='\033[42m'
        orange='\033[43m'
        blue='\033[44m'
        purple='\033[45m'
        cyan='\033[46m'
        lightgrey='\033[47m'

def isuuid(s:str):
  if isinstance(s, UUID): return True
  elif isinstance(s, str): return re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', s)
  elif isinstance(s, (tuple, list)) and len(s) == 1: return isuuid(s[0])
  else: return False

class Project(object):
  def __init__(self, nameorid:Union[None, str, UUID], state:str='stopped', when:datetime.datetime=now()):
    self.id = None
    self.name = None
    self.state = state
    self.when = when
    self._load_project(nameorid)

  def _load_project(self, nameorid:Union[None, str, UUID]):
    if nameorid is None:
      debug(f"Project {nameorid!r} was empty.")
      return (None, None)
    elif isinstance(nameorid, Sequence) and len(nameorid) == 0:
      debug(f"Project {nameorid!r} was empty.")
      return (None, None)

    if isinstance(nameorid, Project):
      self.id   = nameorid.id
      self.name = nameorid.name
      if self.is_last():
        self.state = db('hget', 'last', 'state')
        self.when  = parse_timestamp(db('hget', 'last', 'when'))
    elif isinstance(nameorid, UUID):
      if hash_exists('projects', str(nameorid)):
        self.id   = nameorid
        self.name = db('hget', 'projects', str(nameorid))
    elif isinstance(nameorid, str):
      if nameorid.casefold().strip() == 'last':
        if db('exists', 'last'):
          last = db('hgetall', 'last')
          self.id    = UUID(last.get('project'))
          self.name  = db('hget', 'projects', str(self.id))
          self.state = last.get('state', 'stopped')
          self.when  = parse_timestamp(last.get('when'))
        else:
          self.id    = uuid4()
          self.name  = 'last'
          self.state = 'stopped'
          self.when  = now()
      elif isuuid(nameorid) and hash_exists('projects', nameorid):
        self.id   = UUID(nameorid)
        self.name = db('hget', 'projects', nameorid)
      elif hash_exists('projects', nameorid.casefold().strip()):
        self.id   = UUID(db('hget', 'projects', nameorid.casefold().strip()))
        self.name = db('hget', 'projects', str(self.id))
      else:
        self.id   = uuid4()
        self.name = nameorid
        if isuuid(self.id) and isuuid(self.name):
          raise Exception(f'Attempting to set the project id {self.id!r} to a uuid bad project name {self.name!r}!')
        db('hsetnx', 'projects', nameorid.casefold().strip(), str(self.id))
        db('hsetnx', 'projects', str(self.id), nameorid.strip())
    else:
      msg = f'Unable to find or create a new nameorid {nameorid} of type {type(nameorid)}.'
      debug(msg)
      raise Exception(msg)

  def __eq__(self, other):
    if isinstance(other, Project):
      if isinstance(other.id, UUID):
        return self.id == other.id
      elif isinstance(other.id, str) and isuuid(other.id):
        return self.id == UUID(other.id)
    elif isinstance(other, UUID):
      return self.id == other
    elif isinstance(other, str) and isuuid(other):
      return self.id == UUID(other)
    else:
      return False

  def __hash__(self):
    return self.id.int

  def __str__(self):
    return f'<Project hash:{hash(self)} id: {self.id!r} name: {db("hget", "projects", str(self.id))!r} state: {self.state!r} when: {self.when.strftime("%a %F %T")!r}>'

  @classmethod
  def nearest_project_by_name(kind, project:str) -> set[str]:
    matches = set([])
    counts = [0, 0]
    if project == 'last':
      matches.add(Project('last'))
      counts = [1, 1]
    elif hash_exists('projects', project):
      matches.add(Project(project))
      counts = [1, 1]
    elif hash_exists('projects', project.strip().casefold()):
      matches.add(Project(project.strip().casefold()))
      counts = [1, 1]
    else:
      for label in db('hkeys', 'projects'):
        counts[0] += 1
        if len(label) < len(project):
          continue
        elif label == project or label.casefold() == project.casefold():
          matches.add(label)
          break
        else:
          matched = True
          for i in range(len(project)):
            counts[1] += 1
            if project[i].casefold() != label[i].casefold():
              matched = False
              continue

          if matched:
            matches.add(label)
    debug(f'counts {counts!r}')
    return sorted([Project(match) for match in matches], key=lambda p: p.name.casefold())

  @classmethod
  def all(kind) -> list:
    return [Project(UUID(pid)) for pid, project in sorted(db('hgetall', 'projects').items(), key=lambda kv: kv[1].casefold()) if isuuid(pid)]

  def is_running(self):
    return db('exists', 'last') and self.state == 'started'

  def is_last(self):
    return self == db('hget', 'last', 'project')

  @property
  def log_format(self):
    r = f'{parse_timestamp(self.when).isoformat(" ", timespec="seconds")} '
    if self.is_running():
      r += f'state {colors.fg.green}{self.state!r}{colors.reset} '
    else:
      r += f'state {colors.fg.orange}{self.state!r}{colors.reset} '
    r += f'id {self.id} project {self.name!r}'
    return r

  def log(self, state:str, at:datetime.datetime=now()):
    _ts = str(at.timestamp()).replace('.', '')[:13]
    db('hsetnx', 'projects', str(self.id), self.name)
    db('hsetnx', 'projects', self.name.casefold(), str(self.id))
    db('xadd', 'logs', dict(project=str(self.id), state=state), id=f'{_ts:0<13}-*')
    db('hset', 'last', mapping=dict(state=state, project=str(self.id), when=_ts))
    db('save')

  def stop(self, at:datetime.datetime=now()):
    if self.is_running():
      self.log('stopped', at)

  def start(self, at:datetime.datetime=now()) -> None:
    if not db('exists', 'begin'):
      db('set', 'begun', str(now().timestamp()))
      db('expire', 'begun', 3600)

    Project('last').stop(at=at)
    self.log('started', at)

  def rename(self, new) -> None:
    if not isinstance(new, Project):
      raise Exception(f"Project {new!r} is the wrong type {type(new)!r}.")

    db('hset', 'projects', str(self.id), new.name)
    db('hdel', 'projects', self.name.casefold())
    db('hset', 'projects', new.name.casefold(), str(self.id))
    db('save')

  def remove(self):
    for timeid, log_project in db('xrange', 'logs', '-', '+'):
      if self == log_project.get('project'):
        db('xdel', 'logs', timeid)

    if self.is_last():
      db('del', 'last')

    db('hdel', 'projects', self.name)
    db('hdel', 'projects', str(self.id))
    db('save')

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

def gui_action(event, cb:ttk.Combobox) -> None:
  button_state = event.widget.cget('text')
  project = Project(cb.get())
  if 'Start' in button_state:
    project.start()

    cb['values'] = [project.name for project in Project.all()]
    cb['width']  = len(max(_projects, key=len))-10
  elif button_state == 'Stop':
    project.stop()
  else:
    debug(f"Unknown state {state!r}")

def gui() -> None:
  root = Tk()
  root.title('Worn')

  proj = StringVar()

  frm = ttk.LabelFrame(root, text='Project', underline=0, padding=11)
  frm.grid(sticky=(N, S, E, W))

  _projects = [project.name for project in Project.all()]
  c = ttk.Combobox(frm, values=_projects, textvariable=proj, width=len(max(_projects, key=len))-10)
  
  if (project := Project('last')).is_running():
    c.set(project.name)
  c.grid(row=0, column=0, pady=7, columnspan=4, sticky=(E, W))

  hl = ttk.Label(frm, text='At time')
  hl.grid(row=1, column=0, sticky=(E))

  hour = StringVar()
  hour.set(now().hour)
  hr = ttk.Spinbox(frm, from_=0, to=23, width=3, values=list(range(0, 24)), textvariable=hour)
  hr.grid(row=1, column=1, sticky=(E))

  hc = ttk.Label(frm, text=':')
  hc.grid(row=1, column=2)

  mins = StringVar()
  mins.set(now().minute)
  hm = ttk.Spinbox(frm, from_=0, to=59, width=3, values=list(range(0, 60)), textvariable=mins)
  hm.grid(row=1, column=3, sticky=(W))

  bfrm = ttk.Frame(root, padding=11)
  bfrm.grid(sticky=(N, S, E, W))

  s = ttk.Button(bfrm, text="(Re-)Start", underline=5)
  t = ttk.Button(bfrm, text="Stop", underline=1)
  q = ttk.Button(bfrm, text="Quit", underline=0, command=root.destroy)

  s.grid(row=0, column=0, sticky=(N, S))
  t.grid(row=0, column=1, sticky=(N, S, E, W))
  q.grid(row=0, column=3, sticky=(N, S, E))

  root.bind('<Alt-p>', lambda *e: c.focus_set())
  root.bind('<Alt-s>', lambda *e: s.focus_set())
  root.bind('<Alt-t>', lambda *e: t.focus_set())
  root.bind('<Alt-q>', lambda *e: root.destroy())

  s.bind('<ButtonPress>',    lambda e: gui_action(e, c))
  s.bind('<KeyPress-space>', lambda e: gui_action(e, c))
  t.bind('<ButtonPress>',    lambda e: gui_action(e, c))
  t.bind('<KeyPress-space>', lambda e: gui_action(e, c))

  root.columnconfigure(0, weight=5)
  root.rowconfigure(0,    weight=5)
#  frm.columnconfigure(0,  weight=5)
#  frm.rowconfigure(0,     weight=5)
#  frm.rowconfigure(1,     weight=5)
#  frm.rowconfigure(2,     weight=5)
#  frm.rowconfigure(3,     weight=5)

  root.mainloop()

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

def csv_format(stats:dict[str, float], at:Union[datetime.datetime, None]=None, largest_scale:str='h', still_running:Union[UUID, None]=None, include_all:bool=False) -> None:
  r = 'Time spent report\n'
  if largest_scale == 'w':   r += 'weeks,days,hours,minutes,seconds'
  elif largest_scale == 'd': r += 'days,hours,minutes,seconds'
  elif largest_scale == 'h': r += 'hours,minutes,seconds'
  elif largest_scale == 'm': r += 'minutes,seconds'
  elif largest_scale == 's': r += 'seconds'

  r += ',total (in seconds),id,project,running'
  if isinstance(at, datetime.datetime):
    r += ',since'
  else:
    r += ''
  r += "\n"

  for pid, total in stats.items():
    if total == 0 and not include_all:
      continue

    if largest_scale == 'w':
      r += f'{weeks_long(total):02},'
      r += f'{days_long(total):02},'
      r += f'{hours_long(total):02},'
      r += f'{minutes_long(total):02},'
      r += f'{seconds_long(total):02},'

    if largest_scale == 'd':
      r += f'{days_long(total):03},'
      r += f'{hours_long(total):02},'
      r += f'{minutes_long(total):02},'
      r += f'{seconds_long(total):02},'

    if largest_scale == 'h':
      r += f'{hours_long(total):03},'
      r += f'{minutes_long(total):02},'
      r += f'{seconds_long(total):02},'

    if largest_scale == 'm':
      r += f'{minutes_long(total):03},'
      r += f'{seconds_long(total):02},'

    if largest_scale == 's':
      r += f'{total},{total},'
    else:
      r += f'{total},'

    r += f'{pid},'
    r += '"{0}",'.format(db('hget', 'projects', str(pid)))
    if (last := Project('last')).is_running() and last == pid:
      r += 'true'
    else:
      r += 'false'

    if isinstance(at, datetime.datetime):
      r += f',{at.strftime("%a %F %T")}'
    r += "\n"

  return r

def simple_format(stats:dict[str, float], at:Union[datetime.datetime, None]=None, largest_scale:str='h', include_all:bool=False) -> io.StringIO:
  r = 'Time spent report'
  if isinstance(at, datetime.datetime):
    r += f' since: {at.strftime("%a %F %T")}'
  else:
    r += ':'
  r += "\n"

  for project, total in stats.items():
    if total == 0 and not include_all:
      continue

    if largest_scale == 'w':
      r += f'{weeks_long(total):02}w'
      r += f' {days_long(total):02}d'
      r += f' {hours_long(total):02}h'
      r += f' {minutes_long(total):02}m'
      r += f' {seconds_long(total):02}s'

    if largest_scale == 'd':
      r += f'{days_long(total):03}d'
      r += f' {hours_long(total):02}h'
      r += f' {minutes_long(total):02}m'
      r += f' {seconds_long(total):02}s'

    if largest_scale == 'h':
      r += f'{hours_long(total):03}h'
      r += f' {minutes_long(total):02}m'
      r += f' {seconds_long(total):02}s'

    if largest_scale == 'm':
      r += f'{minutes_long(total):03}m'
      r += f' {seconds_long(total):02}s'

    if largest_scale == 's':
      r += f'{int(total): >8}s'
    else:
      r += f' total {int(total): >8}'

    r += f' id {project.id}'
    r += f' project {project.name!r}'
    if project.is_last() and Project('last').is_running():
        r += f' ...{colors.bg.blue}and counting{colors.reset}'
    r += "\n"
  return r

def get_project_stats(project:Project, at:Union[datetime.datetime, None]=None) -> dict[Project, float]:
  if not isinstance(project, Project):
    raise Exception(f"Project {project!r} is the wrong type {type(project)!r}.")

  stats = 0
  accum = 0
  if at is None:
    start = '-'
  else:
    _ts = str(at.timestamp()).replace('.', '')[:13]
    start = f'{_ts:0<13}-0'

  for tid, log_project in db('xrange', 'logs', start, '+'):
    if project != log_project.get('project'):
      continue
    
    if log_project.get('state') == 'started':
      accum = parse_timestamp(tid).timestamp()
    elif log_project.get('state') == 'stopped' and accum > 0:
      stats += parse_timestamp(tid).timestamp()-accum
      accum = 0

  if project.is_last() and project.is_running():
    stats += int(now().timestamp()-project.when.timestamp())

  return {project: stats}

def get_all_stats(at:Union[datetime.datetime, None]=None) -> dict[Project, float]:
  stats = {}
  if at is None:
    start = '-'
  else:
    _ts = str(at.timestamp()).replace('.', '')[:13]
    start = f'{_ts:0<13}-0'

  for project in Project.all():
    stats.setdefault(project, 0)

  for tid, log_project in db('xrange', 'logs', start, '+'):
    log_project = Project(log_project.get('project'), log_project.get('state'), parse_timestamp(tid))
    stats.update(get_project_stats(log_project, at))
  return stats

def post_report(stats:dict[str, float], args:argparse.Namespace) -> None:
  import request

  for project, time in stats.items():
    request.post('https://portal.viviotech.net/api/2.0/', params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=args.ticket, time_spent=time, body=f'Time spent on {project.name}'))

def mail_report(stats:dict[str, float], args:argparse.Namespace) -> None:
  if args.format == 'simple':
    msg = simple_format(stats, when, args.largest_scale, args.include_all)
  elif args.format == 'csv':
    msg = csv_format(   stats, when, args.largest_scale, args.include_all)

  with smtplib.SMTP('localhost') as mc:
    mc.set_debuglevel(1)
    mc.sendmail('scott@viviotech.net', p.mailto, msg)

def _datetime(dtin:str) -> datetime.datetime:
  weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  abbrev_weekdays = [day[:3] for day in weekdays]
  if dtin.isdigit():
    return parse_timestamp(dtin)
  elif dtin.casefold() == 'today':
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S')
  elif dtin.casefold() == 'yesterday':
    return datetime.datetime.strptime(f'{datetime.date.today().strftime("%F")} 00:00:00', '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)
  elif dtin.casefold() in weekdays:
    current_dow = now().weekday()
    if current_dow <= weekdays.index(dtin.casefold()): 
      return now() - datetime.timedelta(days=7 - (weekdays.index(dtin.casefold()) - current_dow))
    else:
      return now() - datetime.timedelta(days=current_dow - weekdays.index(dtin.casefold()))
  elif dtin.casefold() in abbrev_weekdays:
    current_dow = now().weekday()
    if current_dow <= abbrev_weekdays.index(dtin.casefold()): 
      return now() - datetime.timedelta(days=7 - (abbrev_weekdays.index(dtin.casefold()) - current_dow))
    else:
      return now() - datetime.timedelta(days=current_dow - abbrev_weekdays.index(dtin.casefold()))
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

  stats = sub.add_parser('stat', help='Show the last status.')
  stats.set_defaults(action='show_last')

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
  rep.add_argument('-l', '--largest_scale', type=str,       choices='w,d,h,m,s'.split(','),                                    default='h',      help='The largest component of time to display (default: "h"): w => Weeks; d => Days; h => Hours; m => Minutes; s => Seconds.')
  rep.add_argument('-f', '--format',        type=str,       choices='simple,csv'.split(','),                                   default='simple', help='Output the report in this format (default: simple).')
  prep = rep.add_mutually_exclusive_group(required=False)
  prep.add_argument('-p', '--project',                       nargs='+',                      metavar='NAME|UUID',                                help='Project name or uuid.')
  prep.add_argument('-a', '--include_all',                   action='store_true',                                               default=False,   help='Display ALL projects including those without any tracked time.')
  trep = rep.add_mutually_exclusive_group(required=False)
  trep.add_argument('-s', '--since',         type=_datetime,                                 metavar='DATETIME',                                  help='Report details since this datetime.')
  trep.add_argument('-b', '--between',       type=_datetime, nargs=2,                        metavar=('DATETIME', 'DATETIME'),                    help='Report details between these date and times.')
  rrep = rep.add_mutually_exclusive_group(required=False)
  rrep.add_argument('-t', '--ticket',       type=int,                                                                          default=None,     help='Document the report to this ticket.')
  rrep.add_argument('-m', '--mailto',       type=email,                                                                        default=None,     help='Email the report to this user.')
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

def main() -> None:
  p = pargs()
  if p.action == 'show_id':
    print(f"{db('hget', 'projects', str(p.project))!r}")
  elif p.action == 'show_last':

    last = Project('last')
    print('Last project: {last.name!r}; state: {colour}{last.state!r}{rst}; at: {last.when}, id: {last.id}.'.format(last=last, colour=last.is_running() and colors.fg.green or colors.fg.orange, rst=colors.reset))
  elif p.action == 'show_projects':
    for project in Project.all():
      fmt = f'{project.id}: {project.name}'
      if project.is_last() and Project('last').is_running():
        fmt += f' ({colors.underline}{colors.bg.blue}currently running{colors.reset})'
      print(fmt)
  elif p.action == 'show_logs':
    if p.since is None:
      start = '-'
    else:
      _ts = str(p.since.timestamp()).replace('.', '')[:13]
      start = f'{_ts:0<13}-0'

    for tid, log_project in db('xrange', 'logs', start, '+'):
      log_project = Project(log_project.get('project'), log_project.get('state'), parse_timestamp(tid))

      _fmt = log_project.log_format
      if p.project is None or log_project == Project(p.project):
        if p.timestamp:
          _fmt = f'{tid:17} {log_project.log_format}'
        print(_fmt)

  elif p.action in ['start', 'stop']:
    projects = Project.nearest_project_by_name(p.project)
    if len(projects) == 1:
      f = getattr(projects.pop(), p.action)
    elif len(projects) == 0:
      debug(f'No project found matching the name or id: {p.project!r}.')
      sys.exit(2)
    else:
      _prompt = '''Multiple projects found. Please choose the number of the matching project that you want to start? 
0: quit/cancel
'''
      n = 1
      for _project in projects:
        _prompt += f'{n}: {_project.id}: {_project.name}\n'
        n+=1
      try:
        project_number = input(_prompt)
      except EOFError:
        debug('Exiting')
        sys.exit(0)
      except KeyboardInterrupt:
        debug('Exiting')
        sys.exit(0)

      if not ( project_number.isdigit() and project_number.isprintable() ):
        debug('The value that you entered is not a number!')
        sys.exit(4)

      num = int(project_number)
      if num == 0:
        debug('You requested to cancel. Cancelling!')
        sys.exit(0)

      if num >= len(projects)+1:
        debug('The number that you entered was not valid!')
        sys.exit(4)

      f = getattr(list(projects)[num-1], p.action)
    f(p.at)
  elif p.action == 'rename':
    Project(p.project).rename(Project(' '.join(p.to).strip().replace('\n', ' ')))
  elif p.action == 'rm':
    Project(p.project).remove()
  elif p.action == 'gui':
    gui()
  elif p.action == 'report':
    if p.since:
      when = p.since
    elif p.between:
      when = p.between
    else:
      when = None

    if p.project is None:
      stats = get_all_stats(when)
    else:
      stats = get_project_stats(Project(p.project), when)

    if p.ticket:
      post_report(stats, p)
    elif p.mailto:
      mail_report(stats, p)
    elif p.format == 'simple':
      print(simple_format(stats, when, p.largest_scale, p.include_all))
    elif p.format == 'csv':
      print(csv_format( stats, when, p.largest_scale, p.include_all))

if __name__ == '__main__':
  main()
