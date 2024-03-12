from . import *
from .colors import colors

class Project(object):
  def __init__(self, id:UUID, name:str, state:str='stopped', when:datetime=now()):
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

  def __hash__(self) -> int:
    return self.id.int

  def __str__(self):
    return f'<Project hash:{hash(self)} id: {self.id!r} name: {Project._db("hget", "projects", str(self.id))!r} state: {self.state!r} when: {self.when.strftime("%a %F %T")!r}>'

  def __format__(self, fmt_spec: Any) -> str:
    if 'id' in fmt_spec:
      return f'{self.id}'
    elif 'name' in fmt_spec:
      return f'{self.name}'
    elif 'plain' in fmt_spec:
      return f'{self.name.casefold()}'
    else:
      return super().__format__(fmt_spec)

  def log_format(self):
    r = f'{parse_timestamp(self.when).isoformat(" ", timespec="seconds")} '
    if self.is_running():
      r += f'state {colors.fg.green}{self.state!r}{colors.reset} '
    else:
      r += f'state {colors.fg.orange}{self.state!r}{colors.reset} '
    r += f'id {self.id} project {self.name!r}'
    return r

  def is_running(self):
    return self.state == 'started'

  def is_last(self):
    return self == Project.make('last')

  def add(self):
    Project._db('hsetnx', 'projects', self.name.casefold().strip(), str(self.id))
    Project._db('hsetnx', 'projects', str(self.id), self.name.strip())
    Project._db('save')

  def log(self, state:str, at:datetime=now()) -> None:
    self.add()
    LogProject.add(self, state, at)

  def stop(self, at:datetime=now()) -> None:
    if self.is_running():
      self.log('stopped', at)

  def start(self, at:datetime=now()) -> None:
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

  def remove(self) -> None:
    for log_project in LogProject.find(matching=self):
      log_project.remove()

    Project._db('hdel', 'projects', self.name)
    Project._db('hdel', 'projects', str(self.id))
    Project._db('save')

  @classmethod
  def _db(kind, cmd, key='', *args, **kw) -> Any:
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
  def make(kind, nameorid:Union[None, str, UUID], when:datetime=now()) -> Union['Project', 'LogProject', 'FauxProject']:
    if nameorid is None:
      debug(f"Project {nameorid!r} was empty.")
      return FauxProject()

    elif isinstance(nameorid, Sequence) and len(nameorid) == 0:
      debug(f"Project {nameorid!r} was empty.")
      return FauxProject()

    if isinstance(nameorid, Project):
      return nameorid
    elif isinstance(nameorid, UUID):
      if Project._db('exists', 'projects') and Project._db('hexists', 'projects', str(nameorid)):
        return Project(nameorid, Project._db('hget', 'projects', str(nameorid)))
      else:
        raise Exception(f'Name or id {nameorid!r} is not found in the list of available projects.')

    elif isinstance(nameorid, str):
      if nameorid.casefold().strip() == 'last':
        records = Project._db('xrevrange', 'logs', '+', '-', count=1)
        if len(records) == 0:
          return FauxProject()
        else:
          tsid, last = records[0]
          _id = UUID(last.get('project'))
          return Project(_id, Project._db('hget', 'projects', str(_id)), last.get('state', 'stopped'), parse_timestamp(tsid))
      elif isuuid(nameorid) and Project._db('exists', 'projects') and Project._db('hexists', 'projects', nameorid):
        return Project(UUID(nameorid), Project._db('hget', 'projects', nameorid))
      elif istimestamp_id(nameorid):
        record = LogProject._db('xrange', 'logs', nameorid, '+', count=1)
        if len(record) > 0:
          return Project.make(record[0][1], record[0][0])
        else:
          raise Exception(f'No log entry found with id {nameorid}.')
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
  def nearest_project_by_name(kind, name:str) -> set[str]:
    matches = set([])
    counts = [0, 0]
    if name == 'last':
      matches.add(Project.make('last'))
      counts = [1, 1]
    elif Project._db('exists', 'projects') and Project._db('hexists', 'projects', name):
      matches.add(Project.make(name))
      counts = [1, 1]
    elif Project._db('exists', 'projects') and Project._db('hexists', 'projects', name.strip().casefold()):
      matches.add(Project.make(name.strip().casefold()))
      counts = [1, 1]
    else:
      for label in Project._db('hkeys', 'projects'):
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
  def all(kind) -> list:
    return [Project.make(UUID(pid)) for pid, project in sorted(Project._db('hgetall', 'projects').items(), key=lambda kv: kv[1].casefold()) if isuuid(pid)]

