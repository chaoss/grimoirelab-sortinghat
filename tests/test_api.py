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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import datetime
import json

from dateutil.tz import UTC

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow, datetime_to_utc

from sortinghat.core import api
from sortinghat.core.errors import (AlreadyExistsError,
                                    NotFoundError,
                                    InvalidValueError)
from sortinghat.core.models import (Country,
                                    UniqueIdentity,
                                    Identity,
                                    Enrollment,
                                    Organization,
                                    Domain,
                                    Transaction,
                                    Operation)

NOT_FOUND_ERROR = "{entity} not found in the registry"
ALREADY_EXISTS_ERROR = "{entity} already exists in the registry"
SOURCE_NONE_OR_EMPTY_ERROR = "'source' cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be empty"
UUID_NONE_OR_EMPTY_ERROR = "'uuid' cannot be"
FROM_ID_NONE_OR_EMPTY_ERROR = "'from_id' cannot be"
FROM_UUID_NONE_OR_EMPTY_ERROR = "'from_uuid' cannot be"
FROM_UUIDS_NONE_OR_EMPTY_ERROR = "'from_uuids' cannot be"
TO_UUID_NONE_OR_EMPTY_ERROR = "'to_uuid' cannot be"
FROM_UUID_TO_UUID_EQUAL_ERROR = "'from_uuid' and 'to_uuid' cannot be"
IS_BOT_VALUE_ERROR = "'is_bot' must have a boolean value"
COUNTRY_CODE_ERROR = r"'country_code' \({code}\) does not match with a valid code"
GENDER_ACC_INVALID_ERROR = "'gender_acc' can only be set when 'gender' is given"
GENDER_ACC_INVALID_TYPE_ERROR = "'gender_acc' must have an integer value"
GENDER_ACC_INVALID_RANGE_ERROR = r"'gender_acc' \({acc}\) is not in range \(1,100\)"
PERIOD_INVALID_ERROR = "'start' date {start} cannot be greater than {end}"
PERIOD_OUT_OF_BOUNDS_ERROR = "'{type}' date {date} is out of bounds"
WITHDRAW_PERIOD_INVALID_ERROR = "'from_date' date {from_date} cannot be greater than {to_date}"
ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR = "'name' cannot be"
ORGANIZATION_NOT_FOUND_ERROR = "{name} not found in the registry"
ORGANIZATION_ALREADY_EXISTS_ERROR = "Organization '{name}' already exists in the registry"
ORGANIZATION_VALUE_ERROR = "field value must be a string; int given"
DOMAIN_NAME_NONE_OR_EMPTY_ERROR = "'domain_name' cannot be"
DOMAIN_NOT_FOUND_ERROR = "{domain_name} not found in the registry"
DOMAIN_ALREADY_EXISTS_ERROR = "'{domain_name}' already exists in the registry"
DOMAIN_VALUE_ERROR = "field value must be a string; int given"
DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR = "'org_name' cannot be"


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

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(AlreadyExistsError):
            api.add_identity(source,
                             name=name,
                             email=email,
                             username=username)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check whether it fails adding identities to one uuid that does not exist"""

        # Add a pair of identities first
        api.add_identity('scm', email='jsmith@example.com')
        api.add_identity('scm', email='jdoe@example.com')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.add_identity('mls',
                             name=None,
                             email='jsmith@example.com',
                             username=None,
                             uuid='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

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

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity('scm', name="None", email=None, username=None)

        self.assertEqual(context.exception.eid,
                         'f0999c4eed908d33365fa3435d9686d3add2412d')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_unaccent_identities(self):
        """Check if it fails adding an identity that already exists with accent values"""

        # Add a pair of identities first
        api.add_identity('scm', name='John Smith')
        api.add_identity('scm', name='Jöhn Doe')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

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

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

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

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        with self.assertRaisesRegex(InvalidValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.add_identity('')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        with self.assertRaisesRegex(InvalidValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.add_identity('scm', name='', email=None, username=None)

        with self.assertRaisesRegex(InvalidValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.add_identity('scm', name='', email='', username='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding a new identity"""

        timestamp = datetime_utcnow()

        api.add_identity('scm',
                         name='John Smith',
                         email='jsmith@example.com',
                         username='jsmith')

        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_identity')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when adding a new identity"""

        timestamp = datetime_utcnow()

        identity = api.add_identity('scm',
                                    name='John Smith',
                                    email='jsmith@example.com',
                                    username='jsmith')

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 2)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'unique_identity')
        self.assertEqual(op1.target, identity.uidentity.uuid)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['uuid'], identity.uidentity.uuid)

        op2 = operations[1]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op2.entity_type, 'identity')
        self.assertEqual(op2.target, identity.id)
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 6)
        self.assertEqual(op2_args['uidentity'], identity.uidentity.uuid)
        self.assertEqual(op2_args['identity_id'], identity.id)
        self.assertEqual(op2_args['source'], identity.source)
        self.assertEqual(op2_args['name'], identity.name)
        self.assertEqual(op2_args['email'], identity.email)
        self.assertEqual(op2_args['username'], identity.username)


