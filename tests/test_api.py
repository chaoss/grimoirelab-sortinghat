# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2020 Bitergia
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

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow, datetime_to_utc

from sortinghat.core import api
from sortinghat.core.context import SortingHatContext
from sortinghat.core.errors import (AlreadyExistsError,
                                    NotFoundError,
                                    InvalidValueError,
                                    LockedIdentityError,
                                    DuplicateRangeError,
                                    EqualIndividualError)
from sortinghat.core.models import (Country,
                                    Individual,
                                    Identity,
                                    Enrollment,
                                    Organization,
                                    Team,
                                    Domain,
                                    Transaction,
                                    Operation,
                                    ScheduledTask,
                                    Alias,
                                    MergeRecommendation)

NOT_FOUND_ERROR = "{entity} not found in the registry"
ENROLLMENT_RANGE_INVALID = "range date '{start}'-'{end}' is part of an existing range for {org}"
ALREADY_EXISTS_ERROR = "{entity} already exists in the registry"
SOURCE_NONE_OR_EMPTY_ERROR = "'source' cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be empty"
UUID_NONE_OR_EMPTY_ERROR = "'uuid' cannot be"
UUID_LOCKED_ERROR = "Individual {uuid} is locked"
UUIDS_NONE_OR_EMPTY_ERROR = "'uuids' cannot be"
FROM_UUID_NONE_OR_EMPTY_ERROR = "'from_uuid' cannot be"
FROM_DATE_NONE_OR_EMPTY_ERROR = "'from_date' cannot be"
FROM_UUID_IS_INDIVIDUAL_ERROR = "'from_uuid' is an individual and it cannot be moved; use 'merge' instead"
FROM_UUIDS_NONE_OR_EMPTY_ERROR = "'from_uuids' cannot be"
TO_UUID_NONE_OR_EMPTY_ERROR = "'to_uuid' cannot be"
TO_DATE_NONE_OR_EMPTY_ERROR = "'to_date' cannot be"
BOTH_NEW_DATES_NONE_OR_EMPTY_ERROR = "'new_from_date' and 'to_from_date' cannot be"
FROM_UUID_TO_UUID_EQUAL_ERROR = "'to_uuid' {to_uuid} cannot be part of 'from_uuids'"
IS_BOT_VALUE_ERROR = "'is_bot' must have a boolean value"
COUNTRY_CODE_ERROR = r"'country_code' \({code}\) does not match with a valid code"
GENDER_ACC_INVALID_ERROR = "'gender_acc' can only be set when 'gender' is given"
GENDER_ACC_INVALID_TYPE_ERROR = "'gender_acc' must have an integer value"
GENDER_ACC_INVALID_RANGE_ERROR = r"'gender_acc' \({acc}\) is not in range \(1,100\)"
PERIOD_INVALID_ERROR = "'start' date {start} cannot be greater than {end}"
PERIOD_OUT_OF_BOUNDS_ERROR = "'{type}' date {date} is out of bounds"
WITHDRAW_PERIOD_INVALID_ERROR = "'from_date' date {from_date} cannot be greater than {to_date}"
UPDATE_ENROLLMENT_PERIOD_INVALID_ERROR = "'from_date' date {from_date} cannot be greater than {to_date}"
UPDATE_ENROLLMENT_NEW_PERIOD_INVALID_ERROR = "'new_from_date' date {from_date} cannot be greater than {to_date}"
ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR = "'name' cannot be"
ORGANIZATION_NOT_FOUND_ERROR = "{name} not found in the registry"
ORGANIZATION_ALREADY_EXISTS_ERROR = "Organization '{name}' already exists in the registry"
ORGANIZATION_VALUE_ERROR = "field value must be a string; int given"
TEAM_ORG_NAME_MISSING = "'org_name' cannot be"
TEAM_NAME_MISSING = "'team_name' cannot be"
DOMAIN_NAME_NONE_OR_EMPTY_ERROR = "'domain_name' cannot be"
DOMAIN_NOT_FOUND_ERROR = "{domain_name} not found in the registry"
DOMAIN_ALREADY_EXISTS_ERROR = "'{domain_name}' already exists in the registry"
DOMAIN_VALUE_ERROR = "field value must be a string; int given"
DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR = "'org_name' cannot be"
FORMAT_NONE_OR_EMPTY_ERROR = "'{}' cannot be"
INTERVAL_MUST_BE_NUMBER_ERROR = "'interval' must be a positive number"
FROM_ORG_TO_ORG_EQUAL_ERROR = "'to_org' cannot be the same as 'from_org'"
ALIAS_ALREADY_EXISTS_ERROR = "'{name}' already exists in the registry"
ALIAS_NAME_NONE_OR_EMPTY_ERROR = "'name' cannot be"
ALIAS_VALUE_ERROR = "field value must be a string; int given"
ALIAS_ORG_NAME_NONE_OR_EMPTY_ERROR = "'organization' cannot be"
ALIAS_NOT_FOUND_ERROR = "{name} not found in the registry"


