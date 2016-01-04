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

from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.organizations import Organizations
from sortinghat.db.database import Database
from sortinghat.exceptions import NotFoundError, CODE_ALREADY_EXISTS_ERROR, CODE_NOT_FOUND_ERROR

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


REGISTRY_ORG_ALREADY_EXISTS_ERROR = "Error: Bitergium already exists in the registry"
REGISTRY_DOM_ALREADY_EXISTS_ERROR = "Error: bitergia.com (Bitergia) already exists in the registry"
REGISTRY_ORG_NOT_FOUND_ERROR = "Error: Bitergium not found in the registry"
REGISTRY_ORG_NOT_FOUND_ERROR_ALT = "Error: LibreSoft not found in the registry"
REGISTRY_DOM_NOT_FOUND_ERROR = "Error: example.com not found in the registry"
REGISTRY_DOM_NOT_FOUND_ERROR_ALT = "Error: bitergia.com not found in the registry"
REGISTRY_EMPTY_OUTPUT = ""

REGISTRY_OUTPUT = """Bitergia\tbitergia.net
Bitergia\tbitergia.com *
Example\texample.com
Example\texample.org
Example\texample.net
LibreSoft"""

REGISTRY_OUTPUT_ALT = """Bitergia\tbitergia.net
Example\texample.com
Example\tbitergia.com
Example\texample.org
Example\texample.net
LibreSoft"""

REGISTRY_OUTPUT_EXAMPLE = """Example\texample.com
Example\texample.org
Example\texample.net
MyExample\tmyexample.com"""

REGISTRY_OUTPUT_EXAMPLE_ALT = """Example\texample.com
Example\texample.net"""


