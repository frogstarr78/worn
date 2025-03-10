from . import *
from . import db
from .colors import colors
from typing import Any, Generator, Self, Union
from functools import partialmethod

class Project(object):
  __match_args__ = ("id","name")

  class BaseException(Exception): pass
  class InvalidIDE(BaseException): pass
  class FauxProjectE(BaseException): pass

  def __init__(self, id:UUID, name:Union[UUID, str], /, state:str='stopped', when:datetime=now()):
    if isuuid(id) and isuuid(name):
      raise Project.InvalidIDE(f'Attempting to set the project {id=} to a uuid bad project name {name=}!')

    if isinstance(id, str):
      assert isuuid(id), f"{id=} should be an instance of UUID, but isn't."
    assert isinstance(state, str), f"{state=} should be a string but isn't."
    assert state in ('started', 'stopped'), f"{state=} should be either 'started' or 'stopped'."
    assert isinstance(when, datetime) or istimestamp_id(when), f"{when=} should be a datetime or valid timestamp id, but isn't."

    self.id = id if isinstance(id, UUID) else UUID(id)
    self.name = name
    self.state = state
    self.when = when

  def __eq__(self, other):
    return hash(self) == hash(other)

  def equiv(self, other:Self) -> bool:
    if other is None: return False
    elif isinstance(other, Project):
      if isinstance(other.id, UUID):                       return self.id == other.id
      elif isinstance(other.id, str) and isuuid(other.id): return self.id == UUID(other.id)
    elif isinstance(other, UUID):                          return self.id == other
    elif isinstance(other, str):
      if isuuid(other):
        return self.id == UUID(other)
      else:
        return self.name == other or self.name.casefold() == other.casefold()
    return False

  def __sub__(self, other:Self) -> int:
    return self.when.timestamp() - other.when.timestamp()

  def __hash__(self) -> int:
    return hash(self.id)

  def __str__(self) -> str:
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

  def is_running(self) -> bool:
    return self.state == 'started'

  def is_last(self) -> bool:
    return self == Project.last()

  def add(self) -> None:
    db.add('begun', str(now().timestamp()).replace('.', ''), expire=3600, nx=True)
    db.add('projects', {self.name.casefold().strip(): self.id, self.id: self.name.strip()}, nx=True)

  def rename(self, new:Self) -> None:
    if not isinstance(new, Project): raise InvalidTypeE(f'Rename argument new {new} is an invalid type {type(new)}.')

    db.add('projects', {self.id: new.name})
    db.rm('projects', self.name.casefold())
    db.add('projects', {new.name.casefold(): self.id})

  def log(self, state:str, at:datetime=now()) -> None:
    assert isinstance(state, str), f"{state=} should be a string but isn't."
    assert isinstance(at, datetime), f"{at=} should be a datetime but isn't."
    LogProject(self.id, self.name, state, at).add()

  def stop(self, at:datetime=now()) -> None:
    assert isinstance(at, datetime), f"{at=} should be a datetime but isn't."
    if self.is_running():
      self.log('stopped', at)

  def start(self, at:datetime=now()) -> None:
    assert isinstance(at, datetime), f"{at=} should be a datetime but isn't."
    if (last := Project.last()) and not isinstance(last, FauxProject):
      last.stop(at)
    self.add()
    self.log('started', at)

  def remove(self) -> None:
    for log_project in LogProject.all(matching=self):
      log_project.remove()

    db.rm('projects', self.name.casefold().strip())
    db.rm('projects', self.id)

  @classmethod
  def last(kind) -> Self:
    if not db.has('logs') or len(logs := db.xrange('logs', count=1, reverse=True)) == 0:
      return FauxProject()

    tsid, last = logs[0]
    _id = UUID(last.get('project'))
    return kind(_id, db.get('projects', _id), last.get('state', 'stopped'), parse_timestamp(tsid))

  @classmethod
  def make(kind, nameorid:Any, when:datetime=now()) -> Self:
    assert isinstance(when, datetime) or istimestamp_id(when), f"{when=} should be a datetime or timestamp id, but isn't."

    match nameorid:
      case {'project': nameorid as _uuid, 'state': state} if isuuid(_uuid):
        return LogProject(_uuid, db.get('projects', _uuid), state, when)
#      case {'project': nameorid as _uuid} if isuuid(_uuid):
#        return LogProject(_uuid, db.get('projects', _uuid), nameorid.get('state'), when)
      case 'last':
        return kind.last()
      case nameorid as _uuid if isinstance(_uuid, UUID) and db.has('projects', _uuid):
        return Project(nameorid, db.get('projects', _uuid))
      case str(nameorid) as _uuid if isuuid(_uuid) and db.has('projects', _uuid):
        return Project(UUID(_uuid), db.get('projects', _uuid))
      case str(nameorid) if istimestamp_id(nameorid) and len(db.xrange('logs', start=nameorid, count=1)) == 1:
        record = db.xrange('logs', start=nameorid, count=1)[0]
        return LogProject.make(record[1], record[0])
      case str(nameorid) as _name if db.has('projects', _name.casefold().strip()):
        return Project.make(UUID(db.get('projects', _name.casefold().strip())))
      case str(nameorid) as _name:
        project = Project(uuid4(), _name)
        project.add()
        return project
      case ( Project(id=_) | Project(name=_) ) as project:
        return project
      case None | [] | tuple() | {} | set():
        debug(f"Project {nameorid=} was empty.")
        return FauxProject()
      case _:
        debug(msg := f'Unable to find or create a new nameorid {nameorid} of type {type(nameorid)}.')
        raise InvalidTypeE(msg)

  @classmethod
  def nearest_project_by_name(kind, name:str) -> set[Self]:
    assert isinstance(name, str | UUID), f"{name=} should be one of str but isn't."

    matches = set([])
    counts = [0, 0]
    if name == 'last' or db.has('projects', name) or db.has('projects', name.strip().casefold()):
      counts = [1, 1]
      debug(f'counts {counts!r}')
      if isinstance(name, str) and not isuuid(name):
        return {Project.make(name.strip().casefold())}
      else:
        return {Project.make(name)}

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
    if len(_projects := db.get('projects')) > 0:
      yield from (Project.make(UUID(pid)) for pid, p in sorted(_projects.items(), key=lambda kv: str(kv[1]).casefold()) if isuuid(pid))
    else:
      print('No projects', file=sys.stderr)
      yield from []

  @classmethod
  def cache(kind, ticket:str | int, project:Self) -> None:
    assert isinstance(ticket, str | int), f"{ticket=} should be one of str or int, but isn't."
    if isinstance(ticket, str):
      assert ticket.isdigit(), f"{ticket=} should be a valid number, but isn't."

    db.add('cache:tickets', {project.id: ticket})
    db.add('cache:recorded', {project.id: project.when})

