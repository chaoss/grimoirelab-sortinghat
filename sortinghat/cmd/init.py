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

import argparse

from ..command import Command, CMD_SUCCESS
from ..exceptions import DatabaseError, LoadError
from ..db.database import Database
from ..db.model import Country


class Init(Command):
    """Create an empty Sorting Hat registry.

    This command creates an empty registry creating a new database
    of <name> and its required tables. Any attempt to create
    a new registry over an existing instance will make fail the command.
    """
    def __init__(self, **kwargs):
        super(Init, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Positional arguments
        self.parser.add_argument('name',
                                 help="Name of the database to store the registry")

    @property
    def description(self):
        return """Create an empty Sorting Hat registry."""

    @property
    def usage(self):
        return """%(prog)s init <name>"""

    def run(self, *args):
        """Initialize a registry.

        Create and initialize an empty registry which its name is defined by
        <name> parameter. Required tables will be also created.
        """
        params = self.parser.parse_args(args)

        code = self.initialize(params.name)

        return code

    def initialize(self, name):
        """Create an empty Sorting Hat registry.

        This method creates a new database including the schema of Sorting Hat.
        Any attempt to create a new registry over an existing instance will
        procede an error.

        :param name: name of the database
        """
        user = self._kwargs['user']
        password = self._kwargs['password']
        host = self._kwargs['host']
        port = self._kwargs['port']

        try:
            Database.create(user, password, name, host, port)

            # Try to access and create schema
            db = Database(user, password, name, host, port)

            # Load countries list
            self.__load_countries(db)
        except DatabaseError as e:
            self.error(str(e))
            return e.code
        except LoadError as e:
            Database.drop(user, password, name, host, port)
            self.error(str(e))
            return e.code

        return CMD_SUCCESS

    def __load_countries(self, db):
        """Load the list of countries"""

        try:
            countries = self.__read_countries_file()
        except IOError as e:
            raise LoadError(str(e))

        try:
            with db.connect() as session:
                for country in countries:
                    session.add(country)
        except Exception as e:
            raise LoadError(str(e))

    def __read_countries_file(self):
        """Read countries from a CSV file"""
        import csv
        import pkg_resources

        filename = pkg_resources.resource_filename('sortinghat', 'data/countries.csv')

        with open(filename, 'r') as f:
            reader = csv.DictReader(f, fieldnames=['name', 'code', 'alpha3'])
            countries = [Country(**c) for c in reader]

        return countries
