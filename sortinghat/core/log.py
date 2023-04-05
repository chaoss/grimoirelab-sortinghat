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


import json
import logging
import re
import uuid

import django.core.exceptions
import django.db.utils

from django.contrib.auth.models import User, AnonymousUser

from grimoirelab_toolkit.datetime import datetime_utcnow

from .context import SortingHatContext
from .errors import AlreadyExistsError, ClosedTransactionError
from .models import (Operation,
                     Transaction)

from .aux import validate_field


logger = logging.getLogger(__name__)


class TransactionsLog:
    """Class for logging transactions and operations related with the database.

    Every object of this class is created using the `open` class method receiving
    as a parameter the name of the method opening the transaction, which creates a
    `Transaction` object in the database. If the context was created by a job,
    the logger will add the job identifier to the name of the transaction.

    The method `log_operation` creates a new `Operation` objects linked to the
    transaction which was generated when the object was instanced. This method
    receives, among other parameters, the arguments from the method logging the
    operation in a Python dict object which will be converted to a serialized
    JSON.

    The `close` method adds a `closed_at` timestamp (before calling this method,
    this field has a `NULL` value in the DB) and it also sets to `True` the
    `is_closed` flag.

    :param trx: Transaction object generated with the class method `open`

    :raises ClosedTransactionError: When trying to log an operation on a closed transaction
    :raises TypeError: When the `op_type` is not an instance of `Operation.OpType` class
    """
    def __init__(self, trx, ctx):
        self.trx = trx
        self.ctx = ctx

    @classmethod
    def open(cls, name, ctx):
        """Create a new transaction object and save it into the DB.

        When the context was created by a job, this method will add
        the job identifier as a suffix to the name of the transaction.

        :param name: mame of the method opening the transaction
        :param ctx: context from the method opening the transaction

        :returns: a new `TransactionsLog` object containing the
            generated `Transaction` object
        """
        # Check if input values are valid
        validate_field('name', name)
        if not isinstance(ctx, SortingHatContext):
            msg = "ctx value must be a SortingHatContext; {} given".format(ctx.__class__.__name__)
            raise TypeError(msg)
        if not isinstance(ctx.user, (User, AnonymousUser)):
            msg = "ctx.user must be a Django User or AnonymousUser; {} given".format(ctx.__class__.__name__)
            raise TypeError(msg)

        trx_name = name
        if ctx.job_id:
            trx_name += '-' + str(ctx.job_id)

        tuid = uuid.uuid4().hex

        username = None
        if not isinstance(ctx.user, AnonymousUser):
            username = ctx.user.username
            validate_field('username', username)

        trx = Transaction(tuid=tuid,
                          name=trx_name,
                          created_at=datetime_utcnow(),
                          authored_by=username,
                          tenant=ctx.tenant)

        try:
            trx.save(force_insert=True)
        except django.db.utils.IntegrityError as exc:
            _handle_integrity_error(Transaction, exc, tuid)

        logger.debug(
            f"Transaction {trx.tuid} started; "
            f"name='{trx.name}' author='{trx.authored_by}' tenant='{ctx.tenant}'"
        )

        return cls(trx, ctx)

    def close(self):
        """Close a given transaction adding a timestamp as closing date and setting a flag"""

        self.trx.closed_at = datetime_utcnow()
        self.trx.is_closed = True

        try:
            self.trx.save()
        except django.db.utils.IntegrityError as exc:
            _handle_integrity_error(Transaction, exc, self.trx.tuid)

        logger.debug(f"Transaction {self.trx.tuid} finished")

    def log_operation(self, op_type, entity_type, timestamp, args, target):
        """Create a new operation object and save it into the DB.

        :param op_type: Type of the operation which is recorded (ADD, DELETE, UPDATE)
        :param entity_type: Type of entity involved in the operations (UUID, ENROLLMENT, etc.)
        :param timestamp: Datetime when the operation is created
        :param args: Input arguments from the method creating the operation
        :param target: Argument which the operation is directed to

        :raises ClosedTransactionError: When trying to log an operation on a closed transaction
        :raises TypeError: When the `op_type` is not an instance of `Operation.OpType` class

        :returns: a new Operation object
        """
        if self.trx.is_closed:
            msg = 'Log operation not allowed, transaction {} is already closed'.format(self.trx.tuid)
            raise ClosedTransactionError(msg=msg)

        # Check if input values are valid
        validate_field('entity_type', entity_type)
        validate_field('target', target)
        if not isinstance(op_type, Operation.OpType):
            msg = "'op_type' value must be a 'Operation.OpType'; {} given".format(op_type.__class__.__name__)
            raise TypeError(msg)

        args_dump = json.dumps(args)

        ouid = uuid.uuid4().hex

        operation = Operation(ouid=ouid, trx=self.trx, op_type=op_type, target=target,
                              entity_type=entity_type, timestamp=timestamp, args=args_dump)

        try:
            operation.save(force_insert=True)
        except django.db.utils.IntegrityError as exc:
            _handle_integrity_error(Operation, exc, self.trx.tuid)

        logger.debug(
            f"Operation {operation.ouid} completed; "
            f"trx='{operation.trx.tuid}' op='{operation.op_type}' "
            f"type='{entity_type}' target='{target}' args={args};"
        )

        return operation


_MYSQL_DUPLICATE_ENTRY_ERROR_REGEX = re.compile(r"Duplicate entry '(?P<value>.+)' for key")


def _handle_integrity_error(model, exc, tuid):
    """Handle integrity error internal logging exceptions"""

    logger.error(f"Transaction {tuid} aborted; integrity error;",
                 exc_info=True)

    m = re.match(_MYSQL_DUPLICATE_ENTRY_ERROR_REGEX,
                 exc.__cause__.args[1])
    if not m:
        raise exc

    entity = model.__name__
    eid = m.group('value')

    raise AlreadyExistsError(entity=entity, eid=eid)
