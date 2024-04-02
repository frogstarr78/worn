from argparse import Namespace
from . import *
from .colors import colors
from .project import Project, LogProject
import smtplib

class Report(object):
  SCALES = {'w': WEEK, 'd': DAY, 'h': HOUR, 'm': MINUTE, 's': SECOND}

  def __init__(self, data:Generator, at:datetime=None, scale:str='h', *, include_all:bool=False, show_header:bool=True):
    if scale not in Report.SCALES:
      raise Exception(f'Invalid scale specified {scale!r}.')

    self._last = Project.make('last')
    self.at = at
    self.scale = scale
    self.include_all = include_all
    self.show_header = show_header

    self._data = self._collate(data)

    if self._last is not None and self._last in self._data and self._last.is_running():
      self._data[self._last] += int(now().timestamp()-self._last.when.timestamp())

    if self.include_all:
      for project in Project.all():
        self._data.setdefault(project, 0)

  def _collate(self, logs:Generator) -> dict[Project, float]:
    data = {}
    accum = 0

    for log in logs:
      data.setdefault(log, 0)
      if log.is_running():
        accum = log.when.timestamp()
      elif accum > 0:
        data[log] += log.when.timestamp()-accum
        accum = 0

    return data

  @property
  def _sorted_data(self):
    return sorted(self._data.items(), key=lambda pnt: pnt[0].name.casefold())

  def mail(self, to:str, fmt:str='simple', *, noop:bool=False) -> None:
    body = f'{self:{fmt}}'
    if noop:
      print(body)
      return

    with smtplib.SMTP('localhost') as mc:
      mc.set_debuglevel(1)
      mc.sendmail('scott@viviotech.net', to, body)

  def post(self, ticket:str | int, comment:str, *, noop:bool=False) -> None:
    if not noop:
      import requests

    r = set([])
    for project, time in self._sorted_data:
      _duration = float(time)/MINUTE
      _comment = comment.format(project=project)
      if noop:
        debug(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id={ticket}&time_spent={_duration}&body="{_comment}"')
        r.add(True)
      else:
        Project.cache(ticket, project)
        resp = requests.post('https://portal.viviotech.net/api/2.0/', params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=ticket, time_spent=_duration, body=_comment))
        r.add(resp.status_code < 400)
    return all(isinstance(_, bool) and _ for _ in r)

  def _how_long(self, ts:int) -> tuple[int | float]:
    if self.scale == 'w':
      return (
        int(ts/WEEK),
        int(ts/DAY),
        int(ts%DAY/HOUR),
        int(ts%HOUR/MINUTE),
        int(ts%MINUTE)
      )
    elif self.scale == 'd':
      return (
        int(ts/DAY),
        int(ts%DAY/HOUR),
        int(ts%HOUR/MINUTE),
        int(ts%MINUTE)
      )

    elif self.scale == 'h':
      return ( int(ts/HOUR), int(ts%HOUR/MINUTE), int(ts%MINUTE) )

    elif self.scale == 'm':
      return ( int(ts/MINUTE), int(ts%MINUTE) )

  def _simple_format(self) -> str:
    if self.show_header:
      r = 'Time spent report'
      r += isinstance(self.at, datetime) and f' since: {self.at.strftime("%a %F %T")}' or ':'
      r += "\n"
    else:
      r = ''

    all_total = sum(self._data.values())
    t = ''
    for project, total in self._sorted_data:
      if total == 0 and not self.include_all:
        continue

      if self.scale == 'w':
        r += '{:02}w {:02}d {:02}h {:02}m {:02}s'.format(*self._how_long(total))
        t =  '{:02}w {:02}d {:02}h {:02}m {:02}s'.format(*self._how_long(all_total))
      if self.scale == 'd':
        r += '{:03}d {:02}h {:02}m {:02}s'.format(*self._how_long(total))
        t =  '{:03}d {:02}h {:02}m {:02}s'.format(*self._how_long(all_total))
      if self.scale == 'h':
        r += '{:04}h {:02}m {:02}s'.format(*self._how_long(total))
        t =  '{:04}h {:02}m {:02}s'.format(*self._how_long(all_total))
      if self.scale == 'm':
        r += '{:04}m {:02}s'.format(*self._how_long(total))
        t =  '{:04}m {:02}s'.format(*self._how_long(all_total))

      if self.scale == 's':
        r += f'{int(total): >8}s'
      else:
        r += f' total {int(total): >8}'

      r += f' id {project:id} project {project:name!r}'
      r += project.is_last() and self._last.is_running() and f' ...{colors.bg.blue}and counting{colors.reset}' or ''
      r += "\n"
    if len(t) > 0:
        r += f'{t}                                                                 Total\n'
    return r

  def _csv_format(self) -> str:
    if self.show_header:
      r = 'Time spent report\n'
    else:
      r = ''
    if self.scale == 'w':   r += 'weeks,days,hours,minutes,seconds,'
    elif self.scale == 'd': r += 'days,hours,minutes,seconds,'
    elif self.scale == 'h': r += 'hours,minutes,seconds,'
    elif self.scale == 'm': r += 'minutes,seconds,'
    elif self.scale == 's': pass

    r += 'total (in seconds),id,project,running'
    r += isinstance(self.at, datetime) and ',since' or ''
    r += "\n"

    for project, total in self._sorted_data:
      if total == 0 and not self.include_all:
        continue

      if self.scale == 's':
        pass
      else:
        r += ','.join(map(str, self._how_long(total)))
        r += ','

      r += f'{int(total)},{project:id},"{project:name}",'
      r += self._last.is_running() and self._last.equiv(project) and 'true' or 'false'

      r += isinstance(self.at, datetime) and f',{self.at.strftime("%a %F %T")}' or ''
      r += "\n"

    return r

  def _time_format(self) -> str:
    if self.show_header:
      if self.scale == 'w':   r = ' w  d  h  m  s\n'
      elif self.scale == 'd': r = '  d  h  m  s\n'
      elif self.scale == 'h': r = '  h  m  s\n'
      elif self.scale == 'm': r = '   m  s\n'
      elif self.scale == 's': r = '       s\n'
    else:
      r = ''

    all_total = sum(self._data.values())
    t = ''
    for project, total in self._sorted_data:
      if total == 0 and not self.include_all:
        continue

      if self.scale in ['w', 'd', 'h']:
        duration = self._how_long(total)
        total_duration = self._how_long(all_total)
        r += '{:03}:'.format(duration[0])
        r += ('{:02}:'*(len(duration)-1)).rstrip(':').format(*duration[1:])
        t =  '{:03}:'.format(total_duration[0])
        t += ('{:02}:'*(len(total_duration)-1)).rstrip(':').format(*total_duration[1:])
        t += ' Total'

      if self.scale == 'm':
        r += '{:04}:{:02}'.format(*self._how_long(total))
        t =  '{:04}:{:02} Total'.format(*self._how_long(all_total))

      if self.scale == 's':
        r += f'{int(total): >8}'
        t = ''

      r += f' {project:name!r}\n'
    r += f'{t}\n'
    return r

  def __format__(self, fmt_spec: Any) -> str:
    match fmt_spec:
      case 'csv':    return self._csv_format()
      case 'simple': return self._simple_format()
      case 'time':   return self._time_format()
      case _:        return super().__format__(fmt_spec)