class TestOrgsCommand(unittest.TestCase):
    """Organization command unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Organizations(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_default_action(self):
        """Check whether when no action is given it runs --list"""

        # Add some contents first
        self.cmd.add('Example')
        self.cmd.add('Example', 'example.com')
        self.cmd.add('Example', 'example.org')
        self.cmd.add('Example', 'example.net')
        self.cmd.add('MyExample')
        self.cmd.add('MyExample', 'myexample.com')

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT_EXAMPLE)

    def test_list_without_args(self):
        """Test list action with and without arguments"""

        self.__load_test_dataset()

        code = self.cmd.run('-l')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT)

    def test_list_with_args(self):
        """Test list action with arguments"""

        self.__load_test_dataset()

        # Add an extra organization
        self.cmd.add('MyExample')
        self.cmd.add('MyExample', 'myexample.com')

        code = self.cmd.run('--list', 'Example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT_EXAMPLE)

    def test_add_with_args(self):
        """Test add action"""

        code = self.cmd.run('--add', 'LibreSoft')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-a', 'Example')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--add', 'Example', 'example.com')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--add', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-a', 'Bitergia', 'bitergia.net')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--add', 'Example', 'example.org')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--add', 'Bitergia', 'bitergia.com', '--top-domain')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-a', 'Example', 'example.net')
        self.assertEqual(code, CMD_SUCCESS)

        self.cmd.run('--list')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT)

    def test_add_without_args(self):
        """Check when calling --add without args, it does not do anything"""

        code = self.cmd.run('--add')
        self.assertEqual(code, CMD_SUCCESS)

        self.cmd.run('-l')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_EMPTY_OUTPUT)

    def test_add_with_overwrite_option(self):
        """Check whether it not fails running add with overwrite option"""

        self.__load_test_dataset()

        code = self.cmd.run('--add', 'Example', 'bitergia.com')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REGISTRY_DOM_ALREADY_EXISTS_ERROR)

        code = self.cmd.run('--add', '--overwrite', 'Example', 'bitergia.com')
        self.assertEqual(code, CMD_SUCCESS)

        self.cmd.run('-l')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT_ALT)

    def test_delete_with_args(self):
        """Test delete action"""

        self.__load_test_dataset()

        # Delete contents
        code = self.cmd.run('--delete', 'Bitergia', 'bitergia.com')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-d', 'LibreSoft')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--delete', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-d', 'Example', 'example.org')
        self.assertEqual(code, CMD_SUCCESS)

        self.cmd.run('--list')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT_EXAMPLE_ALT)

    def test_delete_without_args(self):
        """Check when calling --delete without args, it does not do anything"""

        self.__load_test_dataset()

        code = self.cmd.run('--delete')
        self.assertEqual(code, CMD_SUCCESS)

        self.cmd.run('-l')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT)

    def test_run_mixing_actions(self):
        """Check how it works when mixing actions"""

        self.cmd.run('--add', 'LibreSoft')
        self.cmd.run('-a', 'LibreSoft', 'libresoft.es')
        self.cmd.run('-a', 'Example')
        self.cmd.run('--add', 'Example', 'example.org')
        self.cmd.run('-d', 'Example', 'example.org')
        self.cmd.run('--add', 'Bitergia')
        self.cmd.run('-a', 'Bitergia', 'bitergia.net')
        self.cmd.run('--delete', 'LibreSoft')
        self.cmd.run('--add', 'Example', 'example.com')
        self.cmd.run('--add', 'Bitergia', 'bitergia.com')
        self.cmd.run('-a', 'Example', 'example.net')
        self.cmd.run('--delete', 'Bitergia', 'bitergia.com')
        self.cmd.run('-d', 'Bitergia')
        self.cmd.run()

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT_EXAMPLE_ALT)

    def __load_test_dataset(self):
        self.cmd.add('Example')
        self.cmd.add('Example', 'example.com')
        self.cmd.add('Bitergia')
        self.cmd.add('Bitergia', 'bitergia.net')
        self.cmd.add('Bitergia', 'bitergia.com', is_top_domain=True)
        self.cmd.add('LibreSoft')
        self.cmd.add('Example', 'example.org')
        self.cmd.add('Example', 'example.net')


class TestOrgsAdd(unittest.TestCase):

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Organizations(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_add(self):
        """Check whether everything works ok when adding organizations and domains"""

        code = self.cmd.add('Example')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('Example', 'example.com')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('Bitergia', 'bitergia.net')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('Bitergia', 'bitergia.com', is_top_domain=True)
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('LibreSoft', '') # This will work like adding a organization
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('Example', 'example.org')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('Example', 'example.net')
        self.assertEqual(code, CMD_SUCCESS)

        # List the registry and check the output
        self.cmd.registry()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT)

    def test_existing_organization(self):
        """Check if it fails adding an organization that already exists"""

        code1 = self.cmd.add('Bitergium')
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.add('Bitergium')
        self.assertEqual(code2, CODE_ALREADY_EXISTS_ERROR)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REGISTRY_ORG_ALREADY_EXISTS_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails adding domains to not existing organizations"""

        code = self.cmd.add('Bitergium', 'bitergium.com')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REGISTRY_ORG_NOT_FOUND_ERROR)

    def test_existing_domain(self):
        """Check if it fails adding a domain that already exists"""

        # Add a pair of organizations and domains first
        self.cmd.add('Example')
        self.cmd.add('Example', 'example.com')
        self.cmd.add('Bitergia')
        self.cmd.add('Bitergia', 'bitergia.com')

        # Add 'bitergia.com' to 'Example' org
        # It should print an error
        code = self.cmd.add('Example', 'bitergia.com')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REGISTRY_DOM_ALREADY_EXISTS_ERROR)

    def test_overwrite_domain(self):
        """Check whether it overwrites the old organization-domain relationship
        and the top_domain flag"""

        # Add a pair of organizations and domains first
        self.cmd.add('Example')
        self.cmd.add('Example', 'example.com')
        self.cmd.add('Example', 'example.org')
        self.cmd.add('Bitergia')
        self.cmd.add('Bitergia', 'bitergia.com')

        # Overwrite the relationship assigning the domain to a different
        # company and top_domain flag
        code = self.cmd.add('Bitergia', 'example.com',
                            is_top_domain=True, overwrite=True)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_EMPTY_OUTPUT)

        # Check if the domain has been assigned to Bitergia
        orgs = api.registry(self.db)

        org1 = orgs[0]
        self.assertEqual(org1.name, 'Bitergia')
        doms1 = org1.domains
        doms1.sort(key=lambda x: x.domain)
        self.assertEqual(len(doms1), 2)
        dom = doms1[0]
        self.assertEqual(dom.domain, 'bitergia.com')
        dom = doms1[1]
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)


        org2 = orgs[1]
        self.assertEqual(org2.name, 'Example')
        doms2 = org2.domains
        doms2.sort(key=lambda x: x.domain)
        self.assertEqual(len(doms2), 1)
        dom1 = doms2[0]
        self.assertEqual(dom1.domain, 'example.org')

    def test_none_organization(self):
        """Check behavior adding None organizations"""

        code = self.cmd.add(None)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_EMPTY_OUTPUT)

        # The registry should be empty
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 0)

    def test_empty_organization(self):
        """Check behavior adding empty organizations"""

        code = self.cmd.add('')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_EMPTY_OUTPUT)

        # The registry should be empty
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 0)


