from . import *
from tkinter import ttk

def gui_action(event, cb:ttk.Combobox) -> None:
  button_state = event.widget.cget('text')
  if 'Start' in button_state:
    project = project.Project.make(cb.get())
    project.start()

    _projects = [project.name for project in project.Project.all()]
    cb['values'] = _projects
    cb['width']  = len(max(_projects, key=len))-10
  elif button_state == 'Stop':
    project = project.Project.make('last')
    project.stop()
  else:
    debug(f"Unknown state {state!r}")

def gui() -> None:
  root = Tk()
  root.title('Worn')

  proj = StringVar()

  pfrm = ttk.LabelFrame(root, text='Project', underline=0, padding=11)
  pfrm.grid(sticky=(N, S, E, W))

  _projects = [project.name for project in project.Project.all()]
  c = ttk.Combobox(pfrm, values=_projects, textvariable=proj, width=len(max(_projects, key=len))-10)

  if (project := project.Project.make('last')).is_running():
    c.set(project.name)
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
  q = ttk.Button(bfrm, text="Quit", underline=0, command=root.destroy)

  s.grid(row=0, column=0)#, sticky=(N, S))
  t.grid(row=0, column=1)#, sticky=(N, S, E, W))
  ttk.Label(bfrm, text=' ').grid(row=0, column=2, sticky=(E, W))
  q.grid(row=0, column=3)#, sticky=(E))

  root.bind('<Alt-p>', lambda *e: c.focus_set())
  root.bind('<Alt-s>', lambda *e: s.focus_set())
  root.bind('<Alt-t>', lambda *e: t.focus_set())
  root.bind('<Alt-q>', lambda *e: root.destroy())

  s.bind('<ButtonPress>',    lambda e: gui_action(e, c))
  s.bind('<KeyPress-space>', lambda e: gui_action(e, c))
  t.bind('<ButtonPress>',    lambda e: gui_action(e, c))
  t.bind('<KeyPress-space>', lambda e: gui_action(e, c))

  root.columnconfigure(0, weight=5)
  root.rowconfigure(0,    weight=5)
#  frm.columnconfigure(0,  weight=5)
#  frm.rowconfigure(0,     weight=5)
#  frm.rowconfigure(1,     weight=5)
#  frm.rowconfigure(2,     weight=5)
#  frm.rowconfigure(3,     weight=5)

  root.mainloop()

