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

from ..db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE, \
    UniqueIdentity, Identity, Enrollment, Organization
from ..exceptions import InvalidDateError, InvalidFormatError
from ..utils import str_to_datetime


class EclipseParser(object):
    """Parse identities and organizations using Eclipse format.

    The Eclipse data format is a JSON stream that contains
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
    def __init__(self, stream, source='eclipse'):
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
        """Parse Eclipse stream"""

        if not stream:
            raise InvalidFormatError(cause="stream cannot be empty or None")

        json = self.__load_json(stream)

        self.__parse_organizations(json)
        self.__parse_identities(json)

    def __parse_identities(self, json):
        """Parse identities using Eclipse format.

        The Eclipse identities format is a JSON document under the "commiters"
        key. The document should follow the next schema:

        {
          'committers' : {
              'john': {
                  'affiliations': {
                      '1': {
                          'active': '2001-01-01',
                          'inactive': null,
                          'name': 'Organization 1'
                      }
                  },
                  'email': [
                      'john@example.com'
                  ],
                  'first': 'John',
                  'id': 'john',
                  'last': 'Doe',
                  'primary': 'john.doe@example.com'
              }
          }
        }

        :parse json: JSON object to parse

        :raise InvalidFormatError: raised when the format of the JSON is
            not valid.
        """
        try:
            for committer in json['committers'].values():
                name = self.__encode(committer['first'] + ' ' + committer['last'])
                email = self.__encode(committer['primary'])
                username = self.__encode(committer['id'])
                uuid = username

                uid = UniqueIdentity(uuid=uuid)
                identity = Identity(name=name, email=email, username=username,
                                    source=self.source, uuid=uuid)
                uid.identities.append(identity)

                if 'email' in committer:
                    for alt_email in committer['email']:
                        alt_email = self.__encode(alt_email)

                        if alt_email == email:
                            continue

                        identity = Identity(name=name, email=alt_email, username=username,
                                            source=self.source, uuid=uuid)
                        uid.identities.append(identity)

                if 'affiliations' in committer:
                    enrollments = self.__parse_affiliations_json(committer['affiliations'],
                                                                 uuid)
                    for rol in enrollments:
                        uid.enrollments.append(rol)

                self._identities[uuid] = uid
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_organizations(self, json):
        """Parse Eclipse organizations.

        The Eclipse organizations format is a JSON document stored under the
        "organizations" key. The next JSON shows the structure of the
        document:

        {
          'organizations' : {
               '1': {
                   'active': '2001-01-01 18:00:00',
                   'id': '1',
                   'image' : 'http://example.com/image/1',
                   'inactive' : null,
                   'isMember': '1',
                   'name': 'Organization 1',
                   'url': 'http://example.com/org/1'
                    },
               '2': {
                   'active': '2015-12-31 23:59:59',
                   'id': '1',
                   'image' : 'http://example.com/image/2',
                   'inactive': '2008-01-01 18:00:00',
                   'isMember': '1',
                   'name': 'Organization 2',
                   'url': 'http://example.com/org/2'
                    }
          }
        }

        :param json: JSON object to parse

        :raises InvalidFormatError: raised when the format of the JSON is
            not valid.
        """
        try:
            for organization in json['organizations'].values():
                name = self.__encode(organization['name'])

                try:
                    active = str_to_datetime(organization['active'])
                    inactive = str_to_datetime(organization['inactive'])

                    # Ignore organization
                    if not active and not inactive:
                        continue

                    if not active:
                        active = MIN_PERIOD_DATE
                    if not inactive:
                        inactive = MAX_PERIOD_DATE
                except InvalidDateError as e:
                    raise InvalidFormatError(cause=str(e))

                org = self._organizations.get(name, None)

                if not org:
                    org = Organization(name=name)

                    # Store metadata valid for identities parsing
                    org.active = active
                    org.inactive = inactive

                    self._organizations[name] = org
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_affiliations_json(self, affiliations, uuid):
        """Parse identity's affiliations from a json dict"""

        enrollments = []

        for affiliation in affiliations.values():
            name = self.__encode(affiliation['name'])

            try:
                start_date = str_to_datetime(affiliation['active'])
                end_date = str_to_datetime(affiliation['inactive'])
            except InvalidDateError as e:
                raise InvalidFormatError(cause=str(e))

            # Ignore affiliation
            if not start_date and not end_date:
                continue

            if not start_date:
                start_date = MIN_PERIOD_DATE
            if not end_date:
                end_date = MAX_PERIOD_DATE

            org = self._organizations.get(name, None)

            # Set enrolllment period according to organization data
            if org:
                start_date = org.active if start_date < org.active else start_date
                end_date = org.inactive if end_date > org.inactive else end_date

            if not org:
                org = Organization(name=name)
                org.active = MIN_PERIOD_DATE
                org.inactive = MAX_PERIOD_DATE

            enrollment = Enrollment(start=start_date, end=end_date,
                                    organization=org)
            enrollments.append(enrollment)

        return enrollments

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
