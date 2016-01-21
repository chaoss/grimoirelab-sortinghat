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

import argparse

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import AlreadyExistsError, MatcherNotSupportedError, NotFoundError, WrappedValueError
from ..matcher import create_identity_matcher
from ..matching import SORTINGHAT_IDENTITIES_MATCHERS


ADD_COMMAND_USAGE_MSG = \
"""%(prog)s add [--name <name>] [--email <email>] [--username <user>] [--source <src>] [--uuid <uuid>]
                      [--matching <matcher>] [--interactive]"""


class Add(Command):
    """Add an identity to the registry.

    This command adds a new identity to the registry. By default, a new
    unique identity will be also added an associated to the new identity.
    When <uuid> parameter is set, it only creates a new identity that will be
    associated to a unique identity defined by <uuid>.

    To add a new identity, at least one of <name>, <email> or <username> must
    be provided. The default value for <source> is 'unknown'.

    The registry considers that two identities are distinct when any value
    of the tuple <source>, <email>, <name>, <username> is different. Thus, the
    identities  id1:('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
    and id2:('mls', 'jsmith@example.com', 'John Smith', 'jsmith') will be
    registered as different identities.

    Optionally, the command can use a <matching> method to look for possible
    identities that match with. When a match is found, identities will be
    merged. When <interactive> parameter is set, the command will wait for
    the user verification to merge both identities.
    """
    def __init__(self, **kwargs):
        super(Add, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Identity options
        self.parser.add_argument('--source', dest='source', default='unknown',
                                 help="source where the identity comes from")
        self.parser.add_argument('--name', dest='name', default=None,
                                 help="name of the identity")
        self.parser.add_argument('--email', dest='email', default=None,
                                 help="email address of the identity")
        self.parser.add_argument('--username', dest='username', default=None,
                                 help="user name of the identity")
        self.parser.add_argument('--uuid', dest='uuid', default=None,
                                 help="associates identity to this unique identity")
        self.parser.add_argument('-m', '--matching', dest='matching', default=None,
                                 choices=SORTINGHAT_IDENTITIES_MATCHERS,
                                 help="match and merge using this type of matching")
        self.parser.add_argument('-i', '--interactive', action='store_true',
                                 help="run interactive mode while matching and merging")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Add an identity to the registry."""

    @property
    def usage(self):
        return ADD_COMMAND_USAGE_MSG

    def run(self, *args):
        """Add an identity to the registry."""

        params = self.parser.parse_args(args)

        code = self.add(params.source, params.email, params.name, params.username,
                        params.uuid, params.matching, params.interactive)

        return code

    def add(self, source, email=None, name=None, username=None, uuid=None,
            matching=None, interactive=False):
        """Add an identity to the registry.

        This method adds a new identity to the registry. By default, a new
        unique identity will be also added an associated to the new identity.
        When <uuid> parameter is set, it only creates a new identity that will be
        associated to a unique identity defined by <uuid>.

        The method will print the uuids associated to the new registered identity.

        Optionally, this method can look for possible identities that match with
        the new one to insert. If a match is found, that means both identities are
        likely the same. Therefore, both identities would be merged into one. The
        algorithm used to search for matches will be defined by <matching> parameter.
        Please take into account that both unique identities will be always merged
        into the one from the registry, not into the new one.

        When <interactive> parameter is set to True, the user will have to confirm
        whether these to identities should be merged into one. By default, the method
        is set to False.

        :param source: data source
        :param email: email of the identity
        :param name: full name of the identity
        :param username: user name used by the identity
        :param uuid: associates the new identity to the unique identity
            identified by this id
        :param matching: type of matching used to merge existing identities
        :param interactive: interactive mode for merging identities, only available
            when <matching> parameter is set
        """
        matcher = None

        if matching:
            try:
                blacklist = api.blacklist(self.db)
                matcher = create_identity_matcher(matching, blacklist)
            except MatcherNotSupportedError as e:
                self.error(str(e))
                return e.code

        try:
            new_uuid = api.add_identity(self.db, source, email, name, username, uuid)
            uuid = uuid or new_uuid
            self.display('add.tmpl', id=new_uuid, uuid=uuid)

            if matcher:
                self.__merge_on_matching(uuid, matcher, interactive)
        except (AlreadyExistsError, NotFoundError, WrappedValueError) as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS

    def __merge_on_matching(self, uuid, matcher, interactive):
        matches = api.match_identities(self.db, uuid, matcher)

        u = api.unique_identities(self.db, uuid)[0]

        for m in matches:
            if m.uuid == uuid:
                continue

            merged = self.__merge(u, m, interactive)

            if not merged:
                continue

            # Swap uids to merge with those that could
            # remain on the list with updated info
            u = api.unique_identities(self.db, m.uuid)[0]

    def __merge(self, uid, match, interactive):
        self.display('match.tmpl', uid=uid, match=match)

        # By default, always merge
        merge = True

        if interactive:
            merge = self.__read_verification()

        if not merge:
            return False

        api.merge_unique_identities(self.db, uid.uuid, match.uuid)

        self.display('merge.tmpl', from_uuid=uid.uuid, to_uuid=match.uuid)

        return True

    def __read_verification(self):
        answer = None

        while answer not in ['y', 'Y', 'n', 'N', '']:
            try:
                answer = raw_input("Merge unique identities [Y/n]? ")
            except EOFError:
                return False

        if answer in ['n', 'N']:
            return False

        return True
