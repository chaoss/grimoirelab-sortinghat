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

import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.countries import Countries
from sortinghat.db.model import Country
from sortinghat.exceptions import CODE_NOT_FOUND_ERROR, CODE_INVALID_FORMAT_ERROR

from tests.base import TestCommandCaseBase


COUNTRIES_OUTPUT = """ES\tSpain
GB\tUnited Kingdom
US\tUnited States of America"""

COUNTRIES_CODE_OUTPUT = """ES\tSpain"""

COUNTRIES_TERM_OUTPUT = """GB\tUnited Kingdom
US\tUnited States of America"""

COUNTRIES_CODE_OR_TERM_ERROR = "Error: Code country or term must have 2 or more characters length"
COUNTRIES_NOT_FOUND_ERROR = "Error: Uk not found in the registry"


class TestCountriesCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on countries unit tests"""

    cmd_klass = Countries

    def load_test_dataset(self):
        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            es = Country(code='ES', name='Spain', alpha3='ESP')
            gb = Country(code='GB', name='United Kingdom', alpha3='GBR')

            session.add(es)
            session.add(us)
            session.add(gb)


class TestCountriesCommand(TestCountriesCaseBase):
    """Unit tests for countries command"""

    def test_countries(self):
        """Check countries command"""

        retval = self.cmd.run()
        self.assertEqual(retval, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, COUNTRIES_OUTPUT)

    def test_countries_code(self):
        """Check output when a code country is given"""

        retval = self.cmd.run('ES')
        self.assertEqual(retval, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, COUNTRIES_CODE_OUTPUT)

    def test_countries_term(self):
        """Check output when a code country is given"""

        retval = self.cmd.run('unit')
        self.assertEqual(retval, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, COUNTRIES_TERM_OUTPUT)

    def test_code_or_term_error(self):
        """Check output error when a code or term is invalid"""

        retval = self.cmd.run('U')
        self.assertEqual(retval, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, COUNTRIES_CODE_OR_TERM_ERROR)

    def test_not_found_error(self):
        """Check output error when a country is not found"""

        retval = self.cmd.run('Uk')
        self.assertEqual(retval, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, COUNTRIES_NOT_FOUND_ERROR)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
