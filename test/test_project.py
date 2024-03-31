from test import *
from lib.project import Project, FauxProject, LogProject

class TestProject(TestWornBase):
  def setUp(self):
    super().setUp()
    self.worn_project = Project(self.valid_uuid, 'Worn', 'stopped', datetime(2024, 3, 23, 23, 4, 13))

  def test_init(self):
    _uuid = uuid4()
    proj = LogProject(_uuid, 'something', 'stopped', self.known_date)
    self.assertEqual(proj.id, _uuid)
    self.assertEqual(proj.name, 'something')
    self.assertEqual(proj.state, 'stopped')
    self.assertEqual(proj.when, self.known_date)
    with self.assertRaises(Exception):
      Project(uuid4(), uuid4())

  def test_equiv(self):
    _uuid = uuid4()
    p  = Project(_uuid, 'Test1', 'stopped', when=self.known_date)
    op = Project(_uuid, 'Test1', 'stopped', when=self.known_date + timedelta(hours=24))
#    self.assertIs(p, op)
    self.assertTrue(p.equiv(op))
    self.assertTrue(p.equiv(_uuid))
    self.assertTrue(p.equiv(str(_uuid)))
    self.assertTrue(p.equiv('Test1'))
    self.assertTrue(p.equiv('test1'))
    oop = Project(str(_uuid), 'Test1', 'stopped', when=self.known_date + timedelta(hours=24))
    self.assertTrue(p.equiv(oop))
    self.assertTrue(p.equiv('Test1'))
    self.assertTrue(p.equiv('test1'))

    _oid = uuid4()
    ooop = Project(_oid, 'Test2', 'stopped', when=self.known_date + timedelta(hours=24))
    self.assertIsNot(p, ooop)
    self.assertFalse(p.equiv(ooop))
    self.assertFalse(p.equiv(_oid))
    self.assertFalse(p.equiv(str(_oid)))
    self.assertFalse(p.equiv('Test2'))
    self.assertFalse(p.equiv('test2'))
    self.assertFalse(p.equiv(1))
    self.assertFalse(p.equiv(list()))
    self.assertFalse(p.equiv(tuple()))
    self.assertFalse(p.equiv(set()))
    self.assertFalse(p.equiv(dict()))

  def test_sub(self):
    p  = Project(uuid4(), 'Test1', 'stopped', when=self.known_date)
    op = Project(uuid4(), 'Test2', 'stopped', when=self.known_date + timedelta(hours=24))
    self.assertEqual(p - op, -86400)
    self.assertEqual(op - p, 86400)

  def test_hash(self):
    _uuid = uuid4()
    self.assertEqual(hash(_uuid), hash(Project(_uuid, 'What?')))

  def test_str(self):
    from lib.colors import colors
    with patch('lib.db.get', return_value='Worn') as mock_db:
      result = f'''<Project hash:{hash(self.worn_project)} id:UUID('244019c2-6d8f-4b09-96c1-b60a91ecb3a5') name:'Worn' state:"{colors.fg.orange}stopped{colors.reset}" when:'Sat 2024-03-23 23:04:13'>'''
      self.assertEqual(str(self.worn_project), result)
      self.assertTrue(mock_db.called)
      self.assertEqual(mock_db.call_count, 1)
      self.assertEqual(mock_db.call_args.args, ('projects', UUID('244019c2-6d8f-4b09-96c1-b60a91ecb3a5')))

  def test_format(self):
    self.assertEqual(f'{self.worn_project:id}', str(self.worn_project.id))
    self.assertEqual(f'{self.worn_project:name}', self.worn_project.name)
    self.assertEqual(f'{self.worn_project:plain}', self.worn_project.name.casefold())
    self.assertEqual(f'{self.worn_project.name: ^6}', " Worn ")

    from lib.colors import colors
    _uuid = uuid4()
    project = Project(_uuid, 'What are you doing right now?', 'started', self.known_date)
    self.assertEqual(f'{project:log}', f"""2024-03-23 21:50:00 state "{colors.fg.green}started{colors.reset}" id {_uuid} project 'What are you doing right now?'""")

    _uuid = uuid4()
    project = Project(_uuid, 'Are you there?', 'stopped', self.known_date)
    self.assertEqual(f'{project:log}', f"""2024-03-23 21:50:00 state "{colors.fg.orange}stopped{colors.reset}" id {_uuid} project 'Are you there?'""")

  def test_is_running(self):
    self.assertFalse(self.worn_project.is_running())
    self.worn_project.state = 'started'
    self.assertTrue(self.worn_project.is_running())

  def test_is_last(self):
    me = Project(uuid4(), 'Central Park')
    with patch('lib.db.xrange', return_value=[(self._timestamp_id(datetime.now()), {'project': str(uuid4()), 'state': 'started'})]) as mock_range:
      with patch('lib.db.get', return_value='Parlor') as mock_get:
        self.assertFalse(me.is_last())

    _uuid = uuid4()
    me = Project(_uuid, 'Paperback')
    with patch('lib.db.xrange', return_value=[(self._timestamp_id(datetime.now()), {'project': str(_uuid), 'state': 'started'})]) as mock_range:
      with patch('lib.db.get', return_value='Paperback') as mock_get:
        self.assertTrue(me.is_last())

  def test_add(self): pass
  def test_log(self): pass
  def test_stop(self):
    proj = LogProject(uuid4(), 'Mud Larker', 'stopped', self._timestamp_id(self.known_date))
    with patch.object(proj, 'log') as mock_log:
      proj.stop(self.known_date)
      self.assertFalse(proj.is_running())
      self.assertFalse(mock_log.called)
      self.assertEqual(mock_log.call_count, 0)

      proj.state = 'started'
      proj.stop(self.known_date)
      self.assertTrue(proj.is_running())
      self.assertTrue(mock_log.called)
      self.assertEqual(mock_log.call_count, 1)
      self.assertEqual(mock_log.call_args.args, ('stopped', self.known_date))

  def test_start(self): pass
  def test_rename(self):
    with self.assertRaises(Exception):
      Project(uuid4(), 'Hooliganism').rename('not a project')

    _uuid = uuid4()
    proj = Project(_uuid, 'Chicken Nuggets')
    with patch('lib.db.add') as mock_add:
      with patch('lib.db.rm') as mock_rm:
        proj.rename(Project(_uuid, 'Pizza'))

        self.assertTrue(mock_add.called)
        self.assertEqual(mock_add.call_count, 2)
        self.assertEqual(mock_add.mock_calls[0].args, ('projects', {_uuid: 'Pizza'}))
        self.assertEqual(mock_add.mock_calls[1].args, ('projects', {'pizza': _uuid}))

        self.assertTrue(mock_rm.called)
        self.assertEqual(mock_rm.call_count, 1)
        self.assertEqual(mock_rm.call_args.args, ('projects', 'chicken nuggets'))

  def test_remove(self):
    _uuid = uuid4()
    _ts   = self._timestamp_id(self.known_date, seq='9')
    proj  = Project(_uuid, 'Peanut Butter')
    with patch('lib.db.xrange', return_value=iter([(_ts, {'project': _uuid, 'state': 'started'})])) as mock_range:
      with patch('lib.db.get') as mock_get:
        with patch('lib.db.rm') as mock_rm:
          proj.remove()

          self.assertTrue(mock_range.called)
          self.assertEqual(mock_range.call_count, 1)
          self.assertEqual(mock_range.call_args.args, ('logs', ))
          self.assertEqual(mock_range.call_args.kwargs, dict(start='-', count=None))

          self.assertTrue(mock_get.called)
          self.assertEqual(mock_get.call_count, 1)
          self.assertEqual(mock_get.call_args.args, ('projects', _uuid))

          self.assertTrue(mock_rm.called)
          self.assertEqual(mock_rm.call_count, 3)
          self.assertEqual(mock_rm.mock_calls[0].args, ('logs', _ts))
          self.assertEqual(mock_rm.mock_calls[1].args, ('projects', 'peanut butter'))
          self.assertEqual(mock_rm.mock_calls[2].args, ('projects', _uuid))

  def test_make_from_dictionary(self):
    '''case {'project': nameorid as _uuid, 'state': state} if isuuid(_uuid):'''
    with patch('lib.db.get', return_value='Worn') as mock_db:
      proj = Project.make(dict(project=self.valid_uuid, state='started'), self._timestamp_id(self.known_date))
      log = LogProject(self.valid_uuid, 'Worn', 'started', self._timestamp_id(self.known_date))
      self.assertEqual(proj, log, msg=f'\n{proj}\n != \n{log}\n')

  def test_make_from_last_keyword(self):
    '''
      case 'last' if len(db.xrange('logs', count=1, reverse=True)) == 0:
      case 'last':
    '''
    with patch('lib.db.xrange', return_value=[]) as mock_db:
      proj = Project.make('last')
      self.assertIsInstance(proj, FauxProject)
      self.assertTrue(mock_db.called)
      self.assertEqual(mock_db.call_count, 1)
      self.assertEqual(mock_db.call_args.args, ('logs',))
      self.assertEqual(mock_db.call_args.kwargs, dict(count=1, reverse=True))

    when = 1711313926.48
    _uuid = uuid4()
    with patch('lib.db.xrange', return_value=[(self._timestamp_id(when), {'project': str(_uuid), 'state': 'started'})]) as mock_range:
      with patch('lib.db.get', return_value='Who dis') as mock_get:
        proj = Project.make('last')
        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 2)
        self.assertEqual(mock_range.call_args.args, ('logs',))
        self.assertEqual(mock_range.call_args.kwargs, dict(count=1, reverse=True))

        self.assertTrue(mock_get.called)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args.args, ('projects', _uuid))

        self.assertIsInstance(proj, Project)
        self.assertEqual(proj.id, _uuid)
        self.assertEqual(proj.name, 'Who dis')
        self.assertEqual(proj.state, 'started')
        self.assertEqual(proj.when, datetime.fromtimestamp(1711313926.000480))

  def test_make_using_an_uuid(self):
    '''
      case nameorid if isinstance(nameorid, UUID) and db.has('projects', nameorid):
      case str(nameorid) if isuuid(nameorid) and db.has('projects', nameorid):
    '''
    _uuid = uuid4()
    with patch('lib.db.has', return_value=True) as mock_has:
      with patch('lib.db.get', return_value='Spiderman') as mock_get:
        proj = Project.make(str(_uuid))
        self.assertTrue(mock_has.called)
        self.assertEqual(mock_has.call_count, 1)
        self.assertEqual(mock_has.call_args.args, ('projects', str(_uuid)))

        self.assertTrue(mock_get.called)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args.args, ('projects', str(_uuid)))

        self.assertIsInstance(proj, Project)
        self.assertEqual(proj.id, _uuid)
        self.assertEqual(proj.name, 'Spiderman')
        self.assertEqual(proj.state, 'stopped')

    _uuid = uuid4()
    with patch('lib.db.has', return_value=True) as mock_has:
      with patch('lib.db.get', return_value='Spiderman') as mock_get:
        proj = Project.make(_uuid)
        self.assertTrue(mock_has.called)
        self.assertEqual(mock_has.call_count, 1)
        self.assertEqual(mock_has.call_args.args, ('projects', _uuid))

        self.assertTrue(mock_get.called)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args.args, ('projects', _uuid))

        self.assertIsInstance(proj, Project)
        self.assertEqual(proj.id, _uuid)
        self.assertEqual(proj.name, 'Spiderman')
        self.assertEqual(proj.state, 'stopped')

  def test_make_from_using_timestamp_id(self):
    '''case str(nameorid) if istimestamp_id(nameorid) and len(db.xrange('logs', start=nameorid, count=1)) > 0:'''
    _uuid = uuid4()
    with patch('lib.db.xrange', return_value=[(self._timestamp_id(self.known_date, seq='5'), {'project': _uuid, 'state': 'started'})]) as mock_range:
      with patch('lib.db.get', return_value='Synthetica') as mock_get:
        proj = Project.make(self._timestamp_id(self.known_date, seq='5'))
        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 2)
        self.assertEqual(mock_range.call_args.args, ('logs',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start=self._timestamp_id(self.known_date, seq='5'), count=1))

        self.assertTrue(mock_get.called)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args.args, ('projects', _uuid))

        self.assertIsInstance(proj, LogProject)
        self.assertEqual(proj.id, _uuid)
        self.assertEqual(proj.name, 'Synthetica')
        self.assertEqual(proj.state, 'started')
        self.assertEqual(proj.timestamp_id, self._timestamp_id(self.known_date, seq='5'))
        self.assertEqual(proj.serial, 5)

  def test_make_from_using_project_name(self):
    '''case str(nameorid) if db.has('projects', nameorid.casefold().strip()):'''
    _name = "  I am doing something that I don't want anyone to know about, including myself, so I am making a very obscure description here instead."
    _clean_name = "i am doing something that i don't want anyone to know about, including myself, so i am making a very obscure description here instead."
    _uuid = uuid4()
    with patch('lib.db.has', return_value=True) as mock_has:
      with patch('lib.db.get', side_effect=(str(_uuid), _name)) as mock_get:
        proj = Project.make(_name)
        self.assertTrue(mock_has.called)
        self.assertEqual(mock_has.call_count, 2)
        self.assertEqual(mock_has.mock_calls[0].args, ('projects', _clean_name))
        self.assertEqual(mock_has.mock_calls[1].args, ('projects', _uuid))

        self.assertTrue(mock_get.called)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_get.mock_calls[0].args, ('projects', _clean_name))
        self.assertEqual(mock_get.mock_calls[1].args, ('projects', _uuid))

        self.assertIsInstance(proj, Project)
        self.assertEqual(proj.id, _uuid)
        self.assertEqual(proj.name, _name)
        self.assertEqual(proj.state, 'stopped')

  def test_make_from_making_new_project(self):
    '''case str(nameorid):'''
    _name = "A slightly shorter project, but that still means nothing really   "
    _clean_name = "a slightly shorter project, but that still means nothing really"
    uuid4 = Mock(return_value='Jimmy Johns')
    with patch('lib.db.has', return_value=False) as mock_has:
      with patch('lib.db.add', return_value=None) as mock_add:
        proj = Project.make(_name)
        self.assertTrue(mock_has.called)
        self.assertEqual(mock_has.call_count, 1)
        self.assertEqual(mock_has.mock_calls[0].args, ('projects', _clean_name))

        self.assertTrue(mock_add.called)
        self.assertEqual(mock_add.call_count, 1)
        self.assertEqual(mock_add.call_args.args[0], 'projects')
        self.assertIn(_clean_name,   list(mock_add.call_args.args[1].keys()))
        self.assertIn(_name.strip(), list(mock_add.call_args.args[1].values()))
        self.assertEqual(mock_add.call_args.kwargs, dict(nx=True))

        self.assertIsInstance(proj, Project)
        self.assertIsInstance(proj.id, UUID)
        self.assertEqual(proj.name,   _name)
        self.assertEqual(proj.state,  'stopped')

  def test_make_from_existing_project_instances(self):
    '''case Project(id=UUID(nameorid)) | Project(name=nameorid):'''
    _uuid = uuid4()
    _proj = Project(_uuid, None)
    proj = Project.make(_proj)

    self.assertEqual(proj, _proj)

    _uuid = uuid4()
    _proj = Project(None, 'Find me')
    proj = Project.make(_proj)

    self.assertEqual(proj, _proj)

  def test_make_from_empty(self):
    '''case None | [] | tuple() | {} | set():'''
    with patch('sys.stderr', new_callable=StringIO) as mock_write:
      self.assertIsInstance(Project.make([]), FauxProject)
      self.assertEqual(mock_write.getvalue(), 'Project [] was empty.\n')

    with patch('builtins.print') as mock_debug:
      self.assertIsInstance(Project.make(tuple()), FauxProject)
      self.assertIsInstance(Project.make(set([])), FauxProject)
      self.assertIsInstance(Project.make(dict()), FauxProject)
      self.assertIsInstance(Project.make(None), FauxProject)
      self.assertEqual(mock_debug.call_count, 4)

  def test_make_fails(self):
    '''case _:'''
    with self.assertRaises(Exception):
      Project.make(123)

  def test_nearest_project_by_name(self): pass

  def test_all(self): pass
  def test_all(self):
    _uuid = uuid4()

