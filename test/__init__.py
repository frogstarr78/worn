import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from argparse import Namespace
import sys
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import os.path
import io
from io import StringIO
import typing

ME     = os.path.abspath(__file__)
MY_DIR = os.path.dirname(ME)

sys.path.append(os.path.join(MY_DIR, '..', 'lib'))

#from lib import *
from lib.project import Project, FauxProject, LogProject


class TestWornBase(unittest.TestCase):
    def setUp(self):
      self.valid_uuid = UUID('244019c2-6d8f-4b09-96c1-b60a91ecb3a5')
      self.worn_project = Project(self.valid_uuid, 'Worn', 'stopped', datetime(2024, 3, 23, 23, 4, 13))
      self.known_date = datetime(2024, 3, 23, 21, 50, 00)

    def tearDown(self): pass

    def _timestamp_id(self, ts, seq='0'):
      if isinstance(ts, datetime):    return '''{ts:0<13}-{seq}'''.format(ts=str(ts.timestamp()).replace('.', '')[:13], seq=seq)
      if isinstance(ts, str):         return self._timestamp_id(datetime.fromtimestamp(float(ts)).seq)
      if isinstance(ts, int | float): return self._timestamp_id(datetime.fromtimestamp(ts), seq)
      else: raise Exception(f'Unknown timestamp {ts!r} type {type(ts)!r}.')

    @property
    def random_uuid(self): return uuid4()
