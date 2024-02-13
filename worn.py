#!/usr/bin/python3

import sys
from tkinter import *
from tkinter import ttk
from uuid import uuid4, UUID
import redis
import argparse
from datetime import datetime
from urllib.parse import urlparse
from typing import Union, Tuple, List
import re

#db = redis.StrictRedis(decode_responses=True, protocol=3)
#db = redis.StrictRedis(decode_responses=True)
#db = redis.StrictRedis()
def db(cmd, key='', *args, **kw):
  with redis.StrictRedis(encoding="utf-8", decode_responses=True) as conn:
    if hasattr(conn, cmd.lower()) and callable(f := getattr(conn, cmd.lower())):
      if cmd in ['save', 'bgsave', 'ping']:
        return f()
      else:
        return f(key, *args, **kw)
    else:
      return None
now = datetime.now
fromtimestamp = datetime.fromtimestamp

class Project(object):
  def __init__(self, id:UUID, name:Union[list, str], state:str='stopped'):
    self.id = id
    self.name = Project.desc(name)
    self.state = state

  @classmethod
  def desc(gaudy, name) -> str:
    if isinstance(name, (tuple, list)):
      return ' '.join(name)
    elif isinstance(name, str):
      return name

  @classmethod
  def make(gaudy, thing) -> object:
    id, project = None, None
    try:
      id, project = UUID(thing), db('hget', 'projects', str(id))
    except ValueError:
      id, project = UUID(db('hget', 'project_ids', desc(thing).lower())), Project.desc(thing)
    finally:
      return Project(id, project)

class Db(object):
  def __init__(self):
    self__client = redis.StrictRedis(encoding="utf-8", decode_responses=True)

  def exists(self, key):
    if key in ['last', 'project_ids']:
      return self.__client.exists(key)
    else:
      return self.__client.hexists(key)

  def get(self, key, field=None):
    if key == 'project_logs':
      return self.__client.xrange(key, '-', '+')
    elif key == 'projects':
      return self.__client.hgetall(key)
    else:
      return self.__client.hget(key, field)

  def set(self, key, *args, **kw):
    if key in ['last', 'projects', 'project_ids']:
      return self.__client.hset(key, *args, **kw)
    else:
      return self.__client.xadd(key, *args, **kw)

  def rm(self, key, *args):
    if key in ['projects']:
      return self.__client.hdel(key, *args)
    else:
      return self.__client.xdel(key)

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

def gui() -> None:
  root = Tk()
  frm = ttk.Frame(root, padding=10)
  frm.grid()
  ttk.Button(frm, text="Start",   command=start).grid(column=0, row=0)
  ttk.Button(frm, text="Cease",   command=stop_project).grid(column=1, row=0)
  ttk.Button(frm, text="Restart", command=restart).grid(column=2, row=0)
  ttk.Label(frm, text="Hello World!").grid(column=1, row=1)
  ttk.Button(frm, text="Quit", command=root.destroy).grid(column=2, row=1)
  root.mainloop()

def log(id, project, state, at=now()):
  db('hsetnx', 'projects', str(id), project)
  db('hsetnx', 'project_ids', project.lower(), str(id))
  db('xadd', 'project_logs', dict(project=id, action=state))
  db('hset', 'last', mapping=dict(action=state, project=id, when=at.isoformat(' ', timespec='seconds')))

