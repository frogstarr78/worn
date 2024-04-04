from test import *
from lib.project import FauxProject, Project, LogProject
from lib.report import Report
from datetime import datetime

now = datetime.now

class TestReport(TestWornBase):
    def test_init(self):
      with patch.object(Project, 'make') as mock_last:
        r = Report([])

        self.assertTrue(mock_last.called)
        self.assertEqual(mock_last.call_count, 1)
        self.assertEqual(mock_last.call_args.args, ('last',))

        self.assertEqual({}, r._data)
        self.assertIsNone(r.at)
        self.assertEqual('h', r.scale)
        self.assertFalse(r.include_all)
        self.assertTrue(r.show_header)

      with self.assertRaises(Exception):
        Report([], scale='y')

      when = now()
      p1 = LogProject(uuid4(), 'Abc', 'started', when - timedelta(seconds=66))
      p2 = LogProject(p1.id,            'Abc', 'stopped', when)

      p3 = LogProject(uuid4(), 'cBa', 'started', when - timedelta(seconds=72))
      p4 = LogProject(p3.id,            'cBa', 'stopped', when)

      p5 = LogProject(uuid4(), 'BCa', 'started', when - timedelta(minutes=3))
      p6 = LogProject(p5.id,            'BCa', 'stopped', when)

      p7 = Project(uuid4(), 'Rogue underniceness exemplified')

      with patch.object(Project, 'make') as mock_make:
        with patch.object(Project, 'all', return_value=[p1, p3, p5, p7]) as mock_all:
          r = Report([p1, p2, p3, p4, p5, p6], self.known_date, 'w', include_all=True, show_header=False)

          self.assertTrue(mock_make.called)
          self.assertEqual(mock_make.call_count, 1)
          self.assertEqual(mock_make.call_args.args, ('last',))

          self.assertTrue(mock_all.called)
          self.assertEqual(mock_all.call_count, 1)

          self.maxDiff = 3000
          self.assertDictEqual({p3: 72.0, p1: 66.0, p5: 180.0, p7: 0.0}, r._data)
          self.assertEqual(self.known_date, r.at)
          self.assertEqual('w', r.scale)
          self.assertTrue(r.include_all)
          self.assertFalse(r.show_header)

      when = now()
      p1   = LogProject(uuid4(), 'Han-Kengai Beech', 'started', (when - timedelta(seconds=92)))
      p2   = LogProject(p1.id,            p1.name,            'stopped', (when - timedelta(seconds=33)))
      last = Project(p1.id,               p1.name,            'started', (when - timedelta(seconds=10)))
      with patch.object(Project, 'make', return_value=last) as mock_make:
        with patch.object(Project, 'all') as mock_all:
          r = Report([p1, p2], self.known_date)

          self.assertTrue(mock_make.called)
          self.assertEqual(mock_make.call_count, 1)
          self.assertEqual(mock_make.call_args.args, ('last',))

          self.assertEqual(69.0, r._data[p1])

    def test_mail(self):
      _uuid = uuid4()
      with patch('lib.db.get') as mock_get:
        r = Report({Project(_uuid, 'Bye'): 3}, datetime.now(), 's', include_all=False, show_header=True)
        with patch('builtins.print') as mock_debug:
          r.mail('me', 'simple', noop=True)
          self.assertEqual(mock_debug.call_count, 1)

        with patch('smtplib.SMTP') as fake_mail:
          r.mail('you', 'simple')
          self.assertEqual(fake_mail.call_count, 1)
          self.assertEqual(fake_mail.call_args.args, ('localhost',))

#          self.assertEqual(fake_mail.set_debuglevel.call_count, 1)
#          self.assertEqual(fake_mail.set_debuglevel.call_args.args, (1,))

