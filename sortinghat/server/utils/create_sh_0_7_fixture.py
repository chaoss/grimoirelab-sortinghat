#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Bitergia
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
#   Quan Zhou <quan@bitergia.com>
#


import argparse
from datetime import datetime
import json
import logging
import sys

from pytz import timezone
import MySQLdb


DESC_MSG = """This script creates a fixture JSON file given the old SortingHat (0.7.x)
database to load into the new SortingHat using Django.

    Execute:
    ```
    $ python3 create_sh_0_7_fixture.py test_sh -o test_sh_fixture.json
    [2021-06-10 17:29:11,461][INFO] Start creating fixture file for test_sh
    [2021-06-10 17:29:21,252][INFO] Fixture file created to test_sh_fixture.json
    ```

    First you have to create the new database.
    ```
    mysql> CREATE DATABASE new_sh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;
    ```
    Execute Django migrate.
    ```
    $ python3 manage.py migrate --settings=config.settings.devel
    ```
    Load fixture JSON file using Django
    ```
    $ python3 manage.py loaddata test_sh_fixture.json --settings=config.settings.devel
    Installed 148542 object(s) from 1 fixture(s)
    ```
"""

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S%z'
TZ = timezone('UTC')

# Mappings

COUNTRY_MAPPING = {
    "code": "code",
    "name": "name",
    "alpha3": "alpha3"
}

DOMAIN_MAPPING = {
    "id": "id",
    "domain": "domain",
    "is_top_domain": "is_top_domain",
    "organization_id": "organization"
}

ENROLLMENT_MAPPING = {
    "id": "id",
    "start": "start",
    "end": "end",
    "organization_id": "group",
    "uuid": "individual"
}

IDENTITY_MAPPING = {
    "id": "uuid",
    "name": "name",
    "email": "email",
    "username": "username",
    "source": "source",
    "uuid": "individual",
    "last_modified": "last_modified"
}

MATCHING_BLACKLIST_MAPPING = {
    "excluded": "term"
}

ORGANIZATION_MAPPING = {
    "id": "id",
    "name": "name"
}

PROFILE_MAPPING = {
    "uuid": "individual",
    "name": "name",
    "email": "email",
    "gender": "gender",
    "gender_acc": "gender_acc",
    "is_bot": "is_bot",
    "country_code": "country"
}

INDIVIDUAL_MAPPING = {
    "uuid": "mk",
    "last_modified": "last_modified"
}

TABLE_MAPPING = {
    "countries": {
        'model': "core.country",
        'mapping': COUNTRY_MAPPING
    },
    "domains_organizations": {
        'model': "core.domain",
        'mapping': DOMAIN_MAPPING
    },
    "enrollments": {
        'model': "core.enrollment",
        'mapping': ENROLLMENT_MAPPING
    },
    "identities": {
        'model': "core.identity",
        'mapping': IDENTITY_MAPPING
    },
    "matching_blacklist": {
        'model': "core.recommenderexclusionterm",
        'mapping': MATCHING_BLACKLIST_MAPPING
    },
    "organizations": {
        'model': "core.organization",
        'mapping': ORGANIZATION_MAPPING
    },
    "profiles": {
        'model': "core.profile",
        'mapping': PROFILE_MAPPING
    },
    "uidentities": {
        'model': "core.individual",
        'mapping': INDIVIDUAL_MAPPING
    }
}

logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('create_sh_0_7_fixture')


def main():
    args = parse_args()

    if args.debug_mode:
        logger.setLevel(logging.DEBUG)

    create_sh_fixture(db_host=args.host,
                      db_port=args.port,
                      db_user=args.user,
                      db_password=args.password,
                      database=args.database,
                      output_fh=args.output)


def create_sh_fixture(db_host, db_port, db_user, db_password, database, output_fh):
    logger.info(f"Start creating fixture file for {database}")

    conn = MySQLdb.connect(host=db_host,
                           port=db_port,
                           user=db_user,
                           password=db_password,
                           database=database)
    fixtures = generate_sortinghat_fixtures(conn)
    conn.close()

    write_json(output_fh, fixtures)

    logger.info(f"Fixture file created to {output_fh.name}")


