#!bin/python3

import sys
from lib import parse_args, debug
from lib.project import Project, LogProject
from lib.report import Report
from argparse import Namespace

OK = 0
ERR = 1
UNK = 2
INV = 4

class Prompt:
  PROJECT = '''Multiple projects found. Please choose the number of the matching project that you want to start?
0: quit/cancel
''',
  CONFIRM = '''No project found matching the name or id: {args.project!r} at {args.at.strftime('%a %F %T')!r}. Are you sure you want to create a new projected named {args.project!r}? (y|N)'''

def main() -> None:
  parg, sharg, earg, rarg, p = parse_args()

  if p.no_color:
    from lib.nocolors import colors
  else:
    from lib.colors import colors

  match p:
    case Namespace(action='gui'):
      from lib.gui import gui
      gui()
    case Namespace(action='rename'):
      Project.make(p.project).rename(Project(' '.join(p.to).strip().replace('\n', ' ')))
    case Namespace(action='rm'):
      Project.make(p.project).remove()
    case Namespace(action='help', kind='dates'):
      from lib import explain_dates
      explain_dates()
    case Namespace(action='show', display='dates'):
      from lib import explain_dates
      explain_dates()
    case Namespace(action='help'):
      parg.print_help()
    case Namespace(action='show', display='last'):
      last = Project.make('last')
      print('Last project: {last.name!r}; state: {colour}{last.state!r}{rst}; at: {last.when}, id: {last.id}.'.format(last=last, colour=last.is_running() and colors.fg.green or colors.fg.orange, rst=colors.reset))
    case Namespace(action='show', display='id'):
      print(Project.make(p.project))
    case Namespace(action='show', display='projects'):
      for project in Project.all():
        fmt = f'{project.id}: {project.name}'
        if project.is_last() and Project.make('last').is_running():
          fmt += f' ({colors.underline}{colors.bg.blue}currently running{colors.reset})'
        print(fmt)
    case Namespace(action='show', display='logs'):
      for log in LogProject.find(p.project, p.since):
        print(log.log_format(p.timestamp))
    case Namespace(action='show'):
      sharg.print_help()
    case Namespace(action='edit', since=None):
      pass
#      if p.to:
#        if p.reason is None:
#          debug('You are required to provide a reason when changing the time of an entry. Please retry the last command while adding a -r|--reason argument.')
#          sys.exit(ERR)
#
#        logs = LogProject.find(since=p.at, count=2)
#
#        if len(logs) > 1:
#          if logs[0].when == logs[1].when:
#            pass
#          elif all_logs[1].when < p.to:
#            raise Exception(f"The first log entry {all_logs[1]!s} after the one you have attempted to change, was recorded prior to the time you are attempting to change to '{p.to:%F %T}'.\nThis is unacceptable. Failing.")
#
#        LogProject.edit_log_time(p.at, p.to, ' '.join(p.reason))
#      else:
#        last = Project.make('last')
#        project = LogProject.find(since=p.at, count=1)[0]
#        if project != last or project.when != last.when:
#          debug(f'Unable to change no-last project state')
#          sys.exit(ERR)
#
#        project.remove()
#
#        if p.project:
#          _project = Project.make(p.project, when=project.when)
#        else:
#          _project = project
#
#        if p.state:
#          _state = p.state
#        else:
#          _state = project.state
#
#        LogProject(_project.id, _project.name, _state, _project.when).add()
      earg.print_help()
    case Namespace(action='edit'):
      earg.print_help()
    case Namespace(action='report', project=nameorid, since=None, ticket=ticket, comment=[*comment]):
      project = Project.make(nameorid)
      if not db.has('cache:recorded', project.id):
        raise Exception(f'Unable to determine the time frame for when to report the details of {p.project!r}')

      when = db.get('cache:recorded', project.id)

      res = report.post(p.ticket, ' '.join(p.comment).strip(), noop=p.NOOP)
      sys.exit(res)
    case Namespace(action='report', project=nameorid, since=None, ticket=ticket, comment=str(comment)):
      project = Project.make(nameorid)
      if not db.has('cache:recorded', project.id):
        raise Exception(f'Unable to determine the time frame for when to report the details of {p.project!r}')

      when = db.get('cache:recorded', project.id)

      res = report.post(ticket, comment, noop=p.NOOP)
      sys.exit(res)
    case Namespace(action='report', project=project, since=None, ticket=None, mailto=None):
      data = LogProject.collate(LogProject.find_matching(project), p.include_all)
      last = Project.make('last')
      if last == project and last.is_running():
        data[last] += int(now().timestamp()-last.when.timestamp())
      report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
      report.print(p.format)
    case Namespace(action='report', project=project, since=since, ticket=None, mailto=None):
      data = LogProject.collate(LogProject.find_matching_since(project, since), p.include_all)
      last = Project.make('last')
      if last == project and last.is_running():
        data[last] += int(now().timestamp()-last.when.timestamp())
      report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
      report.print(p.format)
    case Namespace(action='report', project=None, since=since, ticket=None, mailto=None):
      data = LogProject.collate(LogProject.find_since(project, since), p.include_all)
      last = Project.make('last')
      if last in data and last.is_running():
        data[last] += int(now().timestamp()-last.when.timestamp())
      report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
      report.print(p.format)
    case Namespace(action='report', project=None, since=None, ticket=None, mailto=None):
      data = LogProject.collate(LogProject.all(), p.include_all)
      last = Project.make('last')
      if last in data and last.is_running():
        data[last] += int(now().timestamp()-last.when.timestamp())
      report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
      report.print(p.format)
    case Namespace(action='report', ticket=None, mailto=mailto):
      res = report.mail(p)
      sys.exit(res)
    case Namespace(action='report'):
      rarg.print_help()
    case _:
      parg.print_help()
  sys.exit(OK)