class TestAddIdentity(TestCase):
    """Unit tests for add_identity"""

    def setUp(self):
        """Load initial values"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_add_new_identity(self):
        """Check if everything goes OK when adding a new identity"""

        identity = api.add_identity(self.ctx,
                                    'scm',
                                    name='John Smith',
                                    email='jsmith@example.com',
                                    username='jsmith')
        self.assertEqual(identity.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, 'jsmith@example.com')
        self.assertEqual(identity.username, 'jsmith')
        self.assertEqual(identity.source, 'scm')

        individual = Individual.objects.get(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(individual.mk, identity.uuid)

        profile = individual.profile
        self.assertEqual(profile.name, identity.name)
        self.assertEqual(profile.email, identity.email)

        identities = Identity.objects.filter(uuid=identity.uuid)
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1, identity)

    def test_add_new_identities_to_uuid(self):
        """Check if everything goes OK when adding new identities to an existing one"""

        # Insert identities that will create the individuals
        jsmith = api.add_identity(self.ctx,
                                  'scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')
        jdoe = api.add_identity(self.ctx,
                                'scm',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe')

        # Create new identities and assign them to John Smith uuid
        identity1 = api.add_identity(self.ctx,
                                     'mls',
                                     name='John Smith',
                                     email='jsmith@example.com',
                                     username='jsmith',
                                     uuid=jsmith.uuid)

        identity2 = api.add_identity(self.ctx,
                                     'mls',
                                     name='John Smith',
                                     username='jsmith',
                                     uuid=jsmith.uuid)

        # Create a new identity for John Doe
        identity3 = api.add_identity(self.ctx,
                                     'mls',
                                     email='jdoe@example.com',
                                     uuid=jdoe.uuid)

        # Check identities
        individuals = Individual.objects.all()
        self.assertEqual(len(individuals), 2)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 5)

        # Check John Smith
        individual = Individual.objects.get(mk=jsmith.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1.uuid, identity1.uuid)
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.source, 'mls')

        id2 = identities[1]
        self.assertEqual(id2.uuid, identity2.uuid)
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, None)
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.source, 'mls')

        id3 = identities[2]
        self.assertEqual(id3.uuid, jsmith.uuid)
        self.assertEqual(id3.name, 'John Smith')
        self.assertEqual(id3.email, 'jsmith@example.com')
        self.assertEqual(id3.username, 'jsmith')
        self.assertEqual(id3.source, 'scm')

        # Next, John Doe
        individual = Individual.objects.get(mk=jdoe.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1.uuid, identity3.uuid)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jdoe@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'mls')

        id2 = identities[1]
        self.assertEqual(id2.uuid, jdoe.uuid)
        self.assertEqual(id2.name, 'John Doe')
        self.assertEqual(id2.email, 'jdoe@example.com')
        self.assertEqual(id2.username, 'jdoe')
        self.assertEqual(id2.source, 'scm')

    def test_add_identity_using_any_identity_uuid(self):
        """Check if it adds a new identity to an existing one using some other related id"""

        # Insert identities that will create the individuals
        jsmith = api.add_identity(self.ctx,
                                  'scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')
        identity1 = api.add_identity(self.ctx,
                                     'mls',
                                     name='John Smith',
                                     email='jsmith@example.com',
                                     username='jsmith',
                                     uuid=jsmith.uuid)

        # Insert a new identity using 'identity1' uuid
        identity2 = api.add_identity(self.ctx,
                                     'mls',
                                     name='John Smith',
                                     username='jsmith',
                                     uuid=identity1.uuid)

        # Check John Smith
        individual = Individual.objects.get(mk=jsmith.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1.uuid, identity1.uuid)
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.source, 'mls')

        id2 = identities[1]
        self.assertEqual(id2.uuid, identity2.uuid)
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, None)
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.source, 'mls')

        id3 = identities[2]
        self.assertEqual(id3.uuid, jsmith.uuid)
        self.assertEqual(id3.name, 'John Smith')
        self.assertEqual(id3.email, 'jsmith@example.com')
        self.assertEqual(id3.username, 'jsmith')
        self.assertEqual(id3.source, 'scm')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        # First, insert the identity that will create the individual
        before_dt = datetime_utcnow()
        jsmith = api.add_identity(self.ctx,
                                  'scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')
        after_dt = datetime_utcnow()

        # Check date on the individual
        individual = Individual.objects.get(mk=jsmith.uuid)
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

        # Check date on the identity
        identity = individual.identities.all()[0]
        self.assertLessEqual(before_dt, identity.last_modified)
        self.assertGreaterEqual(after_dt, identity.last_modified)

        # Check if a new identity added to the existing individual
        # updates both modification dates
        before_new_dt = datetime_utcnow()
        api.add_identity(self.ctx,
                         'scm',
                         name=None,
                         email='jsmith@example.com',
                         username=None,
                         uuid=jsmith.uuid)
        after_new_dt = datetime_utcnow()

        individual = Individual.objects.get(mk=jsmith.uuid)

        # Check date on the individual; it was updated
        self.assertLessEqual(before_new_dt, individual.last_modified)
        self.assertGreaterEqual(after_new_dt, individual.last_modified)

        # Check date of the new identity
        identities = individual.identities.all()
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

        api.add_identity(self.ctx, 'scm', email='jsmith@example.com')

        # Although, this identities belongs to the same individual,
        # the api will create different individuals for each one of
        # them
        id1 = api.add_identity(self.ctx,
                               'scm',
                               name='John Smith',
                               email='jsmith@example.com')
        id2 = api.add_identity(self.ctx,
                               'scm',
                               name='John Smith',
                               email='jsmith@example.com',
                               username='jsmith')
        id3 = api.add_identity(self.ctx,
                               'mls',
                               name='John Smith',
                               email='jsmith@example.com',
                               username='jsmith')
        id4 = api.add_identity(self.ctx, 'mls', name='John Smith')
        id5 = api.add_identity(self.ctx, 'scm', name='John Smith')

        self.assertEqual(id1.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(id2.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(id3.uuid, '539acca35c2e8502951a97d2d5af8b0857440b50')
        self.assertEqual(id4.uuid, 'e7efdaf17ad2cbc0e239b9afd29f6fe054b3b0fe')
        self.assertEqual(id5.uuid, 'c7acd177d107a0aefa6718e2ff0dec6ceba71660')

    def test_duplicate_identities_with_truncated_values(self):
        """Check if the same identity with truncated values is not inserted twice"""

        # Due database limitations, email will be truncated
        source = 'scm'
        email = 'averylongemailaddressthatexceedsthemaximumlengthsoitwillbetruncated' * 2
        name = 'John Smith'
        username = 'jsmith'

        api.add_identity(self.ctx,
                         source,
                         name=name,
                         email=email,
                         username=username)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(AlreadyExistsError):
            api.add_identity(self.ctx,
                             source,
                             name=name,
                             email=email,
                             username=username)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_add_identity_name_none(self):
        """Check if the username is set to the profile when no name is provided"""

        identity = api.add_identity(self.ctx,
                                    'scm',
                                    name=None,
                                    email='jsmith@example.com',
                                    username='jsmith')
        self.assertEqual(identity.uuid, '18f652547d666701fcf1ddb59867bc88bb6e6b86')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, 'jsmith@example.com')
        self.assertEqual(identity.username, 'jsmith')
        self.assertEqual(identity.source, 'scm')

        individual = Individual.objects.get(mk='18f652547d666701fcf1ddb59867bc88bb6e6b86')
        self.assertEqual(individual.mk, identity.uuid)

        profile = individual.profile
        # The profile name must match with the username, as no name was provided
        self.assertEqual(profile.name, 'jsmith')
        self.assertEqual(profile.email, 'jsmith@example.com')

        identities = Identity.objects.filter(uuid=identity.uuid)
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1, identity)

    def test_non_existing_uuid(self):
        """Check whether it fails adding identities to one uuid that does not exist"""

        # Add a pair of identities first
        api.add_identity(self.ctx, 'scm', email='jsmith@example.com')
        api.add_identity(self.ctx, 'scm', email='jdoe@example.com')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.add_identity(self.ctx,
                             'mls',
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
        api.add_identity(self.ctx, 'scm', email='jsmith@example.com')
        api.add_identity(self.ctx, 'scm', email='jdoe@example.com')

        # Insert the first identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.ctx, 'scm', email='jsmith@example.com')

        self.assertEqual(context.exception.eid,
                         '334da68fcd3da4e799791f73dfada2afb22648c6')

        # Insert the same identity with upper case letters.
        # It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.ctx, 'scm', email='JSMITH@example.com')

        self.assertEqual(context.exception.eid,
                         '334da68fcd3da4e799791f73dfada2afb22648c6')

        # "None" tuples also raise an exception
        api.add_identity(self.ctx, 'scm', name=None, email="None", username=None)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.ctx, 'scm', name="None", email=None, username=None)

        self.assertEqual(context.exception.eid,
                         'f0999c4eed908d33365fa3435d9686d3add2412d')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_unaccent_identities(self):
        """Check if it fails adding an identity that already exists with accent values"""

        # Add a pair of identities first
        api.add_identity(self.ctx, 'scm', name='John Smith')
        api.add_identity(self.ctx, 'scm', name='Jöhn Doe')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        # Insert an accent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.ctx, 'scm', name='Jöhn Smith')

        self.assertEqual(context.exception.eid,
                         'c7acd177d107a0aefa6718e2ff0dec6ceba71660')

        # Insert an accent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.ctx, 'scm', name='John Döe')

        # Insert an unaccent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.ctx, 'scm', name='John Doe')

        self.assertEqual(context.exception.eid,
                         'a16659ea83d28c839ffae76ceebb3ca9fb8e8894')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_utf8_4bytes_identities(self):
        """Check if it inserts identities with 4bytes UTF-8 characters"""

        # Emojis are 4bytes characters
        identity = api.add_identity(self.ctx,
                                    'scm',
                                    name='😂',
                                    email='😂',
                                    username='😂')

        individual = Individual.objects.get(mk='843fcc3383ddfd6179bef87996fa761d88a43915')
        self.assertEqual(individual.mk, identity.uuid)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, identity.uuid)
        self.assertEqual(id1.uuid, '843fcc3383ddfd6179bef87996fa761d88a43915')
        self.assertEqual(id1.name, '😂')
        self.assertEqual(id1.email, '😂')
        self.assertEqual(id1.username, '😂')
        self.assertEqual(id1.source, 'scm')

    def test_charset(self):
        """Check if it adds two identities with different encoding"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        id1 = api.add_identity(self.ctx,
                               'scm',
                               name='John Smıth',
                               email='jsmith@example.com',
                               username='jsmith')
        id2 = api.add_identity(self.ctx,
                               'scm',
                               name='John Smith',
                               email='jsmith@example.com',
                               username='jsmith')

        self.assertEqual(id1.uuid, 'cf79edf008b7b2960a0be3972b256c65af449dc1')
        self.assertEqual(id2.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

    def test_none_source(self):
        """Check whether new identities cannot be added when giving a None source"""

        with self.assertRaisesRegex(InvalidValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.add_identity(self.ctx, None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        with self.assertRaisesRegex(InvalidValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            api.add_identity(self.ctx, '')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        with self.assertRaisesRegex(InvalidValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.add_identity(self.ctx, 'scm', name='', email=None, username=None)

        with self.assertRaisesRegex(InvalidValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            api.add_identity(self.ctx, 'scm', name='', email='', username='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        jsmith = api.add_identity(self.ctx,
                                  'scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')

        individual = Individual.objects.get(mk=jsmith.uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=jsmith.uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.add_identity(self.ctx,
                             'mls',
                             name='John Smith',
                             email='jsmith@example.com',
                             username='jsmith',
                             uuid=jsmith.uuid)

    def test_transaction(self):
        """Check if a transaction is created when adding a new identity"""

        timestamp = datetime_utcnow()

        api.add_identity(self.ctx,
                         'scm',
                         name='John Smith',
                         email='jsmith@example.com',
                         username='jsmith')

        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_identity')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when adding a new identity"""

        timestamp = datetime_utcnow()

        identity = api.add_identity(self.ctx,
                                    'scm',
                                    name='John Smith',
                                    email='jsmith@example.com',
                                    username='jsmith')

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 3)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.target, identity.individual.mk)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['mk'], identity.individual.mk)

        op2 = operations[1]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op2.entity_type, 'profile')
        self.assertEqual(op2.target, identity.uuid)
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 3)
        self.assertEqual(op2_args['individual'], identity.individual.mk)
        self.assertEqual(op2_args['name'], identity.name)
        self.assertEqual(op2_args['email'], identity.email)

        op3 = operations[2]
        self.assertIsInstance(op3, Operation)
        self.assertEqual(op3.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op3.entity_type, 'identity')
        self.assertEqual(op3.target, identity.uuid)
        self.assertEqual(op3.trx, trx)
        self.assertGreater(op3.timestamp, timestamp)

        op3_args = json.loads(op3.args)
        self.assertEqual(len(op3_args), 6)
        self.assertEqual(op3_args['individual'], identity.individual.mk)
        self.assertEqual(op3_args['uuid'], identity.uuid)
        self.assertEqual(op3_args['source'], identity.source)
        self.assertEqual(op3_args['name'], identity.name)
        self.assertEqual(op3_args['email'], identity.email)
        self.assertEqual(op3_args['username'], identity.username)


class TestDeleteIdentity(TestCase):
    """Unit tests for delete_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        # Organizations
        example_org = api.add_organization(self.ctx, 'Example')
        bitergia_org = api.add_organization(self.ctx, 'Bitergia')
        libresoft_org = api.add_organization(self.ctx, 'LibreSoft')

        # Identities
        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_identity(self.ctx,
                         'scm',
                         name='John Smith',
                         email='jsmith@example',
                         uuid=jsmith.uuid)
        Enrollment.objects.create(individual=jsmith.individual,
                                  group=example_org)
        Enrollment.objects.create(individual=jsmith.individual,
                                  group=bitergia_org)

        jdoe = api.add_identity(self.ctx, 'scm', email='jdoe@example')
        Enrollment.objects.create(individual=jdoe.individual,
                                  group=example_org)

        jrae = api.add_identity(self.ctx,
                                'scm',
                                name='Jane Rae',
                                email='jrae@example')
        Enrollment.objects.create(individual=jrae.individual,
                                  group=libresoft_org)

    def test_delete_identity(self):
        """Check whether it deletes an identity"""

        # Check initial status
        individuals = Individual.objects.all()
        self.assertEqual(len(individuals), 3)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 4)

        # Delete an identity (John Smith - jsmith@example.com)
        individual = api.delete_identity(self.ctx, '1387b129ab751a3657312c09759caa41dfd8d07d')

        # Check result
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, 'jsmith@example')
        self.assertEqual(identity.username, None)

        # Check remaining identities
        individuals = Individual.objects.all()
        self.assertEqual(len(individuals), 3)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 3)

        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(uuid='1387b129ab751a3657312c09759caa41dfd8d07d')

    def test_delete_individual(self):
        """Check whether it deletes an individual when its identifier is given"""

        # Check initial status
        individuals = Individual.objects.all()
        self.assertEqual(len(individuals), 3)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 4)

        # Delete an individual (John Smith)
        individual = api.delete_identity(self.ctx, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # The individual was removed so the result is None
        self.assertEqual(individual, None)

        # Check remaining identities
        individuals = Individual.objects.all()
        self.assertEqual(len(individuals), 2)

        identities = Identity.objects.all()
        self.assertEqual(len(identities), 2)

        # Neither the individual nor its identities exist
        with self.assertRaises(ObjectDoesNotExist):
            Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(uuid='1387b129ab751a3657312c09759caa41dfd8d07d')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        # Delete an identity (John Smith - jsmith@example.com)
        before_dt = datetime_utcnow()
        individual = api.delete_identity(self.ctx, '1387b129ab751a3657312c09759caa41dfd8d07d')
        after_dt = datetime_utcnow()

        # Check date on the individual
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

        # Other identities were not updated
        identity = individual.identities.all()[0]
        self.assertGreaterEqual(before_dt, identity.last_modified)

    def test_non_existing_uuid(self):
        """Check if it fails removing a identities that does not exists"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.delete_identity(self.ctx, 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        # It should raise an error when the registry is empty
        Individual.objects.all().delete()
        self.assertEqual(len(Individual.objects.all()), 0)

        with self.assertRaises(NotFoundError):
            api.delete_identity(self.ctx, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_uuid(self):
        """Check whether identities cannot be removed when giving a None UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.delete_identity(self.ctx, None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_uuid(self):
        """Check whether identities cannot be removed when giving an empty UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.delete_identity(self.ctx, '')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        jsmith = api.add_identity(self.ctx,
                                  'scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')

        individual = Individual.objects.get(mk=jsmith.uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=jsmith.uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.delete_identity(self.ctx, jsmith.uuid)

    def test_transaction(self):
        """Check if a transaction is created when deleting an identity"""

        timestamp = datetime_utcnow()

        api.delete_identity(self.ctx, '1387b129ab751a3657312c09759caa41dfd8d07d')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_identity')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting an identity"""

        timestamp = datetime_utcnow()

        api.delete_identity(self.ctx, '1387b129ab751a3657312c09759caa41dfd8d07d')

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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        api.add_identity(self.ctx, 'scm', email='jsmith@example')

    def test_update_empty_profile(self):
        """Check if it updates an empty profile"""

        individual = api.update_profile(self.ctx,
                                        'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                        name='Smith, J.', email='jsmith@example.net',
                                        is_bot=True, country_code='US',
                                        gender='male', gender_acc=98)

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        profile = individual.profile
        self.assertEqual(profile.name, 'Smith, J.')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertIsInstance(profile.country, Country)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 98)

        # Check database object
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(profile, individual_db.profile)

    def test_update_profile(self):
        """Check if it updates a profile"""

        api.update_profile(self.ctx,
                           'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='Smith, J.', email='jsmith@example.net',
                           is_bot=True, country_code='US',
                           gender='male', gender_acc=98)

        individual = api.update_profile(self.ctx,
                                        'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                        name='', email='jsmith@example.net',
                                        is_bot=False, country_code='US',
                                        gender='male', gender_acc=89)

        # Tests
        self.assertIsInstance(individual, Individual)

        profile = individual.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, False)
        self.assertIsInstance(profile.country, Country)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 89)

        # Check database object
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(profile, individual_db.profile)

    def test_update_profile_using_any_identity_uuid(self):
        """Check if it updates a profile using any of the related identities uuids"""

        api.add_identity(self.ctx, 'mls', email='jsmith@example',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Use the new identity uuid to update the profile
        individual = api.update_profile(self.ctx,
                                        'de176236636bc488d31e9f91952ecfc6d976a69e',
                                        name='Smith, J.', email='jsmith@example.net',
                                        is_bot=True, country_code='US',
                                        gender='male', gender_acc=98)

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        profile = individual.profile
        self.assertEqual(profile.name, 'Smith, J.')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertIsInstance(profile.country, Country)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 98)

        # Check database object
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(profile, individual_db.profile)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        individual = api.update_profile(self.ctx,
                                        'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                        name='John Smith',
                                        email='jsmith@example.net')
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_non_existing_uuid(self):
        """Check if it fails updating an individual that does not exist"""

        with self.assertRaises(NotFoundError):
            api.update_profile(self.ctx,
                               'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                               name='', email='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_name_email_empty(self):
        """Check if name and email are set to None when an empty string is given"""

        individual = api.update_profile(self.ctx,
                                        'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                        name='', email='')
        profile = individual.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)

    def test_is_bot_invalid_type(self):
        """Check type values of is_bot parameter"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        with self.assertRaisesRegex(InvalidValueError, IS_BOT_VALUE_ERROR):
            api.update_profile(self.ctx, uuid, is_bot=1)

        with self.assertRaisesRegex(InvalidValueError, IS_BOT_VALUE_ERROR):
            api.update_profile(self.ctx, uuid, is_bot='True')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_country_code_not_valid(self):
        """Check if it fails when the given country is not valid"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        msg = COUNTRY_CODE_ERROR.format(code='JKL')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(self.ctx, uuid, country_code='JKL')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_gender_not_given(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        with self.assertRaisesRegex(InvalidValueError, GENDER_ACC_INVALID_ERROR):
            api.update_profile(self.ctx, uuid, gender_acc=100)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_gender_acc_invalid_type(self):
        """Check type values of gender_acc parameter"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        with self.assertRaisesRegex(InvalidValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            api.update_profile(self.ctx, uuid, gender='male', gender_acc=10.0)

        with self.assertRaisesRegex(InvalidValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            api.update_profile(self.ctx, uuid, gender='male', gender_acc='100')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_gender_acc_invalid_range(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='-1')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(self.ctx, uuid, gender='male', gender_acc=-1)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='0')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(self.ctx, uuid, gender='male', gender_acc=0)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='101')

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_profile(self.ctx, uuid, gender='male', gender_acc=101)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        jsmith = api.add_identity(self.ctx,
                                  'scm',
                                  name='John Smith',
                                  email='jsmith@example.com',
                                  username='jsmith')

        individual = Individual.objects.get(mk=jsmith.uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=jsmith.uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.update_profile(self.ctx,
                               jsmith.uuid,
                               name='', email='jsmith@example.net',
                               is_bot=False, country_code='US',
                               gender='male', gender_acc=89)

    def test_transaction(self):
        """Check if a transaction is created when updating a profile"""

        timestamp = datetime_utcnow()

        api.update_profile(self.ctx,
                           'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='Smith, J.', email='jsmith@example.net',
                           is_bot=True, country_code='US',
                           gender='male', gender_acc=98)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'update_profile')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when updating a profile"""

        timestamp = datetime_utcnow()

        individual = api.update_profile(self.ctx,
                                        'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
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
        self.assertEqual(op1_args['individual'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example.com')
        api.add_identity(self.ctx,
                         'scm',
                         name='John Smith',
                         email='jsmith@example.com',
                         uuid=jsmith.uuid)
        jsmith2 = api.add_identity(self.ctx, 'scm', email='jdoe@example.com')
        api.add_identity(self.ctx,
                         'phab',
                         name='J. Smith',
                         email='jsmith@example.org',
                         uuid=jsmith2.uuid)

    def test_move_identity(self):
        """Test whether an identity is moved to an individual"""

        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        # Tests
        individual = api.move_identity(self.ctx, from_uuid, to_uuid)

        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        identity = identities[0]
        self.assertEqual(identity.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identity = identities[1]
        self.assertEqual(identity.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')

        identity = identities[2]
        self.assertEqual(identity.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        # Check database object
        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 3)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')
        self.assertEqual(identity_db.name, 'J. Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.org')

        identity_db = identities_db[2]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

    def test_move_identity_using_any_identity_uuid(self):
        """Check if it moves an identity using any of the identities uuids related to an individual"""

        # John Smith first identity has two identities.
        # Using the one that does not have the main key should
        # move the identity too.
        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '0880dc4e621877e8520cef1747d139dd4f9f110e'

        # Tests
        individual = api.move_identity(self.ctx, from_uuid, to_uuid)

        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        identity = identities[0]
        self.assertEqual(identity.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identity = identities[1]
        self.assertEqual(identity.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')

        identity = identities[2]
        self.assertEqual(identity.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        # Check database object
        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 3)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')
        self.assertEqual(identity_db.name, 'J. Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.org')

        identity_db = identities_db[2]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        # Tests
        before_dt = datetime_utcnow()
        individual = api.move_identity(self.ctx, from_uuid, to_uuid)
        after_dt = datetime_utcnow()

        # Check date on the individual
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_equal_related_individual(self):
        """Check if identities are not moved when 'to_uuid' is the individual related to 'from_uuid'"""

        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '334da68fcd3da4e799791f73dfada2afb22648c6'

        # Move the identity to the same individual
        api.move_identity(self.ctx, from_uuid, to_uuid)

        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')

    def test_equal_related_individual_using_any_identity_uuid(self):
        """
        Check if identities are not moved when 'to_uuid' is a valid
        uuid for the individual related to 'from_uuid'
        """
        api.add_identity(self.ctx,
                         'scm',
                         name='John Doe',
                         email='jdoe@example.net',
                         uuid='334da68fcd3da4e799791f73dfada2afb22648c6')

        from_uuid = '4fbfb210246cab68eb2f8d3d2f1d41b73e83ad03'
        to_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'

        # Move the identity to the same individual
        api.move_identity(self.ctx, from_uuid, to_uuid)

        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 3)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '4fbfb210246cab68eb2f8d3d2f1d41b73e83ad03')

        identity_db = identities_db[2]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')

    def test_create_new_individual(self):
        """Check if a new individual is created when 'from_uuid' has the same value of 'to_uuid'"""

        new_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'

        # This will create a new individual,
        # moving the identity to this new individual
        individual = api.move_identity(self.ctx, new_uuid, new_uuid)

        self.assertEqual(individual.mk, new_uuid)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        profile = individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@example.com')

        identity = identities[0]
        self.assertEqual(identity.uuid, new_uuid)
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, 'jsmith@example.com')

        # Check database objects
        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')
        self.assertEqual(identity_db.name, 'J. Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.org')

    def test_from_uuid_is_individual(self):
        """Test whether it fails when 'from_uuid' is an individual"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        # Check 'from_uuid' parameter
        with self.assertRaisesRegex(InvalidValueError, FROM_UUID_IS_INDIVIDUAL_ERROR):
            api.move_identity(self.ctx,
                              '03877f31261a6d1a1b3971d240e628259364b8ac',
                              '334da68fcd3da4e799791f73dfada2afb22648c6')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_not_found_from_identity(self):
        """Test whether it fails when 'from_uuid' identity is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='FFFFFFFFFFF')

        # Check 'from_uuid' parameter
        with self.assertRaisesRegex(NotFoundError, msg):
            api.move_identity(self.ctx,
                              'FFFFFFFFFFF',
                              '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_not_found_to_identity(self):
        """Test whether it fails when 'to_uuid' individual is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='FFFFFFFFFFF')

        # Check 'to_uuid' parameter
        with self.assertRaisesRegex(NotFoundError, msg):
            api.move_identity(self.ctx,
                              '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
                              'FFFFFFFFFFF')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_from_uuid(self):
        """Check whether identities cannot be moved when giving a None uuid"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUID_NONE_OR_EMPTY_ERROR):
            api.move_identity(self.ctx,
                              None,
                              '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_from_uuid(self):
        """Check whether identities cannot be moved when giving an empty uuid"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUID_NONE_OR_EMPTY_ERROR):
            api.move_identity(self.ctx,
                              '',
                              '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_to_uuid(self):
        """Check whether identities cannot be moved when giving a None UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, TO_UUID_NONE_OR_EMPTY_ERROR):
            api.move_identity(self.ctx,
                              '03877f31261a6d1a1b3971d240e628259364b8ac',
                              None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_to_uuid(self):
        """Check whether identities cannot be moved when giving an empty UUID"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, TO_UUID_NONE_OR_EMPTY_ERROR):
            api.move_identity(self.ctx,
                              '03877f31261a6d1a1b3971d240e628259364b8ac',
                              '')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        individual = Individual.objects.get(mk=to_uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=to_uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.move_identity(self.ctx, from_uuid, to_uuid)

    def test_transaction(self):
        """Check if a transaction is created when moving an identity"""

        timestamp = datetime_utcnow()

        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        api.move_identity(self.ctx, from_uuid, to_uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'move_identity')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when moving an identity"""

        timestamp = datetime_utcnow()

        from_uuid = '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        to_uuid = '03877f31261a6d1a1b3971d240e628259364b8ac'

        api.move_identity(self.ctx, from_uuid, to_uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertEqual(op1.target, from_uuid)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['identity'], from_uuid)
        self.assertEqual(op1_args['individual'], to_uuid)


class TestLock(TestCase):
    """Unit tests for lock"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)
        self.jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example.com')

    def test_lock(self):
        """Test whether an individual is locked"""

        jsmith = api.lock(self.ctx, self.jsmith.individual)

        self.assertEqual(jsmith.is_locked, True)

    def test_lock_using_any_identity_uuid(self):
        """Check if it locks an individual using any of its identities uuids"""

        new_id = api.add_identity(self.ctx, 'mls', email='jsmith@example.com',
                                  uuid=self.jsmith.uuid)

        jsmith = api.lock(self.ctx, new_id.uuid)

        self.assertEqual(jsmith.is_locked, True)
        self.assertEqual(jsmith.mk, self.jsmith.individual.mk)

    def test_lock_uuid_none_or_empty(self):
        """Check if it fails when the uuid is None or an empty string"""

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.lock(self.ctx, None)

    def test_lock_uuid_not_exists(self):
        """Check if it fails when the uuid does not exists"""

        msg = NOT_FOUND_ERROR.format(entity='AAAA')
        with self.assertRaisesRegex(NotFoundError, msg):
            api.lock(self.ctx, 'AAAA')

    def test_transaction(self):
        """Check if a transaction is created when locking an individual"""

        timestamp = datetime_utcnow()
        uuid = self.jsmith.individual.mk

        api.lock(self.ctx, uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'lock')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when locking an individual"""

        timestamp = datetime_utcnow()
        uuid = self.jsmith.individual.mk

        api.lock(self.ctx, uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.target, uuid)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['mk'], uuid)
        self.assertEqual(op1_args['is_locked'], True)


class TestUnlock(TestCase):
    """Unit tests for unlock"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)
        self.jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example.com')

    def test_unlock(self):
        """Test whether an individual is unlocked"""

        uuid = self.jsmith.individual.mk

        jsmith = api.unlock(self.ctx, uuid)

        self.assertEqual(jsmith.is_locked, False)

    def test_unlock_using_any_identity_uuid(self):
        """Check if it unlocks an individual using any of its identities uuids"""

        new_id = api.add_identity(self.ctx, 'mls', email='jsmith@example.com',
                                  uuid=self.jsmith.uuid)

        jsmith = api.unlock(self.ctx, new_id.uuid)

        self.assertEqual(jsmith.is_locked, False)
        self.assertEqual(jsmith.mk, self.jsmith.individual.mk)

    def test_unlock_uuid_none_or_empty(self):
        """Check if it fails when the uuid is None or an empty string"""

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.unlock(self.ctx, None)

    def test_unlock_uuid_not_exists(self):
        """Check if it fails when the uuid does not exists"""

        msg = NOT_FOUND_ERROR.format(entity='AAAA')
        with self.assertRaisesRegex(NotFoundError, msg):
            api.unlock(self.ctx, 'AAAA')

    def test_transaction(self):
        """Check if a transaction is created when unlocking an identity"""

        timestamp = datetime_utcnow()
        uuid = self.jsmith.individual.mk

        api.unlock(self.ctx, uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'unlock')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when unlocking an identity"""

        timestamp = datetime_utcnow()
        uuid = self.jsmith.individual.mk

        api.unlock(self.ctx, uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.target, uuid)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['mk'], uuid)
        self.assertEqual(op1_args['is_locked'], False)


class TestAddOrganization(TestCase):
    """Unit tests for add_organization"""

    def setUp(self):
        """Load initial values"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_add_new_organization(self):
        """Check if everything goes OK when adding a new organization"""

        organization = api.add_organization(self.ctx, name='Example')

        # Tests
        self.assertIsInstance(organization, Organization)
        self.assertEqual(organization.name, 'Example')

        organizations_db = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations_db), 1)

        org1 = organizations_db[0]
        self.assertEqual(organization, org1)

    def test_add_duplicate_organization(self):
        """Check if it fails when adding a duplicate organization"""

        org = api.add_organization(self.ctx, name='Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, ORGANIZATION_ALREADY_EXISTS_ERROR.format(name=org.name)):
            org = api.add_organization(self.ctx, name=org.name)

        organizations = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations), 1)

        organizations = Organization.objects.all()
        self.assertEqual(len(organizations), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_add_existing_alias(self):
        """Check if it fails when adding an organization when it exists as an alias"""

        org = api.add_organization(self.ctx, name='Example')
        als = api.add_alias(self.ctx, name='Example Inc.', organization=org.name)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, ORGANIZATION_ALREADY_EXISTS_ERROR.format(name=als.alias)):
            org = api.add_organization(self.ctx, name=als.alias)

        organizations = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations), 1)

        organizations = Organization.objects.filter(name='Example Inc.')
        self.assertEqual(len(organizations), 0)

        organizations = Organization.objects.all()
        self.assertEqual(len(organizations), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(self.ctx, name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(self.ctx, name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces only"""

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(self.ctx, name='   ')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(self.ctx, name='\t')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.add_organization(self.ctx, name=' \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.add_organization(self.ctx, name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding an organization"""

        timestamp = datetime_utcnow()

        api.add_organization(self.ctx, name='Example')

        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_organization')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when adding an organization"""

        timestamp = datetime_utcnow()

        api.add_organization(self.ctx, name='Example')

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


class TestAddTeam(TestCase):
    """Unit tests for add_team"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)
        self.org = api.add_organization(self.ctx, name='Example')

    def test_add_new_team(self):
        """ Check if new team can be created"""

        team = api.add_team(self.ctx, "suborg", "Example", None)

        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, "suborg")
        self.assertEqual(team.parent_org, self.org)

    def test_organization_is_none(self):
        """Check if it fails when organization name is `None`"""

        team = api.add_team(self.ctx, "suborg", None, None)

        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, "suborg")
        self.assertEqual(team.parent_org, None)

    def test_team_name_is_none(self):
        """Check if it fails when team name is `None`"""

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(InvalidValueError, TEAM_NAME_MISSING):
            api.add_team(self.ctx, None, "Example", None)

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_team_name_is_empty(self):
        """Check if it fails when team name is an empty string"""

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(InvalidValueError, TEAM_NAME_MISSING):
            api.add_team(self.ctx, "", "Example", None)

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_not_found(self):
        """Check if team is created if organization is not found"""

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR.format(name='Exampe')):
            api.add_team(self.ctx, "subteam", "Exampe", None, )

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_find_parent(self):
        """ Check if parent is able to be found"""

        api.add_team(self.ctx, "parent", "Example", None)
        child = api.add_team(self.ctx, "child", "Example", "parent")
        self.assertIsInstance(child, Team)
        self.assertEqual(child.name, "child")
        self.assertEqual(child.parent_org, self.org)

    def test_parent_not_found(self):
        """ Check if a team cannot be created when parent is not found"""

        api.add_team(self.ctx, "suborg", "Example", None)

        with self.assertRaisesRegex(NotFoundError, NOT_FOUND_ERROR.format(entity="parent")):
            api.add_team(self.ctx, "child", "Example", "parent")


class TestDeleteTeam(TestCase):
    """Unit tests for delete_team"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)
        self.org = api.add_organization(self.ctx, name='Example')

    def test_delete_team(self):
        """Check if team can be deleted"""

        api.add_team(self.ctx, "suborg", "Example", None)
        team = api.delete_team(self.ctx, "suborg", self.org.name)

        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, "suborg")
        self.assertEqual(team.parent_org, self.org)

    def test_organization_is_none(self):
        """Check if it passes when team does not belong to any organization"""

        api.add_team(self.ctx, "suborg")

        team = api.delete_team(self.ctx, "suborg")
        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, "suborg")
        self.assertEqual(team.parent_org, None)

    def test_organization_name_is_empty(self):
        """Check if it fails when organization name is empty for a
           team that belongs to an organization"""

        api.add_team(self.ctx, "suborg", "Example", None)

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(NotFoundError, NOT_FOUND_ERROR.format(entity="suborg")):
            api.delete_team(self.ctx, "suborg")

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_team_name_is_none(self):
        """Check if it fails when team name is `None`"""

        api.add_team(self.ctx, "suborg", "Example", None)

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(InvalidValueError, TEAM_NAME_MISSING):
            api.delete_team(self.ctx, None, "Example")

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_team_name_is_empty(self):
        """Check if it fails when team name is an empty string"""

        api.add_team(self.ctx, "suborg", "Example", None)

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(InvalidValueError, TEAM_NAME_MISSING):
            api.delete_team(self.ctx, "", "Example")

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_not_found(self):
        """Check if team is created if organization is not found"""

        api.add_team(self.ctx, "suborg", "Example", None)

        trx_date = datetime_utcnow()

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR.format(name='Exampe')):
            api.delete_team(self.ctx, "suborg", "Exampe")

        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_team_not_found(self):
        """Check if error is raised if team is not found"""

        api.add_team(self.ctx, "suborg", "Example", None)
        with self.assertRaisesRegex(NotFoundError, NOT_FOUND_ERROR.format(entity="sorg")):
            api.delete_team(self.ctx, "sorg", "Example")


class TestAddDomain(TestCase):
    """Unit tests for add_domain"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, name='Example')
        api.add_organization(self.ctx, name='Bitergia')

    def test_add_new_domain(self):
        """Check if everything goes OK when adding a new domain"""

        domain = api.add_domain(self.ctx,
                                organization='Example',
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

        domain = api.add_domain(self.ctx,
                                organization='Example',
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

        domain1 = api.add_domain(self.ctx,
                                 organization='Example',
                                 domain_name='example.com',
                                 is_top_domain=True)

        domain2 = api.add_domain(self.ctx,
                                 organization='Example',
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

        domain = api.add_domain(self.ctx,
                                organization='Example',
                                domain_name='example.com',
                                is_top_domain=True)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, DOMAIN_ALREADY_EXISTS_ERROR.format(domain_name='example.com')):
            api.add_domain(self.ctx,
                           organization='Example',
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

        domain = api.add_domain(self.ctx,
                                organization='Example',
                                domain_name='example.com',
                                is_top_domain=True)

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, DOMAIN_ALREADY_EXISTS_ERROR.format(domain_name='example.com')):
            api.add_domain(self.ctx,
                           organization='Bitergia',
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
            api.add_domain(self.ctx,
                           organization='Botergia',
                           domain_name='bitergia.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_none(self):
        """Check if it fails when domain name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization='Example',
                           domain_name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_empty(self):
        """Check if it fails when domain name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization='Example',
                           domain_name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_whitespaces(self):
        """Check if it fails when domain name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization='Example',
                           domain_name='    ')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization='Example',
                           domain_name='\t')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization='Example',
                           domain_name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_int(self):
        """Check if it fails when domain name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, DOMAIN_VALUE_ERROR):
            api.add_domain(self.ctx,
                           organization='Example',
                           domain_name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization=None,
                           domain_name='example.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization='',
                           domain_name='example.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization=None,
                           domain_name='    ')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization=None,
                           domain_name='\t')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_domain(self.ctx,
                           organization=None,
                           domain_name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.add_domain(self.ctx,
                           organization=12345,
                           domain_name='example.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding a domain"""

        timestamp = datetime_utcnow()

        api.add_domain(self.ctx,
                       organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_domain')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when adding a domain"""

        timestamp = datetime_utcnow()

        api.add_domain(self.ctx,
                       organization='Example',
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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, name='Example')
        api.add_organization(self.ctx, name='Bitergia')
        api.add_organization(self.ctx, name='Libresoft')

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example.com')
        individual = api.enroll(self.ctx,
                                jsmith.uuid, 'Example',
                                from_date=datetime.datetime(1999, 1, 1),
                                to_date=datetime.datetime(2000, 1, 1))

    def test_delete_organization(self):
        """Check if everything goes OK when deleting an organization"""

        api.delete_organization(self.ctx, name='Example')

        organizations = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations), 0)

        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        enrollments = individual_db.enrollments.all()
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
            api.delete_organization(self.ctx, 'Ghost')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(self.ctx, name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(self.ctx, name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(self.ctx, name='   ')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(self.ctx, name='\t')

        with self.assertRaisesRegex(InvalidValueError, ORGANIZATION_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_organization(self.ctx, name=' \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.delete_organization(self.ctx, name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting an organization"""

        timestamp = datetime_utcnow()

        api.delete_organization(self.ctx, name='Example')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_organization')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting an organization"""

        timestamp = datetime_utcnow()

        api.delete_organization(self.ctx, name='Example')

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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, name='Example')
        api.add_domain(self.ctx,
                       organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)
        api.add_domain(self.ctx,
                       organization='Example',
                       domain_name='example.net',
                       is_top_domain=False)

        api.add_organization(self.ctx, name='Bitergia')
        api.add_domain(self.ctx,
                       organization='Bitergia',
                       domain_name='bitergia.com',
                       is_top_domain=True)

    def test_delete_domain(self):
        """Check if everything goes OK when deleting a domain"""

        domain = api.delete_domain(self.ctx, 'example.com')

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
            api.delete_domain(self.ctx, 'botergia.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_not_found(self):
        """Check if it fails when the domain's organization is not found"""

        api.delete_organization(self.ctx, 'Bitergia')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        # Tests
        domains = Domain.objects.filter(domain='bitergia.com')
        self.assertEqual(len(domains), 0)

        with self.assertRaisesRegex(NotFoundError, DOMAIN_NOT_FOUND_ERROR.format(domain_name='bitergia.com')):
            api.delete_domain(self.ctx, 'bitergia.com')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_none(self):
        """Check if it fails when domain name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(self.ctx, domain_name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_empty(self):
        """Check if it fails when domain name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(self.ctx, domain_name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_whitespaces(self):
        """Check if it fails when domain name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(self.ctx, domain_name='    ')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(self.ctx, domain_name='\t')

        with self.assertRaisesRegex(InvalidValueError, DOMAIN_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_domain(self.ctx, domain_name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_domain_name_int(self):
        """Check if it fails when domain name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, DOMAIN_VALUE_ERROR):
            api.delete_domain(self.ctx, domain_name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting a domain"""

        timestamp = datetime_utcnow()

        api.delete_domain(self.ctx, 'example.com')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_domain')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()

        domain = api.delete_domain(self.ctx, 'example.com')

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

    def setUp(self):
        """Load initial values"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_enroll(self):
        """Check whether it adds an enrollment to an individual and an organization"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        individual = api.enroll(self.ctx,
                                jsmith.uuid, 'Example',
                                from_date=datetime.datetime(1999, 1, 1),
                                to_date=datetime.datetime(2000, 1, 1))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk=jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

    def test_enroll_in_team(self):
        """Check whether it adds an enrollment to an individual and a team"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example Org')
        api.add_team(self.ctx, 'Example Team', organization='Example Org')

        individual = api.enroll(self.ctx,
                                jsmith.uuid, 'Example Team',
                                parent_org='Example Org',
                                from_date=datetime.datetime(1999, 1, 1),
                                to_date=datetime.datetime(2000, 1, 1))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example Team')
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk=jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example Team')
        self.assertEqual(enrollment_db.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

    def test_enroll_using_any_identity_uuid(self):
        """
        Check whether it adds an enrollments to an individual and organization
        using any valid identity uuid
        """
        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        jsmith_alt = api.add_identity(self.ctx, 'mls', email='jsmith@example',
                                      uuid=jsmith.uuid)

        api.add_organization(self.ctx, 'Example')

        individual = api.enroll(self.ctx,
                                jsmith_alt.uuid, 'Example',
                                from_date=datetime.datetime(1999, 1, 1),
                                to_date=datetime.datetime(2000, 1, 1))

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, jsmith.uuid)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk=jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

    def test_enroll_default_ranges(self):
        """Check if it enrolls an individual using default ranges when they are not given"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        individual = api.enroll(self.ctx, jsmith.uuid, 'Example')

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk=jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_enroll_multiple(self):
        """Check if it enrolls different times an individual to an organization"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2005, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))

        # Tests
        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2005, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2006, 1, 1, tzinfo=UTC))

        enrollment = enrollments[2]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_upper_bound(self):
        """Check if enrollments are merged for overlapped ranges"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        # Merge enrollments expanding ending date
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2005, 1, 1),
                   to_date=datetime.datetime(2007, 6, 1))

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

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

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        # Merge enrollments expanding starting date
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2002, 1, 1),
                   to_date=datetime.datetime(2013, 6, 1))

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.start, datetime.datetime(2002, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_both_bounds(self):
        """Check if enrollments are merged for overlapped ranges"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        # Merge enrollments expending both bounds
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_overwrite_defaults(self):
        """Check if enrollments are added ignoring default dates"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx, jsmith.uuid, 'Example')

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Tests
        # Add a new enrollment with non-default dates: upper bound
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   force=True)

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(2004, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Add a new enrollment with non-default dates: lower bound
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   to_date=datetime.datetime(2006, 1, 1),
                   force=True)

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(2004, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2006, 1, 1, tzinfo=UTC))

        # Add a new enrollment with default dates with ignore flag
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1),
                   force=True)

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        # Enrollment dates should not change
        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(2004, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2006, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_not_overwrite_defaults(self):
        """Check if enrollments are added with default dates after setting other dates"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        start_date = datetime.datetime(2004, 1, 1, tzinfo=UTC)
        end_date = datetime.datetime(2006, 1, 1, tzinfo=UTC)
        api.enroll(self.ctx, jsmith.uuid, 'Example',
                   from_date=start_date,
                   to_date=end_date)

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, start_date)
        self.assertEqual(enrollment.end, end_date)

        # Tests
        # Add a new enrollment with a wider range (default dates) without ignore flag
        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        # Enrollment dates should change
        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_enrollments_overwrite_not_allowed(self):
        """
        Check if it fails when trying to set non-default values
        and the `ignore_default` flag is not active.
        """
        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx, jsmith.uuid, 'Example')

        individual_db = Individual.objects.get(mk=jsmith.uuid)

        enrollments = individual_db.enrollments.all()

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = ENROLLMENT_RANGE_INVALID.format(start=r'2004-01-01 00:00:00\+00:00',
                                              end=r'2006-01-01 00:00:00\+00:00',
                                              org='Example')

        # Add a new enrollment with non-default dates
        with self.assertRaisesRegex(DuplicateRangeError, msg):
            api.enroll(self.ctx, jsmith.uuid, 'Example',
                       from_date=datetime.datetime(2004, 1, 1),
                       to_date=datetime.datetime(2006, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        before_dt = datetime_utcnow()
        individual = api.enroll(self.ctx,
                                jsmith.uuid, 'Example',
                                from_date=datetime.datetime(2013, 1, 1),
                                to_date=datetime.datetime(2014, 1, 1))
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_period_invalid(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'start': r'2001-01-01 00:00:00\+00:00',
            'end': r'1999-01-01 00:00:00\+00:00'
        }
        msg = PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(self.ctx,
                       jsmith.uuid, 'Example',
                       from_date=datetime.datetime(2001, 1, 1),
                       to_date=datetime.datetime(1999, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_period_out_of_bounds(self):
        """Check whether enrollments cannot be added giving periods out of bounds"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'type': 'start',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(self.ctx,
                       jsmith.uuid, 'Example',
                       from_date=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(self.ctx,
                       jsmith.uuid, 'Example',
                       to_date=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'start',
            'date': r'1898-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.enroll(self.ctx,
                       jsmith.uuid, 'Example',
                       from_date=datetime.datetime(1898, 12, 31, 23, 59, 59, tzinfo=UTC),
                       to_date=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check if it fails adding enrollments to not existing individuals"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='abcdefghijklmnopqrstuvwxyz')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.enroll(self.ctx, 'abcdefghijklmnopqrstuvwxyz', 'Example')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_organization(self):
        """Check if it fails adding enrollments to not existing organizations"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='Bitergia')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.enroll(self.ctx, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_already_exist_enrollment(self):
        """Test if it raises an exception when the enrollment for the given range already exists"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2010, 1, 1))

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(DuplicateRangeError):
            api.enroll(self.ctx,
                       'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                       from_date=datetime.datetime(1999, 1, 1),
                       to_date=datetime.datetime(2010, 1, 1))

        with self.assertRaises(DuplicateRangeError):
            api.enroll(self.ctx,
                       'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                       from_date=datetime.datetime(2005, 1, 1),
                       to_date=datetime.datetime(2009, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        individual = Individual.objects.get(mk=jsmith.uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=jsmith.uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.enroll(self.ctx,
                       jsmith.uuid, 'Example',
                       from_date=datetime.datetime(1999, 1, 1),
                       to_date=datetime.datetime(2000, 1, 1))

    def test_transaction(self):
        """Check if a transaction is created when adding an enrollment"""

        timestamp = datetime_utcnow()

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_organization(self.ctx, 'Example')

        trx_date = datetime_utcnow()  # Ingnoring the transactions before this datetime

        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'enroll')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        org = api.add_organization(self.ctx, 'Example')

        trx_date = datetime_utcnow()

        api.enroll(self.ctx,
                   jsmith.uuid, 'Example',
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
        self.assertEqual(op1_args['individual'], jsmith.individual.mk)
        self.assertEqual(op1_args['group'], org.name)
        self.assertEqual(op1_args['start'], str(datetime_to_utc(datetime.datetime(1999, 1, 1))))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(datetime.datetime(2000, 1, 1))))


class TestWithdraw(TestCase):
    """Unit tests for withdraw"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')
        api.add_organization(self.ctx, 'Bitergia')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2006, 1, 1),
                   to_date=datetime.datetime(2008, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2009, 1, 1),
                   to_date=datetime.datetime(2011, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jrae@example')
        api.enroll(self.ctx,
                   '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

    def test_withdraw(self):
        """Check whether it withdraws an individual from an organization during the given period"""

        individual = api.withdraw(self.ctx,
                                  'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                                  from_date=datetime.datetime(2007, 1, 1),
                                  to_date=datetime.datetime(2013, 1, 1))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2007, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.group.name, 'Bitergia')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment = enrollments[2]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 3)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2007, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Other enrollments were not deleted
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_withdraw_using_any_identity_uuid(self):
        """
        Check whether it withdraws an individual from an organization
        during the given period using any valid identity uuid
        """
        api.add_identity(self.ctx, 'mls', email='jsmith@example',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        individual = api.withdraw(self.ctx,
                                  'de176236636bc488d31e9f91952ecfc6d976a69e', 'Example',
                                  from_date=datetime.datetime(2007, 1, 1),
                                  to_date=datetime.datetime(2013, 1, 1))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2007, 1, 1, tzinfo=UTC))

        enrollment = enrollments[1]
        self.assertEqual(enrollment.group.name, 'Bitergia')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment = enrollments[2]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 3)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2007, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Other enrollments were not deleted
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_withdraw_default_ranges(self):
        """Check if it withdraws an individual using default ranges when they are not given"""

        individual = api.withdraw(self.ctx, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example')

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Bitergia')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Check database object
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_withdraw_from_team(self):
        """Check whether it withdraws an individual from an organization during the given period"""

        api.add_team(self.ctx, 'Example Team', organization='Example')

        individual = api.enroll(self.ctx,
                                'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                'Example Team',
                                parent_org='Example',
                                from_date=datetime.datetime(2020, 1, 1),
                                to_date=datetime.datetime(2022, 1, 1))

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 5)

        individual = api.withdraw(self.ctx,
                                  'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                  'Example Team',
                                  parent_org='Example',
                                  from_date=datetime.datetime(2020, 1, 1),
                                  to_date=datetime.datetime(2022, 1, 1))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 4)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        individual = api.withdraw(self.ctx, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example')
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_period_invalid(self):
        """Check whether enrollments cannot be withdrawn giving invalid period ranges"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'from_date': r'2001-01-01 00:00:00\+00:00',
            'to_date': r'1999-01-01 00:00:00\+00:00'
        }
        msg = WITHDRAW_PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw(self.ctx,
                         'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
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
            api.withdraw(self.ctx,
                         'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(1899, 12, 31, 23, 59, 59))

        data = {
            'type': 'to_date',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw(self.ctx,
                         'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         to_date=datetime.datetime(2100, 1, 1, 0, 0, 1))

        data = {
            'type': 'from_date',
            'date': r'1898-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.withdraw(self.ctx,
                         'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(1898, 12, 31, 23, 59, 59),
                         to_date=datetime.datetime(1899, 12, 31, 23, 59, 59))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check if it fails withdrawing from not existing individuals"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='abcdefghijklmnopqrstuvwxyz')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.withdraw(self.ctx, 'abcdefghijklmnopqrstuvwxyz', 'Example')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_organization(self):
        """Check if it fails withdrawing from not existing organizations"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='LibreSoft')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.withdraw(self.ctx, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'LibreSoft')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_enrollment(self):
        """Check if it fails withdrawing not existing enrollments"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.withdraw(self.ctx,
                         'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(2050, 1, 1),
                         to_date=datetime.datetime(2060, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'

        individual = Individual.objects.get(mk=uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.withdraw(self.ctx,
                         'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                         from_date=datetime.datetime(2007, 1, 1),
                         to_date=datetime.datetime(2013, 1, 1))

    def test_transaction(self):
        """Check if a transaction is created when deleting an enrollment"""

        timestamp = datetime_utcnow()

        api.withdraw(self.ctx,
                     'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                     from_date=datetime.datetime(2007, 1, 1),
                     to_date=datetime.datetime(2013, 1, 1))

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'withdraw')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting an enrollment"""

        timestamp = datetime_utcnow()

        api.withdraw(self.ctx,
                     'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
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
        self.assertEqual(op1_args['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op1_args['group'], 'Example')
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
        self.assertEqual(op2_args['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op2_args['group'], 'Example')
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
        self.assertEqual(op3_args['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op3_args['group'], 'Example')
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
        self.assertEqual(op4_args['individual'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op4_args['group'], 'Example')
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
        self.assertEqual(op5_args['individual'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op5_args['group'], 'Example')
        self.assertEqual(op5_args['start'], str(datetime_to_utc(datetime.datetime(2013, 1, 1))))
        self.assertEqual(op5_args['end'], str(datetime_to_utc(datetime.datetime(2014, 1, 1))))


class TestUpdateEnrollment(TestCase):
    """Unit tests for update_enrollment"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')
        api.add_organization(self.ctx, 'Bitergia')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2006, 1, 1),
                   to_date=datetime.datetime(2008, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2009, 1, 1),
                   to_date=datetime.datetime(2011, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jrae@example')
        api.enroll(self.ctx,
                   '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

    def test_update_enrollment(self):
        """Check whether it updates an individual's enrollment from an organization during the given period"""

        individual = api.update_enrollment(self.ctx,
                                           '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                           datetime.datetime(2012, 1, 1),
                                           datetime.datetime(2014, 1, 1),
                                           new_from_date=datetime.datetime(2012, 1, 2),
                                           new_to_date=datetime.datetime(2013, 12, 31))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

        # Check database objects
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

        # Other enrollments were not modified
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2008, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2011, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[3]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_using_any_identity_uuid(self):
        """
        Check whether it updates an enrollment from an individual
        during the given period using any valid identity uuid
        """
        api.add_identity(self.ctx, 'mls', email='jsmith@example',
                         uuid='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        individual = api.update_enrollment(self.ctx,
                                           'de176236636bc488d31e9f91952ecfc6d976a69e', 'Example',
                                           datetime.datetime(2012, 1, 1),
                                           datetime.datetime(2014, 1, 1),
                                           new_from_date=datetime.datetime(2012, 1, 2),
                                           new_to_date=datetime.datetime(2013, 12, 31))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

        # Check database objects
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

        # Other enrollments were not modified
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2008, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2011, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[3]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_no_new_to_date(self):
        """Check if the enrollment is updated as expected when one of the new dates is not provided"""

        # Test only with 'newFromDate' date, missing 'newToDate'
        individual = api.update_enrollment(self.ctx,
                                           '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                           datetime.datetime(2012, 1, 1),
                                           datetime.datetime(2014, 1, 1),
                                           new_from_date=datetime.datetime(2012, 1, 2))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Check database objects
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_no_new_from_date(self):
        """Check if the enrollment is updated as expected when one of the new dates is not provided"""

        # Test only with 'newToDate' date, missing 'newFromDate'
        individual = api.update_enrollment(self.ctx,
                                           '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                           datetime.datetime(2012, 1, 1),
                                           datetime.datetime(2014, 1, 1),
                                           new_to_date=datetime.datetime(2013, 12, 31))

        # Tests
        self.assertIsInstance(individual, Individual)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

        # Check database objects
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

    def test_update_both_new_dates_none(self):
        """Check if it fails when no new dates are provided (None)"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, BOTH_NEW_DATES_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2014, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_update_both_new_dates_empty(self):
        """Check if it fails when no new dates are provided (empty)"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, BOTH_NEW_DATES_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2014, 1, 1),
                                  new_from_date='', new_to_date='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_update_empty_former_dates(self):
        """Check if it fails when former dates are empty"""

        # Empty from_date
        with self.assertRaisesRegex(InvalidValueError, FROM_DATE_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  '', datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        # Empty to_date
        with self.assertRaisesRegex(InvalidValueError, TO_DATE_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2014, 1, 1), '',
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        # Both dates empty
        with self.assertRaisesRegex(InvalidValueError, FROM_DATE_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  '', '',
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

    def test_update_none_former_from_date(self):
        """Check if it fails when former from_date is None"""

        with self.assertRaisesRegex(InvalidValueError, FROM_DATE_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  None, datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

    def test_update_none_former_to_date(self):
        """Check if it fails when former to_date is None"""

        with self.assertRaisesRegex(InvalidValueError, TO_DATE_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2014, 1, 1), None,
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

    def test_update_none_former_dates(self):
        """Check if it fails when both former dates are None"""

        with self.assertRaisesRegex(InvalidValueError, FROM_DATE_NONE_OR_EMPTY_ERROR):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  None, None,
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        individual = api.update_enrollment(self.ctx,
                                           '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                           datetime.datetime(2012, 1, 1),
                                           datetime.datetime(2014, 1, 1),
                                           new_from_date=datetime.datetime(2012, 1, 2),
                                           new_to_date=datetime.datetime(2013, 12, 31))
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_period_invalid(self):
        """Check whether enrollments cannot be updated giving invalid period ranges"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'from_date': r'2001-01-01 00:00:00',
            'to_date': r'1999-01-01 00:00:00'
        }
        msg = UPDATE_ENROLLMENT_PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2001, 1, 1),
                                  datetime.datetime(1999, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        msg = UPDATE_ENROLLMENT_NEW_PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2001, 1, 1),
                                  new_to_date=datetime.datetime(1999, 1, 1))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_period_out_of_bounds(self):
        """Check whether enrollments cannot be updated giving periods out of bounds"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        data = {
            'type': 'from_date',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(1899, 12, 31, 23, 59, 59),
                                  datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        data = {
            'type': 'to_date',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2100, 1, 1, 0, 0, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        data = {
            'type': 'from_date',
            'date': r'1898-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(InvalidValueError, msg):
            individual = api.update_enrollment(self.ctx,
                                               '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                               datetime.datetime(1898, 12, 31, 23, 59, 59),
                                               datetime.datetime(1899, 12, 31, 23, 59, 59),
                                               new_from_date=datetime.datetime(2012, 1, 2),
                                               new_to_date=datetime.datetime(2013, 12, 31))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check if it fails updating from not existing individuals"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='abcdefghijklmnopqrstuvwxyz')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.update_enrollment(self.ctx,
                                  'abcdefghijklmnopqrstuvwxyz', 'Example',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_organization(self):
        """Check if it fails updating from not existing organizations"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        msg = NOT_FOUND_ERROR.format(entity='LibreSoft')

        with self.assertRaisesRegex(NotFoundError, msg):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'LibreSoft',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_enrollment(self):
        """Check if it fails updating not existing enrollments"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2050, 1, 1),
                                  datetime.datetime(2060, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        uuid = '3283e58cef2b80007aa1dfc16f6dd20ace1aee96'

        individual = Individual.objects.get(mk=uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.update_enrollment(self.ctx,
                                  '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                                  datetime.datetime(2012, 1, 1),
                                  datetime.datetime(2014, 1, 1),
                                  new_from_date=datetime.datetime(2012, 1, 2),
                                  new_to_date=datetime.datetime(2013, 12, 31))

    def test_transaction(self):
        """Check if a transaction is created when updating an enrollment"""

        timestamp = datetime_utcnow()

        api.update_enrollment(self.ctx,
                              '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                              datetime.datetime(2012, 1, 1),
                              datetime.datetime(2014, 1, 1),
                              new_from_date=datetime.datetime(2012, 1, 2),
                              new_to_date=datetime.datetime(2013, 12, 31))

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 3)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'update_enrollment')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

        trx = transactions[1]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'withdraw')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

        trx = transactions[2]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'enroll')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when updating an enrollment"""

        timestamp = datetime_utcnow()

        api.update_enrollment(self.ctx,
                              '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                              datetime.datetime(2012, 1, 1),
                              datetime.datetime(2014, 1, 1),
                              new_from_date=datetime.datetime(2012, 1, 2),
                              new_to_date=datetime.datetime(2013, 12, 31))

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 3)

        trx = transactions[0]
        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 0)

        trx = transactions[1]
        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'enrollment')
        self.assertEqual(op1.target, '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 4)
        self.assertEqual(op1_args['mk'], '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        self.assertEqual(op1_args['group'], 'Example')
        self.assertEqual(op1_args['start'], str(datetime_to_utc(datetime.datetime(2012, 1, 1))))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(datetime.datetime(2014, 1, 1))))

        trx = transactions[2]
        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op2 = operations[0]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op2.entity_type, 'enrollment')
        self.assertEqual(op2.target, '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 4)
        self.assertEqual(op2_args['individual'], '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        self.assertEqual(op2_args['group'], 'Example')
        self.assertEqual(op2_args['start'], str(datetime_to_utc(datetime.datetime(2012, 1, 2))))
        self.assertEqual(op2_args['end'], str(datetime_to_utc(datetime.datetime(2013, 12, 31))))


class TestMergeIndividuals(TestCase):
    """Unit tests for merge"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')
        api.add_organization(self.ctx, 'Bitergia')

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_identity(self.ctx,
                         'git',
                         email='jsmith-git@example',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith@bitergia')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith-phab@bitergia',
                         uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        api.enroll(self.ctx,
                   'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', 'Bitergia',
                   from_date=datetime.datetime(2017, 6, 2),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith-local@bitergia')
        api.enroll(self.ctx,
                   'a11604f983f8786913e6d1449f2eac1618b0b2ee', 'Bitergia',
                   from_date=datetime.datetime(2017, 4, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith-internship@example')
        api.enroll(self.ctx,
                   '4dd0fdcd06a6be6f0b7893bf1afcef3e3191753a', 'Example',
                   from_date=datetime.datetime(2015, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx, 'scm', email='john.doe@bitergia')
        api.enroll(self.ctx,
                   'ebe8f55d8988fce02997389d530579ad939f1698', 'Bitergia',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2015, 1, 1))
        api.enroll(self.ctx,
                   'ebe8f55d8988fce02997389d530579ad939f1698', 'Example',
                   from_date=datetime.datetime(2015, 1, 2),
                   to_date=datetime.datetime(2016, 12, 31))
        api.enroll(self.ctx,
                   'ebe8f55d8988fce02997389d530579ad939f1698', 'Bitergia',
                   from_date=datetime.datetime(2017, 1, 1),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx, 'scm', email='john.doe@biterg.io')
        api.enroll(self.ctx, '437386d9d072320387d0c802f772a5401cddc3e6', 'Bitergia')

        api.add_identity(self.ctx, 'phabricator', email='jsmith@example-phab')
        api.enroll(self.ctx,
                   'f29b50520d35d046db0d53b301418ad9aa16e7e3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith@libresoft')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith2@libresoft',
                         uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith3@libresoft',
                         uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.update_profile(self.ctx,
                           uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e',
                           name='John Smith',
                           email='jsmith@profile-email',
                           is_bot=False,
                           country_code='US')

    def test_merge_identities(self):
        """Check whether it merges two individuals, merging their ids, enrollments and profiles"""

        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith',
                           email='jsmith@example',
                           gender='male',
                           gender_acc=75)

        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed',
                           name='John Smith',
                           email='jsmith@profile-email',
                           is_bot=True,
                           country_code='US')

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                               to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id2.email, 'jsmith-phab@bitergia')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id3.email, 'jsmith@bitergia')
        self.assertEqual(id3.source, 'scm')

        id4 = identities[3]
        self.assertEqual(id4.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id4.email, 'jsmith@example')
        self.assertEqual(id4.source, 'scm')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_multiple_individuals(self):
        """Check whether it merges more than two individuals, merging their ids, enrollments and profiles"""

        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith',
                           email='jsmith@example',
                           gender='male',
                           gender_acc=75)

        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed',
                           name='John Smith',
                           email='jsmith@profile-email',
                           is_bot=True,
                           country_code='US')

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                                           '1c13fec7a328201fc6a230fe43eb81df0e20626e'],
                               to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 7)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3.email, 'jsmith-git@example')
        self.assertEqual(id3.source, 'git')

        id4 = identities[3]
        self.assertEqual(id4.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4.email, 'jsmith-phab@bitergia')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.uuid, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5.email, 'jsmith2@libresoft')
        self.assertEqual(id5.source, 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id6.email, 'jsmith@bitergia')
        self.assertEqual(id6.source, 'scm')

        id7 = identities[6]
        self.assertEqual(id7.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id7.email, 'jsmith@example')
        self.assertEqual(id7.source, 'scm')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_multiple_individuals_from_any_uuid(self):
        """
        Check whether it merges more than two individuals
        using any valid identity uuid
        """
        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith',
                           email='jsmith@example',
                           gender='male',
                           gender_acc=75)

        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed',
                           name='John Smith',
                           email='jsmith@profile-email',
                           is_bot=True,
                           country_code='US')

        individual = api.merge(self.ctx,
                               from_uuids=['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6',
                                           'c2f5aa44e920b4fbe3cd36894b18e80a2606deba'],
                               to_uuid='9225e296be341c20c11c4bae76df4190a5c4a918')

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 7)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3.email, 'jsmith-git@example')
        self.assertEqual(id3.source, 'git')

        id4 = identities[3]
        self.assertEqual(id4.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4.email, 'jsmith-phab@bitergia')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.uuid, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5.email, 'jsmith2@libresoft')
        self.assertEqual(id5.source, 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id6.email, 'jsmith@bitergia')
        self.assertEqual(id6.source, 'scm')

        id7 = identities[6]
        self.assertEqual(id7.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id7.email, 'jsmith@example')
        self.assertEqual(id7.source, 'scm')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_non_existing_from_uuids(self):
        """Check if it fails merging individuals when source uuids is `None` or an empty list"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUIDS_NONE_OR_EMPTY_ERROR):
            api.merge(self.ctx,
                      from_uuids=[],
                      to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_from_uuid(self):
        """Check if it fails merging individuals when source uuid is `None` or empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_UUID_NONE_OR_EMPTY_ERROR):
            api.merge(self.ctx,
                      from_uuids=[''],
                      to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_to_uuid(self):
        """Check if it fails merging two individuals when destination uuid is `None` or empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, TO_UUID_NONE_OR_EMPTY_ERROR):
            api.merge(self.ctx,
                      from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                      to_uuid='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_from_uuid_to_uuid_equal(self):
        """Check if it fails merging two individuals when they are equal"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        error = FROM_UUID_TO_UUID_EQUAL_ERROR.format(to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        with self.assertRaisesRegex(EqualIndividualError, error):
            api.merge(self.ctx,
                      from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                      to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_moved_enrollments(self):
        """Check whether it merges two individuals, merging their enrollments with multiple periods"""

        individual = api.merge(self.ctx,
                               from_uuids=['ebe8f55d8988fce02997389d530579ad939f1698'],
                               to_uuid='437386d9d072320387d0c802f772a5401cddc3e6')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Bitergia')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2015, 1, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Example')
        self.assertEqual(rol2.start, datetime.datetime(2015, 1, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2016, 12, 31, tzinfo=UTC))

        rol3 = enrollments[2]
        self.assertEqual(rol3.group.name, 'Bitergia')
        self.assertEqual(rol3.start, datetime.datetime(2017, 1, 1, tzinfo=UTC))
        self.assertEqual(rol3.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_overlapping_enrollments(self):
        """Check whether it merges two individuals having overlapping enrollments"""

        individual = api.merge(self.ctx,
                               from_uuids=['4dd0fdcd06a6be6f0b7893bf1afcef3e3191753a'],
                               to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertEqual(rol.group.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(2015, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

    def test_overlapping_enrollments_different_orgs(self):
        """Check whether it merges two individuals having overlapping periods in different organizations"""

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                               to_uuid='a11604f983f8786913e6d1449f2eac1618b0b2ee')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 4, 1, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_duplicate_enrollments(self):
        """Check whether it merges two individuals having duplicate enrollments"""

        individual = api.merge(self.ctx,
                               from_uuids=['f29b50520d35d046db0d53b301418ad9aa16e7e3'],
                               to_uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertEqual(rol.group.name, 'Example')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()

        individual1 = api.add_identity(self.ctx,
                                       'scm',
                                       email='john.doe@example')
        api.add_identity(self.ctx,
                         'git',
                         email='john.doe@example',
                         uuid='b6bee805956c03699b59e15175261f85a10d43f3')

        individual2 = api.add_identity(self.ctx,
                                       'scm',
                                       email='jdoe@example')
        api.add_identity(self.ctx,
                         'git',
                         email='jdoe@example',
                         uuid='a033ed6d1498a58f7cf91bd56e3c746d7ddb9874')

        after_dt = datetime_utcnow()

        indv1 = Individual.objects.get(mk=individual1.uuid)
        indv2 = Individual.objects.get(mk=individual2.uuid)

        self.assertLessEqual(before_dt, indv1.last_modified)
        self.assertGreaterEqual(after_dt, indv1.last_modified)

        self.assertLessEqual(before_dt, indv2.last_modified)
        self.assertGreaterEqual(after_dt, indv2.last_modified)

        # Merge identities
        before_merge_dt = datetime_utcnow()
        indv = api.merge(self.ctx,
                         from_uuids=['b6bee805956c03699b59e15175261f85a10d43f3'],
                         to_uuid='a033ed6d1498a58f7cf91bd56e3c746d7ddb9874')
        after_merge_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, indv.last_modified)
        self.assertLessEqual(after_dt, indv.last_modified)
        self.assertLessEqual(before_merge_dt, indv.last_modified)
        self.assertGreaterEqual(after_merge_dt, indv.last_modified)

        identities = indv.identities.all()

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
        """Check whether it merges two individuals, merging their profiles"""

        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', gender_acc=75)
        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email', is_bot=True, country_code='US')

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                               to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
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
        """Check whether it merges two individuals when the profile from the source identity is empty"""

        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email')

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                               to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, None)
        self.assertEqual(profile.country_id, None)
        self.assertEqual(profile.is_bot, False)

    def test_empty_destination_profile(self):
        """Check whether it merges two individuals when the profile from the destination identity is empty"""

        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', country_code='US')

        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed',
                           name='', email='', gender='', country_code='')

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                               to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
        self.assertEqual(profile.name, 'J. Smith')
        self.assertEqual(profile.email, 'jsmith@example')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.country_id, 'US')
        self.assertEqual(profile.is_bot, False)

    def test_empty_profiles(self):
        """Check whether it merges two individuals when both of their profiles are empty"""

        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='', email='', gender='', country_code='')

        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed',
                           name='', email='', gender='', country_code='')

        individual = api.merge(self.ctx,
                               from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                               to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)
        self.assertEqual(profile.gender, None)
        self.assertEqual(profile.country_id, None)
        self.assertEqual(profile.is_bot, False)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        from_uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        to_uuid = 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'

        individual = Individual.objects.get(mk=from_uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=from_uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.merge(self.ctx,
                      from_uuids=[from_uuid],
                      to_uuid=to_uuid)

    def test_transaction(self):
        """Check if a transaction is created when merging identities"""

        timestamp = datetime_utcnow()

        api.merge(self.ctx,
                  from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
                  to_uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'merge')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when merging identities"""

        timestamp = datetime_utcnow()

        api.merge(self.ctx,
                  from_uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
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
        self.assertEqual(op1_args['individual'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
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
        self.assertEqual(op2_args['individual'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
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
        self.assertEqual(op3_args['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op3_args['group'], 'Example')
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
        self.assertEqual(op4_args['mk'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op4_args['group'], 'Bitergia')
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
        self.assertEqual(op5_args['individual'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op5_args['group'], 'Example')
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
        self.assertEqual(op6_args['individual'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(op6_args['group'], 'Bitergia')
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
        self.assertEqual(op7_args['individual'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        op8 = operations[7]
        self.assertIsInstance(op8, Operation)
        self.assertEqual(op8.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op8.entity_type, 'individual')
        self.assertEqual(op8.target, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(op8.trx, trx)
        self.assertGreater(op8.timestamp, timestamp)

        op8_args = json.loads(op8.args)
        self.assertEqual(len(op8_args), 1)
        self.assertEqual(op8_args['individual'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')


class TestUnmergeIdentities(TestCase):
    """Unit tests for unmerge_identities"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')
        api.add_organization(self.ctx, 'Bitergia')

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_identity(self.ctx,
                         'git',
                         email='jsmith-git@example',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='John Smith',
                           email='jsmith@profile-email', is_bot=False, country_code='US')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith@bitergia')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith-phab@bitergia',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia',
                   from_date=datetime.datetime(2017, 6, 2),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx,
                         'scm',
                         email='jsmith@libresoft',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith2@libresoft',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith3@libresoft',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

    def test_unmerge_identities(self):
        """Check whether it unmerges one identity from its parent individual"""

        individuals = api.unmerge_identities(self.ctx,
                                             uuids=['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6'])

        # Tests
        self.assertEqual(len(individuals), 1)

        individual = individuals[0]
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        profile = individual.profile

        self.assertEqual(profile.email, 'jsmith-git@example')
        self.assertEqual(profile.is_bot, False)
        self.assertIsNone(profile.name)
        self.assertIsNone(profile.gender)
        self.assertIsNone(profile.gender_acc)

        self.assertIsNone(profile.country_id)
        self.assertIsNone(profile.country)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 0)

        # Testing everything remained the same in the old parent individual

        former_individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        self.assertIsInstance(former_individual, Individual)
        self.assertEqual(former_individual.mk, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        profile = former_individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.is_bot, False)
        self.assertIsNone(profile.gender)
        self.assertIsNone(profile.gender_acc)

        identities = former_individual.identities.all()
        self.assertEqual(len(identities), 5)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id3.email, 'jsmith-phab@bitergia')
        self.assertEqual(id3.source, 'phabricator')

        id4 = identities[3]
        self.assertEqual(id4.uuid, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id4.email, 'jsmith2@libresoft')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id5.email, 'jsmith@example')
        self.assertEqual(id5.source, 'scm')

        enrollments = former_individual.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_unmerge_multiple_identities(self):
        """Check whether it unmerges more than two identities"""

        individuals = api.unmerge_identities(self.ctx,
                                             uuids=['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6',
                                                    '31581d7c6b039318e9048c4d8571666c26a5622b'])

        # Tests
        self.assertEqual(len(individuals), 2)

        individual = individuals[0]
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        profile = individual.profile
        self.assertEqual(profile.email, 'jsmith-git@example')
        self.assertEqual(profile.is_bot, False)
        self.assertIsNone(profile.name)
        self.assertIsNone(profile.gender)
        self.assertIsNone(profile.gender_acc)

        self.assertIsNone(profile.country_id)
        self.assertIsNone(profile.country)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 0)

        individual = individuals[1]
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, '31581d7c6b039318e9048c4d8571666c26a5622b')

        profile = individual.profile
        self.assertEqual(profile.email, 'jsmith3@libresoft')
        self.assertEqual(profile.is_bot, False)
        self.assertIsNone(profile.name)
        self.assertIsNone(profile.gender)
        self.assertIsNone(profile.gender_acc)

        self.assertIsNone(profile.country_id)
        self.assertIsNone(profile.country)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id1.email, 'jsmith3@libresoft')
        self.assertEqual(id1.source, 'phabricator')

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 0)

        # Testing everything remained the same in the old parent individual

        former_individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        self.assertIsInstance(former_individual, Individual)
        self.assertEqual(former_individual.mk, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        profile = former_individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.is_bot, False)
        self.assertIsNone(profile.gender)
        self.assertIsNone(profile.gender_acc)

        identities = former_individual.identities.all()
        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id2.email, 'jsmith-phab@bitergia')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id3.email, 'jsmith2@libresoft')
        self.assertEqual(id3.source, 'phabricator')

        id4 = identities[3]
        self.assertEqual(id4.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id4.email, 'jsmith@example')
        self.assertEqual(id4.source, 'scm')

        enrollments = former_individual.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_uuid_from_individual(self):
        """Check if it ignores when the identity to unmerge is the same as the parent individual"""

        individuals = api.unmerge_identities(self.ctx,
                                             uuids=['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'])

        self.assertEqual(len(individuals), 1)

        individual = individuals[0]
        self.assertEqual(individual.mk, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        identities = individual.identities.all()
        self.assertEqual(len(identities), 6)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3.email, 'jsmith-git@example')
        self.assertEqual(id3.source, 'git')

        id4 = identities[3]
        self.assertEqual(id4.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4.email, 'jsmith-phab@bitergia')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.uuid, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5.email, 'jsmith2@libresoft')
        self.assertEqual(id5.source, 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id6.email, 'jsmith@example')
        self.assertEqual(id6.source, 'scm')

    def test_non_existing_uuids(self):
        """Check if it fails when source `uuids` field is `None` or an empty list"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, UUIDS_NONE_OR_EMPTY_ERROR):
            api.unmerge_identities(self.ctx,
                                   uuids=[])

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_non_existing_uuid(self):
        """Check if it fails when any `uuid` is `None` or empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.unmerge_identities(self.ctx,
                                   uuids=[''])

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()

        individual1 = api.add_identity(self.ctx,
                                       'scm',
                                       email='john.doe@example')
        api.add_identity(self.ctx,
                         'git',
                         email='john.doe@example',
                         uuid='b6bee805956c03699b59e15175261f85a10d43f3')

        after_dt = datetime_utcnow()

        indv1 = Individual.objects.get(mk=individual1.uuid)

        self.assertLessEqual(before_dt, indv1.last_modified)
        self.assertGreaterEqual(after_dt, indv1.last_modified)

        # Unmerge identities
        before_unmerge_dt = datetime_utcnow()
        indvs = api.unmerge_identities(self.ctx,
                                       uuids=['df9af14b5aeb89d0b536a825039d3042eb4e4c27'])
        after_unmerge_dt = datetime_utcnow()

        # Check new individual
        indv = indvs[0]
        self.assertLessEqual(before_dt, indv.last_modified)
        self.assertLessEqual(after_dt, indv.last_modified)
        self.assertLessEqual(before_unmerge_dt, indv.last_modified)
        self.assertGreaterEqual(after_unmerge_dt, indv.last_modified)

        identities = indv.identities.all()

        id1 = identities[0]

        # Unmerged (moved) identities were updated
        self.assertLessEqual(before_dt, id1.last_modified)
        self.assertLessEqual(after_dt, id1.last_modified)
        self.assertLessEqual(before_unmerge_dt, id1.last_modified)
        self.assertGreaterEqual(after_unmerge_dt, id1.last_modified)

        # Check former parent individual
        indv = Individual.objects.get(mk=individual1.uuid)
        self.assertLessEqual(before_dt, indv.last_modified)
        self.assertLessEqual(after_dt, indv.last_modified)
        self.assertLessEqual(before_unmerge_dt, indv.last_modified)
        self.assertGreaterEqual(after_unmerge_dt, indv.last_modified)

        identities = indv.identities.all()

        # Not unmerged (moved) identities were not modified
        id1 = identities[0]

        self.assertLessEqual(before_dt, id1.last_modified)
        self.assertGreaterEqual(after_dt, id1.last_modified)
        self.assertGreaterEqual(before_unmerge_dt, id1.last_modified)
        self.assertGreaterEqual(after_unmerge_dt, id1.last_modified)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        parent_uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        uuid = '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6'

        individual = Individual.objects.get(mk=parent_uuid)
        individual.is_locked = True
        individual.save()

        msg = UUID_LOCKED_ERROR.format(uuid=parent_uuid)
        with self.assertRaisesRegex(LockedIdentityError, msg):
            api.unmerge_identities(self.ctx,
                                   uuids=[uuid])

    def test_transaction(self):
        """Check if a transaction is created when unmerging identities"""

        timestamp = datetime_utcnow()

        api.unmerge_identities(self.ctx,
                               uuids=['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6'])

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'unmerge_identities')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when unmerging identities"""

        timestamp = datetime_utcnow()

        api.unmerge_identities(self.ctx,
                               uuids=['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6'])

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 3)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.target, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['mk'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        op2 = operations[1]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op2.entity_type, 'profile')
        self.assertEqual(op2.target, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 3)
        self.assertEqual(op2_args['individual'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(op2_args['email'], 'jsmith-git@example')
        self.assertIsNone(op2_args['name'])

        op3 = operations[2]
        self.assertIsInstance(op3, Operation)
        self.assertEqual(op3.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op3.entity_type, 'identity')
        self.assertEqual(op3.target, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(op3.trx, trx)
        self.assertGreater(op3.timestamp, timestamp)

        op3_args = json.loads(op3.args)
        self.assertEqual(len(op3_args), 2)
        self.assertEqual(op3_args['identity'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(op3_args['individual'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')


class TestMergeOrganizations(TestCase):
    """Unit tests for merge"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        from_org = api.add_organization(self.ctx, 'Example')
        to_org = api.add_organization(self.ctx, 'Bitergia')

        api.add_domain(self.ctx,
                       organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)
        api.add_domain(self.ctx,
                       organization='Bitergia',
                       domain_name='bitergia.com',
                       is_top_domain=True)

        Team.add_root(name='Example team', parent_org=from_org)
        Team.add_root(name='Bitergia team', parent_org=to_org)

        self.example_indv = api.add_identity(self.ctx, 'git', email='jsmith@example')
        self.bitergia_indv = api.add_identity(self.ctx, 'scm', email='jsmith@bitergia')

        api.enroll(self.ctx,
                   self.example_indv.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(self.ctx,
                   self.bitergia_indv.uuid, 'Bitergia',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))

        api.add_alias(self.ctx, organization='Example', name='Example Inc.')
        api.add_alias(self.ctx, organization='Example', name='Example Ltd.')
        api.add_alias(self.ctx, organization='Bitergia', name='Bitergium')

    def test_merge_organizations(self):
        """Check whether it merges two organizations, merging their domains, teams and enrollments"""

        organization = api.merge_organizations(self.ctx,
                               from_org='Example',
                               to_org='Bitergia')

        # Tests
        self.assertIsInstance(organization, Organization)
        self.assertEqual(organization.name, 'Bitergia')

        organizations_db = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations_db), 0)

        organizations_db = Organization.objects.filter(name='Bitergia')
        self.assertEqual(len(organizations_db), 1)

        organization = Organization.objects.get(name='Bitergia')

        domains = organization.domains.all()
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0].domain, 'bitergia.com')
        self.assertEqual(domains[1].domain, 'example.com')

        teams = organization.teams.all()
        self.assertEqual(len(teams), 2)
        self.assertEqual(teams[0].name, 'Example team')
        self.assertEqual(teams[1].name, 'Bitergia team')

        enrollments = organization.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.individual.mk, self.bitergia_indv.uuid)

        enrollment = enrollments[1]
        self.assertEqual(enrollment.individual.mk, self.example_indv.uuid)

        aliases = organization.aliases.all()
        self.assertEqual(len(aliases), 4)
        self.assertEqual(aliases[0].alias, 'Bitergium')
        self.assertEqual(aliases[1].alias, 'Example')
        self.assertEqual(aliases[2].alias, 'Example Inc.')
        self.assertEqual(aliases[3].alias, 'Example Ltd.')

    def test_from_org_to_org_equal(self):
        """Check if it fails merging two organizations when they are equal"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FROM_ORG_TO_ORG_EQUAL_ERROR):
            api.merge_organizations(self.ctx,
                                    from_org='Bitergia',
                                    to_org='Bitergia')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_duplicate_enrollments(self):
        """Check it does not duplicate enrollments when two organizations are merged"""

        individual = api.add_identity(self.ctx, 'abc', email='duplicate@example')

        api.enroll(self.ctx,
                   individual.uuid, 'Example',
                   from_date=datetime.datetime(2003, 1, 1),
                   to_date=datetime.datetime(2004, 1, 1))
        api.enroll(self.ctx,
                   individual.uuid, 'Bitergia',
                   from_date=datetime.datetime(2003, 1, 1),
                   to_date=datetime.datetime(2004, 1, 1))

        organization = api.merge_organizations(self.ctx,
                                               from_org='Example',
                                               to_org='Bitergia')

        organizations_db = Organization.objects.filter(name='Example')
        self.assertEqual(len(organizations_db), 0)

        organizations_db = Organization.objects.filter(name='Bitergia')
        self.assertEqual(len(organizations_db), 1)

        organization = Organization.objects.get(name='Bitergia')
        enrollments = organization.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.individual.mk, self.bitergia_indv.uuid)

        enrollment = enrollments[1]
        self.assertEqual(enrollment.individual.mk, self.example_indv.uuid)

        enrollment = enrollments[2]
        self.assertEqual(enrollment.individual.mk, individual.uuid)

    def test_transaction(self):
        """Check if a transaction is created when merging organizations"""

        timestamp = datetime_utcnow()

        api.merge_organizations(self.ctx,
                                from_org='Example',
                                to_org='Bitergia')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'merge_organizations')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when merging organizations"""

        timestamp = datetime_utcnow()

        api.merge_organizations(self.ctx,
                                from_org='Example',
                                to_org='Bitergia')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 7)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'domain')
        self.assertEqual(op1.target, 'example.com')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['domain'], 'example.com')
        self.assertEqual(op1_args['organization'], 'Bitergia')

        op2 = operations[1]
        self.assertIsInstance(op2, Operation)
        self.assertEqual(op2.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op2.entity_type, 'team')
        self.assertEqual(op2.target, 'Example team')
        self.assertEqual(op2.trx, trx)
        self.assertGreater(op2.timestamp, timestamp)

        op2_args = json.loads(op2.args)
        self.assertEqual(len(op2_args), 2)
        self.assertEqual(op2_args['team'], 'Example team')
        self.assertEqual(op2_args['organization'], 'Bitergia')

        op3 = operations[2]
        self.assertIsInstance(op3, Operation)
        self.assertEqual(op3.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op3.entity_type, 'enrollment')
        self.assertEqual(op3.target, self.example_indv.uuid)
        self.assertEqual(op3.trx, trx)
        self.assertGreater(op3.timestamp, timestamp)

        op3_args = json.loads(op3.args)
        self.assertEqual(len(op3_args), 4)
        self.assertEqual(op3_args['individual'], self.example_indv.uuid)
        self.assertEqual(op3_args['group'], 'Bitergia')
        self.assertEqual(op3_args['start'], '1999-01-01 00:00:00+00:00')
        self.assertEqual(op3_args['end'], '2000-01-01 00:00:00+00:00')

        op4 = operations[3]
        self.assertIsInstance(op4, Operation)
        self.assertEqual(op4.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op4.entity_type, 'alias')
        self.assertEqual(op4.target, 'Example Inc.')
        self.assertEqual(op4.trx, trx)
        self.assertGreater(op4.timestamp, timestamp)

        op4_args = json.loads(op4.args)
        self.assertEqual(len(op4_args), 2)
        self.assertEqual(op4_args['alias'], 'Example Inc.')
        self.assertEqual(op4_args['organization'], 'Bitergia')

        op5 = operations[4]
        self.assertIsInstance(op5, Operation)
        self.assertEqual(op5.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op5.entity_type, 'alias')
        self.assertEqual(op5.target, 'Example Ltd.')
        self.assertEqual(op5.trx, trx)
        self.assertGreater(op5.timestamp, timestamp)

        op5_args = json.loads(op5.args)
        self.assertEqual(len(op5_args), 2)
        self.assertEqual(op5_args['alias'], 'Example Ltd.')
        self.assertEqual(op5_args['organization'], 'Bitergia')

        op6 = operations[5]
        self.assertIsInstance(op6, Operation)
        self.assertEqual(op6.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op6.entity_type, 'organization')
        self.assertEqual(op6.target, 'Example')
        self.assertEqual(op6.trx, trx)
        self.assertGreater(op6.timestamp, timestamp)

        op6_args = json.loads(op6.args)
        self.assertEqual(len(op6_args), 1)
        self.assertEqual(op6_args['organization'], 'Example')

        op7 = operations[6]
        self.assertIsInstance(op7, Operation)
        self.assertEqual(op7.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op7.entity_type, 'alias')
        self.assertEqual(op7.target, 'Bitergia')
        self.assertEqual(op7.trx, trx)
        self.assertGreater(op7.timestamp, timestamp)

        op7_args = json.loads(op7.args)
        self.assertEqual(len(op7_args), 2)
        self.assertEqual(op7_args['organization'], 'Bitergia')
        self.assertEqual(op7_args['name'], 'Example')