def project(project:Union[Tuple[str], List[str], str, UUID]) -> Tuple[str, UUID]:
  if project is None or len(project) == 0:
    debug(f"Project {project!r} was empty.")
    return (None, None)

  if isinstance(project, UUID) or ( isinstance(project, str) and re.search(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', project) ):
    if db('exists', 'projects') and db('hexists', 'projects', project):
      return (UUID(project), db('hget', 'projects', str(project)))
  elif isinstance(project, (tuple, list)):
    name = ' '.join(project)
  elif isinstance(project, str):
    name = project

  if db('exists', 'project_ids') and db('hexists', 'project_ids', name.lower()):
    id = UUID(db('hget', 'project_ids', name.lower()))
  else:
    id = uuid4()
  return (id, name)

def start(project:list, at:datetime=now()) -> None:
  project_id, project_name = project(project)
  if not db('exists', 'last') or db('hget', 'last', 'action') != 'started':
    log(project_id, project, 'started', at)
  else:
    debug(f"The previous project {db('hget', 'projects', db('hget', 'last', 'project'))!r} has not finished yet.")

def stop_id(pid:UUID, at:datetime=now()) -> None:
  log(pid, db('hget', 'project_ids', id), 'stopped', at)

def stop_project(project:list, at:datetime=now()) -> None:
  last_project_id = UUID(db('hget', 'last', 'project'))
#  debug(f'id {last_project_id} pid {project_id} {last_project_id == project_id} {project}.')
  if len(project) == 0:
    stop_id(last_project_id)
  elif last_project_id != project_id:
    debug(f"The previous project {db('hget', 'projects', last_project_id)!r} was not the same project specified.")
  elif db('hget', 'last', 'action') != 'started':
    debug(f"The previous project {db('hget', 'projects', last_project_id)!r} has not started.")
  else:
    stop_id(project_id)

def remove(project:list) -> None:
  project_id, project_name = project(project)
  if db('hexists', 'projects', _project_id):
    db('hdel', 'projects', _project_id)

  for timeid, project_log in db('xrange', 'project_logs', '-', '+'):
    if project_log.get('project') == _project_id:
      db('xdel', timeid)

def restart(at:datetime=now()) -> None:
  if db('exists', 'last') and db('hget', 'last', 'action') == 'started':
    proj = db('hget', 'projects', db('hget', 'last', 'project')).split(' ')
    stop_project(proj, at)
    start(proj, at)
  else:
    print(f'There is no project to start.')

def report(details) -> None:
  pass

def show_projects() -> None:
  for pid, project in db('hgetall', 'projects').items():
    print(f'{pid}: {project}')

def show_logs() -> None:
  for tid, project_log in db('xrange', 'project_logs', '-', '+'):
    print(f"{fromtimestamp(int(tid[:10])).isoformat(' ')} project {db('hget', 'projects', project_log.get('project'))} action {project_log.get('action')}")

def last() -> None:
  if db('exists', 'last'):
    print(f"Last project: {db('hget', 'projects', db('hget', 'last', 'project'))!r}; action: {db('hget', 'last', 'action')!r} at {db('hget', 'last', 'when')}.")
  else:
    print('There is not current last project.')

def report() -> None:
  stats = {}
  current = {}
  for tid, project_log in db('xrange', 'project_logs', '-', '+'):
    proj = project_log.get('project')
    actn = project_log.get('action')
    stats.setdefault(proj, 0)
    _time = int(tid.split('-')[0][:10])
    if actn == 'started':
      current = {proj: _time}
    elif actn == 'stopped':
      stats[proj] += _time-current[proj]
      current = {}

  for pid, total in stats.items():
    print(f"{pid} {db('hget', 'projects', pid)} time spent {int(total/3600*24)}d {int(total/3600)}h {int(total/60)}m {total%60}s.")

def pargs() -> argparse.Namespace:
  p = argparse.ArgumentParser(description='Working on Right Now')
  sub = p.add_subparsers(help='Various sub-commands')
  ui = sub.add_parser('gui', help='Show the gui')
  ui.set_defaults(action='gui', do=gui)

  beg = sub.add_parser('start', help='Start a project')
  beg.add_argument('-i', '--id', action='store_true', default=False, help='provided argument is a UUID')
  beg.add_argument('name', nargs='+')
  beg.add_argument('-a', '--at', default=now(), metavar='DATETIME',  help='...the project at this specific time')
  beg.set_defaults(action='start', do=start)

  end = sub.add_parser('stop', help='Stop a project', epilog='... or the last project started if no arguments supplied')
  gend = end.add_mutually_exclusive_group(required=False)
  gend.add_argument('-i', '--id',   nargs=1,   type=UUID, metavar='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', help='...by ID')
  gend.add_argument('-n', '--name', nargs='+',                                                            help='...by name')
  end.add_argument('-a', '--at', default=now(),           metavar='DATETIME',                             help='...the project at this specific time')
  end.set_defaults(action='stop', do=stop_project)

  res = sub.add_parser('restart',                  help='Restart a project')
  res.add_argument('-a', '--at', default=now(),           metavar='DATETIME',                             help='...the project at this specific time')
  res.set_defaults(action='restart', do=restart)

  ctrl = sub.add_parser('ctrl', help='Modify the metadata')
  ctrl.add_argument('-r', '--rm',  nargs='+',                                help='Remove a project by name.')
  ctrl.add_argument('-i', '--ri',                                            help='Remove a project by id/uuid.')
  ctrl.add_argument('-m', '--rename', nargs=2, metavar=('FROM_ID', 'TO_ID'), help="Rename a project using it's ID.")
  ctrl.set_defaults(action='ctrl', do=None)

  show = sub.add_parser('show', help='Modify the metadata')
  showsub = show.add_subparsers()
  ssl = showsub.add_parser('last',     help='Show the last project worked on and what we last did.')
  ssl.set_defaults(do=last)

  ssp = showsub.add_parser('projects', help='Show the available projects.')
  ssp.set_defaults(do=show_projects)

  sso = showsub.add_parser('logs',     help='Show the project logs.')
  sso.set_defaults(do=show_logs)

  show.set_defaults(action='show')

  rep = sub.add_parser('report', help='Report the results of work done')
  grep = rep.add_mutually_exclusive_group(required=False)
  grep.add_argument('-i', '--id',   nargs=1,   type=UUID, metavar='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', help='...by ID')
  grep.add_argument('-n', '--name', nargs='+',                                                            help='...by name')
  rep.set_defaults(action='report', do=report)
#  g.add_argument('-a', '--stats',         action='store_const', const=report,           dest='action')
#  g.add_argument('-e', '--report',        type=urlparse,                               nargs='+')

  r = p.parse_args()
  debug(r)
  return r

def main() -> None:
  p = pargs()
  if p.action == 'gui':
    p.do()
  elif p.action == 'start':
    if p.id:
      start_id(UUID(p.name), p.at)
    elif p.name:
      start(p.name, p.at)
  elif p.action == 'stop':
    if p.id:
      stop_id(UUID(p.name), p.at)
    elif p.name:
      stop_project(p.name, p.at)
    else:
      stop_project([], p.at)
  elif p.action == 'restart':
    p.do(p.at)
  elif p.action == 'show':
    p.do()
#  if p.action == 'start':
#    start(p.start)
#  elif p.action == 'stop':
#    if len(p.stop) > 0:
#      stop_project(p.stop)
#    else:
#      stop_project()
#  elif p.action == 'report':
#    report(p.record)
#  elif p.action == 'show':
#    p.do()
#  elif p.action == 'gui':
#    p.do()

if __name__ == '__main__':
  main()
