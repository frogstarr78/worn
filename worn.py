#!/usr/bin/python3

import sys
from lib import parse_args, debug, explain_dates
from lib.project import Project, LogProject
from lib.report import Report
from lib.gui import gui

def main() -> None:
  p = parse_args()
  if p.no_color:
    from lib.nocolors import colors
  else:
    from lib.colors import colors

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
    explain_dates()
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
#    elif p.between:
#      when = p.between
    else:
      when = None

    data = LogProject.report(p.project, when)
    report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
    if p.ticket:
      if p.ticket == 'last' and p.project:
        _ticket = db.get('cache:tickets', Project.make(p.project))
      elif p.ticket.isdigit():
        _ticket = int(p.ticket)
      else:
        debug(f'Unable to report results to unknown ticket')
        sys.exit(1)
      report.post(_ticket, ' '.join(p.comment).strip(), noop=p.NOOP)
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
    else:
      last = Project.make('last')
      project = LogProject.find(since=p.at, count=1)[0]
      if project != last or project.when != last.when:
        debug(f'Unable to change no-last project state')
        sys.exit(1)

      project.remove()

      if p.project:
        _project = Project.make(p.project, when=project.when)
      else:
        _project = project

      if p.state:
        _state = p.state
      else:
        _state = project.state

      LogProject.add(_project, _state, _project.when)

if __name__ == '__main__':
  main()
