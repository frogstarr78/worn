#!/usr/bin/python3

import sys
from tkinter import *
from tkinter import ttk
from uuid import uuid4, UUID
import redis
import argparse
import datetime
from urllib.parse import urlparse

#db = redis.StrictRedis(decode_responses=True, protocol=3)
db = redis.StrictRedis(decode_responses=True)
#db = redis.StrictRedis()

def debug(*msgs) -> None:
  for _ in msgs:
    print(_, file=sys.stderr)

def gui() -> None:
  root = Tk()
  frm = ttk.Frame(root, padding=10)
  frm.grid()
  ttk.Button(frm, text="Start",   command=start).grid(column=0, row=0)
  ttk.Button(frm, text="Cease",   command=cease).grid(column=1, row=0)
  ttk.Button(frm, text="Restart", command=restart).grid(column=2, row=0)
  ttk.Label(frm, text="Hello World!").grid(column=1, row=1)
  ttk.Button(frm, text="Quit", command=root.destroy).grid(column=2, row=1)
  root.mainloop()

def project_desc(project:list) -> str:
  return ' '.join(project)

def project_id(project:list) -> str:
  if db.exists('project_ids') and db.hexists('project_ids', project_desc(project).lower()):
    pid = UUID(f"{db.hget('project_ids', project_desc(project).lower())}")
  else:
    pid = uuid4()
    db.hset('projects', str(pid), project_desc(project))
    db.hset('project_ids', project_desc(project).lower(), str(pid))
  return str(pid)

def start(project:list) -> None:
  if not db.exists('last') or db.hget('last', 'action') != 'start':
    db.xadd('project_logs', dict(project=project_id(project), action='start'))
    db.hset('last', mapping=dict(action='start', project=project_id(project)))
  else:
    debug(f"The previous project {db.hget('projects', db.hget('last', 'project'))!r} has not finished yet.")

def cease(project:list) -> None:
  last_project_id = db.hget('last', 'project')
#  debug(f'id {last_project_id} pid {project_id(project)} {last_project_id == project_id(project)} {project}.')
  if last_project_id != project_id(project):
    debug(f"The previous project {db.hget('projects', last_project_id)!r} was not the same project specified.")
  elif db.hget('last', 'action') != 'start':
    debug(f"The previous project {db.hget('projects', last_project_id)!r} has not started.")
  else:
    db.xadd('project_logs', dict(project=project_id(project), action='cease'))
    db.hset('last', mapping=dict(action='cease', project=project_id(project)))

def remove(project:list) -> None:
  _project_id = project_id(project)
  if db.hexists('projects', _project_id):
    db.hdel('projects', _project_id)

  for timeid, project_log in db.xrange('project_logs', '-', '+'):
    if project_log.get('project') == _project_id:
      db.xdel(timeid)

def restart() -> None:
  if db.exists('last') and db.hget('last', 'action') == 'start':
    proj = db.hget('projects', db.hget('last', 'project')).split(' ')
    cease(proj)
    start(proj)
  else:
    print(f'There is no project to start.')

def record(details) -> None:
  pass

def list_projects() -> None:
  for pid, project in db.hgetall('projects').items():
    print(f'{pid}: {project}')

def list_logs() -> None:
  for tid, project_log in db.xrange('project_logs', '-', '+'):
    print(f"{tid} project {db.hget('projects', project_log.get('project'))} action {project_log.get('action')}")

def last() -> None:
  if db.exists('last'):
    print(f"Last project: {db.hget('projects', db.hget('last', 'project'))!r}; action: {db.hget('last', 'action')!r}.")
  else:
    print('There is not current last project.')

def stats() -> None:
  stats = {}
  current = {}
  for tid, project_log in db.xrange('project_logs', '-', '+'):
    proj = project_log.get('project')
    actn = project_log.get('action')
    stats.setdefault(proj, 0)
    _time = int(tid.split('-')[0][:10])
    if actn == 'start':
      current = {proj: _time}
    elif actn == 'cease':
      stats[proj] += _time-current[proj]
      current = {}

  for project_id, total in stats.items():
    print(f"{project_id} {db.hget('projects', project_id)} time spent {int(total/3600*24)}d {int(total/3600)}h {int(total/60)}m {total%60}s.")

def pargs() -> argparse.Namespace:
  p = argparse.ArgumentParser(description='Working on Right Now')
  g = p.add_mutually_exclusive_group(required=True)
  g.add_argument('-g', '--gui',           action='store_const', const=gui,             dest='action')
  g.add_argument('-s', '--start',                                                      nargs='+')
  g.add_argument('-c', '--cease',                                                      nargs='+')
  g.add_argument('-m', '--rm',                                                         nargs='+')
  g.add_argument('-r', '--restart',       action='store_const', const=restart,         dest='action')
  g.add_argument('-a', '--stats',         action='store_const', const=stats,           dest='action')
  g.add_argument('-e', '--record',        type=urlparse,                               nargs='+')
  g.add_argument('-l', '--list_projects', action='store_const', const=list_projects,   dest='action')
  g.add_argument('-w', '--show_logs',     action='store_const', const=list_logs,       dest='action')
  g.add_argument('-z', '--last',          action='store_const', const=last,            dest='action')
  r = p.parse_args()
  print(r)
  return r

def main() -> None:
  p = pargs()
  if p.start:
    start(p.start)
  elif p.cease:
    cease(p.cease)
  elif p.record:
    record(p.record)
  elif p.rm:
    remove(p.rm)
  else:
    p.action()

if __name__ == '__main__':
  main()
