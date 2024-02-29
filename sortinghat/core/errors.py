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
CODE_INVALID_FORMAT_ERROR = 6
CODE_LOAD_ERROR = 7
CODE_NOT_FOUND_ERROR = 9
CODE_VALUE_ERROR = 10
CODE_CLOSED_TRANSACTION_ERROR = 12
CODE_LOCKED_IDENTITY_ERROR = 13
CODE_DUPLICATE_RANGE_ERROR = 14
CODE_EQUAL_INDIVIDUAL_ERROR = 15
CODE_FILTER_ERROR = 16
CODE_JOB_ERROR = 80
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
        self.message = self._msg % kwargs

    def __str__(self):
        return self.message

    def __int__(self):
        return self.code


class AlreadyExistsError(BaseError):
    """Exception raised when an entity already exists in the registry"""

    _msg = "%(entity)s '%(eid)s' already exists in the registry"
    code = CODE_ALREADY_EXISTS_ERROR

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entity = kwargs['entity']
        self.eid = kwargs['eid']


class InvalidFormatError(BaseError):
    """Exception raised when a format is invalid"""

    _msg = "%(cause)s"
    code = CODE_INVALID_FORMAT_ERROR


class LoadError(BaseError):
    """Exception raised when an error occurs loading data"""

    _msg = "%(cause)s"
    code = CODE_LOAD_ERROR


class NotFoundError(BaseError):
    """Exception raised when an entity is not found in the registry"""

    _msg = "%(entity)s not found in the registry"
    code = CODE_NOT_FOUND_ERROR


class InvalidValueError(BaseError):
    """Exception raised when a value is invalid"""

    _msg = "%(msg)s"
    code = CODE_VALUE_ERROR


class InvalidFilterError(BaseError):
    """Exception raised when a filter is invalid"""

    _msg = "Error in %(filter_name)s filter: %(msg)s"
    code = CODE_FILTER_ERROR


class EqualIndividualError(BaseError):
    """Exception raised when the source and destination individual are the same"""

    _msg = "%(msg)s"
    code = CODE_EQUAL_INDIVIDUAL_ERROR


class ClosedTransactionError(BaseError):
    """Exception raised when performing a change on a closed transaction"""

    _msg = "%(msg)s"
    code = CODE_CLOSED_TRANSACTION_ERROR


class LockedIdentityError(BaseError):
    """Exception raised when performing a change on a locked individual"""

    _msg = "Individual %(uuid)s is locked"
    code = CODE_LOCKED_IDENTITY_ERROR


class DuplicateRangeError(BaseError):
    """Exception raised when setting an enrollment with an existing date range"""

    _msg = "range date '%(start)s'-'%(end)s' is part of an existing range for %(group)s"
    code = CODE_DUPLICATE_RANGE_ERROR


class JobError(BaseError):
    """Exception raised when there is an job related error"""

    _msg = "%(msg)s"
    code = CODE_JOB_ERROR


class RecommendationEngineError(BaseError):
    """Exception raised when there is an error in the recommendation engine"""

    _msg = "%(msg)s"
    code = CODE_RECOMMENDATION_ERROR
