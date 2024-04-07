import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock, DEFAULT
from argparse import Namespace
import sys
from uuid import uuid4, UUID
import os.path
import io
from io import StringIO
import typing

import datetime
import importlib
import sys

sys.modules["_datetime"] = None
importlib.reload(datetime)

from datetime import datetime, timedelta

ME     = os.path.abspath(__file__)
MY_DIR = os.path.dirname(ME)

sys.path.append(os.path.join(MY_DIR, '..', 'lib'))

class TestWornBase(unittest.TestCase):
  def setUp(self):
    self.valid_uuid = UUID('244019c2-6d8f-4b09-96c1-b60a91ecb3a5')
    self.known_date = datetime(2024, 3, 23, 21, 50, 00)

  def tearDown(self): pass

if __name__ == '__main__':
  unittest.main(buffer=True)
