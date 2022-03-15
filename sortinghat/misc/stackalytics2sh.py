#!/usr/bin/env python
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

import argparse
import datetime
import json
import sys

from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.stackalytics import StackalyticsParser


STACKALYTICS2SH_DESC_MSG = \
    """Convert Stackalytics file into a Sorting Hat JSON format."""


def main():
    """Export identities and organizations data from a Stackalytics file"""

    args = parse_args()

    try:
        parser = parse_stackalytics_file(args.infile, args.source)
    except (IOError, UnicodeDecodeError, InvalidFormatError) as e:
        raise RuntimeError(str(e))

    j = to_json(parser.identities, parser.organizations, args.source)

    try:
        args.outfile.write(j)
        args.outfile.write('\n')
    except IOError as e:
        raise RuntimeError(str(e))


def parse_args():
    """Parse arguments from the command line"""

    parser = argparse.ArgumentParser(description=STACKALYTICS2SH_DESC_MSG)

    parser.add_argument('-s', '--source', dest='source', required=True,
                        help='name of the source')
    parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Sorting Hat JSON output filename')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='Stackalytics JSON file')

    return parser.parse_args()


def parse_stackalytics_file(infile, source):
    """Parse Stackalytics JSON file"""

    content = read_file(infile)

    parser = StackalyticsParser(content, source=source)

    return parser


def to_json(uidentities, organizations, source):
    """Convert unique identities and organizations to Sorting Hat JSON format"""

    uids = {}
    orgs = {}

    # Convert to dict objects
    for uidentity in uidentities:
        uuid = uidentity.uuid

        uid = uidentity.to_dict()
        uid['identities'].sort(key=lambda x: x['uuid'])

        enrollments = [rol.to_dict()
                       for rol in uidentity.enrollments]
        uid['enrollments'] = enrollments

        uids[uuid] = uid

    for organization in organizations:
        domains = [
            {
                'domain': domain.domain,
                'is_top': False
            } for domain in organization.domains
        ]
        orgs[organization.name] = domains

    # Generate JSON file
    obj = {'time': str(datetime.datetime.now()),
           'source': source,
           'blacklist': [],
           'organizations': orgs,
           'uidentities': uids}

    return json.dumps(obj, default=json_encoder,
                      indent=4, sort_keys=True)


def json_encoder(obj):
    """Default JSON encoder"""

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        return json.JSONEncoder.default(obj)


def read_file(f):
    content = f.read()
    return content


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        s = "\n\nReceived Ctrl-C or other break signal. Exiting.\n"
        sys.stdout.write(s)
        sys.exit(0)
    except RuntimeError as e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