class TestDeleteIdentity(TestCase):
    """Unit tests for delete_identity"""

    def setUp(self):
        """Load initial dataset"""

        # Organizations
        example_org = api.add_organization('Example')
        bitergia_org = api.add_organization('Bitergia')
        libresoft_org = api.add_organization('LibreSoft')

        # Identities
        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_identity('scm',
                         name='John Smith',
                         email='jsmith@example',
                         uuid=jsmith.id)
        Enrollment.objects.create(uidentity=jsmith.uidentity,
                                  organization=example_org)
        Enrollment.objects.create(uidentity=jsmith.uidentity,
                                  organization=bitergia_org)

        jdoe = api.add_identity('scm', email='jdoe@example')
        Enrollment.objects.create(uidentity=jdoe.uidentity,
                                  organization=example_org)

        jrae = api.add_identity('scm',
                                name='Jane Rae',
                                email='jrae@example')
        Enrollment.objects.create(uidentity=jrae.uidentity,
                                  organization=libresoft_org)

    def test_delete_identity(self):
        """Check whether it deletes an identity"""

        # Check initial status
        uidentities = UniqueIdentity.objects.all()
        self.assertEqual(len(uidentities), 3)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 4)

        # Delete an identity (John Smith - jsmith@example.com)
        uidentity = api.delete_identity('1387b129ab751a3657312c09759caa41dfd8d07d')

        # Check result
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.id, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, 'jsmith@example')
        self.assertEqual(identity.username, None)

        # Check remaining identities
        uidentities = UniqueIdentity.objects.all()
        self.assertEqual(len(uidentities), 3)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 3)

        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(id='1387b129ab751a3657312c09759caa41dfd8d07d')

    def test_delete_unique_identity(self):
        """Check whether it deletes a unique identity when its identifier is given"""

        # Check initial status
        uidentities = UniqueIdentity.objects.all()
        self.assertEqual(len(uidentities), 3)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 4)

        # Delete an unique identity (John Smith)
        uidentity = api.delete_identity('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # The unique identity was removed so the result is None
        self.assertEqual(uidentity, None)

        # Check remaining identities
        uidentities = UniqueIdentity.objects.all()
        self.assertEqual(len(uidentities), 2)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 2)

        # Neither the unique identity nor its identities exist
        with self.assertRaises(ObjectDoesNotExist):
            UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(id='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(id='1387b129ab751a3657312c09759caa41dfd8d07d')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        # Delete an identity (John Smith - jsmith@example.com)
        before_dt = datetime_utcnow()
        uidentity = api.delete_identity('1387b129ab751a3657312c09759caa41dfd8d07d')
        after_dt = datetime_utcnow()

        # Check date on the unique identity
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        # Other identities were not updated
        identity = uidentity.identities.all()[0]
        self.assertGreaterEqual(before_dt, identity.last_modified)

    def test_non_existing_uuid(self):
        """Check if it fails removing a identities that does not exists"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.delete_identity('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        # It should raise an error when the registry is empty
        UniqueIdentity.objects.all().delete()
        self.assertEqual(len(UniqueIdentity.objects.all()), 0)

        with self.assertRaises(NotFoundError):
            api.delete_identity('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_uuid(self):
        """Check whether identities cannot be removed when giving a None UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.delete_identity(None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_uuid(self):
        """Check whether identities cannot be removed when giving an empty UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.delete_identity('')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting an identity"""

        timestamp = datetime_utcnow()

        api.delete_identity('1387b129ab751a3657312c09759caa41dfd8d07d')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_identity')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when deleting an identity"""

        timestamp = datetime_utcnow()

        api.delete_identity('1387b129ab751a3657312c09759caa41dfd8d07d')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '1387b129ab751a3657312c09759caa41dfd8d07d')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['identity'], '1387b129ab751a3657312c09759caa41dfd8d07d')


