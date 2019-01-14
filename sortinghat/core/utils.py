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

import unicodedata


def unaccent_string(unistr):
    """Convert a Unicode string to its canonical form without accents.

    This allows to convert Unicode strings which include accent
    characters to their unaccent canonical form. For instance,
    characters 'Ê, ê, é, ë' are considered the same character as 'e';
    characters 'Ĉ, ć' are the same as 'c'.

    :param unistr: Unicode string to unaccent

    :returns: Unicode string on its canonical form
    """
    if not isinstance(unistr, str):
        msg = "argument must be a string; {} given".format(unistr.__class__.__name__)
        raise TypeError(msg)

    cs = [c for c in unicodedata.normalize('NFD', unistr)
          if unicodedata.category(c) != 'Mn']
    string = ''.join(cs)

    return string