class TestOrgsDelete(unittest.TestCase):

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Organizations(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_delete(self):
        """Check whether everything works ok when deleting organizations and domains"""

        # First, add a set of organizations, including some domains
        self.cmd.add('Example')
        self.cmd.add('Example', 'example.com')
        self.cmd.add('Example', 'example.org')
        self.cmd.add('Example', 'example.net')
        self.cmd.add('Bitergia')
        self.cmd.add('Bitergia', 'bitergia.com')
        self.cmd.add('LibreSoft')
        self.cmd.add('Bitergium')
        self.cmd.add('Bitergium', 'bitergium.com')
        self.cmd.add('Bitergium', 'bitergium.net')

        # Delete an organization
        orgs = api.registry(self.db, 'Bitergia')
        self.assertEqual(len(orgs), 1)

        code = self.cmd.delete('Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        self.assertRaises(NotFoundError, api.registry,
                          self.db, 'Bitergia')

        # Delete a domain
        orgs = api.registry(self.db, 'Bitergium')
        self.assertEqual(len(orgs[0].domains), 2)

        code = self.cmd.delete('Bitergium', 'bitergium.com')
        self.assertEqual(code, CMD_SUCCESS)

        orgs = api.registry(self.db, 'Bitergium')
        self.assertEqual(len(orgs[0].domains), 1)

        # Delete organization with several domains
        orgs = api.registry(self.db, 'Example')
        self.assertEqual(len(orgs), 1)

        code = self.cmd.delete('Example')
        self.assertEqual(code, CMD_SUCCESS)

        self.assertRaises(NotFoundError, api.registry,
                          self.db, 'Example')

        # The final content of the registry should have
        # two companies and one domain
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 2)

        org1 = orgs[0]
        self.assertEqual(org1.name, 'Bitergium')
        doms1 = org1.domains
        self.assertEqual(len(doms1), 1)
        self.assertEqual(doms1[0].domain, 'bitergium.net')

        org2 = orgs[1]
        self.assertEqual(org2.name, 'LibreSoft')
        doms2 = org2.domains
        self.assertEqual(len(doms2), 0)

    def test_not_found_organization(self):
        """Check if it fails removing an organization that does not exists"""

        # It should print an error when the registry is empty
        code = self.cmd.delete('Bitergium')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, REGISTRY_ORG_NOT_FOUND_ERROR)

        # Add a pair of organizations to check delete with a registry
        # with contents
        self.cmd.add('Example')
        self.cmd.add('Bitergia')
        self.cmd.add('Bitergia', 'bitergia.com')

        # The error should be the same
        code = self.cmd.delete('Bitergium')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, REGISTRY_ORG_NOT_FOUND_ERROR)

        # It fails again, when trying to delete a domain from
        # a organization that does not exist
        code = self.cmd.delete('LibreSoft', 'bitergium.com')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[2]
        self.assertEqual(output, REGISTRY_ORG_NOT_FOUND_ERROR_ALT)

        # Nothing has been deleted from the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 2)
        self.assertEqual(len(orgs[0].domains), 1)
        self.assertEqual(len(orgs[1].domains), 0)

    def test_not_found_domain(self):
        """Check if it fails removing an domain that does not exists"""

        # Add a pair of organizations to check delete with a registry
        # with contents
        self.cmd.add('Example')
        self.cmd.add('Bitergia')
        self.cmd.add('Bitergia', 'bitergia.com')

        code = self.cmd.delete('Example', 'example.com')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, REGISTRY_DOM_NOT_FOUND_ERROR)

        # It should not fail because the domain is assigned
        # to other organization
        code = self.cmd.delete('Example', 'bitergia.com')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, REGISTRY_DOM_NOT_FOUND_ERROR_ALT)

        # Nothing has been deleted from the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 2)
        self.assertEqual(len(orgs[0].domains), 1)
        self.assertEqual(len(orgs[1].domains), 0)


class TestOrgsRegistry(unittest.TestCase):

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a dataset to test the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_domain(self.db, 'Example', 'example.net')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.net')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com', is_top_domain=True)

        api.add_organization(self.db, 'LibreSoft')

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Organizations(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_registry(self):
        """Check registry output list"""

        code = self.cmd.registry()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT)

    def test_registry_term(self):
        """Check if it returns the info about orgs using a search term"""

        # Add an extra organization first
        api.add_organization(self.db, 'MyExample')
        api.add_domain(self.db, 'MyExample', 'myexample.com')

        code = self.cmd.registry('Example')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT_EXAMPLE)

    def test_not_found_term(self):
        """Check whether it prints an error for not existing organizations"""

        code = self.cmd.registry('Bitergium')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REGISTRY_ORG_NOT_FOUND_ERROR)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.registry()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
