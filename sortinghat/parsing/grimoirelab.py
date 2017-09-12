# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Bitergia
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
#     Luis Cañas-Díaz <sduenas@bitergia.com>
#

from __future__ import absolute_import
from __future__ import unicode_literals

import itertools
import re
import datetime
import yaml

from ..db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE, \
    UniqueIdentity, Identity, Enrollment, Organization, Domain, Profile
from ..exceptions import InvalidFormatError

PERCEVAL_BACKENDS = ['askbot','bugzilla','bugzillarest','confluence','discourse',
                    'dockerhub','gerrit','git','github','gmane','hyperkitty','jenkins',
                    'jira','mbox','mediawiki','meetup','nntp','phabricator','pipermail',
                    'redmine','rss','slack','stackexchange','supybot','telegram']


class GrimoireLabParser(object):
    """Parse identities and organizations using GrimoireLab format.

    The GrimoireLab data format is a YAML stream that contains information
    about unique identities and organizations.

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

    EMAIL_ADDRESS_REGEX = r"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$"


    def __init__(self, identities=None, domain_employer=None,
                 source='grimoirelab'):
        self._identities = {}
        self._organizations = {}
        self.source = source

        if not (identities or domain_employer):
            raise ValueError('Null identities and organization streams')

        self.__parse(identities, domain_employer)

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

    def __parse(self, identities_stream, domain_employer_stream):
        """Parse GrimoireLab stream"""
        if domain_employer_stream:
            self.__parse_organizations(domain_employer_stream)

        if identities_stream:
            self.__parse_identities(identities_stream)

    def __parse_identities(self, stream):
        """Parse identities using GrimoireLab format.

        The GrimoireLab identities format is a YAML document following a
        schema similar to the example below. More information available
        at https://github.com/bitergia/identities

        - profile:
            name: Vivek K.
            is_bot: false
          github:
            - vsekhark
          email:
            - vivek@****.com
          enrollments:
            - organization: Community
              start: 1900-01-01
              end: 2100-01-01

        :parse json: YAML object to parse

        :raise InvalidFormatError: raised when the format of the YAML is
            not valid.
        """
        def __create_sh_identities(name, emails, yaml_entry):
            """Create SH identities based on name, emails and backens data in yaml_entry"""
            my_ids = []
            my_ids.append(Identity(name=name, source=self.source))

            # FIXME we should encourage our users to add email or usernames
            # and if not returning at least a WARNING
            if emails:
                for m in emails:
                    my_ids.append(Identity(email=m, source=self.source))

            for pb in PERCEVAL_BACKENDS:

                if pb not in yaml_entry:
                    continue

                for username in yaml_entry[pb]:
                    identity = Identity(username=username, source=pb)
                    my_ids.append(identity)

            return my_ids


        yaml = self.__load_yml(stream)

        try:
            for yid in yaml:
                profile = yid['profile']
                if profile is None:
                    raise AttributeError('profile')

                #we want the KeyError if name is missing
                name = yid['profile']['name']
                is_bot = profile.get('is_bot', False)

                emails = yid.get('email', None)
                enrollments = yid.get('enrollments', None)

                first_email, first_username = self.__first_email_username(yid)
                uuid = self.__compose_uuid(name, first_email, first_username)

                uid = UniqueIdentity(uuid=uuid)

                prf = Profile(name=name, is_bot=is_bot)
                uid.profile = prf

                # now it is time to add the identities for name, emails and backends
                sh_identities = __create_sh_identities(name, emails, yid)
                uid.identities += sh_identities

                if enrollments:
                    affiliations = self.__parse_affiliations_yml(enrollments, uuid)
                    uid.enrollments += affiliations

                self._identities[uuid] = uid

        except KeyError as e:
            msg = "invalid GrimoireLab yaml format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_organizations(self, stream):
        """Parse GrimoireLab organizations.

        The GrimoireLab organizations format is a YAML element stored
        under the "organizations" key. The next example shows the
        structure of the document:

        - organizations:
            Bitergia:
                - bitergia.com
                - support.bitergia.com
                - biterg.io
            LibreSoft:
                - libresoft.es

        :param json: YAML object to parse

        :raises InvalidFormatError: raised when the format of the YAML is
            not valid.
        """
        if not stream:
            return

        yaml = self.__load_yml(stream)

        try:
            for element in yaml:
                name = self.__encode(element['organization'])

                if not name:
                    msg = "invalid GrimoireLab yaml format. Empty organization name"
                    raise InvalidFormatError(cause=msg)

                o = Organization(name=name)

                if 'domains' in element:
                    if isinstance(element['domains'], list):
                        for dom in element['domains']:
                            if dom:
                                d = Domain(domain=dom, is_top_domain=False)
                                o.domains.append(d)
                            else:
                                msg = "invalid GrimoireLab yaml format. Empty domain name for organization %s" % name
                                raise InvalidFormatError(cause=msg)
                    else:
                        msg = "invalid GrimoireLab yaml format. List of elements expected for organization %s" % name
                        raise InvalidFormatError(cause=msg)
                self._organizations[name] = o

        except KeyError as e:
            msg = "invalid GrimoireLab yaml format. Attribute %s not found" % e.args
            raise InvalidFormatError(cause=msg)

        except TypeError as e:
            msg = "invalid GrimoireLab yaml format. %s" % e.args
            raise InvalidFormatError(cause=msg)

    def __parse_affiliations_yml(self, affiliations, uuid):
        """Parse identity's affiliations from a yaml dict."""
        enrollments = []

        for aff in affiliations:
            name = self.__encode(aff['organization'])
            if not name:
                msg = "invalid GrimoireLab yaml format. Empty organization name"
                raise InvalidFormatError(cause=msg)

            # we trust the Organization name included in the identities file
            org = Organization(name=name)

            if org is None:
                continue

            if 'start' in aff:
                start_date = self.__force_datetime(aff['start'])
            else:
                start_date = MIN_PERIOD_DATE

            if 'end' in aff:
                end_date = self.__force_datetime(aff['end'])
            else:
                end_date = MAX_PERIOD_DATE

            enrollment = Enrollment(start=start_date, end=end_date,
                                    organization=org)
            enrollments.append(enrollment)

        self.__validate_enrollment_periods(enrollments)

        return enrollments

    def __force_datetime(self, obj):
        """Converts ojb to time.datetime.datetime

        YAML parsing returns either date or datetime object depending
        on how the date is written. YYYY-MM-DD will return a date and
        YYYY-MM-DDThh:mm:ss will return a datetime

        :param obj: date or datetime object
        """
        if isinstance(obj,datetime.datetime):
            return obj

        t = datetime.time(0,0)
        return datetime.datetime.combine(obj, t)

    def __load_yml(self, stream):
        """Load yml stream into a dict object """
        try:
            return yaml.load(stream)
        except ValueError as e:
            cause = "invalid yml format. %s" % str(e)
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

    def __compose_uuid(self, name, email, username):
        """Composes a uuid string as result of the concatenation of name and (email and/or username)"""
        uuid = ''
        uuid += name
        if email:
            uuid += email
        if username:
            uuid += username
        return uuid

    def __first_email_username(self, yaml_identity):
        """Returns first email and first username found in the YAML identity"""
        first_email = None
        first_username = None
        emails = yaml_identity.get('email', None)

        if emails:
            first_email = self.__validate_email(emails[0])

        for pb in PERCEVAL_BACKENDS:
            if pb in yaml_identity:
                first_username = yaml_identity[pb][0]
                break

        #either first_email or first_username must exist
        if (first_email is None) and (first_username is None):
            msg = "invalid GrimoireLab yaml format. At least email or user account must be included"
            raise InvalidFormatError(cause=msg)
        return (first_email, first_username)

    def __validate_email(self, email):
        """Checks if a string looks like an email address"""
        e = re.match(self.EMAIL_ADDRESS_REGEX, email, re.UNICODE)
        if e:
            return email
        else:
            msg = "invalid GrimoireLab yaml format. Invalid email address: " + str(email)
            raise InvalidFormatError(cause=msg)

    def __validate_enrollment_periods(self, enrollments):
        """Check for overlapped periods in the enrollments"""
        for a, b in itertools.combinations(enrollments, 2):

            max_start = max(a.start, b.start)
            min_end = min(a.end, b.end)

            if max_start < min_end:
                msg = "invalid GrimoireLab enrollment dates. " \
                "Organization dates overlap."
                raise InvalidFormatError(cause=msg)

        return enrollments
