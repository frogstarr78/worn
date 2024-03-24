import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from argparse import Namespace
import sys
from datetime import datetime, date, timedelta
import os.path
import shutil
import io
import copy

ME     = os.path.abspath(__file__)
MY_DIR = os.path.dirname(ME)
CLIENT_ID = 821
CACHE_HOURS = 24

sys.path.append(os.path.join(MY_DIR, '..', 'lib'))

import lib
from lib import uuid4

class TestWornBase(unittest.TestCase):
    def setUp(self): pass
    def tearDown(self): pass
