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

import argparse

from sortinghat.command import Command
from sortinghat.exceptions import DatabaseError
from sortinghat.db.database import Database


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

        self.initialize(params.name)

    def initialize(self, name):
        """Create an empty Sorting Hat registry.

        This method creates a new database including the schema of Sorting Hat.
        Any attempt to create a new registry over an existing instance will
        procede an error.

        :param name: name of the database
        """
        try:
            Database.create(self._kwargs['user'], self._kwargs['password'],
                            name, self._kwargs['host'], self._kwargs['port'])

            # Try to access and create schema
            Database(self._kwargs['user'], self._kwargs['password'],
                     name, self._kwargs['host'], self._kwargs['port'])
        except DatabaseError, e:
            self.error(str(e))
