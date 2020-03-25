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

from ..client import (SortingHatClientError,
                      SortingHatSchema)
from ..utils import (sh_client_cmd_options,
                     sh_client)


@click.group()
@sh_client_cmd_options
@sh_client
def orgs(ctx, user, password, host, port, server_path, disable_ssl):
    """List, add or delete organizations and domains on the registry."""

    pass


@orgs.command()
@click.argument('organization')
@click.argument('domain', required=False)
@click.option('--top-domain', 'is_top_domain', is_flag=True,
              help="Set the domain as a top domain.")
@click.pass_obj
def add(client, organization, domain, is_top_domain):
    """Add organizations and domains to the registry.

    This command will add a given <organization> or <domain>
    to the registry, but not both at the same time.

    When <organization> is the only parameter given, a new
    organization will be added to the registry.

    When both parameters are given, the command will create
    a new <domain>, assigning it to <organization>.
    Take into account <organization> must exist before
    adding the domain. Moreover, a domain can only be assigned
    to one organization.

    A new domain can also be set as a top domain using
    '--top-domain' flag. This might be useful to avoid
    the insertion of sub-domains that belong to the same
    organization. For example, "eu.example.com" and "us.example.com"
    can be replaced by "example.com" as a top domain.

    ORGANIZATION: name of the organization to be added

    DOMAIN: domain to be added to <organization>
    """
    client.connect()

    if domain is None:
        _add_organization(client, name=organization)
    else:
        _add_domain(client,
                    organization=organization,
                    domain=domain,
                    is_top_domain=is_top_domain)


def _add_organization(client, **kwargs):
    """Run a server operation to add an organization to the registry."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.add_organization(**args)
    op.add_organization.organization.name()

    try:
        result = client.execute(op)
    except SortingHatClientError as exc:
        error = exc.errors[0]
        new_exc = click.ClickException(error['message'])
        new_exc.exit_code = error['extensions']['code']
        raise new_exc
    else:
        return result['data']['addOrganization']['organization']['name']


def _add_domain(client, **kwargs):
    """Run a server operation to add a domain to the registry."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.add_domain(**args)
    op.add_domain.domain.domain()

    try:
        result = client.execute(op)
    except SortingHatClientError as exc:
        error = exc.errors[0]
        new_exc = click.ClickException(error['message'])
        new_exc.exit_code = error['extensions']['code']
        raise new_exc
    else:
        return result['data']['addDomain']['domain']['domain']


@orgs.command()
@click.argument('organization')
@click.argument('domain', required=False)
@click.pass_obj
def rm(client, organization, domain):
    """Remove organizations and domains from the registry.

    This command removes the given <organization> or <domain>
    from the registry, but not both at the same time.

    When <organization> is the only parameter given, it will be
    removed from the registry, including those domains related
    to it.

    When both parameters are given, only <domain> will be
    deleted. The <organization> must exist in the registry
    before removing the domain.

    ORGANIZATION: name of the organization to remove

    DOMAIN: domain to remove
    """
    if domain is None:
        _remove_organization(client, name=organization)
    else:
        _check_organization_domain(client, organization, domain)
        _remove_domain(client, domain=domain)


def _remove_organization(client, **kwargs):
    """Run a server operation to remove an organization from the registry."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.delete_organization(**args)
    op.delete_organization.organization.name()

    try:
        result = client.execute(op)
    except SortingHatClientError as exc:
        error = exc.errors[0]
        new_exc = click.ClickException(error['message'])
        new_exc.exit_code = error['extensions']['code']
        raise new_exc
    else:
        return result['data']['deleteOrganization']['organization']['name']


def _remove_domain(client, **kwargs):
    """Run a server operation to remove a domain from the registry."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.delete_domain(**args)
    op.delete_domain.domain.domain()

    try:
        result = client.execute(op)
    except SortingHatClientError as exc:
        error = exc.errors[0]
        new_exc = click.ClickException(error['message'])
        new_exc.exit_code = error['extensions']['code']
        raise new_exc
    else:
        return result['data']['deleteDomain']['domain']['domain']


def _check_organization_domain(client, organization, domain):
    """Run a server operation to check if a domain belongs to an organization."""

    op = Operation(SortingHatSchema.Query)
    filters = SortingHatSchema.OrganizationFilterType(name=organization)
    op.organizations(filters=filters)
    op.organizations.page_info.total_results()
    op.organizations.entities.domains.domain()

    try:
        result = client.execute(op)
    except SortingHatClientError as exc:
        error = exc.errors[0]
        new_exc = click.ClickException(error['message'])
        new_exc.exit_code = error['extensions']['code']
        raise new_exc

    data = op + result

    total = data.organizations.page_info.total_results
    if total == 0:
        error = "{} not found in the registry".format(organization)
        exc = click.ClickException(error)
        exc.exit_code = 9
        raise exc

    org_domains = data.organizations.entities[0].domains
    found_domains = [domain.domain for domain in org_domains]

    if domain not in found_domains:
        error = "{} not found in the registry".format(domain)
        exc = click.ClickException(error)
        exc.exit_code = 9
        raise exc
