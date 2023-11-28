# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import datetime
import os
import re
import unittest.mock

from dateutil.tz import tzutc
from django.contrib.auth import get_user_model
from django.test import TestCase

from sortinghat.core.context import SortingHatContext
from sortinghat.core.importer.backends.gitdm import GitdmImporter, GitdmParser
from sortinghat.core.models import Individual, Identity, MAX_PERIOD_DATE, MIN_PERIOD_DATE


DOMAINS_INVALID_FORMAT_ERROR = "line %(line)s: invalid format"


def read_file(filename, mode='r'):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), mode) as f:
        content = f.read()
    return content


def mock_fetch(cls, url):
    if url == 'valid_aliases':
        return read_file('data/gitdm/gitdm_email_aliases_valid.txt')
    elif url == 'email_employer':
        return read_file('data/gitdm/gitdm_email_to_employer_valid.txt')
    elif url == 'invalid_email_employer':
        return read_file('data/gitdm/gitdm_email_to_employer_invalid.txt')


class TestGitdmImporter(TestCase):
    """Test Gitdm importer"""

    def setUp(self):
        """Initialize database"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_initialized(self):
        """Test whether the importer is initialized"""

        importer = GitdmImporter(self.ctx, 'foo.url')
        self.assertEqual(importer.ctx, self.ctx)
        self.assertEqual(importer.url, 'foo.url')
        self.assertEqual(importer.aliases_url, None)
        self.assertEqual(importer.email_validation, True)

    def test_initialized_extra(self):
        """Test whether the importer is initialized"""

        importer = GitdmImporter(self.ctx, url='foo.url', aliases_url='aliases.url', email_validation=False)
        self.assertEqual(importer.ctx, self.ctx)
        self.assertEqual(importer.url, 'foo.url')
        self.assertEqual(importer.aliases_url, 'aliases.url')
        self.assertEqual(importer.email_validation, False)

    def test_initialize_email_verification(self):
        """Test whether the importer detects email_verification as string"""

        importer = GitdmImporter(self.ctx, url='foo.url', email_validation='False')
        self.assertEqual(importer.email_validation, False)

        importer = GitdmImporter(self.ctx, url='foo.url', email_validation='True')
        self.assertEqual(importer.email_validation, True)

    @unittest.mock.patch.object(GitdmImporter, '_fetch_data', mock_fetch)
    def test_email_employer_parser(self):
        """Test whether the importer detects all the enrollments in the file"""

        importer = GitdmImporter(ctx=self.ctx, url='email_employer')
        individuals = importer.get_individuals()

        self.assertEqual(len(individuals), 4)

        # Individual 1
        ind1 = individuals[0]

        identities = ind1.identities
        identities.sort(key=lambda x: x.email)
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jsmith@example.com')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind1.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(enrollments), 2)

        org = enrollments[0]
        self.assertEqual(org.organization.name, 'Bitergia')
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, datetime.datetime(2015, 1, 1, tzinfo=tzutc()))

        org = enrollments[1]
        self.assertEqual(org.organization.name, 'Example Company')
        self.assertEqual(org.start, datetime.datetime(2015, 1, 1, tzinfo=tzutc()))
        self.assertEqual(org.end, MAX_PERIOD_DATE)

        # Individual 2
        ind2 = individuals[1]

        identities = ind2.identities
        identities.sort(key=lambda x: x.email)
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jdoe@example.com')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind2.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(enrollments), 1)

        org = enrollments[0]
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, MAX_PERIOD_DATE)
        self.assertEqual(org.organization.name, 'Example Company')

        # Individual 3
        ind3 = individuals[2]

        identities = ind3.identities
        identities.sort(key=lambda x: x.email)
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jrae@example.net')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind3.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(enrollments), 1)

        org = enrollments[0]
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, MAX_PERIOD_DATE)
        self.assertEqual(org.organization.name, 'Bitergia')

        # Individual 4
        ind4 = individuals[3]

        identities = ind4.identities
        identities.sort(key=lambda x: x.email)
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'john_doe@example.net')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind4.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(enrollments), 1)

        org = enrollments[0]
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, MAX_PERIOD_DATE)
        self.assertEqual(org.organization.name, 'LibreSoft')

    @unittest.mock.patch.object(GitdmImporter, '_fetch_data', mock_fetch)
    def test_email_employer_aliases_parser(self):
        """Test whether the importer detects all the enrollments in the file"""

        importer = GitdmImporter(ctx=self.ctx,
                                 url='email_employer',
                                 aliases_url='valid_aliases')
        individuals = importer.get_individuals()

        self.assertEqual(len(individuals), 4)

        # jdoe@example.com & john_doe@example.net
        ind1 = individuals[0]

        identities = ind1.identities
        identities.sort(key=lambda x: x.email)
        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jdoe@example.com')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        identity = identities[1]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'john_doe@example.net')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind1.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(enrollments), 2)

        org = enrollments[0]
        self.assertEqual(org.organization.name, 'Example Company')
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, MAX_PERIOD_DATE)

        org = enrollments[1]
        self.assertEqual(org.organization.name, 'LibreSoft')
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, MAX_PERIOD_DATE)

        # jrae@example.net & jrae@example.com
        ind2 = individuals[1]

        identities = ind2.identities
        identities.sort(key=lambda x: x.email)
        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jrae@example.com')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        identity = identities[1]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jrae@example.net')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind2.enrollments
        self.assertEqual(len(enrollments), 1)

        org = enrollments[0]
        self.assertEqual(org.organization.name, 'Bitergia')
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, MAX_PERIOD_DATE)

        # jrae@laptop & jrae@mylaptop
        ind3 = individuals[2]
        identities = ind3.identities
        identities.sort(key=lambda x: x.username)
        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, None)
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, 'jrae@laptop')

        identity = identities[1]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, None)
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, 'jrae@mylaptop')

        enrollments = ind3.enrollments
        self.assertEqual(len(enrollments), 0)

        # jsmith@example.com
        ind4 = individuals[3]

        identities = ind4.identities
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jsmith@example.com')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind4.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(enrollments), 2)

        org = enrollments[0]
        self.assertEqual(org.organization.name, 'Bitergia')
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, datetime.datetime(2015, 1, 1, tzinfo=tzutc()))

        org = enrollments[1]
        self.assertEqual(org.organization.name, 'Example Company')
        self.assertEqual(org.start, datetime.datetime(2015, 1, 1, tzinfo=tzutc()))
        self.assertEqual(org.end, MAX_PERIOD_DATE)

    @unittest.mock.patch.object(GitdmImporter, '_fetch_data', mock_fetch)
    def test_email_validation(self):
        """Test whether the importer validates the emails"""

        importer = GitdmImporter(ctx=self.ctx,
                                 url='invalid_email_employer')
        individuals = importer.get_individuals()

        self.assertEqual(len(individuals), 1)

        # Only 1 valid individual of 5
        ind1 = individuals[0]

        identities = ind1.identities
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.source, 'gitdm')
        self.assertEqual(identity.email, 'jsmith@example.com')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.username, None)

        enrollments = ind1.enrollments
        self.assertEqual(len(enrollments), 1)

        org = enrollments[0]
        self.assertEqual(org.organization.name, 'Bitergia')
        self.assertEqual(org.start, MIN_PERIOD_DATE)
        self.assertEqual(org.end, datetime.datetime(2015, 1, 1, tzinfo=tzutc()))

    @unittest.mock.patch.object(GitdmImporter, '_fetch_data', mock_fetch)
    def test_supress_email_validation(self):
        """Test whether the importer can supress email validation"""

        importer = GitdmImporter(ctx=self.ctx,
                                 url='invalid_email_employer',
                                 email_validation=False)
        individuals = importer.get_individuals()

        self.assertEqual(len(individuals), 5)

        expected_emails = ['jsmith.example.com', 'jdoe$example.com', 'jsmith@example.com',
                           'jrae-example-net', 'john_doeexample']

        for uid in individuals:
            identity = uid.identities[0]
            self.assertIn(identity.email, expected_emails)
            self.assertEqual(identity.name, None)
            self.assertEqual(identity.username, None)
            self.assertEqual(identity.source, 'gitdm')
            self.assertEqual(identity.uuid, None)

    @unittest.mock.patch.object(GitdmImporter, '_fetch_data', mock_fetch)
    def test_load_individuals(self):
        """Test the import_identities method works"""

        expected = {
            'd5b277340e6b8a7166e219b3d104f9a2b2c3f9ac': {
                'profile': {
                    'email': 'jsmith@example.com'
                },
                'identities': [
                    {
                        'uuid': 'd5b277340e6b8a7166e219b3d104f9a2b2c3f9ac',
                        'name': None,
                        'email': 'jsmith@example.com',
                        'username': None
                    }
                ]
            },
            '3c5927fa7c7ad2b1276f98eabd603efeb061b089': {
                'profile': {
                    'email': 'jdoe@example.com'
                },
                'identities': [
                    {
                        'uuid': '3c5927fa7c7ad2b1276f98eabd603efeb061b089',
                        'name': None,
                        'email': 'jdoe@example.com',
                        'username': None
                    }
                ]
            },
            '998862fc7300c96d1962565d738fa2481d371c5e': {
                'profile': {
                    'email': 'jrae@example.net'
                },
                'identities': [
                    {
                        'uuid': '998862fc7300c96d1962565d738fa2481d371c5e',
                        'name': None,
                        'email': 'jrae@example.net',
                        'username': None
                    }
                ]
            },
            '1da47c3655012673aef3a7f14ddf18a851fb0e5d': {
                'profile': {
                    'email': 'john_doe@example.net'
                },
                'identities': [
                    {
                        'uuid': '1da47c3655012673aef3a7f14ddf18a851fb0e5d',
                        'name': None,
                        'email': 'john_doe@example.net',
                        'username': None
                    }
                ]
            },
        }

        importer = GitdmImporter(self.ctx, 'email_employer')
        importer.import_identities()

        individuals = Individual.objects.all()
        identities = Identity.objects.all()
        self.assertEqual(len(individuals), 4)
        self.assertEqual(len(identities), 4)

        # Individual 1
        for individual in individuals:
            self.assertIn(individual.mk, expected)
            self.assertEqual(individual.profile.email, expected[individual.mk]['profile']['email'])
            self.assertEqual(individual.identities.count(), len(expected[individual.mk]['identities']))
            self.assertEqual(individual.identities.first().name, expected[individual.mk]['identities'][0]['name'])
            self.assertEqual(individual.identities.first().username, expected[individual.mk]['identities'][0]['username'])
            self.assertEqual(individual.identities.first().email, expected[individual.mk]['identities'][0]['email'])
            self.assertEqual(individual.identities.first().source, 'gitdm')

    @unittest.mock.patch.object(GitdmImporter, '_fetch_data', mock_fetch)
    def test_load_existing_individuals(self):
        """Test the import_identities method works running twice"""

        importer = GitdmImporter(self.ctx, 'email_employer')
        importer.import_identities()

        individuals = Individual.objects.all()
        identities = Identity.objects.all()
        self.assertEqual(len(individuals), 4)
        self.assertEqual(len(identities), 4)

        mks_before = Individual.objects.values_list('mk', flat=True)
        uuids_before = Identity.objects.values_list('uuid', flat=True)

        importer.import_identities()

        individuals = Individual.objects.all()
        identities = Identity.objects.all()
        self.assertEqual(len(individuals), 4)
        self.assertEqual(len(identities), 4)

        mks_after = Individual.objects.values_list('mk', flat=True)
        uuids_after = Identity.objects.values_list('uuid', flat=True)

        self.assertListEqual(sorted(mks_before), sorted(mks_after))
        self.assertListEqual(sorted(uuids_before), sorted(uuids_after))


class TestGitdmRegEx(unittest.TestCase):
    """Test regular expressions used while parsing Gitdm inputs"""

    def test_valid_lines(self):
        """Check whether it parses valid lines"""

        parser = re.compile(GitdmParser.VALID_LINE_REGEX, re.UNICODE)

        # Parse some valid lines
        m = parser.match("jdoe@example.com\tExample  Company\t# John Doe")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.com\t\tExample < 2010-01-01\t\t# John Doe")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.com\tExample  Company")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.com\t\t\tjohndoe@example.com")
        self.assertIsNotNone(m)

        m = parser.match("example.org\t\tExample/n' Co. ")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.org    Example")
        self.assertIsNotNone(m)

        # Parse some lines with valid comments
        m = parser.match("example.org\torganization\t### comment")
        self.assertIsNotNone(m)

        m = parser.match("jonhdoe@exampl.com\torganization\t#   \t\r")
        self.assertIsNotNone(m)

        m = parser.match("domain\torganization\t#\tcomment #1\r\n")
        self.assertIsNotNone(m)

        m = parser.match(u"example.org\tExamplé")
        self.assertIsNotNone(m)

        # It's weird but it's a valid line
        m = parser.match("jdoe@example.org\tjdoe@exa\tmple.com")
        self.assertIsNotNone(m)

        # These are examples or invalid lines
        m = parser.match("\texample.org\t\tExample")
        self.assertIsNone(m)

        m = parser.match("   example.org   Example")
        self.assertIsNone(m)

        m = parser.match("jdoe@example.org\nExample\t\n")
        self.assertIsNone(m)

        m = parser.match("example.org\t\n\tExample")
        self.assertIsNone(m)

        m = parser.match("example.org\tExa\nmple")
        self.assertIsNone(m)

        m = parser.match("domain organization\t   # comment\n\t")
        self.assertIsNone(m)

    def test_lines_to_ignore(self):
        """Check whether it parses blank or comment lines"""

        parser = re.compile(GitdmParser.LINES_TO_IGNORE_REGEX, re.UNICODE)

        # Parse some valid blank lines
        m = parser.match("")
        self.assertIsNotNone(m)

        m = parser.match("\n\n\n")
        self.assertIsNotNone(m)

        m = parser.match("      \t    \r\n ")
        self.assertIsNotNone(m)

        m = parser.match("\t\t  \n  \t\n")
        self.assertIsNotNone(m)

        # Do not parse invalid blank lines
        m = parser.match("\ndomain organization\n\n")
        self.assertIsNone(m)

        m = parser.match(" domain \t organization  \r\n ")
        self.assertIsNone(m)

        m = parser.match("\t   domain organization\t  \n  \n")
        self.assertIsNone(m)

        # Parse some valid comments
        m = parser.match("#    \t\n\r")
        self.assertIsNotNone(m)

        m = parser.match("#|tcomment #1\r\n")
        self.assertIsNotNone(m)

    def test_email(self):
        """Check email address pattern"""

        parser = re.compile(GitdmParser.EMAIL_ADDRESS_REGEX, re.UNICODE)

        # Parse some valid email addresses
        m = parser.match("johndoe@example.com")
        self.assertIsNotNone(m)

        m = parser.match("jonh.doe@exampel.com")
        self.assertIsNotNone(m)

        m = parser.match("?¡~,123@example.com")
        self.assertIsNotNone(m)

        # Do not parse invalid email addresses
        m = parser.match("jonh@doe@example.com")
        self.assertIsNone(m)

        m = parser.match("   johndoe@example.com")
        self.assertIsNone(m)

        m = parser.match("johndoe@example.com  ")
        self.assertIsNone(m)

        m = parser.match("johndoe@example.com\t")
        self.assertIsNone(m)

        m = parser.match("johndoe@.com")
        self.assertIsNone(m)

    def test_organization(self):
        """Check organization pattern"""

        parser = re.compile(GitdmParser.ORGANIZATION_REGEX, re.UNICODE)

        # Organizations must start with alphanumeric or underscore
        # characters. They can have spaces or other symbols, but
        # cannot include other separators like tabs or #

        # These must work
        m = parser.match("Example")
        self.assertIsNotNone(m)

        m = parser.match("0Example")
        self.assertIsNotNone(m)

        m = parser.match("_Example")
        self.assertIsNotNone(m)

        m = parser.match("My Example")
        self.assertIsNotNone(m)

        m = parser.match("Example\n")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "Example")

        m = parser.match("'Example")
        self.assertIsNotNone(m)

        m = parser.match("/Example")
        self.assertIsNotNone(m)

        m = parser.match("-Example")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("Example   ")
        self.assertIsNone(m)

        m = parser.match("Exa\tmple")
        self.assertIsNone(m)

        m = parser.match("Example #")
        self.assertIsNone(m)

        m = parser.match(" ")
        self.assertIsNone(m)

    def test_domain(self):
        """Check domain pattern"""

        parser = re.compile(GitdmParser.DOMAIN_REGEX, re.UNICODE)

        # Domains must start with alphanumeric or underscore
        # characters.

        # These must work
        m = parser.match("__example.org")
        self.assertIsNotNone(m)

        m = parser.match("9example.org")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("'_example.org")
        self.assertIsNone(m)

        m = parser.match("/example.org")
        self.assertIsNone(m)

        m = parser.match("exa\tmple.org")
        self.assertIsNone(m)

        m = parser.match(" example.org")
        self.assertIsNone(m)

    def test_enrollment(self):
        """Check enrollment pattern"""

        parser = re.compile(GitdmParser.ENROLLMENT_REGEX, re.UNICODE)

        # These must work
        m = parser.match("Example")
        self.assertIsNotNone(m)

        m = parser.match("0Example")
        self.assertIsNotNone(m)

        m = parser.match("_Example")
        self.assertIsNotNone(m)

        m = parser.match("My Example")
        self.assertIsNotNone(m)

        m = parser.match("Example < 2012-01-01")
        self.assertIsNotNone(m)

        m = parser.match("Example, Inc.")
        self.assertIsNotNone(m)

        m = parser.match("'Example")
        self.assertIsNotNone(m)

        m = parser.match("/Example")
        self.assertIsNotNone(m)

        m = parser.match("Example   < 2012-01-01")
        self.assertIsNotNone(m)

        m = parser.match("Exa\tmple")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("Example #")
        self.assertIsNone(m)

        m = parser.match(" ")
        self.assertIsNone(m)

        m = parser.match("Example <")
        self.assertIsNone(m)

        m = parser.match("Example<")
        self.assertIsNone(m)

        m = parser.match("Example < 200-01-01")
        self.assertIsNone(m)

        m = parser.match("Example < 2012-1-1")
        self.assertIsNone(m)

        m = parser.match("Example < 2012-01-1")
        self.assertIsNone(m)

        m = parser.match("Example < 1-1-2001")
        self.assertIsNone(m)

        m = parser.match("Example < 2012-01-01 <")
        self.assertIsNone(m)
