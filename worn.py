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

class Project(object):
  def __init__(self, id:UUID, name:str, state:str='stopped', when:datetime.datetime=now()):
    if isuuid(id) and isuuid(name):
      raise Exception(f'Attempting to set the project id {self.id!r} to a uuid bad project name {self.name!r}!')

    self.id = id
    self.name = name
    self.state = state
    self.when = when

  def __eq__(self, other):
    if isinstance(other, Project):
      if isinstance(other.id, UUID):
        return self.id == other.id
      elif isinstance(other.id, str) and isuuid(other.id):
        return self.id == UUID(other.id)
    elif isinstance(other, UUID):
      return self.id == other
    elif isinstance(other, str):
      if isuuid(other):
        return self.id == UUID(other)
      else:
        return self.name == other or self.name.casefold() == other.casefold()
    else:
      return False

  def __sub__(self, other):
    return self.when.timestamp() - other.when.timestamp()

  def __hash__(self):
    return self.id.int

  def __str__(self):
    return f'<Project hash:{hash(self)} id: {self.id!r} name: {Project._db("hget", "projects", str(self.id))!r} state: {self.state!r} when: {self.when.strftime("%a %F %T")!r}>'

  def log_format(self):
    r = f'{parse_timestamp(self.when).isoformat(" ", timespec="seconds")} '
    if self.is_running():
      r += f'state {colors.fg.green}{self.state!r}{colors.reset} '
    else:
      r += f'state {colors.fg.orange}{self.state!r}{colors.reset} '
    r += f'id {self.id} project {self.name!r}'
    return r

  def is_running(self):
    return Project._db('exists', 'last') and self.state == 'started'

  def is_last(self):
    return self == Project._db('hget', 'last', 'project')

  def add(self):
    Project._db('hsetnx', 'projects', self.name.casefold().strip(), str(self.id))
    Project._db('hsetnx', 'projects', str(self.id), self.name.strip())

  def log(self, state:str, at:datetime.datetime=now()):
    _ts = str(at.timestamp()).replace('.', '')[:13]
    Project._db('hsetnx', 'projects', str(self.id), self.name)
    Project._db('hsetnx', 'projects', self.name.casefold(), str(self.id))
    Project._db('xadd', 'logs', dict(project=str(self.id), state=state), id=f'{_ts:0<13}-*')
    Project._db('hset', 'last', mapping=dict(state=state, project=str(self.id), when=_ts))
    Project._db('save')

  def stop(self, at:datetime.datetime=now()):
    if self.is_running():
      self.log('stopped', at)

  def start(self, at:datetime.datetime=now()) -> None:
    Project._db('setnx', 'begun', str(now().timestamp()))
    Project._db('expire', 'begun', 3600, 'NX')

    Project.make('last').stop(at=at)
    self.log('started', at)

  def rename(self, new) -> None:
    if not isinstance(new, Project):
      raise Exception(f"Project {new!r} is the wrong type {type(new)!r}.")

    Project._db('hset', 'projects', str(self.id), new.name)
    Project._db('hdel', 'projects', self.name.casefold())
    Project._db('hset', 'projects', new.name.casefold(), str(self.id))
    Project._db('save')

  def remove(self):
    for timeid, log_project in Project._db('xrange', 'logs', '-', '+'):
      if self == log_project.get('project'):
        Project._db('xdel', 'logs', timeid)

    if self.is_last():
      Project._db('del', 'last')

    Project._db('hdel', 'projects', self.name)
    Project._db('hdel', 'projects', str(self.id))
    Project._db('save')

  @classmethod
  def _db(kind, cmd, key='', *args, **kw):
    with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
      if int(conn.info('default').get('redis_version', '0')[0]) < 7:
        raise Exception('This software requires version 7+ of Redis.')

      if cmd.casefold() == 'shutdown':
        return None

      if hasattr(conn, cmd.casefold()) and callable(f := getattr(conn, cmd.casefold())):
        if cmd in ['save', 'bgsave', 'ping']:
          return f()
        else:
          return f(key, *args, **kw)
      else:
        return None

  @classmethod
  def make(kind, nameorid:Union[None, str, UUID], when:datetime.datetime=now()):
    if nameorid is None:
      debug(f"Project {nameorid!r} was empty.")
      return FauxProject()
    elif isinstance(nameorid, Sequence) and len(nameorid) == 0:
      debug(f"Project {nameorid!r} was empty.")
      return FauxProject()

    if isinstance(nameorid, Project):
      if nameorid.is_last():
        return Project(nameorid.id, nameorid.name, Project._db('hget', 'last', 'state'), parse_timestamp(Project._db('hget', 'last', 'when')))
      else:
        return Project(nameorid.id, nameorid.name)

    elif isinstance(nameorid, UUID):
      if Project._db('exists', 'projects') and Project._db('hexists', 'projects', str(nameorid)):
        return Project(nameorid, Project._db('hget', 'projects', str(nameorid)))
      else:
        raise Exception(f'Name or id {nameorid!r} is not found in the list of available projects.')

    elif isinstance(nameorid, str):
      if nameorid.casefold().strip() == 'last':
        if Project._db('exists', 'last'):
          last = Project._db('hgetall', 'last')
          _id = UUID(last.get('project'))
          return Project(_id, Project._db('hget', 'projects', str(_id)), last.get('state', 'stopped'), parse_timestamp(last.get('when', when)))
        else:
          return FauxProject()
      elif isuuid(nameorid) and Project._db('exists', 'projects') and Project._db('hexists', 'projects', nameorid):
        return Project(UUID(nameorid), Project._db('hget', 'projects', nameorid))
      elif Project._db('exists', 'projects') and Project._db('hexists', 'projects', nameorid.casefold().strip()):
        _id = UUID(Project._db('hget', 'projects', nameorid.casefold().strip()))
        return Project(_id, Project._db('hget', 'projects', str(_id)))
      else:
        project = Project(uuid4(), nameorid)
        project.add()
        return project
    elif isinstance(nameorid, dict):
      _id = UUID(nameorid.get('project'))
      return LogProject(_id, Project._db('hget', 'projects', str(_id)), nameorid.get('state'), when)
    else:
      msg = f'Unable to find or create a new nameorid {nameorid} of type {type(nameorid)}.'
      debug(msg)
      raise Exception(msg)

  @classmethod
  def nearest_project_by_name(kind, project:str) -> set[str]:
    matches = set([])
    counts = [0, 0]
    if project == 'last':
      matches.add(Project.make('last'))
      counts = [1, 1]
    elif Project._db('exists', 'projects') and Project._db('hexists', 'projects', project):
      matches.add(Project.make(project))
      counts = [1, 1]
    elif Project._db('exists', 'projects') and Project._db('hexists', 'projects', project.strip().casefold()):
      matches.add(Project.make(project.strip().casefold()))
      counts = [1, 1]
    else:
      for label in Project._db('hkeys', 'projects'):
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
    return sorted([Project.make(match) for match in matches], key=lambda p: p.name.casefold())

  @classmethod
  def all(kind) -> list:
    return [Project.make(UUID(pid)) for pid, project in sorted(Project._db('hgetall', 'projects').items(), key=lambda kv: kv[1].casefold()) if isuuid(pid)]

