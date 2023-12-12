# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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

import functools
import logging
import re

from ..db import (find_individual_by_uuid,
                  find_domain,
                  search_enrollments_in_period)
from ..errors import NotFoundError
from ..models import (Individual,
                      MIN_PERIOD_DATE)


EMAIL_ADDRESS_PATTERN = re.compile(r"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$")


logger = logging.getLogger(__name__)


def recommend_affiliations(uuids, last_modified=MIN_PERIOD_DATE):
    """Recommend organizations for a list of individuals.

    Returns a generator of affiliation recommendations
    based on the email addresses of the individuals.

    The function checks if the domains of these email
    addresses of an individual match with any of the
    domains stored on the registry. If this is the case,
    the organization associated to that domain will be
    recommended.

    Each recommendation contains the uuid of the individual
    and a list with the names of the organizations that the
    individual might be enrolled.

    When no affiliation is found, an empty list will be
    returned for that uuid. When the individual is not
    found, it will not be included in the result.

    The function will not return the organizations in which
    the individual is already enrolled.

    :param uuids: list of individual keys
    :param last_modified: only affiliate individuals that have been
        modified after this date

    :returns: a generator of recommendations
    """
    if uuids:
        logger.debug(
            f"Generating affiliation recommendations; "
            f"uuids={uuids}; ..."
        )

        for uuid in uuids:
            try:
                individual = find_individual_by_uuid(uuid)
            except NotFoundError:
                continue
            else:
                yield uuid, individual.mk, _suggest_affiliations(individual)

        logger.info(f"Affiliation recommendations generated; uuids='{uuids}'")
    else:
        logger.debug(
            "Generating affiliation recommendations; uuids='all'; ..."
        )

        individuals = Individual.objects.filter(
            last_modified__gte=last_modified).order_by('mk').iterator()

        for individual in individuals:
            yield individual.mk, individual.mk, _suggest_affiliations(individual)
        logger.info("Affiliation recommendations generated; uuids=all")


def _suggest_affiliations(individual):
    """Generate a list of organizations where the individual is not affiliated."""

    orgs = set()
    domains = _retrieve_individual_email_domains(individual)

    for domain in domains:
        org_name = domain.organization.name

        if _is_enrolled(individual, org_name):
            continue

        orgs.add(org_name)

    return sorted(list(orgs))


def _retrieve_individual_email_domains(individual):
    """Return a list of possible domains linked to an individual."""

    domains = set()

    for identity in individual.identities.all():
        # Only check email address to find new affiliations
        if not identity.email:
            continue
        if not EMAIL_ADDRESS_PATTERN.match(identity.email):
            continue

        domain = identity.email.split('@')[-1]

        if domain in domains:
            continue

        dom = _find_matching_domain(domain)

        if dom:
            domains.add(dom)

    return domains


def _is_enrolled(individual, org_name):
    """Determine if an individual is enrolled to an organization."""

    result = search_enrollments_in_period(individual.mk,
                                          org_name)
    return len(result) > 0


@functools.lru_cache(512)
def _find_matching_domain(domain):
    """Look for domains and sub-domains that match with the given one."""

    keep_looking = True
    is_subdomain = False

    # Splits the domain into root domains until
    # is found in the database.
    while keep_looking:
        try:
            result = find_domain(domain)
            if is_subdomain and not result.is_top_domain:
                result = None
            keep_looking = False
        except NotFoundError:
            index = domain.find('.')
            if index > -1:
                domain = domain[index + 1:]
                is_subdomain = True
            else:
                result = None
                keep_looking = False
        except ValueError:
            result = None
            keep_looking = False
    return result
