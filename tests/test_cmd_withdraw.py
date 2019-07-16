#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import datetime
import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.withdraw import Withdraw
from sortinghat.exceptions import CODE_INVALID_DATE_ERROR, CODE_NOT_FOUND_ERROR, CODE_VALUE_ERROR

from tests.base import TestCommandCaseBase


WITHDRAW_UUID_NOT_FOUND_ERROR = "Error: Jane Roe not found in the registry"
WITHDRAW_ORG_NOT_FOUND_ERROR = "Error: LibreSoft not found in the registry"
WITHDRAW_INVALID_PERIOD_ERROR = "Error: 'from_date' 2001-01-01 00:00:00 cannot be greater than 1999-01-01 00:00:00"
WITHDRAW_ENROLLMENT_NOT_FOUND_ERROR = "Error: John Doe-Bitergia-2050-01-01 00:00:00-2070-01-01 00:00:00 not found in the registry"
WITHDRAW_INVALID_DATE_ERROR = "Error: 1999-13-01 is not a valid date"
WITHDRAW_INVALID_FORMAT_DATE_ERROR = "Error: YYZYY is not a valid date"
WITHDRAW_EMPTY_OUTPUT = ""


class TestWithdrawCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on withdraw unit tests"""

    cmd_klass = Withdraw

    def load_test_dataset(self):
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


class TestWithdrawCommand(TestWithdrawCaseBase):
    """Unit tests for withdraw command"""

    def test_withdraw(self):
        """Check withdraw command"""

        # Remove some enrollments giving partial periods
        code = self.cmd.run('--from', '1970-01-01 21:00:00', 'John Smith', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--to', '2010-01-01', 'John Doe', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        # Check the output list
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        # Remove using a period range
        code = self.cmd.run('--from', '1900-01-01', '--to', '2100-01-01', 'John Smith', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Bitergia')

        # Remove without using ranges
        code = self.cmd.run('John Doe', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 0)

        # Check the output, it should be empty
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

    def test_invalid_dates(self):
        """Check whether it fails when invalid dates are given"""

        code = self.cmd.run('--from', '1999-13-01',
                            'John Smith', 'Example')
        self.assertEqual(code, CODE_INVALID_DATE_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, WITHDRAW_INVALID_DATE_ERROR)

        code = self.cmd.run('--from', 'YYZYY',
                            'John Smith', 'Example')
        self.assertEqual(code, CODE_INVALID_DATE_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, WITHDRAW_INVALID_FORMAT_DATE_ERROR)

        code = self.cmd.run('--to', '1999-13-01',
                            'John Smith', 'Example')
        self.assertEqual(code, CODE_INVALID_DATE_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, WITHDRAW_INVALID_DATE_ERROR)

        code = self.cmd.run('--to', 'YYZYY',
                            'John Smith', 'Example')
        self.assertEqual(code, CODE_INVALID_DATE_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, WITHDRAW_INVALID_FORMAT_DATE_ERROR)


class TestWithdraw(TestWithdrawCaseBase):
    """Unit tests for withdraw"""

    def test_withdraw(self):
        """Check whether everything works right when withdrawing identities from organizations"""

        # This should delete two enrolmments: 1981-1990 and 1991-1993
        # but not the one from 1999-2010 nor 1900-2100
        code = self.cmd.withdraw('John Smith', 'Example',
                                 datetime.datetime(1970, 1, 1),
                                 datetime.datetime(1995, 1, 1))
        self.assertEqual(code, CMD_SUCCESS)

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
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1))

        rol = enrollments[3]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1999, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2010, 1, 1))

        # Remove enrollments from John Doe
        code = self.cmd.withdraw('John Doe', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 3)

        code = self.cmd.withdraw('John Doe', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

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

        code = self.cmd.withdraw('John Smith', 'Example',
                                 datetime.datetime(2001, 1, 1),
                                 datetime.datetime(1999, 1, 1))
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_INVALID_PERIOD_ERROR)

    def test_non_existing_uuid(self):
        """Check if it fails removing enrollments from unique identities that do not exist"""

        code = self.cmd.withdraw('Jane Roe', 'Example')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_UUID_NOT_FOUND_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails removing enrollments from organizations that do not exist"""

        code = self.cmd.withdraw('John Smith', 'LibreSoft')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_ORG_NOT_FOUND_ERROR)

    def test_non_existing_enrollment(self):
        """Check if it fails removing enrollment data that does not exist"""

        # Lets try again with the same period
        code = self.cmd.withdraw('John Doe', 'Bitergia',
                                 datetime.datetime(2050, 1, 1),
                                 datetime.datetime(2070, 1, 1))
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, WITHDRAW_ENROLLMENT_NOT_FOUND_ERROR)

    def test_none_parameters(self):
        """Check behavior removing with None parameters"""

        code = self.cmd.withdraw(None, 'Example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

        code = self.cmd.withdraw('John Smith', None)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

    def test_empty_parameters(self):
        """Check behavior removing with empty parameters"""

        code = self.cmd.withdraw('', 'Example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)

        code = self.cmd.withdraw('John Smith', '')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, WITHDRAW_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
