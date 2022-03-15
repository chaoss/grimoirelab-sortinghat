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
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#     Miguel Ángel Fernández Sánchez <mafesan@bitergia.com>
#     Santiago Dueñas <sduenas@bitergia.com>
#     Quan Zhou <quan@bitergia.com>
#

import argparse
import datetime
import json
import sys

from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.grimoirelab import GrimoireLabParser


GRIMOIRELAB2SH_DESC_MSG = \
    """Export identities information from GrimoireLab files to Sorting Hat JSON format."""


def main():
    """Export identities information from GrimoireLab files"""

    args = parse_args()

    try:
        email_validation = not args.no_email_validation
        enrollment_periods_valdation = not args.no_enrollment_periods_validation
        parser = parse_grimoirelab_file(args.identities, args.organizations,
                                        args.source, email_validation, enrollment_periods_valdation)
    except (IOError, UnicodeDecodeError, InvalidFormatError) as e:
        raise RuntimeError(str(e))

    j = to_json(parser.blacklist,
                parser.identities,
                parser.organizations,
                args.source)

    try:
        args.outfile.write(j)
        args.outfile.write('\n')
    except IOError as e:
        raise RuntimeError(str(e))


def parse_args():
    """Parse arguments from the command line"""

    parser = argparse.ArgumentParser(description=GRIMOIRELAB2SH_DESC_MSG)

    parser.add_argument('-i', '--identities', type=argparse.FileType('r'),
                        help='GrimoireLab profiles/identities mapping file')
    parser.add_argument('-d', '--organizations', dest='organizations',
                        type=argparse.FileType('r'),
                        help='GrimoireLab domain to employer mapping file')
    parser.add_argument('-s', '--source', dest='source', required=True,
                        help='name of the source')
    parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Sorting Hat JSON output filename')
    parser.add_argument('--no-email-validation', dest='no_email_validation',
                        action='store_true',
                        help="do not email addresses validation")
    parser.add_argument('--no-enrollment-periods-validation', dest='no_enrollment_periods_validation',
                        action='store_true',
                        help="do not enrollment periods validation")

    args = parser.parse_args()

    if not (args.identities or args.organizations):
        parser.error('No input file passed, add --domain-employer or --identities')

    return args


def parse_grimoirelab_file(identities, organizations, source, email_validation, enrollment_periods_validation):
    """Parse GrimoireLab JSON file"""

    content_id = read_file(identities) if identities else None
    content_org = read_file(organizations) if organizations else None

    try:
        parser = GrimoireLabParser(content_id, content_org,
                                   source=source,
                                   email_validation=email_validation,
                                   enrollment_periods_validation=enrollment_periods_validation)
    except ValueError:
        s = "Error: Empty input file(s)\n"
        sys.stdout.write(s)
        sys.exit(0)

    return parser


def to_json(blacklist, uidentities, organizations, source):
    """Convert unique identities and organizations to Sorting Hat JSON format"""

    uids = {}
    orgs = {}

    # Convert to dict objects
    for uidentity in uidentities:
        uuid = uidentity.uuid

        uid = uidentity.to_dict()

        enrollments = [rol.to_dict()
                       for rol in uidentity.enrollments]
        uid['enrollments'] = enrollments

        uids[uuid] = uid

    for organization in organizations:
        domains = [{'domain': dom.domain,
                    'is_top': dom.is_top_domain}
                   for dom in organization.domains]
        domains.sort(key=lambda x: x['domain'])

        orgs[organization.name] = domains

    blacklist = [mb.excluded for mb in blacklist]

    # Generate JSON file
    obj = {'time': str(datetime.datetime.now()),
           'source': source,
           'blacklist': blacklist,
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
