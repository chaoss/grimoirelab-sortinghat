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
#     Santiago Dueñas <sduenas@bitergia.com>
#

import re

from urllib.parse import urlparse

from .models import MIN_PERIOD_DATE, MAX_PERIOD_DATE


def merge_datetime_ranges(dates, exclude_limits=False):
    """Merge datetime ranges.

    Generator that merges overlapped datetime ranges. For example,
    assuming all dates where set to the same time and are in UTC
    timezone, these are some expected results:

        * [(1900-01-01, 2010-01-01), (2008-01-01, 2100-01-01)]
          --> [(1900-01-01, 2100-01-01)]
        * [(1900-01-01, 2010-01-01), (2008-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
          --> [(1900-01-01, 2010-01-01), (2011-01-02, 2100-01-01)]
        * [(1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
          --> [(1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]

    Default init and end dates (1900-01-01 and 2100-01-01) are
    considered range limits. These will be removed when a set of
    ranges overlaps and `exclude_limits` is set. Compare the next
    examples with the ones from above:

        * [(1900-01-01, 2010-01-01), (2008-01-01, 2100-01-01)]
          --> [(2008-01-01, 2010-01-01)]
        * [(1900-01-01, 2010-01-01), (2008-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
          --> [(2008-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
        * [(1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
          --> [(1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]

    The condition MIN_PERIOD_DATE <= dt <= MAX_PERIOD_DATE must be
    true for each date. Otherwise, the generator will raise a
    `ValueError` exception.

    :param dates: sequence of datetime ranges where each range is a
        (start_date, end_date) tuple
    :param exclude_limits: remove MIN_PERIOD_DATE and MAX_PERIOD_DATE
        from overlapped ranges
    :returns: a generator of merged datetime ranges where each range
        is a (start_date, end_date) tuple

    :raises ValueError: when a value of the data range is out of bounds
    :raises TypeError: when timezone info is not set in any datetime object
    """
    # This code is based on samplebias' answer to StackOverflow question
    # "Merging a list of time-range tuples that have overlapping time-ranges"
    # (http: // stackoverflow.com / questions / 5679638).

    if not dates:
        return

    sorted_dates = sorted([sorted(t) for t in dates])
    date_range = list(sorted_dates[0])

    for start, end in sorted_dates:
        if start < MIN_PERIOD_DATE or start > MAX_PERIOD_DATE:
            raise ValueError("'start' date {} is out of bounds".format(start))
        if end < MIN_PERIOD_DATE or end > MAX_PERIOD_DATE:
            raise ValueError("'end' date {} is out of bounds".format(end))

        if start <= date_range[1]:
            if exclude_limits:
                if date_range[0] == MIN_PERIOD_DATE:
                    date_range[0] = start
                if MAX_PERIOD_DATE in (end, date_range[1]):
                    date_range[1] = min(date_range[1], end)
                else:
                    date_range[1] = max(date_range[1], end)
            else:
                date_range[1] = max(date_range[1], end)
        else:
            yield tuple(date_range)
            date_range[0] = start
            date_range[1] = end

    yield tuple(date_range)


def validate_field(name, value, allow_none=False):
    """Validate a given string field following a set of rules.

    The conditions to validate `value` consists on checking if its value is `None`
    and if this is allowed or not; if its value is not an empty string or if it is
    not composed only by whitespaces and/or tabs.

    :param name: name of the field to validate
    :param value: value of the field to validate
    :param allow_none: `True` if `None` values are permitted, `False` otherwise

    :raises ValueError: when a condition to validate the string is not satisfied
    :raises TypeError: when the input value is not a string and not `None`
    """
    if value is None:
        if not allow_none:
            raise ValueError("'{}' cannot be None".format(name))
        else:
            return

    if not isinstance(value, str):
        msg = "field value must be a string; {} given".format(value.__class__.__name__)
        raise TypeError(msg)

    if value == '':
        raise ValueError("'{}' cannot be an empty string".format(name))

    m = re.match(r"^\s+$", value)
    if m:
        raise ValueError("'{}' cannot be composed by whitespaces only".format(name))

    if urlparse(value).scheme:
        raise ValueError(f"'{name}' cannot be a URL")
