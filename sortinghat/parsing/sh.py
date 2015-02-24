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

from sortinghat.db.model import UniqueIdentity, Identity, Enrollment, Organization, Domain
from sortinghat.exceptions import InvalidFormatError


class SortingHatParser(object):
    """Parse identities and organizations using Sorting Hat format.

    The Sorting Hat data format is a JSON stream that contains
    information about unique identities and organizations.

    The unique identities are stored in an object named 'uidentities'.
    The keys of this object are the UUID of the unique identities.
    Each unique identity object stores a list of identities and
    enrollments.

    Organizations are stored in 'organizations' object. Its keys
    are the name of the organizations and each organization object is
    related to a list of domains.

    :param stream: stream to parse

    :raises InvalidFormatError: raised when the format of the stream is
        not valid.
    """

    def __init__(self, stream):
        self._identities = []
        self._organizations = {}
        self.__parse(stream)

    @property
    def identities(self):
        self._identities.sort(key=lambda u: u.uuid)
        return [u for u in self._identities]

    @property
    def organizations(self):
        orgs = [o for o in self._organizations.values()]
        orgs.sort(key=lambda o: o.name)
        return orgs

    def __parse(self, stream):
        """Parse Sorting Hat stream"""

        if not stream:
            raise InvalidFormatError(cause="stream cannot be empty or None")

        json = self.__load_json(stream)

        self.__parse_organizations(json)
        self.__parse_identities(json)

    def __parse_identities(self, json):
        """Parse identities using Sorting Hat format.

        The Sorting Hat identities format is a JSON stream on which its
        keys are the UUID of the unique identities. Each unique identity
        object has a list of identities and enrollments.

        When the unique identity does not have a UUID, it will be considered
        as an anonymous unique identity. This means that the UUID of these
        identities will be regenerated during the loading process.

        Next, there is an example of a valid stream:

        {
            "uidentities": {
                "johnsmith@example.net": {
                    "enrollments": [],
                    "identities": [],
                    "uuid": null
                },
                "03e12d00e37fd45593c49a5a5a1652deca4cf302": {
                    "enrollments": [
                        {
                            "end": "2100-01-01T00:00:00",
                            "start": "1900-01-01T00:00:00",
                            "organization": "Example",
                            "uuid": "03e12d00e37fd45593c49a5a5a1652deca4cf302"
                        }
                    ],
                    "identities": [
                        {
                            "email": "jsmith@example.com",
                            "id": "03e12d00e37fd45593c49a5a5a1652deca4cf302",
                            "name": "John Smith",
                            "source": "scm",
                            "username": "jsmith",
                            "uuid": "03e12d00e37fd45593c49a5a5a1652deca4cf302"
                        },
                        {
                            "email": "jsmith@example.com",
                            "id": "75d95d6c8492fd36d24a18bd45d62161e05fbc97",
                            "name": "John Smith",
                            "source": "scm",
                            "username": null,
                            "uuid": "03e12d00e37fd45593c49a5a5a1652deca4cf302"
                        }
                    ],
                    "uuid": "03e12d00e37fd45593c49a5a5a1652deca4cf302"
                }
        }

        :param stream: stream to parse

        :raises InvalidFormatError: raised when the format of the stream is
        not valid.
        """
        try:
            for uidentity in json['uidentities'].values():
                uuid = uidentity['uuid']

                uid = UniqueIdentity(uuid=uuid)

                for identity in uidentity['identities']:
                    sh_id = Identity(id=identity['id'], name=identity['name'],
                                     email=identity['email'], username=identity['username'],
                                     source=identity['source'])

                    uid.identities.append(sh_id)

                for enrollment in uidentity['enrollments']:
                    organization = enrollment['organization']

                    org = self._organizations.get(organization, None)

                    if not org:
                        org = Organization(name=organization)
                        self._organizations[organization] = org

                    start = self.__parse_datetime(enrollment['start'])
                    end = self.__parse_datetime(enrollment['end'])

                    rol = Enrollment(start=start, end=end, organization=org)

                    uid.enrollments.append(rol)

                self._identities.append(uid)
        except KeyError, e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_organizations(self, json):
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

        :param json: stream to parse

        :raises InvalidFormatError: raised when the format of the stream is
            not valid.
        """
        try:
            for organization in json['organizations']:
                org = self._organizations.get(organization, None)

                if not org:
                    org = Organization(name=organization)
                    self._organizations[organization] = org

                domains = json['organizations'][organization]

                for domain in domains:
                    if type(domain['is_top']) != bool:
                        msg = "invalid json format. 'is_top' must have a bool value"
                        raise InvalidFormatError(cause=msg)

                    dom = Domain(domain=domain['domain'],
                                 is_top_domain=domain['is_top'])
                    org.domains.append(dom)
        except KeyError, e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_datetime(self, t):
        """Parse datetime string"""

        import dateutil.parser

        try:
            return dateutil.parser.parse(t)
        except ValueError:
            msg = "invalid date format: %s" % t
            raise InvalidFormatError(cause=msg)

    def __load_json(self, stream):
        """Load json stream into a dict object """

        import json

        try:
            return json.loads(stream)
        except ValueError, e:
            cause = "invalid json format. %s" % str(e)
            raise InvalidFormatError(cause=cause)
