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
from sortinghat.cmd.withdraw import Withdraw
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


WITHDRAW_UUID_NOT_FOUND_ERROR = "Error: Jane Roe not found in the registry"
WITHDRAW_ORG_NOT_FOUND_ERROR = "Error: LibreSoft not found in the registry"
WITHDRAW_INVALID_PERIOD_ERROR = "Error: start date 2001-01-01 00:00:00 cannot be greater than 1999-01-01 00:00:00"
WITHDRAW_ENROLLMENT_NOT_FOUND_ERROR = "Error: John Doe-Bitergia-2050-01-01 00:00:00-2070-01-01 00:00:00 not found in the registry"
WITHDRAW_INVALID_DATE_ERROR = "Error: 1999-13-01 is not a valid date"
WITHDRAW_INVALID_FORMAT_DATE_ERROR = "Error: YYZYY is not a valid date"
WITHDRAW_EMPTY_OUTPUT = ""


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on withdraw unit tests"""

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
        self.cmd = Withdraw(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        api.add_enrollment(self.db, 'John Doe', 'Bitergia')
        api.add_enrollment(self.db, 'John Doe', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2010, 1, 1))

        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1981, 1, 1),
                           datetime.datetime(1990, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1991, 1, 1),
                           datetime.datetime(1993, 1, 1))


class TestWithdrawCommand(TestBaseCase):
    """Unit tests for withdraw command"""

    def test_withdraw(self):
        """Check withdraw command"""

        # Remove some enrollments giving partial periods
        self.cmd.run('--from', '1970-01-01 21:00:00', 'John Smith', 'Example')
        self.cmd.run('--to', '2010-01-01', 'John Doe', 'Example')

        # Check the output list
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.init, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        # Remove using a period range
        self.cmd.run('--from', '1900-01-01', '--to', '2100-01-01', 'John Smith', 'Example')

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')

        # Remove without using ranges
        self.cmd.run('John Doe', 'Bitergia')

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 0)

        # Check the output, it should be empty
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

    def test_invalid_dates(self):
        """Check whether it fails when invalid dates are given"""

        self.cmd.run('--from', '1999-13-01',
                     'John Smith', 'Example')
        output = sys.stderr.getvalue().strip('\n').split('\n')[0]
        self.assertEqual(output, WITHDRAW_INVALID_DATE_ERROR)

        self.cmd.run('--from', 'YYZYY',
                     'John Smith', 'Example')
        output = sys.stderr.getvalue().strip('\n').split('\n')[1]
        self.assertEqual(output, WITHDRAW_INVALID_FORMAT_DATE_ERROR)

        self.cmd.run('--to', '1999-13-01',
                     'John Smith', 'Example')
        output = sys.stderr.getvalue().strip('\n').split('\n')[2]
        self.assertEqual(output, WITHDRAW_INVALID_DATE_ERROR)

        self.cmd.run('--to', 'YYZYY',
                     'John Smith', 'Example')
        output = sys.stderr.getvalue().strip('\n').split('\n')[3]
        self.assertEqual(output, WITHDRAW_INVALID_FORMAT_DATE_ERROR)


class TestWithdraw(TestBaseCase):
    """Unit tests for withdraw"""

    def test_withdraw(self):
        """Check whether everything works right when withdrawing identities from organizations"""

        # This should delete two enrolmments: 1981-1990 and 1991-1993
        # but not the one from 1999-2010 nor 1900-2100
        self.cmd.withdraw('John Smith', 'Example',
                          datetime.datetime(1970, 1, 1),
                          datetime.datetime(1995, 1, 1))

        # List the registry and check the output list
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 4)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Example')

        rol = enrollments[2]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.init, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        rol = enrollments[3]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.init, datetime.datetime(1999, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2010, 1, 1))

        # Remove enrollments from John Doe
        self.cmd.withdraw('John Doe', 'Bitergia')

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 3)

        self.cmd.withdraw('John Doe', 'Example')

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')

    def test_period_ranges(self):
        """Check whether enrollments cannot be removed giving invalid period ranges"""

        self.cmd.withdraw('John Smith', 'Example',
                          datetime.datetime(2001, 1, 1),
                          datetime.datetime(1999, 1, 1))
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_INVALID_PERIOD_ERROR)

    def test_non_existing_uuid(self):
        """Check if it fails removing enrollments from unique identities that do not exist"""

        self.cmd.withdraw('Jane Roe', 'Example')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_UUID_NOT_FOUND_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails removing enrollments from organizations that do not exist"""

        self.cmd.withdraw('John Smith', 'LibreSoft')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_ORG_NOT_FOUND_ERROR)

    def test_non_existing_enrollment(self):
        """Check if it fails removing enrollment data that does not exist"""

        # Lets try again with the same period
        self.cmd.withdraw('John Doe', 'Bitergia',
                          datetime.datetime(2050, 1, 1),
                          datetime.datetime(2070, 1, 1))
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_ENROLLMENT_NOT_FOUND_ERROR)

    def test_none_parameters(self):
        """Check behavior removing with None parameters"""

        self.cmd.withdraw(None, 'Example')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

        self.cmd.withdraw('John Smith', None)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

    def test_empty_parameters(self):
        """Check behavior removing with empty parameters"""

        self.cmd.withdraw('', 'Example')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

        self.cmd.withdraw('John Smith', '')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
