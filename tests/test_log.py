#!/usr/bin/env python
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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import json

from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core.errors import ClosedTransactionError
from sortinghat.core.log import TransactionsLog
from sortinghat.core.models import (Transaction,
                                    Operation)

OPERATION_TYPE_EMPTY_ERROR = "'op_type' value must be a 'Operation.OpType'; str given"
OPERATION_TYPE_NONE_ERROR = "'op_type' value must be a 'Operation.OpType'; NoneType given"
OPERATION_ENTITY_EMPTY_ERROR = "'entity_type' cannot be an empty string"
OPERATION_ENTITY_NONE_ERROR = "'entity_type' cannot be None"
OPERATION_TRANSACTION_NONE_ERROR = "field trx must be a Transaction"
OPERATION_TRANSACTION_CLOSED_ERROR = "Log operation not allowed, transaction {tuid} is already closed"
TRANSACTION_NAME_EMPTY_ERROR = "'name' cannot be an empty string"
TRANSACTION_NAME_NONE_ERROR = "'name' cannot be None"


class TestLogTransaction(TestCase):
    """Unit tests for add_transaction"""

    def test_open_transaction(self):
        """Check if a new transaction is added"""

        timestamp = datetime_utcnow()

        trxl = TransactionsLog.open(name='test')
        self.assertIsInstance(trxl, TransactionsLog)

        trx_db = Transaction.objects.get(tuid=trxl.trx.tuid)
        self.assertIsInstance(trx_db, Transaction)
        self.assertEqual(trx_db.name, 'test')
        self.assertGreater(trx_db.created_at, timestamp)
        self.assertIsNone(trx_db.closed_at)

    def test_close_transaction(self):
        """Check if the transaction gets closed"""

        trxl = TransactionsLog.open(name='test')
        timestamp = datetime_utcnow()
        trxl.close()

        trx_db = Transaction.objects.get(tuid=trxl.trx.tuid)
        self.assertGreater(trx_db.closed_at, timestamp)

    def test_name_empty(self):
        """Check if it fails when `name` field is an empty string"""

        with self.assertRaisesRegex(ValueError, TRANSACTION_NAME_EMPTY_ERROR):
            TransactionsLog.open(name='')

    def test_method_name_none(self):
        """Check if it fails when `method_name` field is `None`"""

        with self.assertRaisesRegex(ValueError, TRANSACTION_NAME_NONE_ERROR):
            TransactionsLog.open(name=None)

    def test_log_operation(self):
        """Check if a new operation is logged"""

        trxl = TransactionsLog.open('test')
        input_args = {'uuid': '12345abcd'}

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
        trxl = TransactionsLog.open('test')
        timestamp1 = datetime_utcnow()
        timestamp2 = datetime_utcnow()
        input_args1 = {'uuid': '12345abcd'}
        input_args2 = {'uuid': '67890efgh'}

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

        input_args = json.dumps({'uuid': '12345abcd'})
        trxl = TransactionsLog.open('test')
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

        trxl = TransactionsLog.open('test')
        input_args = json.dumps({'uuid': '12345abcd'})

        with self.assertRaisesRegex(TypeError, OPERATION_TYPE_EMPTY_ERROR):
            trxl.log_operation(op_type='', entity_type='test_entity',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    def test_operation_type_none(self):
        """Check if it fails when type field is `None`"""

        trxl = TransactionsLog.open('test')
        input_args = json.dumps({'uuid': '12345abcd'})

        with self.assertRaisesRegex(TypeError, OPERATION_TYPE_NONE_ERROR):
            trxl.log_operation(op_type=None, entity_type='test_entity',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    def test_entity_empty(self):
        """Check if it fails when entity field is an empty string"""

        trxl = TransactionsLog.open('test')
        input_args = json.dumps({'uuid': '12345abcd'})

        with self.assertRaisesRegex(ValueError, OPERATION_ENTITY_EMPTY_ERROR):
            trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='',
                               timestamp=datetime_utcnow(), target='test', args=input_args)

    def test_entity_none(self):
        """Check if it fails when entity field is `None`"""

        trxl = TransactionsLog.open('test')
        input_args = json.dumps({'uuid': '12345abcd'})

        with self.assertRaisesRegex(ValueError, OPERATION_ENTITY_NONE_ERROR):
            trxl.log_operation(op_type=Operation.OpType.ADD, entity_type=None,
                               timestamp=datetime_utcnow(), target='test', args=input_args)