#  match p.action:
#    case 'start' | 'stop':
#
#      projects = Project.nearest_project_by_name(p.project)
#      if len(projects) == 1:
#        f = getattr(projects.pop(), p.action)
#      elif len(projects) == 0:
#        really_make_new = input(Prompt.CONFIRM.format(args=p))
#        res = really_make_new.strip()
#        if res == 'y':
#          project = Project.make(p.project)
#          f = getattr(project, p.action)
#        else:
#          sys.exit(UNK)
#      else:
#        n = 1
#        for _project in projects:
#          Prompt.PROJECT += f'{n}: {_project.id}: {_project.name}\n'
#          n+=1
#        try:
#          project_number = input(PROJECT_PROMPT)
#        except EOFError:
#          debug('Exiting')
#          sys.exit(OK)
#        except KeyboardInterrupt:
#          debug('Exiting')
#          sys.exit(OK)
#
#        if not ( project_number.isdigit() and project_number.isprintable() ):
#          debug('The value that you entered is not a number!')
#          sys.exit(INV)
#
#        num = int(project_number)
#        if num == 0:
#          debug('You requested to cancel. Cancelling!')
#          sys.exit(OK)
#
#        if num >= len(projects)+1:
#          debug('The number that you entered was not valid!')
#          sys.exit(INV)
#
#        f = getattr(list(projects)[num-1], p.action)
#      f(p.at)
#    case 'report':
#
#      if p.since:
#        when = p.since
#  #    elif p.between:
#  #      when = p.between
#  #    elif p.ticket and p.project and not p.since:
#  #      project = Project.make(p.project)
#  #      if db.has('cache:recorded', project.id):
#  #        when = db.get('cache:recorded', project.id)
#  #      else:
#  #        raise Exception(f'Unable to determine the time frame for when to report the details of {p.project!r}')
#      else:
#        when = None
#
#      data = LogProject.report(p.project, when)
#      report = Report(data, when, p.largest_scale, p.include_all, not p.no_header)
#      if p.ticket:
#        if isinstance(p.comment, list):
#          _comment = ' '.join(p.comment).strip()
#        else:
#          _comment = p.comment
#
#        res = report.post(p.ticket, _comment, noop=p.NOOP)
#        sys.exit(res)
#      elif p.mailto:
#        res = report.mail(p)
#        sys.exit(res)
#      else:
#        report.print(p.format)
#    case 'edit':
#

if __name__ == '__main__':
  main()
