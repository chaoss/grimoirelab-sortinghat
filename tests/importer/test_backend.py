#!/usr/bin/env python3
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

from django.contrib.auth import get_user_model
from django.test import TestCase

from sortinghat.core.context import SortingHatContext
from sortinghat.core.importer.backend import IdentitiesImporter
from sortinghat.core.models import Individual, Identity
from sortinghat.core.importer.models import (Individual as ImpIndividual,
                                             Identity as ImpIdentity)


class MockedIdentitiesImporter(IdentitiesImporter):
    NAME = 'test_backend'

    def __init__(self, ctx, url, token=None):
        super().__init__(ctx, url)
        self.token = token
        self.post_counter = 0

    def get_individuals(self):
        indiv_1 = ImpIndividual()
        indiv_1.identities.append(ImpIdentity(source='test_backend', username='test_user'))

        indiv_2 = ImpIndividual()
        indiv_2.identities.append(ImpIdentity(source='test_backend', email='test@example.com'))
        return [indiv_1, indiv_2]

    def post_process_individual(self, individual, uuid):
        """Increases the counter each time this method is called."""

        self.post_counter += 1


class TestBackend(TestCase):

    def setUp(self):
        """Initialize database"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_initialized(self):
        """Test whether the importer is initialized"""

        importer = MockedIdentitiesImporter(self.ctx, 'foo.url')
        self.assertEqual(importer.url, 'foo.url')
        self.assertEqual(importer.token, None)
        self.assertEqual(importer.ctx, self.ctx)

    def test_initialize_extra_params(self):
        """Test whether the importer is initialized"""

        importer = MockedIdentitiesImporter(self.ctx, 'foo.url', '1234')
        self.assertEqual(importer.url, 'foo.url')
        self.assertEqual(importer.token, '1234')
        self.assertEqual(importer.ctx, self.ctx)

    def test_get_individuals(self):
        """Test the get_individual method works"""

        importer = MockedIdentitiesImporter(self.ctx, 'foo.url')
        individuals = importer.get_individuals()
        self.assertEqual(len(individuals), 2)

        indiv = individuals[0]
        self.assertEqual(len(indiv.identities), 1)
        identity = indiv.identities[0]
        self.assertEqual(identity.source, 'test_backend')
        self.assertEqual(identity.username, 'test_user')

    def test_base_class_error(self):
        """Test the ImportIdentities class raise NotImplementedError"""

        importer = IdentitiesImporter(self.ctx, 'foo.url')
        with self.assertRaises(NotImplementedError):
            importer.get_individuals()

    def test_load_individuals(self):
        """Test the import_identities method works"""

        importer = MockedIdentitiesImporter(self.ctx, 'foo.url')
        importer.import_identities()

        individuals = Individual.objects.all()
        identities = Identity.objects.all()
        self.assertEqual(len(individuals), 2)
        self.assertEqual(len(identities), 2)

        indiv = individuals[0]
        identities = indiv.identities.all()
        self.assertEqual(len(identities), 1)
        self.assertEqual(identities[0].source, 'test_backend')
        self.assertEqual(identities[0].username, 'test_user')

        indiv = individuals[0]
        identities = indiv.identities.all()
        self.assertEqual(len(identities), 1)
        self.assertEqual(identities[0].source, 'test_backend')
        self.assertEqual(identities[0].username, 'test_user')

    def test_post_processing_individuals(self):
        """Test if it runs the post processing method"""

        # The implementation on the mocked class increases
        # a counter each time the method is call.
        # The result must be the number of individuals imported.
        importer = MockedIdentitiesImporter(self.ctx, 'foo.url')
        importer.import_identities()

        individuals = Individual.objects.all()
        self.assertEqual(len(individuals), 2)
        self.assertEqual(importer.post_counter, 2)

    def test_load_existing_individuals(self):
        """Test the import_identities method works running twice"""

        importer = MockedIdentitiesImporter(self.ctx, 'foo.url')
        importer.import_identities()

        individuals = Individual.objects.all()
        identities = Identity.objects.all()
        self.assertEqual(len(individuals), 2)
        self.assertEqual(len(identities), 2)

        indiv = individuals[0]
        identities = indiv.identities.all()
        self.assertEqual(identities[0].source, 'test_backend')
        self.assertEqual(identities[0].username, 'test_user')

        indiv = individuals[1]
        identities = indiv.identities.all()
        self.assertEqual(identities[0].source, 'test_backend')
        self.assertEqual(identities[0].email, 'test@example.com')

        importer.import_identities()

        individuals = Individual.objects.all()
        identities = Identity.objects.all()
        self.assertEqual(len(individuals), 2)
        self.assertEqual(len(identities), 2)

        indiv = individuals[0]
        identities = indiv.identities.all()
        self.assertEqual(identities[0].source, 'test_backend')
        self.assertEqual(identities[0].username, 'test_user')

        indiv = individuals[1]
        identities = indiv.identities.all()
        self.assertEqual(identities[0].source, 'test_backend')
        self.assertEqual(identities[0].email, 'test@example.com')
