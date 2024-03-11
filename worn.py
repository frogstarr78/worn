#!/usr/bin/python3

from lib import parse_args, debug
from lib.project import Project, LogProject
from lib.report import Report
from lib.colors import colors
from lib.gui import gui

def main() -> None:
  p = parse_args()
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
    for log in LogProject.all(p.project, p.since):
      print(log.log_format(p.timestamp))

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
      report.post(p)
    elif p.mailto:
      report.mail(p)
    else:
      report.print(p.format)
  elif p.action == 'edit':
    all_logs = LogProject.all(since=p.at)

    if all_logs[1].when < p.to:
      raise Exception(f"The first log entry {all_logs[1]!s} after the one you have attempted to change, was recorded prior to the time you are attempting to change to '{p.to:%F %T}'.\nThis is unacceptable. Failing.")

    all_logs[0].change_time(p.to)
    for project in all_logs[1:]:
      project.update_serial(p.to)

if __name__ == '__main__':
  main()
