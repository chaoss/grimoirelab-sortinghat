# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
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

from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core import api
from sortinghat.core.errors import (AlreadyExistsError,
                                    NotFoundError,
                                    InvalidValueError)
from sortinghat.core.models import (UniqueIdentity,
                                    Identity)


SOURCE_NONE_OR_EMPTY_ERROR = "'source' cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be empty"


class TestUUID(TestCase):
    """Unit tests for generate_uuid function"""

    def test_uuid(self):
        """Check whether the function returns the expected UUID"""

        result = api.generate_uuid('scm', email='jsmith@example.com',
                                   name='John Smith', username='jsmith')
        self.assertEqual(result, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        result = api.generate_uuid('scm', email='jsmith@example.com')
        self.assertEqual(result, '334da68fcd3da4e799791f73dfada2afb22648c6')

        result = api.generate_uuid('scm', email='', name='John Smith', username='jsmith')
        self.assertEqual(result, 'a4b4591c3a2171710c157d7c278ea3cc03becf81')

        result = api.generate_uuid('scm', email='', name='John Smith', username='')
        self.assertEqual(result, '76e3624e24aacae178d05352ad9a871dfaf81c13')

        result = api.generate_uuid('scm', email='', name='', username='jsmith')
        self.assertEqual(result, '6e7ce2426673f8a23a72a343b1382dda84c0078b')

        result = api.generate_uuid('scm', email='', name='John Ca\xf1as', username='jcanas')
        self.assertEqual(result, 'c88e126749ff006eb1eea25e4bb4c1c125185ed2')

        result = api.generate_uuid('scm', email='', name="Max Müster", username='mmuester')
        self.assertEqual(result, '9a0498297d9f0b7e4baf3e6b3740d22d2257367c')

    def test_case_insensitive(self):
        """Check if same values in lower or upper case produce the same UUID"""

        uuid_a = api.generate_uuid('scm', email='jsmith@example.com',
                                   name='John Smith', username='jsmith')
        uuid_b = api.generate_uuid('SCM', email='jsmith@example.com',
                                   name='John Smith', username='jsmith')
        self.assertEqual(uuid_a, uuid_b)

        uuid_c = api.generate_uuid('scm', email='jsmith@example.com',
                                   name='john smith', username='jsmith')
        self.assertEqual(uuid_c, uuid_a)

        uuid_d = api.generate_uuid('scm', email='jsmith@example.com',
                                   name='John Smith', username='JSmith')
        self.assertEqual(uuid_d, uuid_a)

        uuid_e = api.generate_uuid('scm', email='JSMITH@example.com',
                                   name='John Smith', username='jsmith')
        self.assertEqual(uuid_e, uuid_a)

    def test_case_unaccent_name(self):
        """Check if same values accent or unaccent produce the same UUID"""

        accent_result = api.generate_uuid('scm', email='', name="Max Müster", username='mmuester')
        unaccent_result = api.generate_uuid('scm', email='', name="Max Muster", username='mmuester')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, '9a0498297d9f0b7e4baf3e6b3740d22d2257367c')

        accent_result = api.generate_uuid('scm', email='', name="Santiago Dueñas", username='')
        unaccent_result = api.generate_uuid('scm', email='', name="Santiago Duenas", username='')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, '0f1dd18839007ee8a11d02572ca0a0f4eedaf2cd')

        accent_result = api.generate_uuid('scm', email='', name="Tomáš Čechvala", username='')
        partial_accent_result = api.generate_uuid('scm', email='', name="Tomáš Cechvala", username='')
        unaccent_result = api.generate_uuid('scm', email='', name="Tomas Cechvala", username='')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, partial_accent_result)

    def test_surrogate_escape(self):
        """Check if no errors are raised for invalid UTF-8 chars"""

        result = api.generate_uuid('scm', name="Mishal\udcc5 Pytasz")
        self.assertEqual(result, '625166bdc2c4f1a207d39eb8d25315010babd73b')

    def test_none_source(self):
        """Check whether UUID cannot be obtained giving a None source"""

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.generate_uuid(None)

    def test_empty_source(self):
        """Check whether UUID cannot be obtained giving aadded to the registry"""

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.generate_uuid('')

    def test_none_or_empty_data(self):
        """Check whether UUID cannot be obtained when identity data is None or empty"""

        with self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.generate_uuid('scm', email=None, name='', username=None)

        with self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.generate_uuid('scm', email='', name='', username='')