#    with patch('lib.db.get', return_value={str(_uuid): 'This and that', 'this and that': str(_uuid)}) as mock_get:
#    with patch('lib.db.get', side_effect={str(_uuid): 'This and that', 'this and that': str(_uuid)}) as mock_get:
    with patch('lib.db.get', return_value={str(_uuid): 'This and that', 'this and that': str(_uuid)}) as mock_get:
      with patch('lib.project.Project.make', return_value=Project(_uuid, 'This and that')) as mock_project:
        all_projects = Project.all()

        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_get.call_args.args, ('projects',))

        all_projects = list(all_projects)
        self.assertEqual(len(all_projects), 1)
        self.assertEqual(all_projects[0], Project(_uuid, 'This and that'))

#      first_project = all_projects[0]
#      self.assertIsInstance(first_project, Project)
#      self.assertEqual(first_project.id, _uuid)
#      self.assertEqual(first_project.name, 'This and that')
#      self.assertEqual(first_project.state, 'stopped')
#      self.assertIsInstance(first_project.when, datetime)


  def test_cache(self):
    with patch('lib.db.add') as mock_add:
      _uuid = uuid4()
      Project.cache(123, Project(_uuid, "I'm a real boy!", when=self.known_date))
      self.assertTrue(mock_add.called)
      self.assertEqual(mock_add.call_count, 2)
      self.assertEqual(mock_add.mock_calls[0].args, ('cache:tickets', {_uuid: 123}))
      self.assertEqual(mock_add.mock_calls[1].args, ('cache:recorded', {_uuid: self.known_date}))

