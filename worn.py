#!/usr/bin/python3

import sys
from lib import parse_args, debug
from lib.project import Project, LogProject
from lib.report import Report
from lib.gui import gui

def main() -> None:
  p = parse_args()
  if p.no_color
    from lib.colors import colors
  else:
    from lib.nocolors import colors

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

    for log in LogProject.find(p.project, p.since):
      print(log.log_format(p.timestamp))

  elif p.action == 'explain_dates':
    msg = '''The system should know how to parse these custom pseudo-values and formats.

In all these instances, case is ignored.
Pseudo-values "understood" by the system.

"now"                 This means right now, to include microseconds. It utilizes datetime.datetime.now(). The default value in most cases.
"today"               Similar to now, however, it starts at Midnight local time.
"yesterday"           Same as today, except yeterday

weekdays              These are understood as the last occurance of the named weekday. So if today is Tuesday and you enter Wednesday, it will be interpreted as the previous Wednesday, approximately a week ago.
                      If you enter Monday, though, it will be understood as meaning yesterday (although at current time, not midnight like "today" and "yesterday" are).
                      examples: monday, Tuesday, Sunday, etc

abbreviated weekdays: same as weekdays
                      examples: Thur, fri, etc

x days ago:           Understood as midnight x days ago.  If today is Friday, then this means midnight on Monday of this week.
                      examples: "5 days ago".


Formats "understood" by the system"
uniz timestamp:              Standard unix time stamps, which may or may not include microseconds (which is necessary for the software to understand redis stream timestamp ids).
                             examples: 17095835400, 17102610000, 1710262561568, 1710478747033

redis stream timestamps:     See https://redis.io/docs/data-types/streams/#entry-ids
                             examples: 17095835400-0, 17102610000-2, 1710262561568-0, 1710478747033-0

See https://docs.python.org/3/library/datetime.html#datetime.datetime.strptime

%Y-%m-%d %I:%M:%S %p         Datetime value with trailing am/pm
                             examples: "2024-03-14 11:54:02 pm"

%Y-%m-%d %H:%M:%S            Datetime value with 24-hour clock
                             examples: "2024-03-14 23:54:02"

%H:%M                        Time value. These are interpreted as today at the time specified, which means, if you're not careful, you could unintentionally enter a time in the future.
%H:%M:%S                     examples: "10:31", "22:22", etc

%Y-%m-%d                     Date value
                             examples: "2024-03-14"'''
    print(msg)
  elif p.action in ['start', 'stop']:

    projects = Project.nearest_project_by_name(p.project)
    if len(projects) == 1:
      f = getattr(projects.pop(), p.action)
    elif len(projects) == 0:
      really_make_new = input(f'No project found matching the name or id: {p.project!r} at {p.at.strftime("%a %F %T")!r}. Are you sure you want to create a new projected named {p.project!r}? (y|N)')
      res = really_make_new.strip()
      if res == 'y':
        project = Project.make(p.project)
        f = getattr(project, p.action)
      else:
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

    data = LogProject.report(p.project, when)
    report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
    if p.ticket:
      report.post(p.ticket, p.comment)
    elif p.mailto:
      report.mail(p)
    else:
      report.print(p.format)
  elif p.action == 'edit':

    if p.to:
      if p.reason is None:
        debug('You are required to provide a reason when changing the time of an entry. Please retry the last command while adding a -r|--reason argument.')
        sys.exit(1)

      logs = LogProject.find(since=p.at, count=2)

      if len(logs) > 1:
        if logs[0].when == logs[1].when:
          pass
        elif all_logs[1].when < p.to:
          raise Exception(f"The first log entry {all_logs[1]!s} after the one you have attempted to change, was recorded prior to the time you are attempting to change to '{p.to:%F %T}'.\nThis is unacceptable. Failing.")

      LogProject.edit_log_time(p.at, p.to, ' '.join(p.reason))
    elif p.state:
      raise Exception("Implement me!")
    elif p.project:
      raise Exception("Implement me!")

if __name__ == '__main__':
  main()