class TestUpdateScheduledTask(TestCase):
    """Unit tests for update_scheduled_task"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.task_affiliate = ScheduledTask.objects.create(job_type='affiliate', interval=1)
        self.task_unify = ScheduledTask.objects.create(job_type='unify', interval=2, args={'criteria': ['name', 'email']})

    def test_update_scheduled_task(self):
        """Check if it updates a task"""

        task = api.update_scheduled_task(self.ctx,
                                         self.task_affiliate.id,
                                         interval=3,
                                         params={'uuids': ['abcd1234']})
        # Tests
        self.assertIsInstance(task, ScheduledTask)

        self.assertEqual(task.job_type, 'affiliate')
        self.assertEqual(task.interval, 3)
        self.assertDictEqual(task.args, {'uuids': ['abcd1234']})

        # Check database object
        task_db = ScheduledTask.objects.get(id=task.id)
        self.assertEqual(task, task_db)

    def test_update_task_only_interval(self):
        """Check if it updates a task interval"""

        task = api.update_scheduled_task(self.ctx,
                                         self.task_affiliate.id,
                                         interval=4)
        # Tests
        self.assertIsInstance(task, ScheduledTask)

        self.assertEqual(task.job_type, 'affiliate')
        self.assertEqual(task.interval, 4)
        self.assertIsNone(task.args)

        # Check database object
        task_db = ScheduledTask.objects.get(id=task.id)
        self.assertEqual(task, task_db)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        task = api.update_scheduled_task(self.ctx,
                                         self.task_affiliate.id,
                                         interval=4)
        after_dt = datetime_utcnow()

        self.assertLessEqual(before_dt, task.last_modified)
        self.assertGreaterEqual(after_dt, task.last_modified)

    def test_non_existing_task(self):
        """Check if it fails updating a task that does not exist"""

        with self.assertRaises(NotFoundError):
            api.update_scheduled_task(self.ctx,
                                      999,
                                      interval=4)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.all()
        self.assertEqual(len(transactions), 0)

    def test_invalid_interval(self):
        """Check wrong interval is not valid"""

        with self.assertRaisesRegex(InvalidValueError, INTERVAL_MUST_BE_NUMBER_ERROR):
            api.update_scheduled_task(self.ctx,
                                      self.task_affiliate.id,
                                      interval='5')
        with self.assertRaisesRegex(InvalidValueError, INTERVAL_MUST_BE_NUMBER_ERROR):
            api.update_scheduled_task(self.ctx,
                                      self.task_affiliate.id,
                                      interval=-1)

            # Check if there are no transactions created when there is an error
            transactions = Transaction.objects.all()
            self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when updating a task"""

        timestamp = datetime_utcnow()

        api.update_scheduled_task(self.ctx,
                                  self.task_affiliate.id,
                                  interval=60)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'update_scheduled_task')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when updating a task"""

        timestamp = datetime_utcnow()

        api.update_scheduled_task(self.ctx,
                                  self.task_affiliate.id,
                                  interval=4,
                                  params={'uuids': ['abcd1234']})

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'scheduled_task')
        self.assertEqual(op1.target, str(self.task_affiliate.id))
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 3)
        self.assertEqual(op1_args['task'], str(self.task_affiliate.id))
        self.assertEqual(op1_args['interval'], 4)
        self.assertDictEqual(op1_args['params'], {'uuids': ['abcd1234']})


class TestDeleteScheduledTask(TestCase):
    """Unit tests for delete_scheduled_task"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.task_foo = ScheduledTask.objects.create(job_type='foo', interval=0)
        self.task_bar = ScheduledTask.objects.create(job_type='bar', interval=1)
        self.task_baz = ScheduledTask.objects.create(job_type='baz', interval=2)

    def test_delete_task(self):
        """Check whether it deletes a task"""

        # Check initial status
        tasks = ScheduledTask.objects.all()
        self.assertEqual(len(tasks), 3)

        # Delete a task
        api.delete_scheduled_task(self.ctx, self.task_foo.id)

        # Check result
        tasks = ScheduledTask.objects.filter(job_type='foo')
        self.assertEqual(len(tasks), 0)

        # Check remaining tasks
        tasks = ScheduledTask.objects.all()
        self.assertEqual(len(tasks), 2)

        with self.assertRaises(ObjectDoesNotExist):
            ScheduledTask.objects.get(id=self.task_foo.id)

    def test_non_existing_task_id(self):
        """Check if it fails removing a task that does not exists"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaises(NotFoundError):
            api.delete_scheduled_task(self.ctx, 999)

        # It should raise an error when the registry is empty
        ScheduledTask.objects.all().delete()
        self.assertEqual(len(ScheduledTask.objects.all()), 0)

        with self.assertRaises(NotFoundError):
            api.delete_scheduled_task(self.ctx, 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_none_task_id(self):
        """Check whether tasks cannot be removed when giving a None id"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FORMAT_NONE_OR_EMPTY_ERROR.format('task_id')):
            api.delete_scheduled_task(self.ctx, None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_empty_task_id(self):
        """Check whether tasks cannot be removed when giving an empty id"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, FORMAT_NONE_OR_EMPTY_ERROR.format('task_id')):
            api.delete_scheduled_task(self.ctx, '')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting a task"""

        timestamp = datetime_utcnow()

        api.delete_scheduled_task(self.ctx, self.task_foo.id)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_scheduled_task')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting a task"""

        timestamp = datetime_utcnow()

        api.delete_scheduled_task(self.ctx, self.task_foo.id)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'scheduled_task')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, str(self.task_foo.id))
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['task'], str(self.task_foo.id))


