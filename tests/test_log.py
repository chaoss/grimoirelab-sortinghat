#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import collections
import json
import unittest.mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core.context import SortingHatContext
from sortinghat.core.errors import (AlreadyExistsError,
                                    ClosedTransactionError)
from sortinghat.core.log import TransactionsLog
from sortinghat.core.models import (Transaction,
                                    Operation)


OPERATION_TYPE_EMPTY_ERROR = "'op_type' value must be a 'Operation.OpType'; str given"
OPERATION_TYPE_NONE_ERROR = "'op_type' value must be a 'Operation.OpType'; NoneType given"
OPERATION_ENTITY_EMPTY_ERROR = "'entity_type' cannot be an empty string"
OPERATION_ENTITY_NONE_ERROR = "'entity_type' cannot be None"
OPERATION_TRANSACTION_NONE_ERROR = "field trx must be a Transaction"
OPERATION_TRANSACTION_CLOSED_ERROR = "Log operation not allowed, transaction {tuid} is already closed"
OPERATION_DUPLICATED_ERROR = "Operation '01234567890abcef01234567890abcef0' already exists in the registry"
TRANSACTION_NAME_EMPTY_ERROR = "'name' cannot be an empty string"
TRANSACTION_NAME_NONE_ERROR = "'name' cannot be None"
TRANSACTION_DUPLICATED_ERROR = "Transaction '01234567890abcef01234567890abcef0' already exists in the registry"
TRANSACTION_CTX_NONE_ERROR = "ctx value must be a SortingHatContext; NoneType given"
TRANSACTION_CTX_INVALID_ERROR = "ctx value must be a SortingHatContext; TestTuple given"
TRANSACTION_CTX_USER_EMPTY_ERROR = "ctx.user must be a Django User or AnonymousUser; SortingHatContext given"
TRANSACTION_CTX_USER_NONE_ERROR = "ctx.user must be a Django User or AnonymousUser; SortingHatContext given"
TRANSACTION_CTX_USER_INVALID_ERROR = "ctx.user must be a Django User or AnonymousUser; SortingHatContext given"


class MockUUID4:
    """Class to mock uuid4 results"""

    @property
    def hex(self):
        return '01234567890abcef01234567890abcef0'


