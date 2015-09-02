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

import sys

import jinja2

from sortinghat.exceptions import DatabaseError
from sortinghat.db.database import Database

CMD_SUCCESS = 0
CMD_FAILURE = 1


class Command(object):
    """Abstract class to run commands"""

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    @property
    def description(self):
        raise NotImplementedError

    @property
    def usage(self):
        raise NotImplementedError

    def run(self, *args):
        raise NotImplementedError

    def display(self, template, **kwargs):
        loader = jinja2.PackageLoader('sortinghat', 'templates')
        env = jinja2.Environment(loader=loader,
                                 lstrip_blocks=True, trim_blocks=True)

        t = env.get_template(template)
        s = t.render(**kwargs)

        s = s.encode('UTF-8')
        sys.stdout.write(s)

    def error(self, msg):
        s = "Error: %s\n" % msg
        sys.stderr.write(s.encode('UTF-8'))

    def warning(self, msg):
        s = "Warning: %s\n" % msg
        sys.stderr.write(s.encode('UTF-8'))

    def _set_database(self, **kwargs):
        try:
            self.db = Database(kwargs['user'], kwargs['password'],
                               kwargs['database'], kwargs['host'], kwargs['port'])
        except DatabaseError, e:
            raise RuntimeError(str(e))