def parse_args():
    parser = argparse.ArgumentParser(description=DESC_MSG,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("database",
                        help="MariaDB/MySQL database")
    parser.add_argument("--host",
                        default="localhost",
                        help="MariaDB/MySQL host (by default = 'localhost')")
    parser.add_argument("--port",
                        default=3306,
                        type=int,
                        help="MariaDB/MySQL port (by default = 3306)")
    parser.add_argument("-u", "--user",
                        default="root",
                        help="MariaDB/MySQL user (by default = 'root')")
    parser.add_argument("-p", "--password",
                        default="",
                        help="MariaDB/MySQL password (by default = '')")
    parser.add_argument('-o', '--output', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help="Output filepath; stdout by default")
    parser.add_argument('-g', dest='debug_mode', action='store_true',
                        default=False,
                        help="Enable debug mode")
    args = parser.parse_args()

    return args


def generate_sortinghat_fixtures(conn):
    """Generate SortingHat fixture.

    :param conn: MySQL connection

    :return: a list of dict objects that contain the fixture data
    """
    fixtures = []

    timestamp = TZ.localize(datetime.now()).strftime(TIMESTAMP_FORMAT)

    for table in TABLE_MAPPING.keys():
        logger.debug(f"Table {table} start")
        fixtures += generate_fixture(conn, table, timestamp)
        logger.debug(f"Table {table} finished")

    return fixtures


def generate_fixture(conn, table, timestamp):
    """Create fixture data of the given table

    :param conn: MySQL connection
    :param table: table
    :param timestamp: Datetime now

    :return: a list of dict objects that contain the fixture data
    """
    fixtures = [
        map_row_data(row, table, timestamp)
        for row in fetch_data(conn, table)
    ]
    logger.debug(f"{table} total items added {len(fixtures)}")

    return fixtures


def fetch_data(conn, table):
    """Fetch data from MySQL and return a iterator with the next format:

        - Keys: column names.
        - Values: row values.
        ```
        {
            "key1": "value1",
            "key2": "value2",
            ...
        }
        ```

    :param conn: MySQL connection
    :param table: table name

    :return: iterator of table rows
    """
    headers = sorted(TABLE_MAPPING[table]['mapping'].keys())
    query = 'SELECT ' + ','.join(headers) + f' FROM {table};'
    logger.debug(f"MySQL: {query}")

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            data = dict(zip(headers, row))
            yield data
    except Exception as ex:
        logger.error(ex)
        raise ex


def map_row_data(data, table, timestamp):
    """Map row data to the Django fixture format.

    The format is:
    ```
    {
        "fields": {
            "<key1>": "<value1>",
            ...
        },
        "model": "<model>"
    }
    ```

    return: fixture entry
    """

    def format_if_datetime(dt):
        value = TZ.localize(dt).strftime(TIMESTAMP_FORMAT) if isinstance(dt, datetime) else dt
        return value

    mapping = TABLE_MAPPING[table]['mapping']

    fields = {
        mapping[key]: format_if_datetime(value)
        for key, value in data.items()
    }
    fields['created_at'] = timestamp
    fields['last_modified'] = timestamp

    if table == "organizations":
        fields['depth'] = 1
        fields['path'] = "{0:0=4d}".format(fields['id'])

    entry = {
        "fields": fields,
        "model": TABLE_MAPPING[table]['model']
    }

    return entry


def write_json(fd, data):
    """Write data in JSON format to a file descriptor."""

    try:
        fd.write(json.dumps(data, indent=4, sort_keys=True))
        fd.write('\n')
    except IOError as ex:
        raise RuntimeError(str(ex))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        s = "\n\nReceived Ctrl-C or other break signal. Exiting.\n"
        sys.stdout.write(s)
        sys.exit(0)
    except RuntimeError as e:
        s = f"Error: {e}\n"
        sys.stderr.write(s)
        sys.exit(1)
