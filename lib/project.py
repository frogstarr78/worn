from . import *
from .colors import colors
from . import db
from typing import Generator

class Project(object):
  __match_args__ = ("id","name")

  def __init__(self, _id:UUID, name:str, state:str='stopped', when:datetime=now()):
    if isuuid(_id) and isuuid(name):
      raise Exception(f'Attempting to set the project id {self.id!r} to a uuid bad project name {self.name!r}!')

    self.id = _id
    self.name = name
    self.state = state
    self.when = when

  def __eq__(self, other):
    return hash(self) == hash(other)

  def equiv(self, other):
    if isinstance(other, Project):
      if isinstance(other.id, UUID):                       return self.id == other.id
      elif isinstance(other.id, str) and isuuid(other.id): return self.id == UUID(other.id)
    elif isinstance(other, UUID):                          return self.id == other
    elif isinstance(other, str):
      if isuuid(other): return self.id == UUID(other)
      else:             return self.name == other or self.name.casefold() == other.casefold()
    return False

  def __sub__(self, other):
    return self.when.timestamp() - other.when.timestamp()

  def __hash__(self) -> int:
    return hash(self.id)

  def __str__(self):
    return f'<Project hash:{hash(self)} id:{self.id!r} name:{db.get("projects", self.id)!r} state:"{self.is_running() and colors.fg.green or colors.fg.orange}{self.state}{colors.reset}" when:{self.when.strftime("%a %F %T")!r}>'

  def __format__(self, fmt_spec:Any) -> str:
    match fmt_spec:
      case 'id':     return str(self.id)
      case 'name!r': return repr(self.name)
      case 'name':   return self.name
      case 'last':   return f'Last project: {str(self).strip("<>")}'
      case 'plain':  return self.name.casefold()
      case 'log':    return f'{parse_timestamp(self.when).isoformat(" ", timespec="seconds")} state "{self.is_running() and colors.fg.green or colors.fg.orange}{self.state}{colors.reset}" id {self.id} project {self.name!r}'
      case _:        return super().__format__(fmt_spec)

  def is_running(self):
    return self.state == 'started'

  def is_last(self):
    return self == Project.make('last')

  def add(self):
    db.add('projects', {self.name.casefold().strip(): self.id, self.id: self.name.strip()}, nx=True)

  def log(self, state:str, at:datetime=now()) -> None:
    if at > now() + timedelta(seconds=10):
      future_time = input(f'The time that you specified "{at:%F %T}" is in the future. Are you certain you want to {state.rstrip("ed")} the {self:name} project in the future (y|N)? ')
      if not future_time.strip().casefold().startswith('y'):
        return
    self.add()
    LogProject(self.id, self.name, state, at).add()

  def stop(self, at:datetime=now()) -> None:
    if self.is_running():
      self.log('stopped', at)

  def start(self, at:datetime=now()) -> None:
    if db.has('logs'):
      oldest_log = parse_timestamp(db.xinfo('logs', 'last-generated-id', now()))
      if at < oldest_log:
        raise Exception(f'The start time that you specified "{at:%F %T}" is older than the last log entered. Please, choose a different time or adjust the previously entered log entry time "{oldest_log:%F %T}".')

    db.add('begun', now().timestamp(), expire=3600, nx=True)

    Project.make('last').stop(at=at)
    self.log('started', at)

  def rename(self, new) -> None:
    if not isinstance(new, Project):
      raise Exception(f"Project {new!r} is the wrong type {type(new)!r}.")

    db.add('projects', {self.id: new.name})
    db.rm('projects', self.name.casefold())
    db.add('projects', {new.name.casefold(): self.id})

  def remove(self) -> None:
    for log_project in LogProject.all_matching(self):
      log_project.remove()

    db.rm('projects', self.name.casefold().strip())
    db.rm('projects', self.id)

  @classmethod
  def make(kind, nameorid:Any, when:datetime=now()) -> Self:
    match nameorid:
      case {'project': nameorid as _uuid, 'state': state} if isuuid(_uuid):
        return LogProject(_uuid, db.get('projects', _uuid), state, when)
