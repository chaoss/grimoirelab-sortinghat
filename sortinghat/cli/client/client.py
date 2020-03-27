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
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import requests
import uri

from sgqlc.endpoint.http import HTTPEndpoint
from sgqlc.operation import Operation

from .schema import sh_schema


class SortingHatClientError(Exception):
    """SortingHat client error.

    Generic exception raised by the client when an error is found
    either with connection problems or with GraphQL queries.

    :param msg: message error
    :param errors: list of GraphQL errors; `None` when the error is
        not related to GraphQL queries
    """
    def __init__(self, msg, errors=None):
        self.msg = msg
        self.errors = errors

    def __str__(self):
        return self.msg


class SortingHatClient:
    """SortingHat client.

    This client allows to run operations in the SortingHat server
    that listens in `host` and `port`.

    After initializing an instance, call to `connect` to establish
    a communication with the server. The method `execute` allows to
    run queries and mutations defined by the server.

    :param host: host of the server
    :param port: port number used in the connection
    :param path: path to the API endpoint; by default the endpoint is in '/'
    :param user: user name to use when authentication is required
    :param password: password to use when authentication is required
    :param ssl: use SSL/TSL connection; this is the default behaviour

    :raises ValueError: when any of the given parameters is invalid
    """
    def __init__(self, host, port=9314, path=None, user=None, password=None, ssl=True):
        self.gqlc = None
        self.host = host
        self.port = port

        if not path:
            self.path = '/'
        elif not path.startswith('/'):
            self.path = '/' + path
        else:
            self.path = path

        self.user = user
        self.password = password

        try:
            scheme = 'https' if ssl else 'http'
            self.url = uri.URI(scheme=scheme,
                               host=self.host, port=self.port,
                               path=self.path)
        except (ValueError, TypeError) as exc:
            msg = "Invalid URL parameters; cause: {}".format(exc)
            raise ValueError(msg)

    def connect(self):
        """Establish a connection to the server."""

        try:
            result = requests.get(self.url, headers={'Accept': 'text/html'})
            result.raise_for_status()
        except requests.exceptions.RequestException as exc:
            msg = "Connection error; cause: {}".format(exc)
            raise SortingHatClientError(msg)

        headers = {
            'X-CSRFToken': result.cookies['csrftoken'],
            'Cookie': 'csrftoken=' + result.cookies['csrftoken']
        }

        self.gqlc = HTTPEndpoint(self.url, headers)

        if self.user and self.password:
            op = Operation(sh_schema.SortingHatMutation)
            op.token_auth(username=self.user, password=self.password).token()

            result = self.gqlc(op)

            if 'errors' in result:
                cause = result['errors'][0]['message']
                msg = "Authentication error; cause: {}".format(cause)
                raise SortingHatClientError(msg)

            auth_token = result['data']['tokenAuth']['token']
            headers['Authorization'] = "JWT {}".format(auth_token)

    def disconnect(self):
        """Disconnect the client from the server."""

        self.gqlc = None

    def execute(self, operation):
        """Execute operations in the server.

        This method allows to run GraphQL operations: queries and mutations.
        To run an operation, use `sgqlc.operation.Operation` object and a
        valid SortingHat schema.

        :param operation: GraphQL operation to execute

        :returns: a dict that maps the JSON result returned by the server

        :raises SortingHatClient: raised when either the client is not connected
            or when an error is returned while running the operation
        """
        if not self.gqlc:
            msg = "Client not connected with {}; call connect() before executing any operation"
            raise SortingHatClientError(msg.format(self.url))

        result = self.gqlc(operation)

        if 'errors' in result:
            msg = "GraphQL operation error; {} errors found".format(len(result['errors']))
            raise SortingHatClientError(msg, errors=result['errors'])

        return result
