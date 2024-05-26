#!bin/python3

import sys
from lib import debug, db
from lib.project import Project, LogProject
from lib.report import Report
from lib.args import parse_args
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
      gui([project.name for project in Project.all()], Project.last())
    case Namespace(action='gen'):
      from uuid import uuid4
      print(uuid4())
    case Namespace(action='rename'):
      Project.make(p.project).rename(Project(' '.join(p.to).strip().replace('\n', ' ')))
    case Namespace(action='rm'):
      Project.make(p.project).remove()
    case Namespace(action='start') | Namespace(action='stop'):
      projects = Project.nearest_project_by_name(p.project)
      if len(projects) == 1:
        f = getattr(projects.pop(), p.action)
      elif len(projects) == 0:
        really_make_new = input(Prompt.CONFIRM.format(args=p))
        res = really_make_new.strip()
        if res == 'y':
          project = Project.make(p.project)
          f = getattr(project, p.action)
        else:
          sys.exit(UNK)
      else:
        n = 1
        for _project in projects:
          Prompt.PROJECT += f'{n}: {_project.id}: {_project.name}\n'
          n+=1
        try:
          project_number = input(Prompt.PROJECT)
        except EOFError:
          debug('Exiting')
          sys.exit(OK)
        except KeyboardInterrupt:
          debug('Exiting')
          sys.exit(OK)

        if not ( project_number.isdigit() and project_number.isprintable() ):
          debug('The value that you entered is not a number!')
          sys.exit(INV)

        num = int(project_number)
        if num == 0:
          debug('You requested to cancel. Cancelling!')
          sys.exit(OK)

        if num >= len(projects)+1:
          debug('The number that you entered was not valid!')
          sys.exit(INV)

        f = getattr(list(projects)[num-1], p.action)
      f(p.at)
    case Namespace(action='help', kind='dates'):
      from lib import explain_dates
      print(explain_dates())
    case Namespace(action='show', display='dates'):
      from lib import explain_dates
      explain_dates()
    case Namespace(action='help'):
      parg.print_help()
    case Namespace(action='show', display='last') | Namespace(action='stat'):
      last = Project.last()
      if isinstance(last, FauxProject):
        print('There are no projects to display.')
      else:
        print(f'{Project.last():last}')
    case Namespace(action='show', display='id'):
      print(Project.make(p.project))
    case Namespace(action='show', display='projects'):
      for project in Project.all():
        fmt = f'{project.id}: {project.name}'
        if project.is_last() and Project.make('last').is_running():
          fmt += f' ({colors.underline}{colors.bg.blue}currently running{colors.reset})'
        print(fmt)
    case Namespace(action='show', display='logs', project=project, since=since):
      if not db.has('logs') or len(logs := db.xrange('logs', count=1, reverse=True)) == 0:
        print('There are no logs to display.')
      else:
        fmt = 'log'
        if p.timestamp: fmt = 'log!t'
        for log in LogProject.all(matching=project, since=since):
          print(f'{log:{fmt}}'.format(log))
    case Namespace(action='show'):
      sharg.print_help()
    case Namespace(action='edit', to=None, project=None, state=new_state) if (project := LogProject.last()).state != new_state:
      project.remove()
      project.state =  new_state
      project.add()
    case Namespace(action='edit', to=None, project=new_name,  state=None) if (project := LogProject.last()).name != new_name:
      project.remove()
      project.name =  new_name
      project.add()
    case Namespace(action='edit', to=to, reason=str(reason), project=None, state=None):
      LogProject.edit_log_time(since, to, reason)
    case Namespace(action='edit', to=to, reason=[reason]) | Namespace(action='edit', to=to, reason=[*reason]):
      LogProject.edit_log_time(since, to, ' '.join(reason))
    case Namespace(action='edit', to=to, reason=None):
      debug('You are required to provide a reason when changing the time of an entry. Please retry the last command while adding a -r|--reason argument.')
      sys.exit(ERR)
    case Namespace(action='edit'):
      earg.print_help()
    case Namespace(action='report', project=None, since=None, ticket=None, mailto=None):
      report = Report(LogProject.all(), LogProject.last().when, p.largest_scale, include_all=p.include_all, show_header=(not p.no_header))
      print(f'{report:{p.format}}')
    case Namespace(action='report', project=None, since=since, ticket=None, mailto=None):
      report = Report(LogProject.all(since=since), since, p.largest_scale, include_all=p.include_all, show_header=(not p.no_header))
      print(f'{report:{p.format}}')
    case Namespace(action='report', project=None, since=None, ticket=ticket, mailto=None):
      debug('Reporting ALL logs to a ticket is currently not supported.')
      sys.exit(OK)
    case Namespace(action='report', project=None, since=None, ticket=None, mailto=to):
      res = report.mail(to, p.format, p.noop)
      sys.exit(res)
    case Namespace(action='report', project=project, since=None, ticket=None, mailto=None):
      report = Report(LogProject.all(matching=project), None, p.largest_scale, include_all=p.include_all, show_header=(not p.no_header))
      print(f'{report:{p.format}}')
    case Namespace(action='report', project=project, since=since, ticket=None, mailto=None):
      report = Report(LogProject.all(matching=project, since=since), since, p.largest_scale, include_all=p.include_all, show_header=(not p.no_header))
      print(f'{report:{p.format}}')
    case Namespace(action='report', project=nameorid, since=None, ticket=ticket) if not db.has('cache:recorded', Project.make(nameorid).id):
      raise Exception(f'Unable to determine the time frame for when to report the details of {nameorid!r}')
    case Namespace(action='report', project=nameorid, since=None, ticket=ticket):
      when = db.get('cache:recorded', project.id)
      res  = Report(LogProject.all(matching=nameorid), when, p.largest_scale, include_all=False, show_header=False).post(ticket, p.comment, noop=p.NOOP)
      sys.exit(res)
    case Namespace(action='report', project=nameorid, since=since, ticket=ticket):
      res = Report(LogProject.all(matching=nameorid, since=since), since, p.largest_scale, include_all=False, show_header=False).post(ticket, p.comment, noop=p.NOOP)
      sys.exit(res)
    case Namespace(action='report'):
      rarg.print_help()
    case _:
      parg.print_help()
  sys.exit(OK)

if __name__ == '__main__':
  main()