class TestUpdateProfile(TestCase):
    """Unit tests for update_profile"""

    def setUp(self):
        """Load initial dataset"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        api.add_identity('scm', email='jsmith@example')

    def test_update_empty_profile(self):
        """Check if it updates an empty profile"""

        uidentity = api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                       name='Smith, J.', email='jsmith@example.net',
                                       is_bot=True, country_code='US',
                                       gender='male', gender_acc=98)

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        profile = uidentity.profile
        self.assertEqual(profile.name, 'Smith, J.')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertIsInstance(profile.country, Country)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 98)

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(profile, uidentity_db.profile)

    def test_update_profile(self):
        """Check if it updates a profile"""

        api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='Smith, J.', email='jsmith@example.net',
                           is_bot=True, country_code='US',
                           gender='male', gender_acc=98)

        uidentity = api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                       name='', email='jsmith@example.net',
                                       is_bot=False, country_code='US',
                                       gender='male', gender_acc=89)

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)

        profile = uidentity.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, False)
        self.assertIsInstance(profile.country, Country)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 89)

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(profile, uidentity_db.profile)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        uidentity = api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                       name='John Smith',
                                       email='jsmith@example.net')
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_non_existing_uuid(self):
        """Check if it fails updating a unique identity that does not exist"""

        with self.assertRaises(NotFoundError):
            api.update_profile('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                               name='', email='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_name_email_empty(self):
        """Check if name and email are set to None when an empty string is given"""

        uidentity = api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                       name='', email='')
        profile = uidentity.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)

    def test_is_bot_invalid_type(self):
        """Check type values of is_bot parameter"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        with self.assertRaisesRegex(InvalidValueError, IS_BOT_VALUE_ERROR):
            api.update_profile(uuid, is_bot=1)

        with self.assertRaisesRegex(InvalidValueError, IS_BOT_VALUE_ERROR):
            api.update_profile(uuid, is_bot='True')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_country_code_not_valid(self):
        """Check if it fails when the given country is not valid"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        msg = COUNTRY_CODE_ERROR.format(code='JKL')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(uuid, country_code='JKL')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_gender_not_given(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        with self.assertRaisesRegex(InvalidValueError, GENDER_ACC_INVALID_ERROR):
            api.update_profile(uuid, gender_acc=100)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_gender_acc_invalid_type(self):
        """Check type values of gender_acc parameter"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        with self.assertRaisesRegex(InvalidValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            api.update_profile(uuid, gender='male', gender_acc=10.0)

        with self.assertRaisesRegex(InvalidValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            api.update_profile(uuid, gender='male', gender_acc='100')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_gender_acc_invalid_range(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='-1')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(uuid, gender='male', gender_acc=-1)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='0')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(uuid, gender='male', gender_acc=0)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='101')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(uuid, gender='male', gender_acc=101)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_transaction(self):
        """Check if a transaction is created when updating a profile"""

        timestamp = datetime_utcnow()

        api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='Smith, J.', email='jsmith@example.net',
                           is_bot=True, country_code='US',
                           gender='male', gender_acc=98)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'update_profile')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when updating a profile"""

        timestamp = datetime_utcnow()

        uidentity = api.update_profile('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                       name='Smith, J.', email='jsmith@example.net',
                                       is_bot=True, country_code='US',
                                       gender='male', gender_acc=98)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'profile')
        self.assertEqual(op1.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 7)
        self.assertEqual(op1_args['uidentity'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op1_args['name'], 'Smith, J.')
        self.assertEqual(op1_args['email'], 'jsmith@example.net')
        self.assertEqual(op1_args['is_bot'], True)
        self.assertEqual(op1_args['country_code'], 'US')
        self.assertEqual(op1_args['gender'], 'male')
        self.assertEqual(op1_args['gender_acc'], 98)


class TestMoveIdentity(TestCase):
    """Unit tests for move_identity"""

    def setUp(self):
        """Load initial dataset"""

        jsmith = api.add_identity('scm', email='jsmith@example.com')
        api.add_identity('scm',
                         name='John Smith',
                         email='jsmith@example.com',
                         uuid=jsmith.id)
        api.add_identity('scm', email='jdoe@example.com')

    def test_move_identity(self):
        """Test whether an identity is moved to a unique identity"""

        from_id = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        # Tests
        uidentity = api.move_identity(from_id, to_uuid)

        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity.id, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identity = identities[1]
        self.assertEqual(identity.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        uidentity_db = UniqueIdentity.objects.get(uuid='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        from_id = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        # Tests
        before_dt = datetime_utcnow()
        uidentity = api.move_identity(from_id, to_uuid)
        after_dt = datetime_utcnow()

        # Check date on the unique identity
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_equal_related_unique_identity(self):
        """Check if identities are not moved when 'to_uuid' is the unique identity related to 'from_id'"""

        from_id = '03877f31261a6d1a1b3971d240e628259364b8ac'

        # Move the identity to the same unique identity
        api.move_identity(from_id, from_id)

        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '334da68fcd3da4e799791f73dfada2afb22648c6')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        uidentity_db = UniqueIdentity.objects.get(uuid='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '03877f31261a6d1a1b3971d240e628259364b8ac')

    def test_create_new_unique_identity(self):
        """Check if a new unique identity is created when 'from_id' has the same value of 'to_uuid'"""

        new_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'

        # This will create a new unique identity,
        # moving the identity to this new unique identity
        uidentity = api.move_identity(new_uuid, new_uuid)

        self.assertEqual(uidentity.uuid, new_uuid)

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.id, new_uuid)
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, 'jsmith@example.com')

        # Check database objects
        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        uidentity_db = UniqueIdentity.objects.get(uuid='880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        uidentity_db = UniqueIdentity.objects.get(uuid='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

    def test_not_found_from_identity(self):
        """Test whether it fails when 'from_id' identity is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='FFFFFFFFFFF')

        # Check 'from_id' parameter
        with self.assertRaisesRegex(NotFoundError, msg):
            api.move_identity('FFFFFFFFFFF',
                              '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_not_found_to_identity(self):
        """Test whether it fails when 'to_uuid' unique identity is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='FFFFFFFFFFF')

        # Check 'to_uuid' parameter
        with self.assertRaisesRegex(NotFoundError, msg):
            api.move_identity('03877f31261a6d1a1b3971d240e628259364b8ac',
                              'FFFFFFFFFFF')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_from_id(self):
        """Check whether identities cannot be moved when giving a None id"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_ID_NONE_OR_EMPTY_ERROR):
            api.move_identity(None, '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_from_id(self):
        """Check whether identities cannot be moved when giving an empty id"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_ID_NONE_OR_EMPTY_ERROR):
            api.move_identity('', '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_to_uuid(self):
        """Check whether identities cannot be moved when giving a None UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, TO_UUID_NONE_OR_EMPTY_ERROR):
            api.move_identity('03877f31261a6d1a1b3971d240e628259364b8ac', None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_to_uuid(self):
        """Check whether identities cannot be moved when giving an empty UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, TO_UUID_NONE_OR_EMPTY_ERROR):
            api.move_identity('03877f31261a6d1a1b3971d240e628259364b8ac', '')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when moving an identity"""

        timestamp = datetime_utcnow()

        from_id = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        api.move_identity(from_id, to_uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'move_identity')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when moving an identity"""

        timestamp = datetime_utcnow()

        from_id = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        api.move_identity(from_id, to_uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertEqual(op1.target, from_id)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['identity'], from_id)
        self.assertEqual(op1_args['uidentity'], to_uuid)


class TestAddOrganization(TestCase):
    """Unit tests for add_organization"""

    def test_add_new_organization(self):
        """Check if everything goes OK when adding a new organization"""

        organization = api.add_organization(name='Example')

        # Tests
        self.assertIsInstance(organization, Organization)
        self.assertEqual(organization.name, 'Example')

        organizations_db = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations_db), 1)

        org1 = organizations_db[0]
        self.assertEqual(organization, org1)

    def test_add_duplicate_organization(self):
        """Check if it fails when adding a duplicate organization"""

        org = api.add_organization(name='Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, ORGANIZATION_ALREADY_EXISTS_ERROR.format(name=org.name)):
            org = api.add_organization(name=org.name)

        organizations = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations), 1)

        organizations = Organization.objects.all()
        self.assertEqual(len(organizations), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces only"""

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(name='   ')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(name='\t')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(name=' \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.add_organization(name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding an organization"""

        timestamp = datetime_utcnow()

        api.add_organization(name='Example')

        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_organization')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when adding an organization"""

        timestamp = datetime_utcnow()

        api.add_organization(name='Example')

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'organization')
        self.assertEqual(op1.target, 'Example')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['name'], 'Example')


class TestAddDomain(TestCase):
    """Unit tests for add_domain"""

    def setUp(self):
        """Load initial dataset"""

        api.add_organization(name='Example')
        api.add_organization(name='Bitergia')

    def test_add_new_domain(self):
        """Check if everything goes OK when adding a new domain"""

        domain = api.add_domain(organization='Example',
                                domain_name='example.com',
                                is_top_domain=True)

        # Tests
        self.assertIsInstance(domain, Domain)
        self.assertEqual(domain.organization.name, 'Example')
        self.assertEqual(domain.domain, 'example.com')
        self.assertEqual(domain.is_top_domain, True)

        domains_db = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains_db), 1)

        dom1 = domains_db[0]
        self.assertEqual(domain, dom1)

    def test_top_domain_default(self):
        """Check if the domain is a top domain by default"""

        domain = api.add_domain(organization='Example',
                                domain_name='example.com')

        # Tests
        self.assertIsInstance(domain, Domain)
        self.assertEqual(domain.organization.name, 'Example')
        self.assertEqual(domain.domain, 'example.com')
        self.assertEqual(domain.is_top_domain, True)

        domains_db = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains_db), 1)

        dom1 = domains_db[0]
        self.assertEqual(domain, dom1)

    def test_add_multiple_domains(self):
        """Check if everything goes OK when adding a new domain"""

        domain1 = api.add_domain(organization='Example',
                                 domain_name='example.com',
                                 is_top_domain=True)

        domain2 = api.add_domain(organization='Example',
                                 domain_name='example.net',
                                 is_top_domain=False)

        # Tests
        self.assertEqual(domain1.organization.name, 'Example')
        self.assertEqual(domain1.domain, 'example.com')
        self.assertEqual(domain1.is_top_domain, True)

        self.assertEqual(domain2.organization.name, 'Example')
        self.assertEqual(domain2.domain, 'example.net')
        self.assertEqual(domain2.is_top_domain, False)

        domains_db = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains_db), 1)

        dom1 = domains_db[0]
        self.assertEqual(domain1, dom1)

        domains_db = Domain.objects.filter(domain='example.net')
        self.assertEqual(len(domains_db), 1)

        dom2 = domains_db[0]
        self.assertEqual(domain2, dom2)

    def test_add_duplicate_domain(self):
        """Check if it fails when adding a duplicate domain"""

        domain = api.add_domain(organization='Example',
                                domain_name='example.com',
                                is_top_domain=True)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, DOMAIN_ALREADY_EXISTS_ERROR.format(domain_name='example.com')):
            api.add_domain(organization='Example',
                           domain_name='example.com')

        domains = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains), 1)

        dom1 = domains[0]
        self.assertEqual(dom1, domain)

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_add_domain_different_org(self):
        """Check if it fails when adding the same domain to a different organization"""

        domain = api.add_domain(organization='Example',
                                domain_name='example.com',
                                is_top_domain=True)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, DOMAIN_ALREADY_EXISTS_ERROR.format(domain_name='example.com')):
            api.add_domain(organization='Bitergia',
                           domain_name='example.com')

        domains = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains), 1)

        domains = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains), 1)

        dom1 = domains[0]
        self.assertEqual(dom1.organization.name, 'Example')
        self.assertEqual(dom1.organization.name, domain.organization.name)

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_not_found(self):
        """Check if it fails when the organization is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR.format(name='Botergia')):
            api.add_domain(organization='Botergia',
                           domain_name='bitergia.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_none(self):
        """Check if it fails when domain name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization='Example',
                           domain_name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_empty(self):
        """Check if it fails when domain name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization='Example',
                           domain_name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_whitespaces(self):
        """Check if it fails when domain name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization='Example',
                           domain_name='    ')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization='Example',
                           domain_name='\t')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization='Example',
                           domain_name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_int(self):
        """Check if it fails when domain name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, DOMAIN_VALUE_ERROR):
            api.add_domain(organization='Example',
                           domain_name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization=None,
                           domain_name='example.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization='',
                           domain_name='example.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization=None,
                           domain_name='    ')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization=None,
                           domain_name='\t')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(organization=None,
                           domain_name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.add_domain(organization=12345,
                           domain_name='example.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding a domain"""

        timestamp = datetime_utcnow()

        api.add_domain(organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_domain')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when adding a domain"""

        timestamp = datetime_utcnow()

        api.add_domain(organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'domain')
        self.assertEqual(op1.target, 'Example')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 3)
        self.assertEqual(op1_args['organization'], 'Example')
        self.assertEqual(op1_args['domain_name'], 'example.com')
        self.assertEqual(op1_args['is_top_domain'], True)


