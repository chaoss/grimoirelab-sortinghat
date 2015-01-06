#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import datetime
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.cmd.log import Log
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


LOG_UUID_NOT_FOUND_ERROR = "Error: Jane Roe not found in the registry"
LOG_ORG_NOT_FOUND_ERROR = "Error: LibreSoft not found in the registry"
LOG_INVALID_PERIOD_ERROR = "Error: start date 2001-01-01 00:00:00 cannot be greater than 1999-01-01 00:00:00"
LOG_INVALID_DATE_ERROR = "Error: 1999-13-01 is not a valid date"
LOG_INVALID_FORMAT_DATE_ERROR = "Error: YYZYY is not a valid date"

LOG_EMPTY_OUTPUT = ""

LOG_OUTPUT = """John Doe\tExample\t1900-01-01 00:00:00\t2100-01-01 00:00:00
John Smith\tBitergia\t1900-01-01 00:00:00\t2100-01-01 00:00:00
John Smith\tBitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
John Smith\tBitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00
John Smith\tExample\t1900-01-01 00:00:00\t2100-01-01 00:00:00"""

LOG_UUID_OUTPUT = """John Doe\tExample\t1900-01-01 00:00:00\t2100-01-01 00:00:00"""

LOG_ORG_OUTPUT = """John Smith\tBitergia\t1900-01-01 00:00:00\t2100-01-01 00:00:00
John Smith\tBitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
John Smith\tBitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00"""

LOG_TIME_PERIOD_OUTPUT = """John Smith\tBitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00"""


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on log unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Import predefined dataset for testing
        self._load_test_dataset()

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Log(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        self.db.clear()

        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Bitergia',
                           datetime.datetime(2006, 1, 1),
                           datetime.datetime(2008, 1, 1))


class TestLogCommand(TestBaseCase):
    """Unit tests for log command"""

    def test_log(self):
        """Check log output"""

        self.cmd.run()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_OUTPUT)

    def test_log_uuid(self):
        """Check log using a uuid"""

        self.cmd.run('--uuid', 'John Doe')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_UUID_OUTPUT)

    def test_log_organization(self):
        """Check log using a organization"""

        self.cmd.run('--organization', 'Bitergia')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_ORG_OUTPUT)

    def test_log_period(self):
        """Check log using a time period"""

        self.cmd.run('--from', '1990-1-1 08:59:17',
                     '--to', '2005-1-1')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_TIME_PERIOD_OUTPUT)

    def test_log_mix_filter(self):
        """Check log using some filters"""

        self.cmd.run('--uuid', 'John Doe',
                     '--organization', 'Example',
                     '--from', '1990-1-1 08:59:17',
                     '--to', '2005-1-1')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_EMPTY_OUTPUT)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        self.cmd.run()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_EMPTY_OUTPUT)

    def test_invalid_dates(self):
        """Check whether it fails when invalid dates are given"""

        self.cmd.run('--from', '1999-13-01')
        output = sys.stderr.getvalue().strip('\n').split('\n')[0]
        self.assertEqual(output, LOG_INVALID_DATE_ERROR)

        self.cmd.run('--from', 'YYZYY')
        output = sys.stderr.getvalue().strip('\n').split('\n')[1]
        self.assertEqual(output, LOG_INVALID_FORMAT_DATE_ERROR)

        self.cmd.run('--to', '1999-13-01')
        output = sys.stderr.getvalue().strip('\n').split('\n')[2]
        self.assertEqual(output, LOG_INVALID_DATE_ERROR)

        self.cmd.run('--to', 'YYZYY')
        output = sys.stderr.getvalue().strip('\n').split('\n')[3]
        self.assertEqual(output, LOG_INVALID_FORMAT_DATE_ERROR)


class TestLog(TestBaseCase):
    """Unit tests for log"""

    def test_log(self):
        """Check log output"""

        self.cmd.log()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_OUTPUT)

    def test_log_uuid(self):
        """Check log using a uuid"""

        self.cmd.log('John Doe')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_UUID_OUTPUT)

    def test_log_organization(self):
        """Check log using a organization"""

        self.cmd.log(organization='Bitergia')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_ORG_OUTPUT)

    def test_log_period(self):
        """Check log using a time period"""

        self.cmd.log(from_date=datetime.datetime(1990, 1, 1),
                     to_date=datetime.datetime(2005, 1, 1))
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOG_TIME_PERIOD_OUTPUT)

    def test_period_ranges(self):
        """Check whether enrollments cannot be listed giving invalid period ranges"""

        self.cmd.log('John Smith', 'Example',
                     datetime.datetime(2001, 1, 1),
                     datetime.datetime(1999, 1, 1))
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOG_INVALID_PERIOD_ERROR)

    def test_not_found_uuid(self):
        """Check whether it raises an error when the uiid is not available"""

        self.cmd.log(uuid='Jane Roe')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOG_UUID_NOT_FOUND_ERROR)

    def test_not_found_organization(self):
        """Check whether it raises an error when the organization is not available"""

        self.cmd.log(organization='LibreSoft')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOG_ORG_NOT_FOUND_ERROR)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        self.cmd.log()
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOG_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
