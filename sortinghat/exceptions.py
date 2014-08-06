# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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

class BaseError(Exception):
    """Base class error.

    Derived classes can overwrite error message declaring 'message' property.
    """
    message = 'Unknown error'

    def __init__(self, **kwargs):
        super(BaseError, self).__init__(kwargs)
        self.msg = self.message % kwargs

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return unicode(self.msg)


class AlreadyExistsError(BaseError):
    """Exception raised when an entity already exists in the registry"""

    message = "%(entity)s already exists in the registry"


class BadFileFormatError(BaseError):
    """Exception raised when an input file does not have the expected format"""

    message = "%(cause)s"


class DatabaseError(BaseError):
    """Exception raised when a database error occurs"""

    message = "%(error)s (err: %(code)s)"


class InvalidDateError(BaseError):
    """Exception raised when a date is invalid"""

    message = "%(date)s is not a valid date"


class NotFoundError(BaseError):
    """Exception raised when an entity is not found in the registry"""

    message = "%(entity)s not found in the registry"
