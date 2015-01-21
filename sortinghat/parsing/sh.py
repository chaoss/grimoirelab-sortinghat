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

from sortinghat.db.model import Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parser import OrganizationsParser


class SortingHatOrganizationsParser(OrganizationsParser):
    """Parse organizations using Sorting Hat format.

    The Sorting Hat organizations format is a JSON stream which
    its keys are the name of the organizations. Each organization
    object has a list of domains. For instance:

    {
        "organizations": {
            "Bitergia": [
                {
                    "domain": "api.bitergia.com",
                    "is_top": false
                },
                {
                    "domain": "bitergia.com",
                    "is_top": true
                }
            ],
            "Example": []
        },
        "time": "2015-01-20 20:10:56.133378"
    }
    """
    def __init__(self):
        super(SortingHatOrganizationsParser, self).__init__()

    def organizations(self, stream):
        """Parse organizations stream

        This method creates a generator of Organization objects from the
        'stream' object.

        :param stream: string of organizations

        :returns: organizations generator

        :raises InvalidFormatError: exception raised when the format of
            the stream is not valid
        """
        if not stream:
            raise InvalidFormatError(cause="stream cannot be empty or None")

        json = self.__load_json(stream)

        try:
            for organization in json['organizations']:
                org = Organization(name=organization)

                domains = json['organizations'][organization]

                for domain in domains:
                    if type(domain['is_top']) != bool:
                        msg = "invalid json format. 'is_top' must have a bool value"
                        raise InvalidFormatError(cause=msg)

                    dom = Domain(domain=domain['domain'],
                                 is_top_domain=domain['is_top'])
                    org.domains.append(dom)

                yield org
        except KeyError, e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __load_json(self, stream):
        """Load json stream into a dict object """

        import json

        try:
            return json.loads(stream)
        except ValueError, e:
            cause = "invalid json format. %s" % str(e)
            raise InvalidFormatError(cause=cause)
