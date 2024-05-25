from . import *
from .project import Project
from tkinter import ttk, Tk, StringVar, N, S, E, W
from pathlib import Path
from os import getpid

CONTROL = Path(f'~/run/worn.{getpid()}').expanduser()

def gui(_projects, last=None) -> None:
  if CONTROL.exists(): return

  root = Tk()
  root.title('Worn')

  def bye(*e):
    CONTROL.unlink(missing_ok=True)
    root.destroy()

  proj = StringVar()

  pfrm = ttk.LabelFrame(root, text='Project', underline=0, padding=11)
  pfrm.grid(sticky=(N, S, E, W))

  c = ttk.Combobox(pfrm, values=_projects, textvariable=proj, width=len(max(_projects, key=len))-10)

  if isinstance(last, Project) and last.is_running():
    c.set(last.name)
  c.grid(row=0, column=0, pady=7, columnspan=4, sticky=(E, W))

  hl = ttk.Label(pfrm, text='At time')
  hl.grid(row=1, column=0, sticky=(E))

  hour = StringVar()
  hour.set(now().hour)
  hr = ttk.Spinbox(pfrm, from_=0, to=23, width=3, values=list(range(0, 24)), textvariable=hour)
  hr.grid(row=1, column=1, sticky=(E))

  hc = ttk.Label(pfrm, text=':')
  hc.grid(row=1, column=2)

  mins = StringVar()
  mins.set(now().minute)
  hm = ttk.Spinbox(pfrm, from_=0, to=59, width=3, values=list(range(0, 60)), textvariable=mins)
  hm.grid(row=1, column=3, sticky=(W))

#  s1 = ttk.Style()
#  s1.configure('Clr.TFrame', background='blue')
#  bfrm = ttk.Frame(root, padding=11, style='Clr.TFrame')
  bfrm = ttk.Frame(root, padding=11)
  bfrm.grid(sticky=(E, W))

  s = ttk.Button(bfrm, text="(Re-)Start", underline=5)
  t = ttk.Button(bfrm, text="Stop", underline=1)
  q = ttk.Button(bfrm, text="Quit", underline=0, command=bye)

  s.grid(row=0, column=0)#, sticky=(N, S))
  t.grid(row=0, column=1)#, sticky=(N, S, E, W))
  ttk.Label(bfrm, text=' ').grid(row=0, column=2, sticky=(E, W))
  q.grid(row=0, column=3)#, sticky=(E))

  root.bind('<Alt-p>', lambda *e: c.focus_set())
  root.bind('<Alt-s>', lambda *e: s.focus_set())
  root.bind('<Alt-t>', lambda *e: t.focus_set())
  root.bind('<Alt-q>', bye)

  def gui_action(event) -> None:
    button_state = event.widget.cget('text')
    if 'Start' in button_state:
      project = Project.make(c.get())
      project.start()

      _projects = [project.name for project in Project.all()]
      c['values'] = _projects
      c['width']  = len(max(_projects, key=len))-10
    elif button_state == 'Stop':
      project = Project.make('last')
      project.stop()
    else:
      debug(f"Unknown state {state!r}")
    bye()

  s.bind('<ButtonPress>',    lambda e: gui_action(e))
  s.bind('<KeyPress-space>', lambda e: gui_action(e))
  t.bind('<ButtonPress>',    lambda e: gui_action(e))
  t.bind('<KeyPress-space>', lambda e: gui_action(e))

  root.columnconfigure(0, weight=5)
  root.rowconfigure(0,    weight=5)
#  frm.columnconfigure(0,  weight=5)
#  frm.rowconfigure(0,     weight=5)
#  frm.rowconfigure(1,     weight=5)
#  frm.rowconfigure(2,     weight=5)
#  frm.rowconfigure(3,     weight=5)

  root.protocol("WM_DELETE_WINDOW", bye)
  CONTROL.touch()
  root.mainloop()
