#!/usr/bin/env python
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

CODE_BASE_ERROR = 1
CODE_ALREADY_EXISTS_ERROR = 2
CODE_NOT_FOUND_ERROR = 9
CODE_VALUE_ERROR = 10
CODE_CLOSED_TRANSACTION_ERROR = 12
CODE_LOCKED_IDENTITY_ERROR = 13
CODE_DUPLICATE_RANGE_ERROR = 14
CODE_EQUAL_INDIVIDUAL_ERROR = 15
CODE_FILTER_ERROR = 16
CODE_RECOMMENDATION_ERROR = 100
CODE_TOKEN_EXPIRED = 126
CODE_PERMISSION_DENIED = 127
CODE_UNKNOWN_ERROR = 128
CODE_INVALID_CREDENTIALS = 129


class BaseError(Exception):
    """Base class error.

    Derived classes can overwrite error message declaring
    'message' property.
    """
    code = CODE_BASE_ERROR
    message = "SortingHat unknown error"

    def __init__(self, **kwargs):
        super().__init__()
        self.msg = self.message % kwargs

    def __str__(self):
        return self.msg

    def __int__(self):
        return self.code


class AlreadyExistsError(BaseError):
    """Exception raised when an entity already exists in the registry"""

    message = "%(entity)s '%(eid)s' already exists in the registry"
    code = CODE_ALREADY_EXISTS_ERROR

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entity = kwargs['entity']
        self.eid = kwargs['eid']


class NotFoundError(BaseError):
    """Exception raised when an entity is not found in the registry"""

    message = "%(entity)s not found in the registry"
    code = CODE_NOT_FOUND_ERROR


class InvalidValueError(BaseError):
    """Exception raised when a value is invalid"""

    code = CODE_VALUE_ERROR
    message = "%(msg)s"


class InvalidFilterError(BaseError):
    """Exception raised when a filter is invalid"""

    code = CODE_FILTER_ERROR
    message = "Error in %(filter_name)s filter: %(msg)s"


class EqualIndividualError(BaseError):
    """Exception raised when the source and destination individual are the same"""

    code = CODE_EQUAL_INDIVIDUAL_ERROR
    message = "%(msg)s"


class ClosedTransactionError(BaseError):
    """Exception raised when performing a change on a closed transaction"""

    code = CODE_CLOSED_TRANSACTION_ERROR
    message = "%(msg)s"


class LockedIdentityError(BaseError):
    """Exception raised when performing a change on a locked individual"""

    code = CODE_LOCKED_IDENTITY_ERROR
    message = "Individual %(uuid)s is locked"


class DuplicateRangeError(BaseError):
    """Exception raised when setting an enrollment with an existing date range"""

    code = CODE_DUPLICATE_RANGE_ERROR
    message = "range date '%(start)s'-'%(end)s' is part of an existing range for %(group)s"


class RecommendationEngineError(BaseError):
    """Exception raised when there is an error in the recommendation engine"""

    code = CODE_RECOMMENDATION_ERROR
    message = "%(msg)s"
