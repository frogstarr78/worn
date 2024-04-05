from test import *
from lib.project import Project, FauxProject
from lib import now

class TestFauxProject(TestWornBase):
  def test_init(self):
    faux = FauxProject()
    self.assertIsInstance(faux.id, UUID)
    self.assertEqual(faux.name, 'Faux')
    self.assertEqual(faux.state, 'stopped')
    self.assertIsInstance(faux.when, datetime)

  def test_actions(self):
    faux = FauxProject()
    with self.assertRaises(Project.FauxProjectE):
      faux.add()

    with self.assertRaises(Project.FauxProjectE):
      faux.log('started', now())

    with self.assertRaises(Project.FauxProjectE):
      faux.start(now())

    with self.assertRaises(Project.FauxProjectE):
      faux.stop(now())

    with self.assertRaises(Project.InvalidTypeE):
      faux.rename('rumplestilskin')

if __name__ == '__main__':
  unittest.main(buffer=True)
