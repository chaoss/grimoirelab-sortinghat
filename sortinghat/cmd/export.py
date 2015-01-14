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

import argparse
import datetime
import json
import sys

from sortinghat import api
from sortinghat.command import Command


class Export(Command):
    """Export data from the registry.

    This command exports data about identities. Data are exported, by default,
    to the standard output. A file path can also be given to store the data.

    Identities are exported using the option '--identities'. Using the option
    '--source' will only export those identities which have one or more
    identities associated to that source.
    """
    def __init__(self, **kwargs):
        super(Export, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--identities', action='store_true',
                           help="export identities")

        # General options
        self.parser.add_argument('--source', dest='source', default=None,
                                 help="source of the identities to export")

        # Positional arguments
        self.parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                                 default=sys.stdout,
                                 help="output file")

    @property
    def description(self):
        return """Export data from the registry."""

    @property
    def usage(self):
        return "%(prog)s export --identities [file]"

    def run(self, *args):
        """Export data from the registry.

        By default, it writes the data to the standard output. If a
        positional argument is given, it will write the data on that
        file.
        """
        params = self.parser.parse_args(args)

        if params.identities:
            self.export_identities(params.outfile, params.source)

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
        except IOError, e:
            raise RuntimeError(str(e))


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

            uidentities[uid.uuid] = uid.to_dict()
            uidentities[uid.uuid]['enrollments'] = enrollments

        obj = {'time' : str(datetime.datetime.now()),
               'source' : source,
               'uidentities' : uidentities}

        return json.dumps(obj, default=self._json_encoder,
                          indent=4, sort_keys=True)

    def _json_encoder(self, obj):
        """Default JSON encoder"""

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(obj)
