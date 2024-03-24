from . import *
from .colors import colors
from .project import Project, LogProject

class Report(object):
  def __init__(self, data:dict[str, float], at:datetime=None, scale:str='h', include_all:bool=False, show_header:bool=True):
    self.data = sorted(data.items(), key=lambda pt: pt[0].name.casefold())
    self.at = at
    self.scale = scale
    self.include_all = include_all
    self.show_header = show_header

  def mail(self, args:argparse.Namespace) -> None:
    if args.NOOP:
      print(f'{self:{args.format}}')
    else:
      with smtplib.SMTP('localhost') as mc:
        mc.set_debuglevel(1)
        mc.sendmail('scott@viviotech.net', args.mailto, f'{self:{args.format}}')

  def post(self, ticket:str | int, comment:str, noop:bool=False) -> None:
    import requests

    r = {}
    for project, time in self.data:
      Project.cache(ticket, project)
      _comment = comment.format(project=project)
      if noop:
        debug(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id={ticket}&time_spent={float(time)/MINUTE}&body="{_comment}"')
        r.add(False)
      else:
        resp = requests.post('https://portal.viviotech.net/api/2.0/', params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=ticket, time_spent=float(time)/MINUTE, body=_comment))
        r.add(resp.status_code <= 400)
    return all(isinstance(_, bool) and _ for _ in r) and 0 or 1

  def print(self, fmt):
    print(f'{self:{fmt}}')

  def __how_long(self, ts:int) -> int:
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
      return ( int(ts/MINUTE), int(ts%MINUTE))

  def __simple_format(self) -> str:
    if self.show_header:
      r = 'Time spent report'
      r += isinstance(self.at, datetime) and f' since: {self.at.strftime("%a %F %T")}' or ':'
      r += "\n"
    else:
      r = ''

    all_total = sum(v for (p, v) in self.data)
    t = ''
    for project, total in self.data:
      if total == 0 and not self.include_all:
        continue

      if self.scale == 'w':
        r += '{:02}w {:02}d {:02}h {:02}m {:02}s'.format(*self.__how_long(total))
        t =  '{:02}w {:02}d {:02}h {:02}m {:02}s'.format(*self.__how_long(all_total))
      if self.scale == 'd':
        r += '{:03}d {:02}h {:02}m {:02}s'.format(*self.__how_long(total))
        t =  '{:03}d {:02}h {:02}m {:02}s'.format(*self.__how_long(all_total))
      if self.scale == 'h':
        r += '{:04}h {:02}m {:02}s'.format(*self.__how_long(total))
        t =  '{:04}h {:02}m {:02}s'.format(*self.__how_long(all_total))
      if self.scale == 'm':
        r += '{:04}m {:02}s'.format(*self.__how_long(total))
        t =  '{:04}m {:02}s'.format(*self.__how_long(all_total))

      if self.scale == 's':
        r += f'{int(total): >8}s'
      else:
        r += f' total {int(total): >8}'

      r += f' id {project:id} project {project:name!r}'
      r += project.is_last() and Project.make('last').is_running() and f' ...{colors.bg.blue}and counting{colors.reset}' or ''
      r += "\n"
    if len(t) > 0:
        r += f'{t}                                                                Total\n'
    return r

  def __csv_format(self) -> str:
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

    for project, total in self.data:
      if total == 0 and not self.include_all:
        continue

      if self.scale == 's':
        pass
      else:
        r += ','.join(map(str, self.__how_long(total)))
        r += ','

      r += f'{int(total)},{project:id},"{project:name}",'
      r += (last := Project.make('last')).is_running() and last == project and 'true' or 'false'

      r += isinstance(self.at, datetime) and f',{self.at.strftime("%a %F %T")}' or ''
      r += "\n"

    return r

  def __time_format(self) -> str:
    if self.show_header:
      if self.scale == 'w':   r = ' w  d  h  m  s\n'
      elif self.scale == 'd': r = '  d  h  m  s\n'
      elif self.scale == 'h': r = '  h  m  s\n'
      elif self.scale == 'm': r = '   m  s\n'
      elif self.scale == 's': r = '       s\n'
    else:
      r = ''

    all_total = sum(v for (p, v) in self.data)
    t = ''
    for project, total in self.data:
      if total == 0 and not self.include_all:
        continue

      if self.scale in ['w', 'd', 'h']:
        duration = self.__how_long(total)
        total_duration = self.__how_long(all_total)
        r += '{:03}:'.format(duration[0])
        r += ('{:02}:'*(len(duration)-1)).rstrip(':').format(*duration[1:])
        t =  '{:03}:'.format(total_duration[0])
        t += ('{:02}:'*(len(total_duration)-1)).rstrip(':').format(*total_duration[1:])
        t += ' Total'

      if self.scale == 'm':
        r += '{:04}:{:02}'.format(*self.__how_long(total))
        t =  '{:04}:{:02} Total'.format(*self.__how_long(all_total))

      if self.scale == 's':
        r += f'{int(total): >8}'
        t = ''

      r += f' {project:name!r}\n'
    r += f'{t}\n'
    return r

  def __format__(self, fmt_spec: Any) -> str:
    if 'csv' in fmt_spec:
      return self.__csv_format()
    elif 'simple' in fmt_spec:
      return self.__simple_format()
    elif 'time' in fmt_spec:
      return self.__time_format()
    else:
      return super().__format__(fmt_spec)
