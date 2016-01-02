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
import datetime
import json
import sys

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST


class Export(Command):
    """Export data from the registry.

    This command exports data about identities. Data are exported, by default,
    to the standard output. A file path can also be given to store the data.

    Identities are exported using the option '--identities'. Using the option
    '--source' will only export those identities which have one or more
    identities associated to that source.

    To export organizations and domains information use the option '--orgs'.
    """
    def __init__(self, **kwargs):
        super(Export, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--identities', action='store_true',
                           help="export identities")
        group.add_argument('--orgs', action='store_true',
                           help="export organizations")

        # General options
        self.parser.add_argument('--source', dest='source', default=None,
                                 help="source of the identities to export")

        # Positional arguments
        self.parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                                 default=sys.stdout,
                                 help="output file")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Export data from the registry."""

    @property
    def usage(self):
        return "%(prog)s export --identities [--source <source>] [file]\n   or: %(prog)s export --orgs [file]"

    def run(self, *args):
        """Export data from the registry.

        By default, it writes the data to the standard output. If a
        positional argument is given, it will write the data on that
        file.
        """
        params = self.parser.parse_args(args)

        with params.outfile as outfile:
            if params.identities:
                code = self.export_identities(outfile, params.source)
            elif params.orgs:
                code = self.export_organizations(outfile)
            else:
                # The running proccess never should reach this section
                raise RuntimeError("Unexpected export option")

        return code

    def export_identities(self, outfile, source=None):
        """Export identities information to a file.

        The method exports information related to unique identities, to
        the given 'outfile' output file.

        When 'source' parameter is given, only those unique identities which have
        one or more identities from the given source will be exported.

        :param outfile: destination file object
        :param source: source of the identities to export
        """
        exporter = SortingHatIdentitiesExporter(self.db)

        dump = exporter.export(source)

        try:
            outfile.write(dump)
            outfile.write('\n')
        except IOError as e:
            raise RuntimeError(str(e))

        return CMD_SUCCESS

    def export_organizations(self, outfile):
        """Export organizations information to a file.

        The method exports information related to organizations, to
        the given 'outfile' output file.

        :param outfile: destination file object
        """
        exporter = SortingHatOrganizationsExporter(self.db)

        dump = exporter.export()

        try:
            outfile.write(dump)
            outfile.write('\n')
        except IOError as e:
            raise RuntimeError(str(e))

        return CMD_SUCCESS


class IdentitiesExporter(object):
    """Abstract class for exporting identities"""

    def __init__(self, db):
        self.db = db

    def export(self, source=None):
        raise NotImplementedError


class SortingHatIdentitiesExporter(IdentitiesExporter):
    """Export identities to Sorting Hat identities format.

    This class exports the identities stored in the registry
    following the Sorting Hat identities JSON format.

    :param db: database manager
    """
    def __init__(self, db):
        super(SortingHatIdentitiesExporter, self).__init__(db)

    def export(self, source=None):
        """Export a set of unique identities.

        Method to export unique identities from the registry. Identities schema
        will follow Sorting Hat JSON format.

        When source parameter is given, only those unique identities which have
        one or more identities from the given source will be exported.

        :param source: source of the identities to export

        :returns: a JSON formatted str
        """
        uidentities = {}

        uids = api.unique_identities(self.db, source=source)

        for uid in uids:
            enrollments = [rol.to_dict()\
                           for rol in api.enrollments(self.db, uuid=uid.uuid)]

            u = uid.to_dict()
            u['identities'].sort(key=lambda x: x['id'])

            uidentities[uid.uuid] = u
            uidentities[uid.uuid]['enrollments'] = enrollments

        blacklist = [mb.excluded for mb in api.blacklist(self.db)]

        obj = {'time' : str(datetime.datetime.now()),
               'source' : source,
               'blacklist' : blacklist,
               'organizations' : {},
               'uidentities' : uidentities}

        return json.dumps(obj, default=self._json_encoder,
                          indent=4, sort_keys=True)

    def _json_encoder(self, obj):
        """Default JSON encoder"""

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(obj)


class OrganizationsExporter(object):
    """Abstract class for exporting organizations"""

    def __init__(self, db):
        self.db = db

    def export(self, source=None):
        raise NotImplementedError


class SortingHatOrganizationsExporter(OrganizationsExporter):
    """Export organizations to Sorting Hat organizations format.

    This class exports the organizations stored in the registry
    following the Sorting Hat organizations JSON format.

    :param db: database manager
    """
    def __init__(self, db):
        super(SortingHatOrganizationsExporter, self).__init__(db)

    def export(self):
        """Export a set of organizations.

        Method to export organizations from the registry. Organizations schema
        will follow Sorting Hat JSON format.

        :returns: a JSON formatted str
        """
        organizations = {}

        orgs = api.registry(self.db)

        for org in orgs:
            domains = [{'domain': dom.domain,
                        'is_top': dom.is_top_domain} \
                       for dom in org.domains]
            domains.sort(key=lambda x: x['domain'])

            organizations[org.name] = domains

        obj = {'time' : str(datetime.datetime.now()),
               'blacklist' : [],
               'organizations' : organizations,
               'uidentities' : {}}

        return json.dumps(obj, default=self._json_encoder,
                          indent=4, sort_keys=True)

    def _json_encoder(self, obj):
        """Default JSON encoder"""

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(obj)
