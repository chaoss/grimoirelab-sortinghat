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

from ..db.model import UniqueIdentity, Identity, Profile,\
    Enrollment, Organization, Domain, Country, MatchingBlacklist
from ..exceptions import InvalidFormatError, InvalidDateError
from ..utils import str_to_datetime


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
        self._blacklist = {}
        self._identities = []
        self._organizations = {}
        self.__parse(stream)

    @property
    def blacklist(self):
        bl = [b for b in self._blacklist.values()]
        bl.sort(key=lambda b: b.excluded)
        return bl

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
        self.__parse_blacklist(json)

    def __parse_blacklist(self, json):
        """Parse blacklist entries using Sorting Hat format.

        The Sorting Hat blacklist format is a JSON stream that
        stores a list of blacklisted entries.

        Next, there is an example of a valid stream:

        {
            "blacklist": [
                "John Doe",
                "John Smith",
                "root@example.com"
            ]
        }

        :param stream: stream to parse

        :raises InvalidFormatError: raised when the format of the stream is
            not valid.
        """
        try:
            for entry in json['blacklist']:
                if not entry:
                    msg = "invalid json format. Blacklist entries cannot be null or empty"
                    raise InvalidFormatError(cause=msg)

                excluded = self.__encode(entry)

                bl = self._blacklist.get(excluded, None)

                if not bl:
                    bl = MatchingBlacklist(excluded=excluded)
                    self._blacklist[excluded] = bl
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

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
                    "profile": {
                        "country": {
                            "alpha3": "USA",
                            "code": "US",
                            "name": "United States of America"
                        },
                        "email": "jsmith@example.com",
                        "name": null,
                        "is_bot": true,
                        "uuid": "03e12d00e37fd45593c49a5a5a1652deca4cf302"
                    },
                    "uuid": "03e12d00e37fd45593c49a5a5a1652deca4cf302"
                }
            }
        }

        :param stream: stream to parse

        :raises InvalidFormatError: raised when the format of the stream is
            not valid.
        """
        try:
            for uidentity in json['uidentities'].values():
                uuid = self.__encode(uidentity['uuid'])

                uid = UniqueIdentity(uuid=uuid)

                if uidentity['profile']:
                    profile = uidentity['profile']

                    if type(profile['is_bot']) != bool:
                        msg = "invalid json format. 'is_bot' must have a bool value"
                        raise InvalidFormatError(cause=msg)

                    is_bot = profile['is_bot']

                    name = self.__encode(profile['name'])
                    email = self.__encode(profile['email'])

                    prf = Profile(uuid=uuid, name=name, email=email,
                                  is_bot=is_bot)

                    if profile['country']:
                        alpha3 = self.__encode(profile['country']['alpha3'])
                        code = self.__encode(profile['country']['code'])
                        name = self.__encode(profile['country']['name'])

                        c = Country(alpha3=alpha3, code=code, name=name)

                        prf.country_code = code
                        prf.country = c

                    uid.profile = prf

                for identity in uidentity['identities']:
                    identity_id = self.__encode(identity['id'])
                    name = self.__encode(identity['name'])
                    email = self.__encode(identity['email'])
                    username = self.__encode(identity['username'])
                    source = self.__encode(identity['source'])

                    sh_id = Identity(id=identity_id, name=name,
                                     email=email, username=username,
                                     source=source, uuid=uuid)

                    uid.identities.append(sh_id)

                for enrollment in uidentity['enrollments']:
                    organization = self.__encode(enrollment['organization'])

                    org = self._organizations.get(organization, None)

                    if not org:
                        org = Organization(name=organization)
                        self._organizations[organization] = org

                    try:
                        start = str_to_datetime(enrollment['start'])
                        end = str_to_datetime(enrollment['end'])
                    except InvalidDateError as e:
                        raise InvalidFormatError(cause=str(e))

                    rol = Enrollment(start=start, end=end, organization=org)

                    uid.enrollments.append(rol)

                self._identities.append(uid)
        except KeyError as e:
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
                name = self.__encode(organization)

                org = self._organizations.get(name, None)

                if not org:
                    org = Organization(name=name)
                    self._organizations[name] = org

                domains = json['organizations'][organization]

                for domain in domains:
                    if type(domain['is_top']) != bool:
                        msg = "invalid json format. 'is_top' must have a bool value"
                        raise InvalidFormatError(cause=msg)

                    dom = Domain(domain=domain['domain'],
                                 is_top_domain=domain['is_top'])
                    org.domains.append(dom)
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __load_json(self, stream):
        """Load json stream into a dict object """

        import json

        try:
            return json.loads(stream)
        except ValueError as e:
            cause = "invalid json format. %s" % str(e)
            raise InvalidFormatError(cause=cause)

    def __encode(self, s):
        import sys

        if sys.version_info[0] >= 3: # Python 3
            return s if s else None
        else: # Python 2
            if type(s) is str:
                return s.encode('UTF-8') if s else None
            else:
                return s
