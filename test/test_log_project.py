from test import *
from lib.project import Project, LogProject
from lib import now

def _time_traveled(since=now(), direction='back', **kw):
  if direction == 'back':
    return since - timedelta(**kw)
  elif direction == 'forward':
    return since + timedelta(**kw)

class TestLogProject(TestWornBase):
  def test_init(self):
#    with self.assertRaises(InvalidTimeE):
#      LogProject(uuid4(), 'Bad when value', 'stopped', str(self.now.timestamp()).replace('.',''))
    _uuid = uuid4()
    tsid = f'{self.known_date:%s%f}-0'
    log = LogProject(_uuid, 'IDK', 'started', tsid)
    self.assertEqual(log.id, _uuid)
    self.assertEqual(log.name, 'IDK')
    self.assertEqual(log.state, 'started')
    self.assertEqual(log.when, self.known_date)
    self.assertEqual(log.timestamp_id, tsid)
    self.assertEqual(log.serial, 0)

    _uuid = uuid4()
    tsid = f'{self.known_date:%s%f}-3'
    log = LogProject(_uuid, 'IDK', 'started', tsid)
    self.assertEqual(log.id, _uuid)
    self.assertEqual(log.name, 'IDK')
    self.assertEqual(log.state, 'started')
    self.assertEqual(log.when, self.known_date)
    self.assertEqual(log.timestamp_id, tsid)
    self.assertEqual(log.serial, 3)

    _uuid = uuid4()
    tsid = f'{self.known_date:%s%f}-*'
    log = LogProject(_uuid, 'IDK', 'started', tsid)
    self.assertEqual(log.id, _uuid)
    self.assertEqual(log.name, 'IDK')
    self.assertEqual(log.state, 'started')
    self.assertEqual(log.when, self.known_date)
    self.assertEqual(log.timestamp_id, tsid)
    self.assertEqual(log.serial, '*')

  def test_add_time_before_oldest_id(self):
    '''Test that the code properly raises an exception when the date is earlier than the last recorded date'''
    _uuid = uuid4()
    _when = now()
    p = LogProject(_uuid, 'What are we doing?', when=_time_traveled(_when, seconds=4))
    with self.assertRaises(Project.InvalidTimeE):
      with patch('lib.db.has', return_value=True) as dbh:
        with patch('lib.db.xinfo', return_value=f'{_time_traveled(_when, seconds=3):%s%f}-0') as dbi:
          with patch('lib.db.add') as mock_add:
            p.add()
            self.assertEqual(mock_add.call_count, 0)

  def test_add_future_time(self):
    '''Test that the code properly records entries when the date is in the future'''
    _uuid = uuid4()
    p = LogProject(_uuid, '  What are we doing?  ')
    with patch('lib.db.has', return_value=True) as dbh:
      with patch('lib.db.add') as mock_add:
        p.log('stopped', self.known_date)

        self.assertEqual(dbh.call_count, 1)
        self.assertEqual(mock_add.call_count, 2)
        self.assertEqual(mock_add.mock_calls[0].args, ('projects', {'what are we doing?': _uuid, _uuid: 'What are we doing?'}))
        self.assertEqual(mock_add.mock_calls[1].args, ('logs', {'project': _uuid, 'state': 'stopped'}))
        self.assertEqual(mock_add.mock_calls[0].kwargs, dict(nx=True))

      _uuid = uuid4()
      p = LogProject(_uuid, '  What else are we doing?  ')
      with patch('builtins.input', return_value='y') as mock_in:
        with patch('lib.db.add') as mock_add:
          p.log('stopped', _time_traveled('forward', seconds=20))

        self.assertEqual(mock_in.call_count, 1)
        self.assertEqual(mock_add.call_count, 2)
        self.assertEqual(mock_add.mock_calls[0].args, ('projects', {'what else are we doing?': _uuid, _uuid: 'What else are we doing?'}))
        self.assertEqual(mock_add.mock_calls[1].args, ('logs', {'project': _uuid, 'state': 'stopped'}))
        self.assertEqual(mock_add.mock_calls[0].kwargs, dict(nx=True))

      _uuid = uuid4()
      p = LogProject(_uuid, "Don't start in the future")
      with patch('builtins.input', return_value='not yes') as mock_in:
        with patch('lib.db.add') as mock_add:
          p.log('stopped', _time_traveled('forward', seconds=20))

        self.assertEqual(mock_in.call_count, 1)
        self.assertEqual(mock_add.call_count, 0)

  def test_vanillaish_add(self):
    _uuid = uuid4()
    _when = now()
    p = LogProject(_uuid, 'Packed some things', 'stopped', _time_traveled(_when, seconds=2))
    with patch('lib.db.has', return_value=False) as dernt_hav:
      with patch('lib.db.add') as mock_add:
        p.add()

        self.assertEqual(dernt_hav.call_count, 1)
        self.assertEqual(mock_add.call_count, 1)
        self.assertEqual(mock_add.call_args.args, ('logs', {'project': _uuid, 'state': 'stopped', 'id': f'{_time_traveled(_when, seconds=2):%s%f}-0'}))
 
    p = LogProject(_uuid, 'Your phone is going off', 'started', _time_traveled(_when, seconds=2))
    with patch('lib.db.has', return_value=True) as dbh:
      with patch('lib.db.xinfo', return_value=f'{_time_traveled(_when, seconds=3):%s%f}-0') as dbi:
        with patch('lib.db.add') as mock_add:
          p.add()

          self.assertEqual(dbh.call_count, 1)
          self.assertEqual(dbi.call_count, 1)
          self.assertEqual(mock_add.call_count, 1)
          self.assertEqual(mock_add.call_args.args, ('logs', {'project': _uuid, 'state': 'started', 'id': f'{_time_traveled(_when, seconds=2):%s%f}-0'}))

  def test_remove(self):
    log = LogProject(uuid4(), 'A project', state='started', when=self.known_date)
    with patch('lib.db.rm') as mock_rm:
      log.remove()
      self.assertTrue(mock_rm.called)
      self.assertEqual(mock_rm.call_count, 1)
      self.assertEqual(mock_rm.call_args.args, ('logs', f'{self.known_date:%s%f}-0'))
  
  def test_rename(self):
    log = LogProject(uuid4(), 'I used to be a tree, please cry with me.', 'stopped', now())
    with self.assertRaises(Project.InvalidTypeE):
      log.rename('But now I am a real boy!')

  def test_all(self):
    _uuid = uuid4()
    p1 = LogProject(uuid4(), 'This and that',            state='stopped', when=_time_traveled(seconds=5))
    p2 = LogProject(uuid4(), 'This is the project name', state='started', when=_time_traveled(seconds=3))
    p3 = LogProject(p2.id,   'This is the project name', state='stopped', when=_time_traveled(seconds=1))
    sample_log_entries = [
      (p1.timestamp_id, {'project': str(p1.id), 'state': 'stopped'}),
      (p2.timestamp_id, {'project': str(p2.id), 'state': 'started'}),
      (p3.timestamp_id, {'project': str(p2.id), 'state': 'stopped'})
    ]
    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
      with patch('lib.project.LogProject.make', side_effect=iter([p1, p2, p3])) as mock_project:
        all_projects = list(LogProject.all())

        self.assertEqual(mock_range.call_count, 1)
        self.assertEqual(mock_range.call_args.args, ('logs',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start='-', count=None))

        self.assertEqual(mock_project.call_count, 3)
        self.assertEqual(mock_project.mock_calls[0].args, (sample_log_entries[0][1], ))
        self.assertEqual(mock_project.mock_calls[0].kwargs, dict(when=sample_log_entries[0][0]))
        self.assertEqual(mock_project.mock_calls[1].args, (sample_log_entries[1][1], ))
        self.assertEqual(mock_project.mock_calls[1].kwargs, dict(when=sample_log_entries[1][0]))
        self.assertEqual(mock_project.mock_calls[2].args, (sample_log_entries[2][1], ))
        self.assertEqual(mock_project.mock_calls[2].kwargs, dict(when=sample_log_entries[2][0]))
 
    _vuuid = uuid4()
    when = _time_traveled(seconds=4)
    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
      with patch('lib.project.LogProject.make', side_effect=iter([p1, p2, p3])) as mock_project:
        all_projects = list(LogProject.all(count=9, _version=_vuuid))

        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 1)
        self.assertEqual(mock_range.call_args.args, (f'logs-{_vuuid}',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start='-', count=9))
        self.assertEqual(mock_project.call_count, 3)
 
  def test_all_matching_since(self): pass
