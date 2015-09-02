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
from sortinghat.command import CMD_SUCCESS, CMD_FAILURE
from sortinghat.cmd.enroll import Enroll
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


ENROLL_UUID_NOT_FOUND_ERROR = "Error: Jane Roe not found in the registry"
ENROLL_ORG_NOT_FOUND_ERROR = "Error: LibreSoft not found in the registry"
ENROLL_INVALID_PERIOD_ERROR = "Error: start date 2001-01-01 00:00:00 cannot be greater than 1999-01-01 00:00:00"
ENROLL_EXISTING_ERROR = "Error: John Smith-Example-1900-01-01 00:00:00-2100-01-01 00:00:00 already exists in the registry"
ENROLL_INVALID_DATE_ERROR = "Error: 1999-13-01 is not a valid date"
ENROLL_INVALID_FORMAT_DATE_ERROR = "Error: YYZYY is not a valid date"
ENROLL_EMPTY_OUTPUT = ""



class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on enroll unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
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
        self.cmd = Enroll(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')


class TestEnrollCommand(TestBaseCase):
    """Enroll command unit tests"""

    def test_enroll(self):
        """Check how it works when enrolling"""

        code = self.cmd.run('John Smith', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--from', '2013-01-01', '--to', '2014-01-01', 'John Doe', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('John Smith', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--from', '1999-01-01 18:33:58', 'John Smith', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--to', '1970-01-01 01:02:03', 'John Smith', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ENROLL_EMPTY_OUTPUT)

        # Check the output list
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 5)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(2013, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2014, 1, 1))

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[2]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1999, 1, 1, 18, 33, 58))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        rol = enrollments[3]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(1970, 1, 1, 1, 2, 3))

        rol = enrollments[4]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        # Enroll and merge
        code = self.cmd.run('--from', '2008-01-01', '--merge', 'John Doe', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--merge', 'John Smith', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 4)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(2008, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2014, 1, 1))

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        rol = enrollments[2]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1999, 1, 1, 18, 33, 58))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        rol = enrollments[3]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(1970, 1, 1, 1, 2, 3))

    def test_invalid_dates(self):
        """Check whether it fails when invalid dates are given"""

        code = self.cmd.run('--from', '1999-13-01',
                            'John Smith', 'Example')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip('\n').split('\n')[0]
        self.assertEqual(output, ENROLL_INVALID_DATE_ERROR)

        code = self.cmd.run('--from', 'YYZYY',
                            'John Smith', 'Example')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip('\n').split('\n')[1]
        self.assertEqual(output, ENROLL_INVALID_FORMAT_DATE_ERROR)

        code = self.cmd.run('--to', '1999-13-01',
                            'John Smith', 'Example')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip('\n').split('\n')[2]
        self.assertEqual(output, ENROLL_INVALID_DATE_ERROR)

        code = self.cmd.run('--to', 'YYZYY',
                            'John Smith', 'Example')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip('\n').split('\n')[3]
        self.assertEqual(output, ENROLL_INVALID_FORMAT_DATE_ERROR)


class TestEnroll(TestBaseCase):
    """Unit tests for enroll"""

    def test_enroll(self):
        """Check whether everything works right when enrolling identities"""

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(2013, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(1981, 1, 1),
                               datetime.datetime(1995, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Smith', 'Bitergia',
                               datetime.datetime(2001, 1, 1),
                               datetime.datetime(2010, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Doe', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Doe', 'Bitergia',
                               datetime.datetime(1999, 1, 1),
                               datetime.datetime(2001, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

        # List the registry and check the output list
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 5)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Example')

        rol = enrollments[2]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[3]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1981, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(1995, 1, 1))

        rol = enrollments[4]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(2013, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

    def test_enroll_with_merge(self):
        """Check whether everything works right when enrolling and merging"""

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(2013, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(1981, 1, 1),
                               datetime.datetime(2003, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(1982, 1, 1),
                               datetime.datetime(1997, 1, 1),
                               True)
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(1996, 1, 1),
                               datetime.datetime(2005, 1, 1),
                               True)
        self.assertEqual(code, CMD_SUCCESS)

        # List the registry and check the output list
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1981, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2005, 1, 1))

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(2013, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

    def test_period_ranges(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        code = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(2001, 1, 1),
                               datetime.datetime(1999, 1, 1))
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_INVALID_PERIOD_ERROR)

    def test_non_existing_uuid(self):
        """Check if it fails adding enrollments to unique identities that do not exist"""

        code = self.cmd.enroll('Jane Roe', 'Example')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_UUID_NOT_FOUND_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails adding enrollments to organizations that do not exist"""

        code = self.cmd.enroll('John Smith', 'LibreSoft')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_ORG_NOT_FOUND_ERROR)

    def test_existing_enrollment(self):
        """Check if it fails adding enrollment data that already exists"""

        # Lets try again with the same period
        code1 = self.cmd.enroll('John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(2100, 1, 1))
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.enroll('John Smith', 'Example',
                                datetime.datetime(1900, 1, 1),
                                datetime.datetime(2100, 1, 1))
        self.assertEqual(code2, CMD_FAILURE)

        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, ENROLL_EXISTING_ERROR)

        # Test it without giving any period
        code = self.cmd.enroll('John Smith', 'Example')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, ENROLL_EXISTING_ERROR)

    def test_existing_enrollment_with_merge(self):
        """Check if does not fail adding enrollment data that already exists when using merge option"""

        # Lets try again with the same period
        code1 = self.cmd.enroll('John Smith', 'Example',
                                datetime.datetime(1900, 1, 1),
                                datetime.datetime(2100, 1, 1))
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.enroll('John Smith', 'Example',
                                datetime.datetime(1900, 1, 1),
                                datetime.datetime(2100, 1, 1),
                                True)
        self.assertEqual(code2, CMD_SUCCESS)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_EMPTY_OUTPUT)

    def test_none_parameters(self):
        """Check behavior adding None parameters"""

        code = self.cmd.enroll(None, 'Example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_EMPTY_OUTPUT)

        code = self.cmd.enroll('John Smith', None)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_EMPTY_OUTPUT)

    def test_empty_parameters(self):
        """Check behavior adding empty parameters"""

        code = self.cmd.enroll('', 'Example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_EMPTY_OUTPUT)

        code = self.cmd.enroll('John Smith', '')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ENROLL_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
