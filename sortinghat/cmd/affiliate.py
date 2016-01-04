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
from ..exceptions import NotFoundError, WrappedValueError


class Affiliate(Command):
    """Affiliate unique identities.

    The command affiliates unique identities to organizations using email
    addresses and top/sub domains data. Only new enrollments will be created.
    """
    def __init__(self, **kwargs):
        super(Affiliate, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Affiliate unique identities."""

    @property
    def usage(self):
        return """%(prog)s affiliate"""

    def run(self, *args):
        """Affiliate unique identities to organizations."""

        self.parser.parse_args(args)

        code = self.affiliate()

        return code

    def affiliate(self):
        """Affiliate unique identities.

        This method enrolls unique identities to organizations using email
        addresses and top/sub domains data. Only new enrollments will be created.
        """
        try:
            uidentities = api.unique_identities(self.db)

            for uid in uidentities:
                uid.identities.sort(key=lambda x: x.id)

                for identity in uid.identities:
                    # Only check email address to find new affiliations
                    if not identity.email:
                        continue

                    domain = identity.email.split('@')[-1]

                    try:
                        doms = api.domains(self.db, domain=domain, top=True)
                    except NotFoundError as e:
                        continue

                    if len(doms) > 1:
                        doms.sort(key=lambda d: len(d.domain), reverse=True)

                        msg = "multiple top domains for %s sub-domain. Domain %s selected."
                        msg = msg % (domain, doms[0].domain)
                        self.warning(msg)

                    organization = doms[0].organization.name

                    # Check enrollments to avoid insert affiliation twice
                    enrollments = api.enrollments(self.db, uid.uuid,
                                                  organization)

                    if enrollments:
                        continue

                    api.add_enrollment(self.db, uid.uuid, organization)

                    self.display('affiliate.tmpl', id=uid.uuid,
                                 email=identity.email, organization=organization)
        except (NotFoundError, WrappedValueError) as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