class TestDeleteOrganization(TestCase):
    """Unit tests for delete_organization"""

    def setUp(self):
        """Load initial dataset"""

        api.add_organization(name='Example')
        api.add_organization(name='Bitergia')
        api.add_organization(name='Libresoft')

        jsmith = api.add_identity('scm', email='jsmith@example.com')
        uidentity = api.enroll(jsmith.id, 'Example',
                               from_date=datetime.datetime(1999, 1, 1),
                               to_date=datetime.datetime(2000, 1, 1))

    def test_delete_organization(self):
        """Check if everything goes OK when deleting an organization"""

        api.delete_organization(name='Example')

        organizations = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations), 0)

        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        enrollments = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments), 0)

        organizations = Organization.objects.all()
        self.assertEqual(len(organizations), 2)

        org1 = organizations[0]
        self.assertEqual(org1.name, 'Bitergia')

        org2 = organizations[1]
        self.assertEqual(org2.name, 'Libresoft')

    def test_delete_non_existing_organization(self):
        """Check if it fails when deleting a non existing organization"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR.format(name='Ghost')):
            api.delete_organization('Ghost')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(name='   ')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(name='\t')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(name=' \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.delete_organization(name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting an organization"""

        timestamp = datetime_utcnow()

        api.delete_organization(name='Example')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_organization')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when deleting an organization"""

        timestamp = datetime_utcnow()

        api.delete_organization(name='Example')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'organization')
        self.assertEqual(op1.target, 'Example')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['organization'], 'Example')


