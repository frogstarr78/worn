from test import *
from lib.project import FauxProject
from lib.report import Report

class TestProject(FauxProject):
  def __init__(self, name):
    super().__init__()
    self.name = name

class TestReport(TestWornBase):
    def test_init(self):
      r = Report({})
      self.assertEqual({}, r._data)
      self.assertIsNone(r.at)
      self.assertEqual('h', r.scale)
      self.assertFalse(r.include_all)
      self.assertTrue(r.show_header)

      p = TestProject('Abc')
      p2 = TestProject('cBa')
      p3 = TestProject('BCa')
      r = Report({p2: 1.1, p: 5, p3: 3}, self.known_date, 'w', include_all=True, show_header=False)
      self.assertDictEqual({p2: 1.1, p: 5, p3: 3}, r._data)
      self.assertEqual(self.known_date, r.at)
      self.assertEqual('w', r.scale)
      self.assertTrue(r.include_all)
      self.assertFalse(r.show_header)

      with self.assertRaises(Exception):
        Report({}, scale='y')

    def test_mail(self): pass
    def test_post(self):
      with patch('sys.stderr', new_callable=StringIO) as mock_debug:
        r = Report({TestProject('bob'): 66})
        res = r.post(1, 'hello', noop=True)
        self.assertEqual(f'https://portal.viviotech.net/api/2.0/?method=support.ticket_post_staff_response&comment=1&ticket_id=1&time_spent=1.1&body="hello"\n', mock_debug.getvalue())
        self.assertEqual(1, res)

      with patch('requests.post', return_value=Mock(status_code=200)) as mock_reqs:
        r = Report({TestProject('bob'): 72})
        res = r.post(1, 'hello {project.state}')
        self.assertTrue(mock_reqs.called)
        self.assertEqual(mock_reqs.call_count, 1)
        self.assertEqual(mock_reqs.call_args.args, ('https://portal.viviotech.net/api/2.0/',))
        self.assertEqual(mock_reqs.call_args.kwargs, dict(params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=1, time_spent=1.2, body='hello stopped')))
#        self.assertEqual(0, res)

      with patch('requests.post', return_value=Mock(status_code=400)) as mock_reqs:
        r = Report({TestProject('joe'): 72})
        res = r.post(1, 'hello {project.name}')
        self.assertTrue(mock_reqs.called)
        self.assertEqual(mock_reqs.call_count, 1)
        self.assertEqual(mock_reqs.call_args.args, ('https://portal.viviotech.net/api/2.0/',))
        self.assertEqual(mock_reqs.call_args.kwargs, dict(params=dict(method='support.ticket_post_staff_response', comment=1, ticket_id=1, time_spent=1.2, body='hello joe')))
        self.assertEqual(1, res)

    def test_format(self):
      with patch.object(Report, '_csv_format', return_value='abc') as csv_fmt:
        self.assertEqual('{0:csv}'.format(Report({})), 'abc')
        self.assertTrue(csv_fmt.called)
        self.assertEqual(csv_fmt.call_count, 1)

      with patch.object(Report, '_simple_format', return_value='cba') as simple_fmt:
        self.assertEqual('{0:simple}'.format(Report({})), 'cba')
        self.assertTrue(csv_fmt.called)
        self.assertEqual(csv_fmt.call_count, 1)

      with patch.object(Report, '_time_format', return_value='a4q') as time_fmt:
        self.assertEqual('{0:time}'.format(Report({})), 'a4q')
        self.assertTrue(csv_fmt.called)
        self.assertEqual(csv_fmt.call_count, 1)

      self.assertIn('<lib.report.Report object at 0x7', '{0!s}'.format(Report({})))
