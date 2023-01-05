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


import hashlib
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


def generate_uuid(source, email=None, name=None, username=None):
    """Generate a UUID related to identity data.

    Based on the input data, the function will return the UUID
    associated to an identity. On this version, the UUID will
    be the SHA1 of `source:email:name:username` string.

    This string is case insensitive, which means same values
    for the input parameters in upper or lower case will produce
    the same UUID.

    The value of `name` will converted to its unaccent form which
    means same values with accent or unaccent chars (i.e 'ö and o')
    will generate the same UUID.

    For instance, these combinations will produce the same UUID:
        ('scm', 'jsmith@example.com', 'John Smith', 'jsmith'),
        ('scm', 'jsmith@example,com', 'Jöhn Smith', 'jsmith'),
        ('scm', 'jsmith@example.com', 'John Smith', 'JSMITH'),
        ('scm', 'jsmith@example.com', 'john Smith', 'jsmith')

    :param source: data source
    :param email: email of the identity
    :param name: full name of the identity
    :param username: user name used by the identity

    :returns: a universal unique identifier for Sorting Hat

    :raises ValueError: when source is `None` or empty; each one
        of the parameters is `None`; or the parameters are empty.
    """
    def to_str(value, unaccent=False):
        s = str(value)
        if unaccent:
            return unaccent_string(s)
        else:
            return s

    if source is None:
        raise ValueError("'source' cannot be None")
    if source == '':
        raise ValueError("'source' cannot be an empty string")
    if not (email or name or username):
        raise ValueError("identity data cannot be empty")

    s = ':'.join((to_str(source),
                  to_str(email),
                  to_str(name, unaccent=True),
                  to_str(username))).lower()
    s = s.encode('UTF-8', errors="surrogateescape")

    sha1 = hashlib.sha1(s)
    uuid = sha1.hexdigest()

    return uuid