#          self.assertEqual(fake_mail.sendmail.call_count, 1)
#          self.assertEqual(fake_mail.sendmail.call_args.args, ('scott@viviotech.net', 'you', f'''{3: >8}s id {_uuid} project 'Bye'\n'''))
        

    def test_sorted_data(self):
      _uuid = uuid4()
      _uuid2 = uuid4()
      with patch.object(Project, 'make', return_value=Project(uuid4(), 'React', 'stopped')) as mock_last:
        rep = Report({Project(_uuid, 'Bye'): 30, Project(_uuid2, 'Abc'): 50})
        res = rep._sorted_data
        self.assertEqual((Project(_uuid2, 'Abc'), 0), res[0])
        self.assertEqual((Project(_uuid, 'Bye'), 0), res[1])

    def test_post_with_noop_doesnt_post(self):
      '''
        Test that a call to the post method of report, with the noop argument, doesn't actually attempt to post anything, merely output the url that it would have posted to.
        Ensure that it acts like a successful result, though.
      '''
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch('builtins.print') as mock_debug:
          with patch.multiple(Project, cache=DEFAULT, make=DEFAULT, all=DEFAULT) as whos_line:
            p1  = LogProject(uuid4(), 'bob',   'started', when - timedelta(seconds=78))
            p2  = LogProject(p1.id,            p1.name, 'stopped', when)
            r   = Report([p1, p2])
            res = r.post(1, 'hello', noop=True)

            self.assertFalse(whos_line['cache'].called)
            self.assertEqual(whos_line['cache'].call_count, 0)

            self.assertEqual(mock_debug.call_args.args, (f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id=1&time_spent=1.3&body="hello"',))
            self.assertTrue(res)

    def test_post_with_custom_comment_and_sccessful_result(self):
      '''
        Test that we can post, including using a custom comment, and that a successful result is returned as expected
      '''
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch.multiple(Project, cache=DEFAULT, make=DEFAULT, all=DEFAULT) as whos_line:
          p1  = LogProject(uuid4(), 'Bob',   'started', when - timedelta(seconds=72))
          p2  = LogProject(p1.id,            p1.name, when=when)
          r   = Report([p1, p2])

          with patch('requests.post') as mock_req:
            mock_req.return_value.status_code = 200
            res = r.post(1, 'hello {project.state}')

            self.assertTrue(whos_line['cache'].called)
            self.assertEqual(whos_line['cache'].call_count, 1)
            self.assertEqual(whos_line['cache'].call_args.args, (1, p1))

            self.assertTrue(mock_req.called)
            self.assertEqual(mock_req.call_count, 1)
            self.assertEqual(mock_req.call_args.args, ('https://portal.viviotech.net/api/2.0/',))
            self.assertEqual(mock_req.call_args.kwargs, dict(params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=1, time_spent=1.2, body='hello started')))
            self.assertTrue(res)

    def test_post_with_custom_comment_but_failed_result(self):
      '''
        Test that we can post, including using a custom comment, and that a failed result is returned as expected
      '''
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch.multiple(Project, cache=DEFAULT, make=DEFAULT, all=DEFAULT) as whos_line:
          p1  = LogProject(uuid4(), 'Joe',   'started', when - timedelta(seconds=72))
          p2  = LogProject(p1.id,            p1.name, when=when)
          r   = Report([p1, p2])

          with patch('requests.post', return_value=Mock(status_code=400)) as mock_req:
            mock_req.return_value.status_code = 400
            res = r.post(1, 'hello {project.name}')

            self.assertTrue(whos_line['cache'].called)
            self.assertEqual(whos_line['cache'].call_count, 1)
            self.assertEqual(whos_line['cache'].call_args.args, (1, p1))

            self.assertTrue(mock_req.called)
            self.assertEqual(mock_req.call_count, 1)
            self.assertEqual(mock_req.call_args.args, ('https://portal.viviotech.net/api/2.0/',))
            self.assertEqual(mock_req.call_args.kwargs, dict(params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=1, time_spent=1.2, body='hello Joe')))
            self.assertFalse(res)

    def test_format(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        r = Report({})
        with patch.object(Report, '_csv_format', return_value='abc') as csv_fmt:
          self.assertEqual('{0:csv}'.format(r), 'abc')
          self.assertTrue(csv_fmt.called)
          self.assertEqual(csv_fmt.call_count, 1)

        with patch.object(Report, '_simple_format', return_value='cba') as simple_fmt:
          self.assertEqual('{0:simple}'.format(r), 'cba')
          self.assertTrue(csv_fmt.called)
          self.assertEqual(csv_fmt.call_count, 1)

        with patch.object(Report, '_time_format', return_value='a4q') as time_fmt:
          self.assertEqual('{0:time}'.format(r), 'a4q')
          self.assertTrue(csv_fmt.called)
          self.assertEqual(csv_fmt.call_count, 1)

        self.assertIn('<lib.report.Report object at 0x7', f'{r!s}')

    def test_format_simple(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        r = Report({})
        self.assertIn('Time spent report', r._simple_format())
        r.show_header=False
        self.assertNotIn('Time spent report', r._simple_format())

        _now = now()
        _data = (
          Project(0, 'aw', 'started', when=_now - timedelta(weeks=1, days=2, hours=3, minutes=4, seconds=5)),
          Project(0, 'aw', 'stopped', when=_now)
        )
        rep = Report(_data, scale='w')
        res = rep._simple_format()
        self.assertIn(" total   788645 id 0 project 'aw'", res)
        self.assertIn('01w 02d 03h 04m 05s', res)
        self.assertIn('01w 02d 03h 04m 05s                                                                 Total\n', res)

        rep.scale = 'd'
        res = rep._simple_format()
        self.assertIn(" total   788645 id 0 project 'aw'", res)
        self.assertIn('009d 03h 04m 05s', res)
        self.assertIn('009d 03h 04m 05s                                                                 Total\n', res)

        rep.scale = 'h'
        res = rep._simple_format()
        self.assertIn(" total   788645 id 0 project 'aw'", res)
        self.assertIn('0219h 04m 05s', res)
        self.assertIn('0219h 04m 05s                                                                 Total\n', res)

        rep.scale = 'm'
        res = rep._simple_format()
        self.assertIn(" total   788645 id 0 project 'aw'", res)
        self.assertIn('13144m 05s', res)
        self.assertIn('13144m 05s                                                                 Total\n', res)

        rep.scale = 's'
        res = rep._simple_format()
        self.assertIn("  788645s id 0 project 'aw'", res)
        self.assertNotIn('Total\n', res)

        rep.scale = 'o'
        with self.assertRaises(Exception):
          rep._simple_format()

    def test_format_csv(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        r = Report({})
        self.assertIn('Time spent report', r._csv_format())
        r.show_header=False
        self.assertNotIn('Time spent report', r._csv_format())

        _now = now()
        _data = (
          Project(9, 'BMW', 'started', when=_now - timedelta(weeks=2, days=3, hours=4, minutes=5, seconds=1)),
          Project(9, 'bMW', 'stopped', when=_now)
        )
        diff = _data[1].when - _data[0].when
        _diff = diff.days * (24*3600) + diff.seconds
        rep = Report(_data, scale='w')
        res = rep._csv_format()
        self.assertIn("weeks,days,hours,minutes,seconds,total (in seconds),id,project,running", res)
        self.assertIn(f'2,3,4,5,1,{_diff},9,"BMW",false', res)

        rep.scale = 'd'
        res = rep._csv_format()
        self.assertIn("days,hours,minutes,seconds,total (in seconds),id,project,running", res)
        self.assertNotIn('weeks', res)
        self.assertIn(f'17,4,5,1,{_diff},9,"BMW",false', res)

        rep.scale = 'h'
        res = rep._csv_format()
        self.assertIn("hours,minutes,seconds,total (in seconds),id,project,running", res)
        self.assertNotIn('weeks,', res)
        self.assertNotIn('days,', res)
        self.assertIn(f'412,5,1,{_diff},9,"BMW",false', res)

        rep.scale = 'm'
        res = rep._csv_format()
        self.assertIn("minutes,seconds,total (in seconds),id,project,running", res)
        self.assertNotIn('weeks,', res)
        self.assertNotIn('days,', res)
        self.assertNotIn('hours,', res)
        self.assertIn(f'24725,1,{_diff},9,"BMW",false', res)

        rep.scale = 's'
        res = rep._csv_format()
        self.assertIn("total (in seconds),id,project,running", res)
        self.assertNotIn('weeks,', res)
        self.assertNotIn('days,', res)
        self.assertNotIn('hours,', res)
        self.assertNotIn('minutes,', res)
        self.assertIn(f'{_diff},9,"BMW",false', res)
        self.assertEqual(1483501,_diff)

    def test_format_time(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        r = Report({})
        self.assertIn('  h  m  s', r._time_format())
        r.show_header=False
        self.assertNotIn('  h  m  s', r._time_format())

    def test_how_long_in_minutes(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch.multiple(Project, make=DEFAULT, all=DEFAULT) as whose_line:
          p1   = LogProject(uuid4(), 'Han-Kengai Beech', 'started', (when - timedelta(seconds=152)))
          p2   = LogProject(p1.id,   p1.name,            'stopped', (when - timedelta(seconds=38)))
          diff = p2.when - p1.when
          self.assertEqual(152-38, diff.seconds)
          r = Report([p1, p2], scale='h')
          self.assertEqual((0, 1.0, 54), r._how_long(diff.seconds))
          r.scale = 'm'
          self.assertEqual((1.0, 54), r._how_long(diff.seconds))
          r.scale = 's'
          self.assertEqual((114,), r._how_long(diff.seconds))

    def test_how_long_in_hours(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch.multiple(Project, make=DEFAULT, all=DEFAULT) as whose_line:
          p1   = LogProject(uuid4(), 'Kengai Juniper', 'started', (when - timedelta(hours=2, minutes=3, seconds=34)))
          p2   = LogProject(p1.id,   p1.name,          'stopped', when)
          diff = p2.when - p1.when
          r = Report([p1, p2], scale='d')
          self.assertEqual((0, 2, 3, 34), r._how_long(diff.seconds))
          r.scale = 'h'
          self.assertEqual((2, 3, 34), r._how_long(diff.seconds))
          r.scale = 'm'
          self.assertEqual((123, 34), r._how_long(diff.seconds))
          r.scale = 's'
          self.assertEqual((7414,), r._how_long(diff.seconds))

    def test_how_long_in_days(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch.multiple(Project, make=DEFAULT, all=DEFAULT) as whose_line:
          p1   = LogProject(uuid4(), 'Hokidachi Maple', 'started', (when - timedelta(days=3, hours=13, minutes=7, seconds=17)))
          p2   = LogProject(p1.id,   p1.name,           'stopped', when)
          diff = p2.when - p1.when
          _diff = diff.days * (24*3600) + diff.seconds
          r = Report([p1, p2], scale='w')
          self.assertEqual(306437, _diff)
          self.assertEqual((0, 3, 13, 7, 17), r._how_long(_diff))
          r.scale = 'd'
          self.assertEqual((3, 13, 7, 17), r._how_long(_diff))
          r.scale = 'h'
          self.assertEqual((85, 7, 17), r._how_long(_diff))
          r.scale = 'm'
          self.assertEqual((5107, 17), r._how_long(_diff))
          r.scale = 's'
          self.assertEqual((306437,), r._how_long(_diff))

    def test_how_long_in_weeks(self):
      with patch.object(Project, 'make', return_value=Project(5, 'Ima sneeky thing', 'stopped')) as fake_last_not_running:
        when = now()
        with patch.multiple(Project, make=DEFAULT, all=DEFAULT) as whose_line:
          p1   = LogProject(uuid4(), 'Fukinagashi Pine', 'started', (when - timedelta(weeks=1, days=2, hours=23, minutes=17, seconds=27)))
          p2   = LogProject(p1.id,   p1.name,           'stopped', when)
          diff = p2.when - p1.when
          _diff = diff.days * (24*3600) + diff.seconds
          r = Report([p1, p2], scale='w')
          self.assertEqual((1, 2, 23, 17, 27), r._how_long(_diff))
          r.scale = 'd'
          self.assertEqual((9, 23, 17, 27), r._how_long(_diff))
          r.scale = 'h'
          self.assertEqual((239, 17, 27), r._how_long(_diff))
          r.scale = 'm'
          self.assertEqual((14357, 27), r._how_long(_diff))
          r.scale = 's'
          self.assertEqual((861447,), r._how_long(_diff))
