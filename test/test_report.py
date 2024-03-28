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
      p1 = LogProject(self.random_uuid, 'Abc', 'started', when - timedelta(seconds=66))
      p2 = LogProject(p1.id,            'Abc', 'stopped', when)

      p3 = LogProject(self.random_uuid, 'cBa', 'started', when - timedelta(seconds=72))
      p4 = LogProject(p3.id,            'cBa', 'stopped', when)

      p5 = LogProject(self.random_uuid, 'BCa', 'started', when - timedelta(minutes=3))
      p6 = LogProject(p5.id,            'BCa', 'stopped', when)

      p7 = Project(self.random_uuid, 'Rogue underniceness exemplified')

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
      p1   = LogProject(self.random_uuid, 'Han-Kengai Beech', 'started', (when - timedelta(seconds=92)))
      p2   = LogProject(p1.id,            p1.name,            'stopped', (when - timedelta(seconds=33)))
      last = Project(p1.id,               p1.name,            'started', (when - timedelta(seconds=10)))
      with patch.object(Project, 'make', return_value=last) as mock_make:
        with patch.object(Project, 'all') as mock_all:
          r = Report([p1, p2], self.known_date)

          self.assertTrue(mock_make.called)
          self.assertEqual(mock_make.call_count, 1)
          self.assertEqual(mock_make.call_args.args, ('last',))

          self.assertEqual(69.0, r._data[p1])

#    def test_mail(self): self.fail('implement me')
    def test_mail(self): pass

#    def test_sorted_data(self): self.fail('implement me')
    def test_sorted_data(self): pass

    def test_post_with_noop_doesnt_post(self):
      '''
        Test that a call to the post method of report, with the noop argument, doesn't actually attempt to post anything, merely output the url that it would have posted to.
        Ensure that it acts like a successful result, though.
      '''
      when = now()
      with patch('sys.stderr', new_callable=StringIO) as mock_debug:
        with patch.multiple(Project, cache=DEFAULT, make=DEFAULT, all=DEFAULT) as whos_line:
          p1  = LogProject(self.random_uuid, 'bob',   'started', when - timedelta(seconds=78))
          p2  = LogProject(p1.id,            p1.name, 'stopped', when)
          r   = Report([p1, p2])
          res = r.post(1, 'hello', noop=True)

          self.assertFalse(whos_line['cache'].called)
          self.assertEqual(whos_line['cache'].call_count, 0)

          self.assertEqual(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id=1&time_spent=1.3&body="hello"\n', mock_debug.getvalue())
          self.assertTrue(res)

    def test_post_with_custom_comment_and_sccessful_result(self):
      '''
        Test that we can post, including using a custom comment, and that a successful result is returned as expected
      '''
      when = now()
      with patch.multiple(Project, cache=DEFAULT, make=DEFAULT, all=DEFAULT) as whos_line:
        p1  = LogProject(self.random_uuid, 'Bob',   'started', when - timedelta(seconds=72))
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
      when = now()
      with patch.multiple(Project, cache=DEFAULT, make=DEFAULT, all=DEFAULT) as whos_line:
        p1  = LogProject(self.random_uuid, 'Joe',   'started', when - timedelta(seconds=72))
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

    def test_format(self): pass
#    def test_format(self):
#      self.fail('implement me')
#      with patch.object(Report, '_csv_format', return_value='abc') as csv_fmt:
#        self.assertEqual('{0:csv}'.format(Report({})), 'abc')
#        self.assertTrue(csv_fmt.called)
#        self.assertEqual(csv_fmt.call_count, 1)
#
#      with patch.object(Report, '_simple_format', return_value='cba') as simple_fmt:
#        self.assertEqual('{0:simple}'.format(Report({})), 'cba')
#        self.assertTrue(csv_fmt.called)
#        self.assertEqual(csv_fmt.call_count, 1)
#
#      with patch.object(Report, '_time_format', return_value='a4q') as time_fmt:
#        self.assertEqual('{0:time}'.format(Report({})), 'a4q')
#        self.assertTrue(csv_fmt.called)
#        self.assertEqual(csv_fmt.call_count, 1)
#
#      self.assertIn('<lib.report.Report object at 0x7', '{0!s}'.format(Report({})))

    def test_how_long(self):
      when = now()
      with patch.multiple(Project, make=DEFAULT, all=DEFAULT) as whose_line:
        p1   = LogProject(self.random_uuid, 'Han-Kengai Beech', 'started', (when - timedelta(seconds=152)))
        p2   = LogProject(p1.id,            p1.name,            'stopped', (when - timedelta(seconds=38)))
        r = Report([p1, p2], scale='m')
        self.assertEqual((1.0, 54), r._how_long(114))

      with patch.multiple(Project, make=DEFAULT, all=DEFAULT) as whose_line:
        p1   = LogProject(self.random_uuid, 'Kengai Juniper', 'started', (when - timedelta(hours=2, minutes=3, seconds=34)))
        p2   = LogProject(p1.id,            p1.name,          'stopped', when)
        r = Report([p1, p2], scale='h')
        self.assertEqual((2, 57, 26), r._how_long(7283))
