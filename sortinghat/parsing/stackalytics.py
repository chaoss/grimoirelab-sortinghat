# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2017 Bitergia
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import logging

from ..db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE, \
    UniqueIdentity, Identity, Enrollment, Organization, Domain
from ..exceptions import InvalidFormatError
from ..utils import str_to_datetime

logger = logging.getLogger(__name__)


class StackalyticsParser(object):
    """Parse identities and organizations using the Stackalytics format.

    The Stackalytics data format is a JSON stream that contains
    information about unique identities and organizations.

    The unique identities are stored in an object named 'users'.
    Each 'user' is an object that stores its email addresses
    and enrollments or affiliations.

    Organizations are stored in the 'companies' object. Each object
    stores the name of the organization, its aliases and domains.

    :param stream: stream to parse

    :raises InvalidFormatError: raised when the format of the stream is
    not valid.
    """
    def __init__(self, stream, source='stackalytics'):
        self._identities = {}
        self._organizations = {}
        self.source = source

        self.__parse(stream)

    def __parse(self, stream):
        """Parse Stackalytics stream"""

        if not stream:
            raise InvalidFormatError(cause="stream cannot be empty or None")

        json = self.__load_json(stream)

        self.__parse_organizations(json)
        self.__parse_identities(json)

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

    def __parse_organizations(self, json):
        """Parse Stackalytics organizations.

        The Stackalytics organizations format is a JSON document stored under the
        "companies" key. The next JSON shows the structure of the
        document:

        {
            "companies" : [
                {
                    "domains": ["alcatel-lucent.com"],
                    "company_name": "Alcatel-Lucent",
                    "aliases": ["Alcatel Lucent", "Alcatel-Lcuent"]
                },
                {
                    "domains": ["allegrogroup.com", "allegro.pl"],
                    "company_name": "Allegro",
                    "aliases": ["Allegro Group", "Grupa Allegro", "Grupa Allegro Sp. z o.o."]
                },
                {
                    "domains": ["altiscale.com"],
                    "company_name": "Altiscale"
                },
            ]
        }

        :param json: JSON object to parse

        :raises InvalidFormatError: raised when the format of the JSON is
            not valid.
        """
        try:
            for company in json['companies']:
                name = self.__encode(company['company_name'])

                org = self._organizations.get(name, None)

                if not org:
                    org = Organization(name=name)
                    self._organizations[name] = org

                for domain in company['domains']:
                    if not domain:
                        continue
                    dom = Domain(domain=domain)
                    org.domains.append(dom)
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_identities(self, json):
        """Parse identities using Stackalytics format.

        The Stackalytics identities format is a JSON document under the
        "users" key. The document should follow the next schema:

        {
            "users": [
                {
                    "launchpad_id": "0-jsmith",
                    "gerrit_id": "jsmith",
                    "companies": [
                        {
                            "company_name": "Example",
                            "end_date": null
                        }
                    ],
                    "user_name": "John Smith",
                    "emails": ["jsmith@example.com", "jsmith@example.net"]
                },
                {
                    "companies": [
                        {
                            "company_name": "Bitergia",
                            "end_date": null
                        },
                        {
                            "company_name": "Example",
                            "end_date": "2010-Jan-01"
                        }
                    ],
                    "user_name": "John Doe",
                    "emails": ["jdoe@bitergia.com", "jdoe@example.com"]
                }
            ]
        }

        :parse json: JSON object to parse

        :raise InvalidFormatError: raised when the format of the JSON is
            not valid.
        """
        try:
            for user in json['users']:
                name = self.__encode(user['user_name'])
                uuid = name

                uid = UniqueIdentity(uuid=uuid)
                identity = Identity(name=name, email=None, username=None,
                                    source=self.source, uuid=uuid)
                uid.identities.append(identity)

                for email_addr in user['emails']:
                    email = self.__encode(email_addr)

                    identity = Identity(name=name, email=email, username=None,
                                        source=self.source, uuid=uuid)
                    uid.identities.append(identity)

                for site_id in ['gerrit_id', 'launchpad_id']:
                    username = user.get(site_id, None)

                    if not username:
                        continue

                    username = self.__encode(username)
                    source = self.source + ':' + site_id.replace('_id', '')
                    identity = Identity(name=name, email=None, username=username,
                                        source=source, uuid=uuid)
                    uid.identities.append(identity)

                for rol in self.__parse_enrollments(user):
                    uid.enrollments.append(rol)

                self._identities[uuid] = uid
        except KeyError as e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_enrollments(self, user):
        """Parse user enrollments"""

        enrollments = []

        for company in user['companies']:
            name = company['company_name']

            org = self._organizations.get(name, None)

            if not org:
                org = Organization(name=name)
                self._organizations[name] = org

            start_date = MIN_PERIOD_DATE
            end_date = MAX_PERIOD_DATE

            if company['end_date']:
                end_date = str_to_datetime(company['end_date'])

            rol = Enrollment(start=start_date, end=end_date,
                             organization=org)
            enrollments.append(rol)

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
        return s if s else None
