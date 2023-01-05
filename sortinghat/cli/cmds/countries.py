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

import click

from sgqlc.operation import Operation

from ..client import SortingHatSchema
from ..utils import (connect,
                     display,
                     sh_client_cmd_options,
                     sh_client)


def validate_code(ctx, param, value):
    if value is None:
        return None
    elif len(value) == 2 and value.isalpha():
        return value
    else:
        msg = "country code must be a 2 alpha characters long"
        raise click.BadParameter(msg)


def validate_term(ctx, param, value):
    if value is None:
        return None
    elif len(value) > 2:
        return value
    else:
        msg = "term must be at least 3 characters long"
        raise click.BadParameter(msg)


@click.command()
@sh_client_cmd_options
@click.option('--code', callback=validate_code,
              help="Country code to search for.")
@click.option('--term', callback=validate_term,
              help="Look for countries which match this term.")
@sh_client
def countries(ctx, code, term, **extra):
    """Show information about countries.

    This command displays information related to the countries
    stored in the registry.

    When <code> or <term> are given, the command will look for
    those countries that match the criteria. Take into account
    <code> is a country identifier composed by two letters
    (e.g ES or US).
    """
    with connect(ctx.obj) as conn:
        for cs in _fetch_countries(conn, code=code, term=term):
            display('countries.tmpl', nl=False, countries=cs)


def _fetch_countries(client, **kwargs):
    """Run a server operation to get the list of countries."""

    filters = {k: v for k, v in kwargs.items() if v is not None}
    page = 1
    paginate = True

    while paginate:
        op = _generate_countries_operation(page, filters)

        result = client.execute(op)

        data = op + result
        paginate = data.countries.page_info.has_next
        page += 1
        yield data.countries.entities


def _generate_countries_operation(page, filters):
    """Define an operation to get the list of countries."""

    args = {
        'page': page
    }

    if filters:
        args['filters'] = filters

    op = Operation(SortingHatSchema.Query)
    op.countries(**args)

    # Select page information
    op.countries().page_info.has_next()

    # Select countries information
    country = op.countries().entities()

    country.code()
    country.name()

    return op