#      case {'project': nameorid as _uuid} if isuuid(_uuid):
#        return LogProject(_uuid, db.get('projects', _uuid), nameorid.get('state'), when)
      case 'last' if len(db.xrange('logs', count=1, reverse=True)) == 0:
        return FauxProject()
      case 'last':
        tsid, last = db.xrange('logs', count=1, reverse=True)[0]
        _id = UUID(last.get('project'))
        return Project(_id, db.get('projects', _id), last.get('state', 'stopped'), parse_timestamp(tsid))
      case nameorid as _uuid if isinstance(_uuid, UUID) and db.has('projects', _uuid):
        return Project(nameorid, db.get('projects', _uuid))
      case str(nameorid) as _uuid if isuuid(_uuid) and db.has('projects', _uuid):
        return Project(UUID(_uuid), db.get('projects', _uuid))
      case str(nameorid) if istimestamp_id(nameorid) and len(db.xrange('logs', start=nameorid, count=1)) == 1:
        record = db.xrange('logs', start=nameorid, count=1)[0]
        return Project.make(record[1], record[0])
      case str(nameorid) as _name if db.has('projects', _name.casefold().strip()):
        return Project.make(UUID(db.get('projects', _name.casefold().strip())))
      case str(nameorid) as _name:
        project = Project(uuid4(), _name)
        project.add()
        return project
      case ( Project(id=_) | Project(name=_) ) as project:
        return project
#      case None | [] | tuple() | set():
      case None | [] | tuple() | {} | set():
        debug(f"Project {nameorid!r} was empty.")
        return FauxProject()
      case _:
        debug(msg := f'Unable to find or create a new nameorid {nameorid} of type {type(nameorid)}.')
        raise Exception(msg)

  @classmethod
  def nearest_project_by_name(kind, name:str) -> set[str]:
    matches = set([])
    counts = [0, 0]
    if name == 'last':
      matches.add(Project.make('last'))
      counts = [1, 1]
    elif db.has('projects', name):
      matches.add(Project.make(name))
      counts = [1, 1]
    elif db.has('projects', name.strip().casefold()):
      matches.add(Project.make(name.strip().casefold()))
      counts = [1, 1]
    else:
      for label in db.keys('projects'):
        counts[0] += 1
        if len(label) < len(name):
          continue
        elif label == name or label.casefold() == name.casefold():
          matches.add(label)
          break
        else:
          matched = True
          for i in range(len(name)):
            counts[1] += 1
            if name[i].casefold() != label[i].casefold():
              matched = False
              continue

          if matched:
            matches.add(label)
    debug(f'counts {counts!r}')
    if len(matches) > 0:
      return sorted([Project.make(match) for match in matches], key=lambda p: p.name.casefold())
    else:
      return matches

  @classmethod
  def all(kind) -> Generator:
    return (Project.make(UUID(pid)) for pid, project in sorted(db.get('projects').items(), key=lambda kv: str(kv[1]).casefold()) if isuuid(pid))

  @classmethod
  def cache(kind, ticket:str | int, project) -> None:
    db.add('cache:tickets', {project.id: ticket})
    db.add('cache:recorded', {project.id: project.when})