class FauxProject(Project):
  def __init__(self):
    super().__init__(uuid4(), 'Faux', 'stopped', now())

  def add(self):
    raise Project.FauxProjectE(f'You attempted to add a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

  def start(self, at=now()):
    raise Project.FauxProjectE(f'You attempted to start a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

  def stop(self, at=now()):
    raise Project.FauxProjectE(f'You attempted to stop a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

  def log(self, state='stopped', at=now()):
    raise Project.FauxProjectE(f'You attempted to log a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

  def rename(self, new='fake2'):
    raise Project.FauxProjectE(f"Project {new!r} is the wrong type {type(new)!r}.")

class LogProject(Project):
  def __init__(self, id:UUID, name:str, /, state:str='stopped', when:str | datetime=None):
    super().__init__(id, name, state, parse_timestamp(when))
    self._stored = False
    if istimestamp_id(when):
      if when.endswith('*'):
        self.serial = '*'
      else:
        self.serial = int(when.split('-')[1])
        self._stored = True
    else:
      self.serial = '*'
    self.timestamp_id = stream_id(self.when, self.serial)

  def __str__(self):
    return f'<LogProject hash:{hash(self): >20} id: {str(self.id)!r} state: {self.state!r} timestamp_id: {self.timestamp_id: >16} serial: {self.serial: >3} when: "{self.when:%a %F %T}" name: {db.get("projects", self.id)!r}>'

  def __hash__(self) -> int:
    return hash(self.id)

  def __format__(self, fmt_spec:Any) -> str:
    match fmt_spec:
      case 'log!t': return f'{self.timestamp_id} {super().__format__("log")}'
      case 'raw':    return f'{self.timestamp_id} project {self.id} state {self.state}'
      case _:       return super().__format__(fmt_spec)

  def add(self) -> None:
    if db.has('logs'):
      oldest_log = parse_timestamp(db.xinfo('logs', 'last-generated-id', default=now()))
      if self.when < oldest_log:
        raise InvalidTimeE(f'The start time that you specified "{self.when:%F %T}" is older than the last log entered. Please, choose a different time or adjust the previously entered log entry time "{oldest_log:%F %T}".')

    if self.when > now() + timedelta(seconds=10):
      future_time = input(f'The time that you specified "{self.when:%F %T}" is in the future. Are you certain you want to {self.state.rstrip("ed")} the {self:name} project in the future (y|N)? ')
      if not future_time.strip().casefold().startswith('y'):
        return

    db.add('logs', {'project': self.id, 'state': self.state, 'id': self.timestamp_id})
    self._stored = True

  def remove(self) -> None:
    db.rm('logs', self.timestamp_id)

  def rename(self, new):
    raise InvalidTypeE(f"Project {new=} is the wrong type {type(new)!r}.")

  @classmethod
  def all(kind, *, matching=None, since=None, count:int=None, _version:str | UUID=None) -> Generator:
    start = '-' if since is None else stream_id(parse_timestamp(since), seq='0')
    key = 'logs' if _version is None else f'logs-{str(_version)}'

    yield from (_proj for (tid, project) in db.xrange(key, start=start, count=count) if (_proj := LogProject.make(project, when=tid)) and ( matching is None or _proj.equiv(matching) ))

  @classmethod
  def edit_log_time(kind, starting:datetime, to:datetime, reason:str) -> None:
    assert isinstance(starting, datetime), f"{starting=} should be an instance of datetime, but isn't."
    assert isinstance(to, datetime), f"{to=} should be an instance of datetime, but isn't."
    assert isinstance(reason, str), f"{reason=} should be an instance of str, but isn't."
    logs = list(LogProject.all(since=starting, count=2))

    if len(logs) > 1:
      if logs[0].when == logs[1].when:
        pass
      elif logs[1].when < to:
        debug(f"You have attempted to change the time of a project to a time that is recorded by another project:\n  {logs[1]!s}.\nConsider running 'worn show logs -s {to:%s}' to see what project is running at that time.\nFailing.")
        return

    version_id = db.new_version(reason)
    for log in LogProject.all(_version=version_id):
      if log.when == starting:
        _when = to
      else:
        _when = log.when

      _log = LogProject(log.id, log.name, log.state, _when)
      _log.log(log.state, _when)
