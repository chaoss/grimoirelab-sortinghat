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
from sortinghat.cmd.show import Show
from sortinghat.db.model import Country
from sortinghat.exceptions import CODE_NOT_FOUND_ERROR

from tests.base import TestCommandCaseBase


SHOW_UUID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFF not found in the registry"

SHOW_EMPTY_OUTPUT = ""

SHOW_OUTPUT = """unique identity 0000000000000000000000000000000000000000

Profile:
    * Name: -
    * E-Mail: -
    * Gender: -
    * Bot: No
    * Country: -

No identities

No enrollments


unique identity 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Gender: -
    * Bot: No
    * Country: US - United States of America

Identities:
  17ab00ed3825ec2f50483e33c88df223264182ba\tJane Roe\tjroe@example.com\tjroe\tscm
  22d1b20763c6f5822bdda8508957486c547bb9de\t-\tjroe@bitergia.com\t-\tunknown
  322397ed782a798ffd9d0bc7e293df4292fe075d\t-\tjroe@example.com\t-\tscm

Enrollments:
  Bitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
  Bitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00


unique identity a9b403e150dd4af8953a52a4bb841051e4b705d9

Profile:
    * Name: -
    * E-Mail: jsmith@example.com
    * Gender: male
    * Bot: Yes
    * Country: -

Identities:
  880b3dfcb3a08712e5831bddc3dfe81fc5d7b331\tJohn Smith\tjsmith@example.com\t-\tscm
  a9b403e150dd4af8953a52a4bb841051e4b705d9\tJohn Smith\tjsmith@example.com\tjsmith\tscm

Enrollments:
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00"""

SHOW_UUID_OUTPUT = """unique identity 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Gender: -
    * Bot: No
    * Country: US - United States of America

Identities:
  17ab00ed3825ec2f50483e33c88df223264182ba\tJane Roe\tjroe@example.com\tjroe\tscm
  22d1b20763c6f5822bdda8508957486c547bb9de\t-\tjroe@bitergia.com\t-\tunknown
  322397ed782a798ffd9d0bc7e293df4292fe075d\t-\tjroe@example.com\t-\tscm

Enrollments:
  Bitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
  Bitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00"""

SHOW_TERM_OUTPUT = """unique identity 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Gender: -
    * Bot: No
    * Country: US - United States of America

Identities:
  17ab00ed3825ec2f50483e33c88df223264182ba\tJane Roe\tjroe@example.com\tjroe\tscm
  22d1b20763c6f5822bdda8508957486c547bb9de\t-\tjroe@bitergia.com\t-\tunknown
  322397ed782a798ffd9d0bc7e293df4292fe075d\t-\tjroe@example.com\t-\tscm

Enrollments:
  Bitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
  Bitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00


unique identity a9b403e150dd4af8953a52a4bb841051e4b705d9

Profile:
    * Name: -
    * E-Mail: jsmith@example.com
    * Gender: male
    * Bot: Yes
    * Country: -

Identities:
  880b3dfcb3a08712e5831bddc3dfe81fc5d7b331\tJohn Smith\tjsmith@example.com\t-\tscm
  a9b403e150dd4af8953a52a4bb841051e4b705d9\tJohn Smith\tjsmith@example.com\tjsmith\tscm

Enrollments:
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00"""


class TestShowCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on show unit tests"""

    cmd_klass = Show

    def load_test_dataset(self):
        # Add country
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add organizations
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        # Add John Smith identity
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com',
                         gender='male', is_bot=True)

        # Add Joe Roe identity
        jroe_uuid = api.add_identity(self.db, 'scm', 'jroe@example.com',
                                     'Jane Roe', 'jroe')
        api.add_identity(self.db, 'scm', 'jroe@example.com',
                         uuid=jroe_uuid)
        api.add_identity(self.db, 'unknown', 'jroe@bitergia.com',
                         uuid=jroe_uuid)
        api.edit_profile(self.db, jroe_uuid, name='Jane Roe', email='jroe@example.com',
                         is_bot=False, country_code='US')

        # Add unique identity, this one won't have neither identities
        # nor enrollments
        api.add_unique_identity(self.db,
                                '0000000000000000000000000000000000000000')

        # Add enrollments
        api.add_enrollment(self.db, jsmith_uuid, 'Example')

        api.add_enrollment(self.db, jroe_uuid, 'Example')
        api.add_enrollment(self.db, jroe_uuid, 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_enrollment(self.db, jroe_uuid, 'Bitergia',
                           datetime.datetime(2006, 1, 1),
                           datetime.datetime(2008, 1, 1))


class TestShowCommand(TestShowCaseBase):
    """Unit tests for show command"""

    def test_show(self):
        """Check show output"""

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_OUTPUT)

    def test_show_uuid(self):
        """Check show using a uuid"""

        code = self.cmd.run('17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_UUID_OUTPUT)

    def test_show_term(self):
        """Check show using a term"""

        code = self.cmd.run('--term', 'example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_TERM_OUTPUT)

    def test_show_uuid_with_term(self):
        """When the UUID is given, term parameter is ignored"""

        code = self.cmd.run('--term', 'jsmith',
                            '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_UUID_OUTPUT)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_EMPTY_OUTPUT)


class TestShow(TestShowCaseBase):
    """Unit tests for show"""

    def test_show(self):
        "Check show"

        code = self.cmd.show()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_OUTPUT)

    def test_show_uuid(self):
        """Check show using a UUID"""

        code = self.cmd.show(uuid='17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_UUID_OUTPUT)

    def test_not_found_uuid(self):
        """Check whether it prints an error when the uiid is not available"""

        code = self.cmd.show(uuid='FFFFFFFFFFFFFFF')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, SHOW_UUID_NOT_FOUND_ERROR)

    def test_show_term(self):
        """Check show using a term"""

        code = self.cmd.show(term='example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_TERM_OUTPUT)

    def test_show_uuid_with_term(self):
        """When the UUID is given, term parameter is ignored"""

        code = self.cmd.show(uuid='17ab00ed3825ec2f50483e33c88df223264182ba',
                             term='jsmith')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_UUID_OUTPUT)

    def test_not_found_term(self):
        """Check whether it prints an error when the term is not found"""

        code = self.cmd.show(term='FFFFFFFFFFFFFFF')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, SHOW_UUID_NOT_FOUND_ERROR)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.show()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, SHOW_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