class TestLogTransaction(TestCase):
    """Unit tests for add_transaction"""

    def setUp(self):
        """Load initial values"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_open_transaction(self):
        """Check if a new transaction is added"""

        timestamp = datetime_utcnow()

        trxl = TransactionsLog.open('test', self.ctx)
        self.assertIsInstance(trxl, TransactionsLog)

        trx_db = Transaction.objects.get(tuid=trxl.trx.tuid)
        self.assertIsInstance(trx_db, Transaction)
        self.assertEqual(trx_db.name, 'test')
        self.assertGreater(trx_db.created_at, timestamp)
        self.assertIsNone(trx_db.closed_at)
        self.assertEqual(trx_db.authored_by, self.ctx.user.username)

    def test_close_transaction(self):
        """Check if the transaction gets closed"""

        trxl = TransactionsLog.open('test', self.ctx)
        timestamp = datetime_utcnow()
        trxl.close()

        trx_db = Transaction.objects.get(tuid=trxl.trx.tuid)
        self.assertGreater(trx_db.closed_at, timestamp)

    def test_name_empty(self):
        """Check if it fails when `name` field is an empty string"""

        with self.assertRaisesRegex(ValueError, TRANSACTION_NAME_EMPTY_ERROR):
            TransactionsLog.open('', self.ctx)

    def test_method_name_none(self):
        """Check if it fails when `method_name` field is `None`"""

        with self.assertRaisesRegex(ValueError, TRANSACTION_NAME_NONE_ERROR):
            TransactionsLog.open(None, self.ctx)

    def test_context_none(self):
        """Check if it fails when `ctx` field is `None`"""

        with self.assertRaisesRegex(TypeError, TRANSACTION_CTX_NONE_ERROR):
            TransactionsLog.open('test', None)

    def test_context_invalid(self):
        """Check if it fails when `ctx` field is not a SortingHatContext"""

        TestTuple = collections.namedtuple('TestTuple', ['user'])
        ctx = TestTuple(self.user)
        with self.assertRaisesRegex(TypeError, TRANSACTION_CTX_INVALID_ERROR):
            TransactionsLog.open('test', ctx)

    def test_name_job_id(self):
        """Check if the job id is included in the name when was defined on the context"""

        ctx = SortingHatContext(self.user, '1234-5678-ABCD-90EF')

        trxl = TransactionsLog.open('test', ctx)
        self.assertIsInstance(trxl, TransactionsLog)

        trx_db = Transaction.objects.get(tuid=trxl.trx.tuid)
        self.assertIsInstance(trx_db, Transaction)
        self.assertEqual(trx_db.name, 'test-1234-5678-ABCD-90EF')

    def test_context_anonymous_user(self):
        """Check if a new transaction is added when the user is anonymous"""

        anon_user = AnonymousUser()
        ctx = SortingHatContext(anon_user)

        timestamp = datetime_utcnow()

        trxl = TransactionsLog.open('test', ctx)
        self.assertIsInstance(trxl, TransactionsLog)

        trx_db = Transaction.objects.get(tuid=trxl.trx.tuid)
        self.assertIsInstance(trx_db, Transaction)
        self.assertEqual(trx_db.name, 'test')
        self.assertGreater(trx_db.created_at, timestamp)
        self.assertIsNone(trx_db.closed_at)
        self.assertIsNone(trx_db.authored_by)

    def test_context_user_none(self):
        """Check if it fails when `user` field is `None`"""

        ctx = SortingHatContext(None)
        with self.assertRaisesRegex(TypeError, TRANSACTION_CTX_USER_NONE_ERROR):
            TransactionsLog.open('test', ctx)

    def test_context_user_empty(self):
        """Check if it fails when `user` field is an empty string"""

        ctx = SortingHatContext('')
        with self.assertRaisesRegex(TypeError, TRANSACTION_CTX_USER_EMPTY_ERROR):
            TransactionsLog.open('test', ctx)

    def test_context_user_invalid(self):
        """Check if it fails when `user` field is not an `User` Django object"""

        UserTuple = collections.namedtuple('UserTuple', 'username')
        user = UserTuple('test')

        ctx = SortingHatContext(user)
        with self.assertRaisesRegex(TypeError, TRANSACTION_CTX_USER_INVALID_ERROR):
            TransactionsLog.open('test', ctx)

    def test_log_operation(self):
        """Check if a new operation is logged"""

        trxl = TransactionsLog.open('test', self.ctx)
        input_args = {'mk': '12345abcd'}

        operation = trxl.log_operation(op_type=Operation.OpType.ADD, timestamp=datetime_utcnow(),
                                       entity_type='test_entity', target='test', args=input_args)
        self.assertIsInstance(operation, Operation)

        operation_db = Operation.objects.get(ouid=operation.ouid)
        self.assertIsInstance(operation_db, Operation)
        self.assertEqual(operation_db.op_type, Operation.OpType.ADD.value)
        self.assertEqual(operation_db.entity_type, 'test_entity')
        self.assertEqual(operation_db.timestamp, operation.timestamp)
        self.assertEqual(operation_db.trx, trxl.trx)
        self.assertEqual(operation_db.target, 'test')
        self.assertEqual(operation_db.args, json.dumps(input_args))
        self.assertEqual(input_args, json.loads(operation_db.args))

    def test_log_multiple_operations(self):
        """Check if multiple operations are logged properly"""

        # Load initial variables
        trxl = TransactionsLog.open('test', self.ctx)
        timestamp1 = datetime_utcnow()
        timestamp2 = datetime_utcnow()
        input_args1 = {'mk': '12345abcd'}
        input_args2 = {'mk': '67890efgh'}

        # Add operations
        op1 = trxl.log_operation(op_type=Operation.OpType.ADD, timestamp=timestamp1,
                                 entity_type='test_entity', target='test', args=input_args1)
        op2 = trxl.log_operation(op_type=Operation.OpType.ADD, timestamp=timestamp2,
                                 entity_type='test_entity', target='test', args=input_args2)

        # Check number of operations
        operations = Operation.objects.filter(trx=trxl.trx)
        self.assertEqual(len(operations), 2)

        # Check op1
        self.assertIsInstance(op1, Operation)

        operation_db = Operation.objects.get(ouid=op1.ouid)
        self.assertIsInstance(operation_db, Operation)
        self.assertEqual(operation_db.op_type, Operation.OpType.ADD.value)
        self.assertEqual(operation_db.entity_type, 'test_entity')
        self.assertEqual(operation_db.timestamp, op1.timestamp)
        self.assertEqual(operation_db.timestamp, timestamp1)
        self.assertEqual(operation_db.trx, trxl.trx)
        self.assertEqual(operation_db.target, op1.target)
        self.assertEqual(operation_db.args, json.dumps(input_args1))
        self.assertEqual(input_args1, json.loads(operation_db.args))

        # Check op2
        self.assertIsInstance(op2, Operation)

        operation_db = Operation.objects.get(ouid=op2.ouid)
        self.assertIsInstance(operation_db, Operation)
        self.assertEqual(operation_db.op_type, Operation.OpType.ADD.value)
        self.assertEqual(operation_db.entity_type, 'test_entity')
        self.assertEqual(operation_db.timestamp, op2.timestamp)
        self.assertEqual(operation_db.timestamp, timestamp2)
        self.assertEqual(operation_db.trx, trxl.trx)
        self.assertEqual(operation_db.target, op2.target)
        self.assertEqual(operation_db.args, json.dumps(input_args2))
        self.assertEqual(input_args2, json.loads(operation_db.args))

    def test_log_operation_closed_transaction(self):
        """Check if it fails when logging an operation on a closed transaction"""

        input_args = json.dumps({'mk': '12345abcd'})
        trxl = TransactionsLog.open('test', self.ctx)
        tuid = trxl.trx.tuid
        trxl.close()

        error_msg = OPERATION_TRANSACTION_CLOSED_ERROR.format(tuid=tuid)
        with self.assertRaisesRegex(ClosedTransactionError, error_msg):
            trxl.log_operation(op_type=Operation.OpType.UPDATE, entity_type='test_entity',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

        operations = Operation.objects.filter(trx=trxl.trx)
        self.assertEqual(len(operations), 0)

    def test_operation_type_empty(self):
        """Check if it fails when type field is an empty string"""

        trxl = TransactionsLog.open('test', self.ctx)
        input_args = json.dumps({'mk': '12345abcd'})

        with self.assertRaisesRegex(TypeError, OPERATION_TYPE_EMPTY_ERROR):
            trxl.log_operation(op_type='', entity_type='test_entity',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    def test_operation_type_none(self):
        """Check if it fails when type field is `None`"""

        trxl = TransactionsLog.open('test', self.ctx)
        input_args = json.dumps({'mk': '12345abcd'})

        with self.assertRaisesRegex(TypeError, OPERATION_TYPE_NONE_ERROR):
            trxl.log_operation(op_type=None, entity_type='test_entity',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    def test_entity_empty(self):
        """Check if it fails when entity field is an empty string"""

        trxl = TransactionsLog.open('test', self.ctx)
        input_args = json.dumps({'mk': '12345abcd'})

        with self.assertRaisesRegex(ValueError, OPERATION_ENTITY_EMPTY_ERROR):
            trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    def test_entity_none(self):
        """Check if it fails when entity field is `None`"""

        trxl = TransactionsLog.open('test', self.ctx)
        input_args = json.dumps({'mk': '12345abcd'})

        with self.assertRaisesRegex(ValueError, OPERATION_ENTITY_NONE_ERROR):
            trxl.log_operation(op_type=Operation.OpType.ADD, entity_type=None,
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    @unittest.mock.patch('uuid.uuid4')
    def test_integrity_error_transaction_id(self, mock_uuid4):
        """Check whether transactions with the same id cannot be inserted"""

        mock_uuid4.return_value = MockUUID4()

        with self.assertRaisesRegex(AlreadyExistsError, TRANSACTION_DUPLICATED_ERROR):
            TransactionsLog.open('test', self.ctx)
            TransactionsLog.open('test', self.ctx)

    @unittest.mock.patch('uuid.uuid4')
    def test_integrity_error_operation_id(self, mock_uuid4):
        """Check whether operations with the same id cannot be inserted"""

        mock_uuid4.return_value = MockUUID4()

        timestamp = datetime_utcnow()
        input_args = json.dumps({'mk': '12345abcd'})

        trxl = TransactionsLog.open('test', self.ctx)

        with self.assertRaisesRegex(AlreadyExistsError, OPERATION_DUPLICATED_ERROR):
            trxl.log_operation(op_type=Operation.OpType.ADD, timestamp=timestamp,
                               entity_type='test_entity', target='test', args=input_args)
            trxl.log_operation(op_type=Operation.OpType.ADD, timestamp=timestamp,
                               entity_type='test_entity', target='test', args=input_args)