def print_format(fmt) -> None:
  def _print(rep, when, largest_scale, include_all):
    if fmt == 'simple':
      print(project.simple_format(rep, when, largest_scale, include_all))
    elif fmt == 'csv':
      print(project.csv_format(rep, when, largest_scale, include_all))

  return _print

def post_report(report:dict[str, float], args:argparse.Namespace) -> None:
  import requests

  for project, time in report.items():
    _comment = args.comment.format(project=project)
    debug(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id={args.ticket}&time_spent={float(time)/60}&body="{_comment}"')
    requests.post('https://portal.viviotech.net/api/2.0/', params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=args.ticket, time_spent=float(time)/60, body=_comment))

  with smtplib.SMTP('localhost') as mc:
    mc.set_debuglevel(1)
    mc.sendmail('scott@viviotech.net', p.mailto, msg)

class FauxProject(Project):
  def __init__(self):
    super().__init__(uuid4(), 'faux', 'stopped', now())

  def add(self):
    raise Exception(f'You attempted to add a fake project to the database. This is merely a placeholder class/instance and is not meant to be operated on.')

class LogProject(Project):
  def __init__(self, id:UUID, name:str, state:str='stopped', when:str=''):
    super().__init__(id, name, state, parse_timestamp(when))
    self.timestamp_id = when
    if isinstance(when, str):
      self.serial = int(when.split('-')[1])
    else:
      self.serial = 0


  def __str__(self):
    return f'<LogProject hash:{hash(self): >20} id: {str(self.id)!r} state: {self.state!r} timestamp_id: {self.timestamp_id: >16} serial: {self.serial: >3} when: "{self.when:%a %F %T}" name: {Project._db("hget", "projects", str(self.id))!r}>'

  def __hash__(self) -> int:
    return int(self.timestamp_id.replace('-', ''))

  def log_format(self, with_timestamp=False):
    if with_timestamp:
      return '{0: >13}-{1} {2}'.format(str(self.when.timestamp()).replace(".", ""), self.serial, super().log_format())
    else:
      return super().log_format()

  def add(self, at:datetime) -> None:
    LogProject.add(self, self.state, at)

  def remove(self) -> None:
    Project._db('xdel', 'logs', self.timestamp_id)

  @classmethod
  def add(kind, project:Project, state:str, at:datetime) -> None:
    _ts = str(at.timestamp()).replace('.', '')[:13]
    Project._db('xadd', 'logs', dict(project=str(project.id), state=state), id=f'{_ts:0<13}-*')
    Project._db('save')

  @classmethod
  def find(kind, matching:Union[str, None]=None, since:Union[datetime, None]=None, count:Union[int, None]=None, _version:Union[str, UUID, None]=None) -> list:
    if since is None:
      start = '-'
    elif isinstance(since, str) and istimestamp_id(since):
      start = since.strip()
    else:
      _ts = str(parse_timestamp(since).timestamp()).replace('.', '')[:13]
      start = f'{_ts.lstrip():0<13}-0'

    key = 'logs'
    if _version is not None:
      key = f'logs-{str(_version)}'

    r = []
    for tid, project in Project._db('xrange', key, start, '+', count=count):
      log = Project.make(project, when=tid)
      if matching is None or log == matching:
        r.append(log)
    return r

  @classmethod
  def report(kind, matching=None, since:Union[datetime, None]=None) -> dict[Project, float]:
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

  @classmethod
  def edit_log_time(kind, starting:datetime, to:datetime, reason:str) -> None:
    version_id = uuid4()
    new_key = f'logs-{str(version_id)}'
    Project._db('hset', 'versions', new_key, reason)
    Project._db('rename', 'logs', new_key)

    for log in LogProject.find(_version=version_id):
      if log.when >= starting:
        _log = LogProject(log.id, log.name, log.state, to)
        _log.log(log.state, to)
      else:
        _log = LogProject(log.id, log.name, log.state, log.when)
        _log.log(log.state, log.when)
