# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

from __future__ import unicode_literals

# Only needed on Python 2.7 to encode to UTF-8
try:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')
except NameError:
    pass


CODE_BASE_ERROR = 1
CODE_ALREADY_EXISTS_ERROR = 2
CODE_BAD_FILE_FORMAT_ERROR = 3
CODE_DATABASE_ERROR = 4
CODE_INVALID_DATE_ERROR = 5
CODE_INVALID_FORMAT_ERROR = 6
CODE_LOAD_ERROR = 7
CODE_MATCHER_NOT_SUPPORTED_ERROR = 8
CODE_NOT_FOUND_ERROR = 9
CODE_VALUE_ERROR = 10


class BaseError(Exception):
    """Base class error.

    Derived classes can overwrite error message declaring 'message' property.
    """
    message = "Unknown error"
    code = CODE_BASE_ERROR

    def __init__(self, **kwargs):
        super(BaseError, self).__init__(kwargs)
        self.msg = self.message % kwargs

    if sys.version_info[0] >= 3: # Python 3
        def __str__(self):
            return self.__unicode__()
    else: # Python 2
        def __str__(self):
            return self.__unicode__().encode('utf8')

    def __int__(self):
        return self.code

    def __unicode__(self):
        return self.msg


class AlreadyExistsError(BaseError):
    """Exception raised when an entity already exists in the registry"""

    message = "%(entity)s already exists in the registry"
    code = CODE_ALREADY_EXISTS_ERROR

    def __init__(self, **kwargs):
        self.uuid = kwargs.pop('uuid', None)
        super(AlreadyExistsError, self).__init__(**kwargs)


class BadFileFormatError(BaseError):
    """Exception raised when an input file does not have the expected format"""

    message = "%(cause)s"
    code = CODE_BAD_FILE_FORMAT_ERROR


class DatabaseError(BaseError):
    """Exception raised when a database error occurs"""

    message = "%(error)s (err: %(code)s)"
    code = CODE_DATABASE_ERROR


class InvalidDateError(BaseError):
    """Exception raised when a date is invalid"""

    message = "%(date)s is not a valid date"
    code = CODE_INVALID_DATE_ERROR


class InvalidFormatError(BaseError):
    """Exception raised when a format is invalid"""

    message = "%(cause)s"
    code = CODE_INVALID_FORMAT_ERROR


class LoadError(BaseError):
    """Exception raised when an error occurs loading data"""

    message = "%(cause)s"
    code = CODE_LOAD_ERROR


class MatcherNotSupportedError(BaseError):
    """Exception raised when an identity matcher is not supported"""

    message = "%(matcher)s identity matcher is not supported"
    code = CODE_MATCHER_NOT_SUPPORTED_ERROR


class NotFoundError(BaseError):
    """Exception raised when an entity is not found in the registry"""

    message = "%(entity)s not found in the registry"
    code = CODE_NOT_FOUND_ERROR


class WrappedValueError(ValueError):
    """Exception WrappedValueError is a normal ValueError with code support"""

    code = CODE_VALUE_ERROR