class TestAddAlias(TestCase):
    """Unit tests for add_alias"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, name='Example')
        api.add_organization(self.ctx, name='Bitergia')

    def test_add_new_alias(self):
        """Check if everything goes OK when adding a new alias"""

        alias = api.add_alias(self.ctx,
                              organization='Example',
                              name='Example Inc.')

        # Tests
        self.assertIsInstance(alias, Alias)
        self.assertEqual(alias.organization.name, 'Example')
        self.assertEqual(alias.alias, 'Example Inc.')

        aliases_db = Alias.objects.filter(alias='Example Inc.')
        self.assertEqual(len(aliases_db), 1)

        alias1 = aliases_db[0]
        self.assertEqual(alias, alias1)

    def test_add_multiple_aliases(self):
        """Check if everything goes OK when adding several aliases"""

        alias1 = api.add_alias(self.ctx,
                               organization='Example',
                               name='Example Inc.')

        alias2 = api.add_alias(self.ctx,
                               organization='Example',
                               name='Example Ltd.')

        # Tests
        self.assertEqual(alias1.organization.name, 'Example')
        self.assertEqual(alias1.alias, 'Example Inc.')

        self.assertEqual(alias2.organization.name, 'Example')
        self.assertEqual(alias2.alias, 'Example Ltd.')

        aliases_db = Alias.objects.filter(alias='Example Inc.')
        self.assertEqual(len(aliases_db), 1)

        als1 = aliases_db[0]
        self.assertEqual(alias1, als1)

        aliases_db = Alias.objects.filter(alias='Example Ltd.')
        self.assertEqual(len(aliases_db), 1)

        als2 = aliases_db[0]
        self.assertEqual(alias2, als2)

    def test_add_duplicate_alias(self):
        """Check if it fails when adding a duplicate alias"""

        alias = api.add_alias(self.ctx,
                              organization='Example',
                              name='Example Inc.')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, ALIAS_ALREADY_EXISTS_ERROR.format(name='Example Inc.')):
            api.add_alias(self.ctx,
                          organization='Example',
                          name='Example Inc.')

        aliases = Alias.objects.filter(alias='Example Inc.')
        self.assertEqual(len(aliases), 1)

        als1 = aliases[0]
        self.assertEqual(als1, alias)

        aliases = Alias.objects.all()
        self.assertEqual(len(aliases), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_add_alias_different_org(self):
        """Check if it fails when adding the same alias to a different organization"""

        alias = api.add_alias(self.ctx,
                              organization='Example',
                              name='Example Inc.')

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(AlreadyExistsError, ALIAS_ALREADY_EXISTS_ERROR.format(name='Example Inc.')):
            api.add_alias(self.ctx,
                          organization='Bitergia',
                          name='Example Inc.')

        aliases = Alias.objects.filter(alias='Example Inc.')
        self.assertEqual(len(aliases), 1)

        als1 = aliases[0]
        self.assertEqual(als1.organization.name, 'Example')
        self.assertEqual(als1.organization.name, alias.organization.name)

        aliases = Alias.objects.all()
        self.assertEqual(len(aliases), 1)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_not_found(self):
        """Check if it fails when the organization is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR.format(name='Botergia')):
            api.add_alias(self.ctx,
                          organization='Botergia',
                          name='Example Inc.')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_none(self):
        """Check if it fails when alias name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_empty(self):
        """Check if it fails when alias name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_whitespaces(self):
        """Check if it fails when alias name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name='    ')

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name='\t')

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_int(self):
        """Check if it fails when domain name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ALIAS_VALUE_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_org_same_name(self):
        """Check if it fails when the alias and the organization names are the same"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='Example',
                          name='Example')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_none(self):
        """Check if it fails when organization name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization=None,
                          name='Example Inc.')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_empty(self):
        """Check if it fails when organization name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_ORG_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='',
                          name='Example Inc.')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_whitespaces(self):
        """Check if it fails when organization name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='    ',
                          name='Example Inc.')

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='\t',
                          name='Example Inc.')

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.add_alias(self.ctx,
                          organization='  \t  ',
                          name='Example Inc.')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_organization_name_int(self):
        """Check if it fails when organization name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ORGANIZATION_VALUE_ERROR):
            api.add_alias(self.ctx,
                          organization=12345,
                          name='Example Inc.')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when adding an alias"""

        timestamp = datetime_utcnow()

        api.add_alias(self.ctx,
                      organization='Example',
                      name='Example Inc.')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_alias')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when adding an alias"""

        timestamp = datetime_utcnow()

        api.add_alias(self.ctx,
                      organization='Example',
                      name='Example Inc.')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'alias')
        self.assertEqual(op1.target, 'Example')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['organization'], 'Example')
        self.assertEqual(op1_args['name'], 'Example Inc.')


