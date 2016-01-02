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

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import NotFoundError, WrappedValueError, CODE_INVALID_FORMAT_ERROR


class Countries(Command):
    """List countries from the registry.

    This command prints information related to the unique identities
    such as identities or enrollments. When <code_or_term> is given, the
    command will list only those companies that match with that country
    code or with term.
    """
    def __init__(self, **kwargs):
        super(Countries, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        self.parser.add_argument('code_or_term', nargs='?', default=None,
                                 help="country code or term to search for")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """List countries from the registry."""

    @property
    def usage(self):
        return "%(prog)s [<code_or_term>]"

    def run(self, *args):
        """Show information about countries."""

        params = self.parser.parse_args(args)

        ct = params.code_or_term

        if ct and len(ct) < 2:
            self.error('Code country or term must have 2 or more characters length')
            return CODE_INVALID_FORMAT_ERROR

        code = ct if ct and len(ct) == 2 else None
        term = ct if ct and len(ct) > 2 else None

        try:
            countries = api.countries(self.db, code=code, term=term)
            self.display('countries.tmpl', countries=countries)
        except (NotFoundError, WrappedValueError) as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
