from test import *
from lib.project import Project, FauxProject, LogProject

class TestProject(TestWornBase):
  def test_eq(self):
    _id = uuid4()
    p  = Project(_id, 'Test1', 'stopped', when=datetime(2024, 3, 23, 21, 50, 00))
    op = Project(_id, 'Test1', 'stopped', when=datetime(2024, 3, 24, 21, 50, 00))
#    self.assertIs(p, op)
    self.assertEqual(p, op)
    self.assertEqual(p, _id)
    self.assertEqual(p, str(_id))
    self.assertEqual(p, 'Test1')
    self.assertEqual(p, 'test1')
    oop = Project(str(_id), 'Test1', 'stopped', when=datetime(2024, 3, 24, 21, 50, 00))
    self.assertEqual(p, oop)
    self.assertEqual(p, 'Test1')
    self.assertEqual(p, 'test1')

    _oid = uuid4()
    ooop = Project(_oid, 'Test2', 'stopped', when=datetime(2024, 3, 24, 21, 50, 00))
    self.assertIsNot(p, ooop)
    self.assertNotEqual(p, ooop)
    self.assertNotEqual(p, _oid)
    self.assertNotEqual(p, str(_oid))
    self.assertNotEqual(p, 'Test2')
    self.assertNotEqual(p, 'test2')

  def test_sub(self): pass
  def test_hash(self): pass
  def test_str(self): pass
  def test_format(self): pass
  def test_log_format(self): pass
  def test_is_running(self): pass
  def test_is_last(self): pass
  def test_add(self): pass
  def test_log(self): pass
  def test_stop(self): pass
  def test_start(self): pass
  def test_rename(self): pass
  def test_remove(self): pass
  def test_make(self): pass
  def test_nearest_project_by_name(self): pass
  def test_all(self): pass
  def test_cache(self): pass

if __name__ == '__main__':
  unittest.main(buffer=True)
