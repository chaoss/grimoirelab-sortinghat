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

import dateutil.parser

from sortinghat.exceptions import InvalidDateError


def str_to_datetime(ts):
    """Format a string to a datetime object.

    This functions supports several date formats like YYYY-MM-DD, MM-DD-YYYY
    and YY-MM-DD. When the given data is None or an empty string, the function
    returns None.

    :param ts: string to convert

    :returns: a datetime object

    :raises IvalidDateError: when the given string cannot be converted into
        a valid date
    """
    if not ts:
        return None

    try:
        return dateutil.parser.parse(ts).replace(tzinfo=None)
    except Exception:
        raise InvalidDateError(date=str(ts))


def uuid(source, email=None, name=None, username=None):
    """Get the UUID related to the identity data.

    Based on the input data, the function will return the UUID associated
    to an identity. On this version, the UUID will be one of the given
    parameters. By priority: email, name, username. Future versions
    will use SHA-1 algorithm.

    :param source: data source
    :param email: email of the identity
    :param name: full name of the identity
    :param username: user name used by the identity

    :returns: a universal an unique identifier

    :raises ValueError: when source is None or empty; each one of the
        parameters is None; parameters are empty.
    """
    if source is None:
        raise ValueError('source cannot be None')
    if source == '':
        raise ValueError('source cannot be an empty string')
    if not (email or name or username):
        raise ValueError('identity data cannot be None or empty')

    uuid = email or name or username

    return uuid