class TestDeleteAlias(TestCase):
    """Unit tests for delete_alias"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, name='Example')
        api.add_alias(self.ctx, name='Example Inc.', organization='Example')
        api.add_alias(self.ctx, name='Example Ltd.', organization='Example')

    def test_delete_alias(self):
        """Check if everything goes OK when deleting an alias"""

        alias = api.delete_alias(self.ctx, 'Example Inc.')

        # Tests
        self.assertIsInstance(alias, Alias)
        self.assertEqual(alias.organization.name, 'Example')
        self.assertEqual(alias.alias, 'Example Inc.')

        aliases = Alias.objects.filter(alias='Example Inc.')
        self.assertEqual(len(aliases), 0)

        # Check if the rest of aliases were not removed
        aliases = Alias.objects.all()
        self.assertEqual(len(aliases), 1)

        alias = aliases[0]
        self.assertEqual(alias.organization.name, 'Example')
        self.assertEqual(alias.alias, 'Example Ltd.')

    def test_alias_not_found(self):
        """Check if it fails when the alias is not found"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(NotFoundError, ALIAS_NOT_FOUND_ERROR.format(name='Example SL')):
            api.delete_alias(self.ctx, 'Example SL')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_none(self):
        """Check if it fails when alias name is `None`"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_alias(self.ctx, name=None)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_empty(self):
        """Check if it fails when alias name is empty"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_alias(self.ctx, name='')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_whitespaces(self):
        """Check if it fails when alias name is composed by whitespaces"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_alias(self.ctx, name='    ')

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_alias(self.ctx, name='\t')

        with self.assertRaisesRegex(InvalidValueError, ALIAS_NAME_NONE_OR_EMPTY_ERROR):
            api.delete_alias(self.ctx, name='  \t  ')

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_alias_name_int(self):
        """Check if it fails when alias name is an integer"""

        trx_date = datetime_utcnow()  # After this datetime no transactions should be created

        with self.assertRaisesRegex(TypeError, ALIAS_VALUE_ERROR):
            api.delete_alias(self.ctx, name=12345)

        # Check if there are no transactions created when there is an error
        transactions = Transaction.objects.filter(created_at__gt=trx_date)
        self.assertEqual(len(transactions), 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting an alias"""

        timestamp = datetime_utcnow()

        api.delete_alias(self.ctx, 'Example Inc.')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_alias')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting an alias"""

        timestamp = datetime_utcnow()

        api.delete_alias(self.ctx, 'Example Inc.')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'alias')
        self.assertEqual(op1.target, 'Example Inc.')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['alias'], 'Example Inc.')