class TestDeleteDomain(TestCase):
    """Unit tests for delete_domain"""

    def setUp(self):
        """Load initial dataset"""

        api.add_organization(name='Example')
        api.add_domain(organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)
        api.add_domain(organization='Example',
                       domain_name='example.net',
                       is_top_domain=False)

        api.add_organization(name='Bitergia')
        api.add_domain(organization='Bitergia',
                       domain_name='bitergia.com',
                       is_top_domain=True)

    def test_delete_domain(self):
        """Check if everything goes OK when deleting a domain"""

        domain = api.delete_domain('example.com')

        # Tests
        self.assertIsInstance(domain, Domain)
        self.assertEqual(domain.organization.name, 'Example')
        self.assertEqual(domain.domain, 'example.com')
        self.assertEqual(domain.is_top_domain, True)

        domains = Domain.objects.filter(domain='example.com')
        self.assertEqual(len(domains), 0)

        # Check if the rest of domains were not removed
        domains = Domain.objects.all()
        self.assertEqual(len(domains), 2)

        dom1 = domains[0]
        self.assertEqual(dom1.organization.name, 'Bitergia')
        self.assertEqual(dom1.domain, 'bitergia.com')
        self.assertEqual(dom1.is_top_domain, True)

        dom2 = domains[1]
        self.assertEqual(dom2.organization.name, 'Example')
        self.assertEqual(dom2.domain, 'example.net')
        self.assertEqual(dom2.is_top_domain, False)

    def test_domain_not_found(self):
        """Check if it fails when domain is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(NotFoundError, DOMAIN_NOT_FOUND_ERROR.format(domain_name='botergia.com')):
            api.delete_domain('botergia.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_not_found(self):
        """Check if it fails when the domain's organization is not found"""

        api.delete_organization('Bitergia')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        # Tests
        domains = Domain.objects.filter(domain='bitergia.com')
        self.assertEqual(len(domains), 0)

        with self.assertRaisesRegex(NotFoundError, DOMAIN_NOT_FOUND_ERROR.format(domain_name='bitergia.com')):
            api.delete_domain('bitergia.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_none(self):
        """Check if it fails when domain name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(domain_name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_empty(self):
        """Check if it fails when domain name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(domain_name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_whitespaces(self):
        """Check if it fails when domain name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(domain_name='    ')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(domain_name='\t')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(domain_name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_int(self):
        """Check if it fails when domain name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, DOMAIN_VALUE_ERROR):
            api.delete_domain(domain_name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting a domain"""

        timestamp = datetime_utcnow()

        api.delete_domain('example.com')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_domain')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()

        domain = api.delete_domain('example.com')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'domain')
        self.assertEqual(op1.target, 'example.com')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['domain'], 'example.com')


class TestEnroll(TestCase):
    """Unit tests for enroll"""

    def test_enroll(self):
        """Check whether it adds an enrollments to a unique identity and an organization"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        uidentity = api.enroll(jsmith.id, 'Example',
                               from_date=datetime.datetime(1999, 1, 1),
                               to_date=datetime.datetime(2000, 1, 1))

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid=jsmith.id)
        enrollments_db = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

    def test_enroll_default_ranges(self):
        """Check if it enrolls a unique identity using default ranges when they are not given"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        uidentity = api.enroll(jsmith.id, 'Example')

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid=jsmith.id)
        enrollments_db = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_enroll_multiple(self):
        """Check if it enrolls different times a unique identity to an organization"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2005, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))

        # Tests
        uidentity_db = UniqueIdentity.objects.get(uuid=jsmith.id)

        enrollments = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2005, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2006, 1, 1, tzinfo=UTC))

        enrollment = enrollments[2]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_upper_bound(self):
        """Check if enrollments are merged for overlapped ranges"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        # Merge enrollments expanding ending date
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2005, 1, 1),
                   to_date=datetime.datetime(2007, 6, 1))

        uidentity_db = UniqueIdentity.objects.get(uuid=jsmith.id)

        enrollments = uidentity_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.start, datetime.datetime(2004, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2007, 6, 1, tzinfo=UTC))

        enrollment = enrollments[2]
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_lower_bound(self):
        """Check if enrollments are merged for overlapped ranges"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        # Merge enrollments expanding starting date
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2002, 1, 1),
                   to_date=datetime.datetime(2013, 6, 1))

        uidentity_db = UniqueIdentity.objects.get(uuid=jsmith.id)

        enrollments = uidentity_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.start, datetime.datetime(2002, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_both_bounds(self):
        """Check if enrollments are merged for overlapped ranges"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        # Merge enrollments expending both bounds
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        uidentity_db = UniqueIdentity.objects.get(uuid=jsmith.id)

        enrollments = uidentity_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        before_dt = datetime_utcnow()
        uidentity = api.enroll(jsmith.id, 'Example',
                               from_date=datetime.datetime(2013, 1, 1),
                               to_date=datetime.datetime(2014, 1, 1))
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_period_invalid(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'start': r'2001-01-01 00:00:00\+00:00',
            'end': r'1999-01-01 00:00:00\+00:00'
        }
        msg = PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(jsmith.id, 'Example',
                       from_date=datetime.datetime(2001, 1, 1),
                       to_date=datetime.datetime(1999, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_period_out_of_bounds(self):
        """Check whether enrollments cannot be added giving periods out of bounds"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'type': 'start',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(jsmith.id, 'Example',
                       from_date=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(jsmith.id, 'Example',
                       to_date=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'start',
            'date': r'1898-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(jsmith.id, 'Example',
                       from_date=datetime.datetime(1898, 12, 31, 23, 59, 59, tzinfo=UTC),
                       to_date=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check if it fails adding enrollments to not existing unique identities"""

        api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='abcdefghijklmnopqrstuvwxyz')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.enroll('abcdefghijklmnopqrstuvwxyz', 'Example')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_organization(self):
        """Check if it fails adding enrollments to not existing organizations"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='Bitergia')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_already_exist_enrollment(self):
        """Test if it raises an exception when the enrollment for the given range already exists"""

        api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2010, 1, 1))

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(AlreadyExistsError):
            api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                       from_date=datetime.datetime(1999, 1, 1),
                       to_date=datetime.datetime(2010, 1, 1))

        with self.assertRaises(AlreadyExistsError):
            api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                       from_date=datetime.datetime(2005, 1, 1),
                       to_date=datetime.datetime(2009, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding an enrollment"""

        timestamp = datetime_utcnow()

        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_organization('Example')

        trx_date = datetime_utcnow()  # Ingnoring the transactions before this datetime

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'enroll')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()

        jsmith = api.add_identity('scm', email='jsmith@example')
        org = api.add_organization('Example')

        trx_date = datetime_utcnow()

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))

        transactions = Transaction.objects.filter(created_at__gte=trx_date)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'enrollment')
        self.assertEqual(op1.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 4)
        self.assertEqual(op1_args['uidentity'], jsmith.uidentity.uuid)
        self.assertEqual(op1_args['organization'], org.name)
        self.assertEqual(op1_args['start'], str(datetime_to_utc(datetime.datetime(1999, 1, 1))))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(datetime.datetime(2000, 1, 1))))


class TestWithdraw(TestCase):
    """Unit tests for withdraw"""

    def setUp(self):
        """Load initial dataset"""

        api.add_organization('Example')
        api.add_organization('Bitergia')

        api.add_identity('scm', email='jsmith@example')
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2006, 1, 1),
                   to_date=datetime.datetime(2008, 1, 1))
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2009, 1, 1),
                   to_date=datetime.datetime(2011, 1, 1))
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        api.add_identity('scm', email='jrae@example')
        api.enroll('3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

    def test_withdraw(self):
        """Check whether it withdraws a unique identity from an organization during the given period"""

        uidentity = api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                                 from_date=datetime.datetime(2007, 1, 1),
                                 to_date=datetime.datetime(2013, 1, 1))

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2007, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.organization.name, 'Bitergia')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment = enrollments[2]
        self.assertEqual(enrollment.organization.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 3)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2007, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.organization.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Other enrollments were not deleted
        uidentity_db = UniqueIdentity.objects.get(uuid='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_withdraw_default_ranges(self):
        """Check if it withdraws a unique identity using default ranges when they are not given"""

        uidentity = api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example')

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.organization.name, 'Bitergia')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        uidentity = api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example')
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_period_invalid(self):
        """Check whether enrollments cannot be withdrawn giving invalid period ranges"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'from_date': r'2001-01-01 00:00:00\+00:00',
            'to_date': r'1999-01-01 00:00:00\+00:00'
        }
        msg = WITHDRAW_PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(2001, 1, 1),
                         to_date=datetime.datetime(1999, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_period_out_of_bounds(self):
        """Check whether enrollments cannot be withdrawn giving periods out of bounds"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'type': 'from_date',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(1899, 12, 31, 23, 59, 59))

        data = {
            'type': 'to_date',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         to_date=datetime.datetime(2100, 1, 1, 0, 0, 1))

        data = {
            'type': 'from_date',
            'date': r'1898-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(1898, 12, 31, 23, 59, 59),
                         to_date=datetime.datetime(1899, 12, 31, 23, 59, 59))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check if it fails withdrawing from not existing unique identities"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='abcdefghijklmnopqrstuvwxyz')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.withdraw('abcdefghijklmnopqrstuvwxyz', 'Example')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_organization(self):
        """Check if it fails withdrawing from not existing organizations"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='LibreSoft')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'LibreSoft')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_enrollment(self):
        """Check if it fails withdrawing not existing enrollments"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(2050, 1, 1),
                         to_date=datetime.datetime(2060, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting an enrollment"""

        timestamp = datetime_utcnow()

        api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                     from_date=datetime.datetime(2007, 1, 1),
                     to_date=datetime.datetime(2013, 1, 1))

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'withdraw')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when deleting an enrollment"""

        timestamp = datetime_utcnow()

        api.withdraw('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                     from_date=datetime.datetime(2007, 1, 1),
                     to_date=datetime.datetime(2013, 1, 1))

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 5)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'enrollment')
        self.assertEqual(op1.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 4)
        self.assertEqual(op1_args['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op1_args['organization'], 'Example')
        self.assertEqual(op1_args['start'], str(datetime_to_utc(datetime.datetime(2006, 1, 1))))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(datetime.datetime(2008, 1, 1))))

        op2 = operations[1]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op2.entity_type, 'enrollment')
        self.assertEqual(op2.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 4)
        self.assertEqual(op2_args['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op2_args['organization'], 'Example')
        self.assertEqual(op2_args['start'], str(datetime_to_utc(datetime.datetime(2009, 1, 1))))
        self.assertEqual(op2_args['end'], str(datetime_to_utc(datetime.datetime(2011, 1, 1))))

        op3 = operations[2]
        self.assertIsInstance(op3, Operation)
        self.assertEqual(op3.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op3.entity_type, 'enrollment')
        self.assertEqual(op3.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op3.trx, trx)
        self.assertGreater(op3.timestamp, timestamp)

        op3_args = json.loads(op3.args)
        self.assertEqual(len(op3_args), 4)
        self.assertEqual(op3_args['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op3_args['organization'], 'Example')
        self.assertEqual(op3_args['start'], str(datetime_to_utc(datetime.datetime(2012, 1, 1))))
        self.assertEqual(op3_args['end'], str(datetime_to_utc(datetime.datetime(2014, 1, 1))))

        op4 = operations[3]
        self.assertIsInstance(op4, Operation)
        self.assertEqual(op4.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op4.entity_type, 'enrollment')
        self.assertEqual(op4.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op4.trx, trx)
        self.assertGreater(op4.timestamp, timestamp)

        op4_args = json.loads(op4.args)
        self.assertEqual(len(op4_args), 4)
        self.assertEqual(op4_args['uidentity'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op4_args['organization'], 'Example')
        self.assertEqual(op4_args['start'], str(datetime_to_utc(datetime.datetime(2006, 1, 1))))
        self.assertEqual(op4_args['end'], str(datetime_to_utc(datetime.datetime(2007, 1, 1))))

        op5 = operations[4]
        self.assertIsInstance(op5, Operation)
        self.assertEqual(op5.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op5.entity_type, 'enrollment')
        self.assertEqual(op5.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op5.trx, trx)
        self.assertGreater(op5.timestamp, timestamp)

        op5_args = json.loads(op5.args)
        self.assertEqual(len(op5_args), 4)
        self.assertEqual(op5_args['uidentity'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op5_args['organization'], 'Example')
        self.assertEqual(op5_args['start'], str(datetime_to_utc(datetime.datetime(2013, 1, 1))))
        self.assertEqual(op5_args['end'], str(datetime_to_utc(datetime.datetime(2014, 1, 1))))


class TestMergeIdentities(TestCase):
    """Unit tests for merge_identities"""

    def setUp(self):
        """Load initial dataset"""

        api.add_organization('Example')
        api.add_organization('Bitergia')

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        api.add_identity('scm', email='jsmith@example')
        api.add_identity('git', email='jsmith-git@example', uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity('scm', email='jsmith@bitergia')
        api.add_identity('phabricator', email='jsmith-phab@bitergia', uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        api.enroll('caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', 'Bitergia',
                   from_date=datetime.datetime(2017, 6, 2),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity('scm', email='jsmith-local@bitergia')
        api.enroll('a11604f983f8786913e6d1449f2eac1618b0b2ee', 'Bitergia',
                   from_date=datetime.datetime(2017, 4, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity('scm', email='jsmith-internship@example')
        api.enroll('4dd0fdcd06a6be6f0b7893bf1afcef3e3191753a', 'Example',
                   from_date=datetime.datetime(2015, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity('scm', email='john.doe@bitergia')
        api.enroll('ebe8f55d8988fce02997389d530579ad939f1698', 'Bitergia',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2015, 1, 1))
        api.enroll('ebe8f55d8988fce02997389d530579ad939f1698', 'Example',
                   from_date=datetime.datetime(2015, 1, 2),
                   to_date=datetime.datetime(2016, 12, 31))
        api.enroll('ebe8f55d8988fce02997389d530579ad939f1698', 'Bitergia',
                   from_date=datetime.datetime(2017, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity('scm', email='john.doe@biterg.io')
        api.enroll('437386d9d072320387d0c802f772a5401cddc3e6', 'Bitergia')

        api.add_identity('phabricator', email='jsmith@example-phab')
        api.enroll('f29b50520d35d046db0d53b301418ad9aa16e7e3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity('scm', email='jsmith@libresoft')
        api.add_identity('phabricator', email='jsmith2@libresoft', uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.add_identity('phabricator', email='jsmith3@libresoft', uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.update_profile(uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e', name='John Smith',
                           email='jsmith@profile-email', is_bot=False, country_code='US')

    def test_merge_identities(self):
        """Check whether it merges two unique identities, merging their ids, enrollments and profiles"""

        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', gender_acc=75)

        api.update_profile(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email', is_bot=True, country_code='US')

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                         to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1.id, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        id2 = identities[1]
        self.assertEqual(id2.id, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id2.email, 'jsmith-phab@bitergia')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.id, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id3.email, 'jsmith@bitergia')
        self.assertEqual(id3.source, 'scm')

        id4 = identities[3]
        self.assertEqual(id4.id, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id4.email, 'jsmith@example')
        self.assertEqual(id4.source, 'scm')

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.organization.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_multiple_identities(self):
        """Check whether it merges more than two unique identities, merging their ids, enrollments and profiles"""

        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', gender_acc=75)

        api.update_profile(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email', is_bot=True, country_code='US')

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                                     '1c13fec7a328201fc6a230fe43eb81df0e20626e'],
                                         to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 7)

        id1 = identities[0]
        self.assertEqual(id1.id, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.id, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.id, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3.email, 'jsmith-git@example')
        self.assertEqual(id3.source, 'git')

        id4 = identities[3]
        self.assertEqual(id4.id, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4.email, 'jsmith-phab@bitergia')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.id, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5.email, 'jsmith2@libresoft')
        self.assertEqual(id5.source, 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6.id, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id6.email, 'jsmith@bitergia')
        self.assertEqual(id6.source, 'scm')

        id7 = identities[6]
        self.assertEqual(id7.id, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id7.email, 'jsmith@example')
        self.assertEqual(id7.source, 'scm')

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.organization.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_non_existing_from_uuids(self):
        """Check if it fails merging unique identities when source uuids is `None` or an empty list"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUIDS_NONE_OR_EMPTY_ERROR):
            api.merge_identities(from_uuids=[], to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_from_uuid(self):
        """Check if it fails merging unique identities when source uuid is `None` or empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUID_NONE_OR_EMPTY_ERROR):
            api.merge_identities(from_uuids=[''], to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_to_uuid(self):
        """Check if it fails merging two unique identities when destination uuid is `None` or empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, TO_UUID_NONE_OR_EMPTY_ERROR):
            api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'], to_uuid='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_from_uuid_to_uuid_equal(self):
        """Check if it fails merging two unique identities when they are equal"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUID_TO_UUID_EQUAL_ERROR):
            api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                 to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_moved_enrollments(self):
        """Check whether it merges two unique identities, merging their enrollments with multiple periods"""

        uidentity = api.merge_identities(from_uuids=['ebe8f55d8988fce02997389d530579ad939f1698'],
                                         to_uuid='437386d9d072320387d0c802f772a5401cddc3e6')

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        rol1 = enrollments[0]
        self.assertEqual(rol1.organization.name, 'Bitergia')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2015, 1, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.organization.name, 'Example')
        self.assertEqual(rol2.start, datetime.datetime(2015, 1, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2016, 12, 31, tzinfo=UTC))

        rol3 = enrollments[2]
        self.assertEqual(rol3.organization.name, 'Bitergia')
        self.assertEqual(rol3.start, datetime.datetime(2017, 1, 1, tzinfo=UTC))
        self.assertEqual(rol3.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_overlapping_enrollments(self):
        """Check whether it merges two unique identities having overlapping enrollments"""

        uidentity = api.merge_identities(from_uuids=['4dd0fdcd06a6be6f0b7893bf1afcef3e3191753a'],
                                         to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(2015, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

    def test_overlapping_enrollments_different_orgs(self):
        """Check whether it merges two unique identities having overlapping periods in different organizations"""

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                         to_uuid='a11604f983f8786913e6d1449f2eac1618b0b2ee')

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.organization.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 4, 1, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_duplicate_enrollments(self):
        """Check whether it merges two unique identities having duplicate enrollments"""

        uidentity = api.merge_identities(from_uuids=['f29b50520d35d046db0d53b301418ad9aa16e7e3'],
                                         to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertEqual(rol.organization.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()

        uidentity1 = api.add_identity('scm', email='john.doe@example')
        api.add_identity('git', email='john.doe@example', uuid='b6bee805956c03699b59e15175261f85a10d43f3')

        uidentity2 = api.add_identity('scm', email='jdoe@example')
        api.add_identity('git', email='jdoe@example', uuid='a033ed6d1498a58f7cf91bd56e3c746d7ddb9874')

        after_dt = datetime_utcnow()

        uid1 = UniqueIdentity.objects.get(uuid=uidentity1.id)
        uid2 = UniqueIdentity.objects.get(uuid=uidentity2.id)

        self.assertLessEqual(before_dt, uid1.last_modified)
        self.assertGreaterEqual(after_dt, uid1.last_modified)

        self.assertLessEqual(before_dt, uid2.last_modified)
        self.assertGreaterEqual(after_dt, uid2.last_modified)

        # Merge identities
        before_merge_dt = datetime_utcnow()
        uid = api.merge_identities(from_uuids=['b6bee805956c03699b59e15175261f85a10d43f3'],
                                   to_uuid='a033ed6d1498a58f7cf91bd56e3c746d7ddb9874')
        after_merge_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, uid.last_modified)
        self.assertLessEqual(after_dt, uid.last_modified)
        self.assertLessEqual(before_merge_dt, uid.last_modified)
        self.assertGreaterEqual(after_merge_dt, uid.last_modified)

        identities = uid.identities.all()

        # Not merged (moved) identities were not modified
        id1 = identities[0]

        self.assertLessEqual(before_dt, id1.last_modified)
        self.assertGreaterEqual(after_dt, id1.last_modified)
        self.assertGreaterEqual(before_merge_dt, id1.last_modified)
        self.assertGreaterEqual(after_merge_dt, id1.last_modified)

        id2 = identities[1]

        self.assertLessEqual(before_dt, id2.last_modified)
        self.assertGreaterEqual(after_dt, id2.last_modified)
        self.assertGreaterEqual(before_merge_dt, id2.last_modified)
        self.assertGreaterEqual(after_merge_dt, id2.last_modified)

        # Merged (moved) identities were updated
        id3 = identities[2]

        self.assertLessEqual(before_dt, id3.last_modified)
        self.assertLessEqual(after_dt, id3.last_modified)
        self.assertLessEqual(before_merge_dt, id3.last_modified)
        self.assertGreaterEqual(after_merge_dt, id3.last_modified)

        id4 = identities[3]

        self.assertLessEqual(before_dt, id4.last_modified)
        self.assertLessEqual(after_dt, id4.last_modified)
        self.assertLessEqual(before_merge_dt, id4.last_modified)
        self.assertGreaterEqual(after_merge_dt, id4.last_modified)

    def test_merge_identities_and_swap_profile(self):
        """Check whether it merges two unique identities, merging their profiles"""

        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', gender_acc=75)
        api.update_profile(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email', is_bot=True, country_code='US')

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                         to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')

        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

    def test_empty_source_profile(self):
        """Check whether it merges two unique identities when the profile from the source identity is empty"""

        api.update_profile(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email')

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                         to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, None)
        self.assertEqual(profile.country_id, None)
        self.assertEqual(profile.is_bot, False)

    def test_empty_destination_profile(self):
        """Check whether it merges two unique identities when the profile from the destination identity is empty"""

        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', country_code='US')

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                         to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity.profile
        self.assertEqual(profile.name, 'J. Smith')
        self.assertEqual(profile.email, 'jsmith@example')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.is_bot, False)

    def test_empty_profiles(self):
        """Check whether it merges two unique identities when both of their profiles are empty"""

        uidentity = api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                                         to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)
        self.assertEqual(profile.gender, None)
        self.assertEqual(profile.country_id, None)
        self.assertEqual(profile.is_bot, False)

    def test_transaction(self):
        """Check if a transaction is created when merging identities"""

        timestamp = datetime_utcnow()

        api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                             to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'merge_identities')
        self.assertGreater(trx.created_at, timestamp)

    def test_operations(self):
        """Check if the right operations are created when merging identities"""

        timestamp = datetime_utcnow()

        api.merge_identities(from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                             to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 8)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertEqual(op1.target, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['uidentity'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op1_args['identity'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        op2 = operations[1]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op2.entity_type, 'identity')
        self.assertEqual(op2.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 2)
        self.assertEqual(op2_args['uidentity'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op2_args['identity'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        op3 = operations[2]
        self.assertIsInstance(op3, Operation)
        self.assertEqual(op3.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op3.entity_type, 'enrollment')
        self.assertEqual(op3.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op3.trx, trx)
        self.assertGreater(op3.timestamp, timestamp)

        op3_args = json.loads(op3.args)
        self.assertEqual(len(op3_args), 4)
        self.assertEqual(op3_args['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op3_args['organization'], 'Example')
        self.assertEqual(op3_args['start'], str(datetime_to_utc(datetime.datetime(1900, 1, 1))))
        self.assertEqual(op3_args['end'], str(datetime_to_utc(datetime.datetime(2017, 6, 1))))

        op4 = operations[3]
        self.assertIsInstance(op4, Operation)
        self.assertEqual(op4.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op4.entity_type, 'enrollment')
        self.assertEqual(op4.target, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op4.trx, trx)
        self.assertGreater(op4.timestamp, timestamp)

        op4_args = json.loads(op4.args)
        self.assertEqual(len(op4_args), 4)
        self.assertEqual(op4_args['uuid'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op4_args['organization'], 'Bitergia')
        self.assertEqual(op4_args['start'], str(datetime_to_utc(datetime.datetime(2017, 6, 2))))
        self.assertEqual(op4_args['end'], str(datetime_to_utc(datetime.datetime(2100, 1, 1))))

        op5 = operations[4]
        self.assertIsInstance(op5, Operation)
        self.assertEqual(op5.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op5.entity_type, 'enrollment')
        self.assertEqual(op5.target, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op5.trx, trx)
        self.assertGreater(op5.timestamp, timestamp)

        op5_args = json.loads(op5.args)
        self.assertEqual(len(op5_args), 4)
        self.assertEqual(op5_args['uidentity'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op5_args['organization'], 'Example')
        self.assertEqual(op5_args['start'], str(datetime_to_utc(datetime.datetime(1900, 1, 1))))
        self.assertEqual(op5_args['end'], str(datetime_to_utc(datetime.datetime(2017, 6, 1))))

        op6 = operations[5]
        self.assertIsInstance(op6, Operation)
        self.assertEqual(op6.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op6.entity_type, 'enrollment')
        self.assertEqual(op6.target, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op6.trx, trx)
        self.assertGreater(op6.timestamp, timestamp)

        op6_args = json.loads(op6.args)
        self.assertEqual(len(op6_args), 4)
        self.assertEqual(op6_args['uidentity'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op6_args['organization'], 'Bitergia')
        self.assertEqual(op6_args['start'], str(datetime_to_utc(datetime.datetime(2017, 6, 2))))
        self.assertEqual(op6_args['end'], str(datetime_to_utc(datetime.datetime(2100, 1, 1))))

        op7 = operations[6]
        self.assertIsInstance(op7, Operation)
        self.assertEqual(op7.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op7.entity_type, 'profile')
        self.assertEqual(op7.target, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op7.trx, trx)
        self.assertGreater(op7.timestamp, timestamp)

        op7_args = json.loads(op7.args)
        self.assertEqual(len(op7_args), 1)
        self.assertEqual(op7_args['uidentity'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        op8 = operations[7]
        self.assertIsInstance(op8, Operation)
        self.assertEqual(op8.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op8.entity_type, 'unique_identity')
        self.assertEqual(op8.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op8.trx, trx)
        self.assertGreater(op8.timestamp, timestamp)

        op8_args = json.loads(op8.args)
        self.assertEqual(len(op8_args), 1)
        self.assertEqual(op8_args['uidentity'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