class FauxProject(Project):
  def __init__(self):
    super().__init__(uuid4(), 'Faux', 'stopped', now())

  def add(self):
    raise Exception(f'You attempted to add a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

class LogProject(Project):
  def __init__(self, id:UUID, name:str, state:str='stopped', when:str=''):
#    if not istimestamp_id(when):
#      raise Exception(f'The supplied when value {when!r} was not a valid timestamp id')

    super().__init__(id, name, state, parse_timestamp(when))
    self.timestamp_id = when
    if istimestamp_id(when):
      if when.endswith('*'):
        self.serial = 0
      else:
        self.serial = int(when.split('-')[1])
    elif isinstance(when, str) and when.isdigit():
      self.serial = 0
    else:
      self.serial = 0

  def __str__(self):
    return f'<LogProject hash:{hash(self): >20} id: {str(self.id)!r} state: {self.state!r} timestamp_id: {self.timestamp_id: >16} serial: {self.serial: >3} when: "{self.when:%a %F %T}" name: {db.get("projects", self.id)!r}>'

  def __hash__(self) -> int:
#    return int(self.timestamp_id.replace('-', ''))
    return hash(self.id)
#
  def __format__(self, fmt_spec:Any):
    match fmt_spec:
      case 'log!t': return f'{str(self.when.timestamp()).replace(".", ""): >13}-{self.serial} {parse_timestamp(self.when).isoformat(" ", timespec="seconds")} state "{self.is_running() and colors.fg.green or colors.fg.orange}{self.state}{colors.reset}" id {self.id} project {self.name!r}'
      case _:       return super().__format__(fmt_spec)

  def add(self) -> None:
    _ts = str(self.when.timestamp()).replace('.', '')[:13]
    db.add('logs', {'project': self.id, 'state': self.state})

  def remove(self) -> None:
    db.rm('logs', self.timestamp_id)

  @classmethod
  def all_matching_since(kind, matching:str, since:datetime, count:int=None, _version:str | UUID=None) -> Generator:
    if isinstance(since, str) and istimestamp_id(since):
      start = since.strip()
    else:
      _ts = str(parse_timestamp(since).timestamp()).replace('.', '')[:13]
      start = f'{_ts.lstrip():0<13}-0'

    key = 'logs'
    if _version is not None:
      key = f'logs-{str(_version)}'

    return (_project for (tid, project) in db.xrange(key, start=start, count=count) if (_project := Project.make(project, when=tid)).equiv(matching))

  @classmethod
  def all_since(kind, since:datetime, count:int=None, _version:str | UUID=None) -> Generator:
    if isinstance(since, str) and istimestamp_id(since):
      start = since.strip()
    else:
      _ts = str(parse_timestamp(since).timestamp()).replace('.', '')[:13]
      start = f'{_ts.lstrip():0<13}-0'

    key = 'logs'
    if _version is not None:
      key = f'logs-{str(_version)}'

    return (Project.make(project, when=tid) for (tid, project) in db.xrange(key, start=start, count=count))

  @classmethod
  def all_matching(kind, matching:str, count:int=None, _version:str | UUID=None) -> Generator:
    key = 'logs'
    if _version is not None:
      key = f'logs-{str(_version)}'

    return (_project for (tid, project) in db.xrange(key, start='-', count=count) if (_project := Project.make(project, when=tid)).equiv(matching))

  @classmethod
  def all(kind, count:int=None, _version:str | UUID=None) -> Generator:
    key = 'logs'
    if _version is not None:
      key = f'logs-{str(_version)}'

    return (Project.make(project, when=tid) for (tid, project) in db.xrange(key, start='-', count=count))

  @classmethod
  def edit_log_time(kind, starting:datetime, to:datetime, reason:str) -> None:
    logs = LogProject.all_since(starting, count=2)

    if len(logs) > 1:
      if logs[0].when == logs[1].when:
        pass
      elif logs[1].when < to:
        raise Exception(f"The first log entry {logs[1]!s} after the one you have attempted to change, was recorded prior to the time you are attempting to change to '{p.to:%F %T}'.\nThis is unacceptable. Failing.")

    version_id = uuid4()
    new_key = f'logs-{str(version_id)}'
    db.add('versions', {new_key: reason})
    db.rename('logs', new_key)

    for log in LogProject.all(_version=version_id):
      if log.when >= starting:
        _log = LogProject(log.id, log.name, log.state, to)
        _log.log(log.state, to)
      else:
        _log = LogProject(log.id, log.name, log.state, log.when)
        _log.log(log.state, log.when)

  @classmethod
  def edit_last_log_name(kind, new_name:str) -> None:
    last = Project.make('last')
    project = LogProject.all_since(at, count=1)[0]
    if project != last or project.when != last.when:
      debug(f'Unable to change no-last project state')
      sys.exit(ERR)

    project.remove()

    LogProject(project.id, new_name, project.state, project.when).add()

  @classmethod
  def edit_last_log_state(kind, new_state:str) -> None:
    last = Project.make('last')
    project = LogProject.all_since(at, count=1)[0]
    if project != last or project.when != last.when:
      debug(f'Unable to change no-last project state')
      sys.exit(ERR)
    project.remove()

    LogProject(project.id, project.name, new_state, project.when).add()