class TestDeleteMergeRecommendations(TestCase):
    """Unit tests for delete_merge_recommendations"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        identity1 = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        identity2 = api.add_identity(self.ctx, 'mls', email='jsmith@example')
        identity3 = api.add_identity(self.ctx, 'scm', email='johnsmith@example')

        self.rec1 = MergeRecommendation.objects.create(individual1=identity1.individual,
                                                       individual2=identity2.individual)
        self.rec2 = MergeRecommendation.objects.create(individual1=identity1.individual,
                                                       individual2=identity3.individual)
        self.rec3 = MergeRecommendation.objects.create(individual1=identity2.individual,
                                                       individual2=identity3.individual,
                                                       applied=0)

    def test_delete_alias(self):
        """Check whether it deletes all unreviewed merge recommendations"""

        api.delete_merge_recommendations(self.ctx)

        recs = MergeRecommendation.objects.all()
        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec, self.rec3)
        self.assertEqual(rec.applied, 0)

    def test_transaction(self):
        """Check if a transaction is created when deleting recommendations"""

        timestamp = datetime_utcnow()

        api.delete_merge_recommendations(self.ctx)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'delete_merge_recommendations')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when deleting recommendations"""

        timestamp = datetime_utcnow()

        api.delete_merge_recommendations(self.ctx)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'merge_recommendation')
        self.assertEqual(op1.target, 'merge_recommendations')
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['merge_recommendations'], [self.rec1.id, self.rec2.id])