class FauxProject(Project):
  def __init__(self):
    super().__init__(uuid4(), 'faux', 'stopped', now())

  def add(self):
    raise Exception(f'You attempted to add a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

class LogProject(Project):
  def __init__(self, id:UUID, name:str, state:str='stopped', when:str=''):
    super().__init__(id, name, state, parse_timestamp(when))
    self.serial = when.split('-')[:1]

  def __str__(self):
    return f'<LogProject hash:{hash(self)} id: {self.id!r} serial: {self.serial} name: {Project._db("hget", "projects", str(self.id))!r} state: {self.state!r} when: {self.when.strftime("%a %F %T")!r}>'

  def log_format(self, with_timestamp=False):
    if with_timestamp:
      return '{0}-{1} {2}'.format(str(self.when.timestamp()).replace(".", ""), self.serial, super().log_format())
    else:
      return super().log_format()

  @classmethod
  def all(kind, matching=None, since=None):
    if since is None:
      start = '-'
    else:
      _ts = str(parse_timestamp(since).timestamp()).replace('.', '')[:13]
      start = f'{_ts:0<13}-0'

    r = []
    for tid, project in Project._db('xrange', 'logs', start, '+'):
      if matching is None:
        r.append(Project.make(project, when=tid))
      elif (log := Project.make(project, when=tid)) == matching:
        r.append(log)
    return r

  @classmethod
  def report(kind, matching=None, since:Union[datetime.datetime, None]=None) -> dict[Project, float]:
    stats = {}
    accum = 0
    for log in LogProject.all(matching, since):
      stats.setdefault(log, 0)
      if log.is_running():
        accum = log.when.timestamp()
      elif accum > 0:
        stats[log] += log.when.timestamp()-accum
        accum = 0

    last = Project.make('last')
    if ( matching is None or last == matching ) and last.is_running():
      stats[last] += int(now().timestamp()-last.when.timestamp())
    return stats

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

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

def gui_action(event, cb:ttk.Combobox) -> None:
  button_state = event.widget.cget('text')
  project = Project.make(cb.get())
  if 'Start' in button_state:
    project.start()

    _projects = [project.name for project in Project.all()]
    cb['values'] = _projects
    cb['width']  = len(max(_projects, key=len))-10
  elif button_state == 'Stop':
    project.stop()
  else:
    debug(f"Unknown state {state!r}")

def gui() -> None:
  root = Tk()
  root.title('Worn')

  proj = StringVar()

  pfrm = ttk.LabelFrame(root, text='Project', underline=0, padding=11)
  pfrm.grid(sticky=(N, S, E, W))

  _projects = [project.name for project in Project.all()]
  c = ttk.Combobox(pfrm, values=_projects, textvariable=proj, width=len(max(_projects, key=len))-10)

  if (project := Project.make('last')).is_running():
    c.set(project.name)
  c.grid(row=0, column=0, pady=7, columnspan=4, sticky=(E, W))

  hl = ttk.Label(pfrm, text='At time')
  hl.grid(row=1, column=0, sticky=(E))

  hour = StringVar()
  hour.set(now().hour)
  hr = ttk.Spinbox(pfrm, from_=0, to=23, width=3, values=list(range(0, 24)), textvariable=hour)
  hr.grid(row=1, column=1, sticky=(E))

  hc = ttk.Label(pfrm, text=':')
  hc.grid(row=1, column=2)

  mins = StringVar()
  mins.set(now().minute)
  hm = ttk.Spinbox(pfrm, from_=0, to=59, width=3, values=list(range(0, 60)), textvariable=mins)
  hm.grid(row=1, column=3, sticky=(W))



#  s1 = ttk.Style()
#  s1.configure('Clr.TFrame', background='blue')
#  bfrm = ttk.Frame(root, padding=11, style='Clr.TFrame')
  bfrm = ttk.Frame(root, padding=11)
  bfrm.grid(sticky=(E, W))

  s = ttk.Button(bfrm, text="(Re-)Start", underline=5)
  t = ttk.Button(bfrm, text="Stop", underline=1)
  q = ttk.Button(bfrm, text="Quit", underline=0, command=root.destroy)

  s.grid(row=0, column=0)#, sticky=(N, S))
  t.grid(row=0, column=1)#, sticky=(N, S, E, W))
  ttk.Label(bfrm, text=' ').grid(row=0, column=2, sticky=(E, W))
  q.grid(row=0, column=3)#, sticky=(E))

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

def csv_format(report:dict[str, float], at:Union[datetime.datetime, None]=None, largest_scale:str='h', still_running:Union[UUID, None]=None, include_all:bool=False) -> None:
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

  for pid, total in report.items():
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

    r += f'{project.id},'
    r += f'"{project.name}",'
    if (last := Project.make('last')).is_running() and last == pid:
      r += 'true'
    else:
      r += 'false'

    if isinstance(at, datetime.datetime):
      r += f',{at.strftime("%a %F %T")}'
    r += "\n"

  return r

def simple_format(report:dict[str, float], at:Union[datetime.datetime, None]=None, largest_scale:str='h', include_all:bool=False) -> io.StringIO:
  r = 'Time spent report'
  if isinstance(at, datetime.datetime):
    r += f' since: {at.strftime("%a %F %T")}'
  else:
    r += ':'
  r += "\n"

  for project, total in report.items():
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
    if project.is_last() and Project.make('last').is_running():
        r += f' ...{colors.bg.blue}and counting{colors.reset}'
    r += "\n"
  return r

def post_report(report:dict[str, float], args:argparse.Namespace) -> None:
  import requests

  for project, time in report.items():
    debug(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id={args.ticket}&time_spent={float(time)/60}&body="Time spent on {project.name}"')
    requests.post('https://portal.viviotech.net/api/2.0/', params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=args.ticket, time_spent=float(time)/60, body=f'Time spent on {project.name}'))

def mail_report(report:dict[str, float], args:argparse.Namespace) -> None:
  if args.format == 'simple':
    msg = simple_format(report, when, args.largest_scale, args.include_all)
  elif args.format == 'csv':
    msg = csv_format(   report, when, args.largest_scale, args.include_all)

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
    print(Project.make(p.project))
  elif p.action == 'show_last':

    last = Project.make('last')
    print('Last project: {last.name!r}; state: {colour}{last.state!r}{rst}; at: {last.when}, id: {last.id}.'.format(last=last, colour=last.is_running() and colors.fg.green or colors.fg.orange, rst=colors.reset))
  elif p.action == 'show_projects':
    for project in Project.all():
      fmt = f'{project.id}: {project.name}'
      if project.is_last() and Project.make('last').is_running():
        fmt += f' ({colors.underline}{colors.bg.blue}currently running{colors.reset})'
      print(fmt)
  elif p.action == 'show_logs':
    for log in LogProject.all(p.project, p.since):
      print(log.log_format(p.timestamp))

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
    Project.make(p.project).rename(Project(' '.join(p.to).strip().replace('\n', ' ')))
  elif p.action == 'rm':
    Project.make(p.project).remove()
  elif p.action == 'gui':
    gui()
  elif p.action == 'report':
    if p.since:
      when = p.since
    elif p.between:
      when = p.between
    else:
      when = None

    rep = LogProject.report(p.project, when)

    if p.ticket:
      post_report(rep, p)
    elif p.mailto:
      mail_report(rep, p)
    elif p.format == 'simple':
      print(simple_format(rep, when, p.largest_scale, p.include_all))
    elif p.format == 'csv':
      print(csv_format( rep, when, p.largest_scale, p.include_all))

if __name__ == '__main__':
  main()