#    when = _time_traveled(seconds=4)
#    p1 = LogProject(uuid4(), 'The flag of Hollywood',  state='stopped', when=_time_traveled(seconds=5))
#    p2 = LogProject(uuid4(), 'Will you do me a favor', state='started', when=_time_traveled(seconds=3))
#    p3 = LogProject(p2.id,   p2.name,                  state='stopped', when=_time_traveled(seconds=1))
#    p4 = LogProject(p1.id,   p1.name,                  state='started', when=datetime.now())
#    sample_log_entries = [
#      (p1.timestamp_id, {'project': str(p1.id), 'state': 'stopped'}),
#      (p2.timestamp_id, {'project': str(p2.id), 'state': 'started'}),
#      (p3.timestamp_id, {'project': str(p2.id), 'state': 'stopped'}),
#      (p4.timestamp_id, {'project': str(p1.id), 'state': 'started'})
#    ]
#    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
#      with patch('lib.db.get') as mock_get:
#        with patch('lib.project.LogProject.make', side_effect=iter([p2, p3, p4])) as mock_project:
#          r = list(LogProject.all_matching_since(p1.name, when))
#
#          self.assertEqual(mock_range.call_count, 1)
#          self.assertEqual(mock_range.call_args.args, ('logs',))
#          self.assertEqual(mock_range.call_args.kwargs, dict(start=f'{when:%s%f}-0', count=None))
#          self.assertEqual(mock_get.call_count, 3)
#          self.assertEqual(mock_project.call_count, 3)
#
#          self.assertListEqual(r, [p2, p3])
#
#    _vuuid = uuid4()
#    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
#      with patch('lib.db.get') as mock_get:
#        with patch('lib.project.LogProject.make', side_effect=iter([p2, p3, p4])) as mock_project:
#          r = list(LogProject.all_matching_since(p1.name, when, _version=_vuuid))
#
#          self.assertEqual(mock_range.call_count, 1)
#          self.assertEqual(mock_range.call_args.args, (f'logs-{_vuuid}',))
#          self.assertEqual(mock_range.call_args.kwargs, dict(start=f'{when:%s%f}-0', count=None))
#          self.assertEqual(mock_get.call_count, 3)
#          self.assertEqual(mock_project.call_count, 3)
#
#          self.assertListEqual(r, [p2, p3])

  def test_all_since(self):
    when = datetime.now()
    p1 = LogProject(uuid4(), 'This is the project name', state='started', when=f'{_time_traveled(when, seconds=3):%s%f}-0')
    p2 = LogProject(p1.id,   'This is the project name', state='stopped', when=f'{_time_traveled(when, seconds=1):%s%f}-0')
    sample_log_entries = [
      (p1.timestamp_id, {'project': str(p2.id), 'state': 'started'}),
      (p2.timestamp_id, {'project': str(p2.id), 'state': 'stopped'})
    ]
    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
      with patch.object(LogProject, 'make', side_effect=iter([p1, p2])) as mock_project:
        r = list(LogProject.all_since(_time_traveled(when, seconds=4)))

        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 1)
        self.assertEqual(mock_range.call_args.args, ('logs',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start=f'{_time_traveled(when, seconds=4):%s%f}-0', count=None))

        self.assertEqual(mock_project.call_count, 2)

        self.assertListEqual(r, [p1, p2])

    _vuuid = uuid4()
    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
      with patch('lib.project.LogProject.make', side_effect=iter([p1, p2])) as mock_project:
        r = LogProject.all_since(_time_traveled(when, seconds=4), _version=_vuuid)

        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 1)
        self.assertEqual(mock_range.call_args.args, (f'logs-{_vuuid}',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start=f'{_time_traveled(when, seconds=4):%s%f}-0', count=None))

  def test_all_matching(self):
    p1 = LogProject(uuid4(), 'This and that',            state='stopped', when=_time_traveled(seconds=5))
    p2 = LogProject(uuid4(), 'This is the project name', state='started', when=_time_traveled(seconds=3))
    p3 = LogProject(p2.id,   'This is the project name', state='stopped', when=_time_traveled(seconds=1))
    sample_log_entries = [
      (p1.timestamp_id, {'project': str(p1.id), 'state': 'stopped'}),
      (p2.timestamp_id, {'project': str(p2.id), 'state': 'started'}),
      (p3.timestamp_id, {'project': str(p2.id), 'state': 'stopped'})
    ]
    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
      with patch('lib.project.LogProject.make', side_effect=iter([p1, p2, p3])) as mock_project:
        r = list(LogProject.all_matching(p2.name))

        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 1)
        self.assertEqual(mock_range.call_args.args, ('logs',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start='-', count=None))

        self.assertEqual(mock_project.call_count, 3)

        self.assertListEqual(r, [p2, p3])

    _vuuid = uuid4()
    with patch('lib.db.xrange', return_value=sample_log_entries) as mock_range:
      with patch('lib.project.Project.make', side_effect=iter([p1, p2, p3])) as mock_project:
        r = LogProject.all_matching(p2.name, _version=_vuuid)

        self.assertTrue(mock_range.called)
        self.assertEqual(mock_range.call_count, 1)
        self.assertEqual(mock_range.call_args.args, (f'logs-{_vuuid}',))
        self.assertEqual(mock_range.call_args.kwargs, dict(start='-', count=None))

  def test_log_format_with_colors(self):
    from lib.colors import colors
    _uuid = uuid4()
    project = LogProject(_uuid, 'paksu tölkki', 'started', self.known_date)
    self.assertEqual(f'{project:log!t}', f"""1711255800000000-0 2024-03-23 21:50:00 state "{colors.fg.green}started{colors.reset}" id {_uuid} project 'paksu tölkki'""")
    self.assertEqual(f'{project:log}',   f"""2024-03-23 21:50:00 state "{colors.fg.green}started{colors.reset}" id {_uuid} project 'paksu tölkki'""")

  def test_log_format_without_colors(self):
    self.fail('fix me')
    from lib.nocolors import colors
    _uuid = uuid4()
    project = LogProject(_uuid, 'ohut tölkki', 'stopped', self.known_date)
    self.assertEqual(f'{project:log!t}', f"""17112558000-0 2024-03-23 21:50:00 state "stopped{colors.reset}" id {_uuid} project 'ohut tölkki'""")
    self.assertEqual(f'{project:log}',   f"""2024-03-23 21:50:00 state "stopped{colors.reset}" id {_uuid} project 'ohut tölkki'""")

  def test_edit_log_time(self): pass
  def test_edit_last_log_name(self): pass
  def test_edit_last_log_state(self):
    _uuid = uuid4()
    with patch('lib.project.LogProject.make', side_effect=iter([Project(_uuid, 'This and that')])) as mock_project:
      pass

if __name__ == '__main__':
  unittest.main(buffer=True)