class TestReview(TestCase):
    """Unit tests for review"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)
        self.jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example.com')

    def test_review(self):
        """Test whether an individual's last review date is saved"""

        before_dt = datetime_utcnow()

        jsmith = api.review(self.ctx, self.jsmith.individual)

        after_dt = datetime_utcnow()

        self.assertLess(before_dt, jsmith.last_reviewed)
        self.assertGreater(after_dt, jsmith.last_reviewed)

    def test_review_using_any_identity_uuid(self):
        """Check if it reviews an individual using any of its identities uuids"""

        new_id = api.add_identity(self.ctx, 'mls', email='jsmith@example.com',
                                  uuid=self.jsmith.uuid)

        jsmith = api.review(self.ctx, new_id.uuid)

        self.assertIsNotNone(jsmith.last_reviewed)
        self.assertEqual(jsmith.mk, self.jsmith.individual.mk)

    def test_review_uuid_none_or_empty(self):
        """Check if it fails when the uuid is None or an empty string"""

        with self.assertRaisesRegex(InvalidValueError, UUID_NONE_OR_EMPTY_ERROR):
            api.review(self.ctx, None)

    def test_review_uuid_not_exists(self):
        """Check if it fails when the uuid does not exists"""

        msg = NOT_FOUND_ERROR.format(entity='AAAA')
        with self.assertRaisesRegex(NotFoundError, msg):
            api.review(self.ctx, 'AAAA')

    def test_transaction(self):
        """Check if a transaction is created when reviewing an individual"""

        timestamp = datetime_utcnow()
        uuid = self.jsmith.individual.mk

        api.review(self.ctx, uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'review')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.ctx.user.username)

    def test_operations(self):
        """Check if the right operations are created when reviewing an individual"""

        timestamp = datetime_utcnow()
        uuid = self.jsmith.individual.mk

        api.review(self.ctx, uuid)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.target, uuid)
        self.assertEqual(op1.trx, trx)
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['mk'], uuid)
        self.assertIsNotNone(op1_args['last_reviewed'])
