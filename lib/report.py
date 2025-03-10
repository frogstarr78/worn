from argparse import Namespace
from . import *
from .colors import colors
from .project import Project, LogProject, FauxProject
import smtplib

class Report(object):
  SCALES = {'w': WEEK, 'd': DAY, 'h': HOUR, 'm': MINUTE, 's': SECOND}

  def __init__(self, data:Generator, at:datetime=None, scale:str='h', *, include_all:bool=False, show_header:bool=True):
    if scale not in Report.SCALES:
      raise Exception(f'Invalid scale specified {scale!r}.')

    self._last = Project.last()
    self.at = at
    self.scale = scale
    self.include_all = include_all
    self.show_header = show_header

    self._data = self._collate(data)

    if not isinstance(self._last, FauxProject) and hash(self._last) in self._data and self._last.is_running():
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
    assert isinstance(to, str), f"{to=} should be an instance of str, but isn't."
    assert isinstance(fmt, str), f"{fmt=} should be an instance of str, but isn't."
    assert isinstance(noop, bool), f"{noop=} should be an instance of bool, but isn't."

    body = f'{self:{fmt}}'
    if noop:
      print(body)
      return

    with smtplib.SMTP('mail3.viviotech.net') as mc:
      mc.set_debuglevel(1)
      mc.sendmail('scott@viviotech.net', to, f'Subject: Time spent report\r\n\r\n{body}')

  def post(self, ticket:str | int, comment:str, *, noop:bool=False) -> None:
    assert isinstance(ticket, str | int), f"{ticket=} should be an instance of str or int, but isn't."
    if isinstance(ticket, str):
      assert ticket.isdigit(), f"{ticket=} should be a valid number, but isn't."
    assert isinstance(comment, str), f"{fmt=} should be an instance of str, but isn't."
    assert isinstance(noop, bool), f"{noop=} should be an instance of bool, but isn't."

    if not noop:
      import requests

    _scale = self.scale
    self.scale = 's'
    r = set([])
    for project, time in self._sorted_data:
      _duration = f'{self._how_long(time)[0]/MINUTE:0.2f}'
      _comment = comment.format(project=project)
      if noop:
        debug(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id={ticket}&time_spent={_duration}&body="{_comment}"')
        r.add(True)
      else:
        Project.cache(ticket, project)
        resp = requests.post('https://portal.viviotech.net/api/2.0/', params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=ticket, time_spent=_duration, body=_comment))
        r.add(resp.status_code < 400)
    self.scale = _scale
    return all(isinstance(_, bool) and _ for _ in r)

  def _how_long(self, ts:int) -> tuple[int | float]:
    assert isinstance(ts, int | float), f"{ts=} should be an instance of int or float, but isn't."

    match self.scale:
      case 'w': return ( int(ts/WEEK), int(ts%WEEK/DAY), int(ts%DAY/HOUR), int(ts%HOUR/MINUTE), int(ts%MINUTE))
      case 'd': return (               int(ts/DAY),      int(ts%DAY/HOUR), int(ts%HOUR/MINUTE), int(ts%MINUTE))
      case 'h': return (                                 int(ts/HOUR),     int(ts%HOUR/MINUTE), int(ts%MINUTE))
      case 'm': return (                                                   int(ts/MINUTE),      int(ts%MINUTE))
      case _:   return (                                                                        int(ts),)

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

      match self.scale:
        case 'w':
          r += '{:02}w {:02}d {:02}h {:02}m {:02}s'.format(*self._how_long(total))
          t =  '{:02}w {:02}d {:02}h {:02}m {:02}s'.format(*self._how_long(all_total))
        case 'd':
          r += '{:03}d {:02}h {:02}m {:02}s'.format(*self._how_long(total))
          t =  '{:03}d {:02}h {:02}m {:02}s'.format(*self._how_long(all_total))
        case 'h':
          r += '{:04}h {:02}m {:02}s'.format(*self._how_long(total))
          t =  '{:04}h {:02}m {:02}s'.format(*self._how_long(all_total))
        case 'm':
          r += '{:04}m {:02}s'.format(*self._how_long(total))
          t =  '{:04}m {:02}s'.format(*self._how_long(all_total))
        case 's':
          r += f'{int(total): >8}s'
        case scale:
          raise Exception('Unknown scale {scale!r}.')


      if self.scale != 's':
        r += f' total {int(total): >8}'

      r += f' id {project:id} project {project:name!r}'
      r += project.is_last() and self._last.is_running() and f' ...{colors.bg.blue}and counting{colors.reset}' or ''
      r += "\n"
    if len(t) > 0:
        r += f'{t}                                                                 Total\n'
    return r

  def _csv_format(self) -> str:
    match (self.show_header, self.scale):
      case (False,  _): r = ''
      case (True, 'w'): r = 'Time spent report\nweeks,days,hours,minutes,seconds,'
      case (True, 'd'): r = 'Time spent report\ndays,hours,minutes,seconds,'
      case (True, 'h'): r = 'Time spent report\nhours,minutes,seconds,'
      case (True, 'm'): r = 'Time spent report\nminutes,seconds,'
      case (True, 's'): r = ''

    r += 'total (in seconds),id,project,running'
    r += ',since' if isinstance(self.at, datetime) else ''
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
      r += 'true' if self._last.is_running() and self._last.equiv(project) else 'false'

      r += f',{self.at:%a %F %T}' if isinstance(self.at, datetime) else ''
      r += "\n"

    return r

  def _time_format(self) -> str:
    match self.scale:
      case 'w': r, fmt = self.show_header and ' w  d  h  m  s\n' or '', '{:03}:{:02}:{:02}:{:02}:{:02}'
      case 'd': r, fmt = self.show_header and '  d  h  m  s\n'   or '', '{:03}:{:02}:{:02}:{:02}'
      case 'h': r, fmt = self.show_header and '  h  m  s\n'      or '', '{:03}:{:02}:{:02}'
      case 'm': r, fmt = self.show_header and '   m  s\n'        or '', '{:04}:{:02}'
      case 's': r, fmt = self.show_header and '       s\n'       or '', ''

    all_total = sum(self._data.values())

    for project, total in self._sorted_data:
      if total == 0 and not self.include_all:
        continue

      if self.scale != 's':
        r += f'{fmt} {project:name!r}'.format(*self._how_long(total))
      else:
        r += f'{int(total): >8} {project:name!r}'
    r += fmt.format(*self._how_long(all_total))
    r += ' Total\n'
    return r

  def __format__(self, fmt_spec:Any) -> str:
    match fmt_spec:
      case 'csv':    return self._csv_format()
      case 'simple': return self._simple_format()
      case 'time':   return self._time_format()
      case _:        return super().__format__(fmt_spec)