class TestAddIdentity(TestCase):
    """Unit tests for add_identity"""

    def test_add_new_identity(self):
        """Check if everything goes OK when adding a new identity"""

        identity = api.add_identity('scm',
                                    name='John Smith',
                                    email='jsmith@example.com',
                                    username='jsmith')
        self.assertEqual(identity.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, 'jsmith@example.com')
        self.assertEqual(identity.username, 'jsmith')
        self.assertEqual(identity.source, 'scm')

        uidentity = UniqueIdentity.objects.get(uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uidentity.uuid, identity.id)

        identities = Identity.objects.filter(id=identity.id)
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1, identity)

    def test_add_new_identities_to_uuid(self):
        """Check if everything goes OK when adding new identities to an existing one"""

        # Insert identities that will create the unique identities
        jsmith = api.add_identity('scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')
        jdoe = api.add_identity('scm',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe')

        # Create new identities and assign them to John Smith id
        identity1 = api.add_identity('mls',
                                     name='John Smith',
                                     email='jsmith@example.com',
                                     username='jsmith',
                                     uuid=jsmith.id)

        identity2 = api.add_identity('mls',
                                     name='John Smith',
                                     username='jsmith',
                                     uuid=jsmith.id)

        # Create a new identity for John Doe
        identity3 = api.add_identity('mls',
                                     email='jdoe@example.com',
                                     uuid=jdoe.id)

        # Check identities
        uidentities = UniqueIdentity.objects.all()
        self.assertEqual(len(uidentities), 2)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 5)

        # Check John Smith
        uidentity = UniqueIdentity.objects.get(uuid=jsmith.id)
        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1.id, identity1.id)
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.source, 'mls')

        id2 = identities[1]
        self.assertEqual(id2.id, identity2.id)
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, None)
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.source, 'mls')

        id3 = identities[2]
        self.assertEqual(id3.id, jsmith.id)
        self.assertEqual(id3.name, 'John Smith')
        self.assertEqual(id3.email, 'jsmith@example.com')
        self.assertEqual(id3.username, 'jsmith')
        self.assertEqual(id3.source, 'scm')

        # Next, John Doe
        uidentity = UniqueIdentity.objects.get(uuid=jdoe.id)
        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1.id, identity3.id)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jdoe@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'mls')

        id2 = identities[1]
        self.assertEqual(id2.id, jdoe.id)
        self.assertEqual(id2.name, 'John Doe')
        self.assertEqual(id2.email, 'jdoe@example.com')
        self.assertEqual(id2.username, 'jdoe')
        self.assertEqual(id2.source, 'scm')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        # First, insert the identity that will create the unique identity
        before_dt = datetime_utcnow()
        jsmith = api.add_identity('scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')
        after_dt = datetime_utcnow()

        # Check date on the unique identity
        uidentity = UniqueIdentity.objects.get(uuid=jsmith.id)
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        # Check date on the identity
        identity = uidentity.identities.all()[0]
        self.assertLessEqual(before_dt, identity.last_modified)
        self.assertGreaterEqual(after_dt, identity.last_modified)

        # Check if a new identity added to the existing unique identity
        # updates both modification dates
        before_new_dt = datetime_utcnow()
        api.add_identity('scm',
                         name=None,
                         email='jsmith@example.com',
                         username=None,
                         uuid=jsmith.id)
        after_new_dt = datetime_utcnow()

        uidentity = UniqueIdentity.objects.get(uuid=jsmith.id)

        # Check date on the unique identity; it was updated
        self.assertLessEqual(before_new_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_new_dt, uidentity.last_modified)

        # Check date of the new identity
        identities = uidentity.identities.all()
        self.assertLessEqual(before_dt, identities[0].last_modified)
        self.assertLessEqual(after_dt, identities[0].last_modified)
        self.assertLessEqual(before_new_dt, identities[0].last_modified)
        self.assertGreaterEqual(after_new_dt, identities[0].last_modified)

        # Check date of the oldest identity; it wasn't modified
        self.assertLessEqual(before_dt, identities[1].last_modified)
        self.assertGreaterEqual(after_dt, identities[1].last_modified)
        self.assertGreaterEqual(before_new_dt, identities[1].last_modified)
        self.assertGreaterEqual(after_new_dt, identities[1].last_modified)

    def test_similar_identities(self):
        """Check if it works when adding similar identities"""

        api.add_identity('scm', email='jsmith@example.com')

        # Although, this identities belongs to the same unique identity,
        # the api will create different unique identities for each one of
        # them
        uid1 = api.add_identity('scm',
                                name='John Smith',
                                email='jsmith@example.com')
        uid2 = api.add_identity('scm',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith')
        uid3 = api.add_identity('mls',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith')
        uid4 = api.add_identity('mls', name='John Smith')
        uid5 = api.add_identity('scm', name='John Smith')

        self.assertEqual(uid1.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(uid2.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uid3.id, '539acca35c2e8502951a97d2d5af8b0857440b50')
        self.assertEqual(uid4.id, 'e7efdaf17ad2cbc0e239b9afd29f6fe054b3b0fe')
        self.assertEqual(uid5.id, 'c7acd177d107a0aefa6718e2ff0dec6ceba71660')

    def test_duplicate_identities_with_truncated_values(self):
        """Check if the same identity with truncated values is not inserted twice"""

        # Due database limitations, email will be truncated
        source = 'scm'
        email = 'averylongemailaddressthatexceedsthemaximumlengthsoitwillbetruncated' * 2
        name = 'John Smith'
        username = 'jsmith'

        api.add_identity(source,
                         name=name,
                         email=email,
                         username=username)

        with self.assertRaises(AlreadyExistsError):
            api.add_identity(source,
                             name=name,
                             email=email,
                             username=username)

    def test_non_existing_uuid(self):
        """Check whether it fails adding identities to one uuid that does not exist"""

        # Add a pair of identities first
        api.add_identity('scm', email='jsmith@example.com')
        api.add_identity('scm', email='jdoe@example.com')

        with self.assertRaises(NotFoundError):
            api.add_identity('mls',
                             name=None,
                             email='jsmith@example.com',
                             username=None,
                             uuid='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

    def test_existing_identity(self):
        """Check if it fails adding an identity that already exists"""

        # Add a pair of identities first
        api.add_identity('scm', email='jsmith@example.com')
        api.add_identity('scm', email='jdoe@example.com')

        # Insert the first identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', email='jsmith@example.com')

        self.assertEqual(context.exception.eid,
                         '334da68fcd3da4e799791f73dfada2afb22648c6')

        # Insert the same identity with upper case letters.
        # It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', email='JSMITH@example.com')

        self.assertEqual(context.exception.eid,
                         '334da68fcd3da4e799791f73dfada2afb22648c6')

        # "None" tuples also raise an exception
        api.add_identity('scm', name=None, email="None", username=None)

        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', name="None", email=None, username=None)

        self.assertEqual(context.exception.eid,
                         'f0999c4eed908d33365fa3435d9686d3add2412d')

    def test_unaccent_identities(self):
        """Check if it fails adding an identity that already exists with accent values"""

        # Add a pair of identities first
        api.add_identity('scm', name='John Smith')
        api.add_identity('scm', name='Jöhn Doe')

        # Insert an accent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', name='Jöhn Smith')

        self.assertEqual(context.exception.eid,
                         'c7acd177d107a0aefa6718e2ff0dec6ceba71660')

        # Insert an accent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', name='John Döe')

        # Insert an unaccent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', name='John Doe')

        self.assertEqual(context.exception.eid,
                         'a16659ea83d28c839ffae76ceebb3ca9fb8e8894')

    def test_utf8_4bytes_identities(self):
        """Check if it inserts identities with 4bytes UTF-8 characters"""

        # Emojis are 4bytes characters
        identity = api.add_identity('scm',
                                    name='😂',
                                    email='😂',
                                    username='😂')

        uidentity = UniqueIdentity.objects.get(uuid='843fcc3383ddfd6179bef87996fa761d88a43915')
        self.assertEqual(uidentity.uuid, identity.id)

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.id, identity.id)
        self.assertEqual(id1.id, '843fcc3383ddfd6179bef87996fa761d88a43915')
        self.assertEqual(id1.name, '😂')
        self.assertEqual(id1.email, '😂')
        self.assertEqual(id1.username, '😂')
        self.assertEqual(id1.source, 'scm')

    def test_charset(self):
        """Check if it adds two identities with different encoding"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        uidentity1 = api.add_identity('scm',
                                      name='John Smıth',
                                      email='jsmith@example.com',
                                      username='jsmith')
        uidentity2 = api.add_identity('scm',
                                      name='John Smith',
                                      email='jsmith@example.com',
                                      username='jsmith')

        self.assertEqual(uidentity1.id, 'cf79edf008b7b2960a0be3972b256c65af449dc1')
        self.assertEqual(uidentity2.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

    def test_none_source(self):
        """Check whether new identities cannot be added when giving a None source"""

        with self.assertRaisesRegex(InvalidValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.add_identity(None)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        with self.assertRaisesRegex(InvalidValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.add_identity('')

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        with self.assertRaisesRegex(InvalidValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.add_identity('scm', name='', email=None, username=None)

        with self.assertRaisesRegex(InvalidValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.add_identity('scm', name='', email='', username='')
