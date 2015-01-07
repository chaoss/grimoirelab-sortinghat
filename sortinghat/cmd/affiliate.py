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

from sortinghat import api
from sortinghat.command import Command
from sortinghat.exceptions import NotFoundError


class Affiliate(Command):
    """Affiliate unique identities.

    The command affiliates unique identities to organizations using email
    addresses and top/sub domains data. Only new enrollments will be created.
    """
    def __init__(self, **kwargs):
        super(Affiliate, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

    @property
    def description(self):
        return """Affiliate unique identities."""

    @property
    def usage(self):
        return """%(prog)s affiliate"""

    def run(self, *args):
        """Affiliate unique identities to organizations."""

        self.parser.parse_args(args)

        self.affiliate()

    def affiliate(self):
        """Affiliate unique identities.

        This method enrolls unique identities to organizations using email
        addresses and top/sub domains data. Only new enrollments will be created.
        """
        try:
            uidentities = api.unique_identities(self.db)

            for uid in uidentities:
                for identity in uid.identities:

                    # Only check email address to find new affiliations
                    if not identity.email:
                        continue

                    domain = identity.email.split('@')[-1]

                    try:
                        doms = api.domains(self.db, domain=domain, top=True)
                    except NotFoundError, e:
                        continue

                    if len(doms) != 1:
                        msg = "multiple top domains for %s sub-domain. Please fix it before continue"
                        msg = msg % domain
                        raise RuntimeError(msg)

                    organization = doms[0].organization.name

                    # Check enrollments to avoid insert affiliation twice
                    enrollments = api.enrollments(self.db, uid.uuid,
                                                  organization)

                    if enrollments:
                        continue

                    api.add_enrollment(self.db, uid.uuid, organization)

                    self.display('affiliate.tmpl', id=uid.uuid,
                                 email=identity.email, organization=organization)
        except (NotFoundError, ValueError), e:
            raise RuntimeError(str(e))
