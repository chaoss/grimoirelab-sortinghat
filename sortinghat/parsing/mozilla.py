# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 Bitergia
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

from ..db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE, \
    UniqueIdentity, Identity, Enrollment, Organization
from ..exceptions import InvalidFormatError
from ..utils import str_to_datetime


MOZILLIANS_ORG = 'Mozillians'


class MozilliansParser(object):
    """Parse identities using Mozillians format.

    The Mozillians data format is a JSON stream that contains
    information about unique identities. Only information about
    Mozillians organization will be added.

    The unique identities are stored in an object named 'uidentities'.
    The keys of this object are the UUID of the unique identities.
    Each unique identity object stores a list of identities.

    Mozillian organizations are stored in 'organizations' object. Its
    key is the name of no list of domains is provided.

    :param stream: stream to parse

    :raises InvalidFormatError: raised when the format of the stream is
        not valid.
    """
    def __init__(self, stream, source='mozillians'):
        self._identities = {}
        self._organizations = {}
        self.source = source

        self.__parse(stream)

    @property
    def identities(self):
        uids = [u for u in self._identities.values()]
        uids.sort(key=lambda u: u.uuid)
        return uids

    @property
    def organizations(self):
        orgs = [o for o in self._organizations.values()]
        orgs.sort(key=lambda o: o.name)
        return orgs

    def __parse(self, stream):
        """Parse Mozillians stream"""

        if not stream:
            raise InvalidFormatError(cause="stream cannot be empty or None")

        json = self.__load_json(stream)

        self.__create_mozillians_org()
        self.__parse_identities(json)

    def __parse_identities(self, json):
        """Parse identities using Mozillians format.

        The Mozillians identities format is a JSON document under the
        "results" key. The document should follow the next schema:

        {
          "results" : [
              {
               "_url": "https://example.com/api/v2/users/1/",
               "alternate_emails": [{
                   "email": "jsmith@example.net",
                   "privacy": "Public"
                }],
               "email": {
                   "privacy": "Public",
                   "value": "jsmith@example.com"
               },
               "full_name": {
                   "privacy": "Public",
                   "value": "John Smith"
               },
               "ircname": {
                   "privacy": "Public",
                   "value": "jsmith"
               },
               "url": "https://mozillians.org/en-US/u/2apreety18/",
               "username": "2apreety18"
              }
          ]
        }

        :parse data: JSON object to parse

        :raise InvalidFormatError: raised when the format of the JSON is
            not valid.
        """
        try:
            for mozillian in json['results']:
                name = self.__encode(mozillian['full_name']['value'])
                email = self.__encode(mozillian['email']['value'])
                username = self.__encode(mozillian['username'])
                uuid = username

                uid = UniqueIdentity(uuid=uuid)
                identity = Identity(name=name, email=email, username=username,
                                    source=self.source, uuid=uuid)
                uid.identities.append(identity)

                # Alternate emails
                for alt_email in mozillian['alternate_emails']:
                    alt_email = self.__encode(alt_email['email'])

                    if alt_email == email:
                        continue

                    identity = Identity(name=name, email=alt_email, username=username,
                                        source=self.source, uuid=uuid)
                    uid.identities.append(identity)

                # IRC account
                ircname = self.__encode(mozillian['ircname']['value'])

                if ircname and ircname != username:
                    identity = Identity(name=None, email=None, username=ircname,
                                        source=self.source, uuid=uuid)
                    uid.identities.append(identity)

                # Mozilla affiliation
                affiliation = mozillian['date_mozillian']
                rol = self.__parse_mozillian_affiliation(affiliation)
                uid.enrollments.append(rol)

                self._identities[uuid] = uid
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_mozillian_affiliation(self, affiliation):
        org = self._organizations.get(MOZILLIANS_ORG, None)

        dt = affiliation['value']
        start_date = str_to_datetime(dt) if dt else MIN_PERIOD_DATE
        end_date = MAX_PERIOD_DATE

        return Enrollment(start=start_date, end=end_date,
                          organization=org)

    def __create_mozillians_org(self):
        org = Organization(name=MOZILLIANS_ORG)
        self._organizations[MOZILLIANS_ORG] = org

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
                return s if s else None
