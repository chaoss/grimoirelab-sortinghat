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

from __future__ import absolute_import
from __future__ import unicode_literals

import dateutil.parser
import hashlib

from .db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE
from .exceptions import InvalidDateError


def merge_date_ranges(dates):
    """Merge date ranges.

    Generator that merges ovelaped data ranges.

    Default init and end dates (1900-01-01 and 2100-01-01) are considered range
    limits and will be removed when a set of ranges overlap. For example:

     * [(1900-01-01, 2010-01-01), (2008-01-01, 2100-01-01)]
           --> (2008-01-01, 2010-01-01)
     * [(1900-01-01, 2010-01-01), (2008-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
           --> (2008-01-01, 2010-01-01),(2010-01-02, 2100-01-01)
     * [(1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
           --> (1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)

    The condition MIN_PERIOD_DATE <= dt <= MAX_PERIOD_DATE must be true for each
    date. Otherwise, the generator will raise a ValueError exception.

    This code is based on samplebias' answer to StackOverflow's question
    "Merging a list of time-range tuples that have overlapping time-ranges"
    (http://stackoverflow.com/questions/5679638).

    :param dates: sequence of date ranges where each range is a
        (st_date, en_date) tuple

    :raises ValueError: when a value of the data range is out of bounds
    """
    if not dates:
        return

    saved = list(dates[0])

    for st, en in sorted([sorted(t) for t in dates]):
        if st < MIN_PERIOD_DATE or st > MAX_PERIOD_DATE:
            raise ValueError("start date %s is out of bounds" % str(st))
        if en < MIN_PERIOD_DATE or en > MAX_PERIOD_DATE:
            raise ValueError("end date %s is out of bounds" % str(en))

        if st <= saved[1]:
            if saved[0] == MIN_PERIOD_DATE:
                saved[0] = st

            if MAX_PERIOD_DATE in (en, saved[1]):
                saved[1] = min(saved[1], en)
            else:
                saved[1] = max(saved[1], en)
        else:
            yield tuple(saved)
            saved[0] = st
            saved[1] = en
    yield tuple(saved)


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


def to_unicode(x):
    import sys

    if sys.version_info[0] >= 3: # Python 3
        return str(x)
    else: # Python 2
        if type(x) is unicode:
            return x
        elif type(x) != str:
            return unicode(x)
        else:
            return unicode(x.decode('utf-8'))


def uuid(source, email=None, name=None, username=None):
    """Get the UUID related to the identity data.

    Based on the input data, the function will return the UUID associated
    to an identity. On this version, the UUID will be the SHA1 of
    "source:email:name:username" string. Future versions will use UUID
    standard.

    :param source: data source
    :param email: email of the identity
    :param name: full name of the identity
    :param username: user name used by the identity

    :returns: a universal an unique identifier

    :raises ValueError: when source is None or empty; each one of the
        parameters is None; parameters are empty.
    """
    if source is None:
        raise ValueError("source cannot be None")
    if source == '':
        raise ValueError("source cannot be an empty string")
    if not (email or name or username):
        raise ValueError("identity data cannot be None or empty")

    s = ':'.join((to_unicode(source), to_unicode(email),
                  to_unicode(name), to_unicode(username)))

    sha1 = hashlib.sha1(s.encode('UTF-8'))
    uuid = sha1.hexdigest()

    return uuid