#  def test_collate(self): self.fail("Implement me")
  def test_collate(self): pass

class TestFauxProject(TestWornBase):
  def test_init(self):
    faux = FauxProject()
    self.assertIsInstance(faux.id, UUID)
    self.assertEqual(faux.name, 'Faux')
    self.assertEqual(faux.state, 'stopped')
    self.assertIsInstance(faux.when, datetime)

  def test_add(self):
    faux = FauxProject()
    with self.assertRaises(Exception):
      faux.add()

class TestLogProject(TestWornBase):
  def test_init(self):
#    with self.assertRaises(Exception):
#      LogProject(uuid4(), 'Bad when value', 'stopped', str(self.now.timestamp()).replace('.',''))

    _uuid = uuid4()
    tsid = f'''{str(self.known_date.timestamp()).replace('.', '')}'''
    log = LogProject(_uuid, 'IDK', 'started', tsid)
    self.assertEqual(log.id, _uuid)
    self.assertEqual(log.name, 'IDK')
    self.assertEqual(log.state, 'started')
    self.assertEqual(log.when, self.known_date)
    self.assertEqual(log.timestamp_id, tsid)
    self.assertEqual(log.serial, 0)

    _uuid = uuid4()
    tsid = self._timestamp_id(self.known_date, 3)
    log = LogProject(_uuid, 'IDK', 'started', tsid)
    self.assertEqual(log.id, _uuid)
    self.assertEqual(log.name, 'IDK')
    self.assertEqual(log.state, 'started')
    self.assertEqual(log.when, self.known_date)
    self.assertEqual(log.timestamp_id, tsid)
    self.assertEqual(log.serial, 3)

    _uuid = uuid4()
    tsid = self._timestamp_id(self.known_date, '*')
    log = LogProject(_uuid, 'IDK', 'started', tsid)
    self.assertEqual(log.id, _uuid)
    self.assertEqual(log.name, 'IDK')
    self.assertEqual(log.state, 'started')
    self.assertEqual(log.when, self.known_date)
    self.assertEqual(log.timestamp_id, tsid)
    self.assertEqual(log.serial, 0)

  def test_remove(self):
    log = LogProject(uuid4(), 'A project', state='started', when=self._timestamp_id(self.known_date))
    with patch('lib.db.rm') as mock_rm:
      log.remove()
      self.assertTrue(mock_rm.called)
      self.assertEqual(mock_rm.call_count, 1)
      self.assertEqual(mock_rm.call_args.args, ('logs', self._timestamp_id(self.known_date)))
  
#  def test_log_format(self):
#    from lib.colors import colors
#    _uuid = uuid4()
#    project = Project(_uuid, 'What are you doing right now?', 'started', self.known_date)
#    self.assertEqual(f'{project:log}', f"2024-03-23 21:50:00 state {colors.fg.green}'started'{colors.reset} id {_uuid} project 'What are you doing right now?'")
#
#    _uuid = uuid4()
#    project = Project(_uuid, 'Are you there?', 'stopped', self.known_date)
#    self.assertEqual(f'{project:log}', f"2024-03-23 21:50:00 state {colors.fg.orange}'stopped'{colors.reset} id {_uuid} project 'Are you there?'")

if __name__ == '__main__':
  unittest.main(buffer=True)
