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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#     Eva Millán <evamillan@bitergia.com>
#


import logging
import re
from functools import lru_cache

import requests
import urllib3.util

from ..db import find_individual_by_uuid, find_identity
from ..errors import NotFoundError, InvalidValueError
from .exclusion import fetch_recommender_exclusion_list

logger = logging.getLogger(__name__)

strict_name_pattern = re.compile(r"(^\w{2,})\s+\w+")
loose_name_pattern = re.compile(r"(^\w{2,})")


def recommend_gender(uuids, exclude=True, no_strict_matching=False):
    """Recommend possible genders for a list of individuals.

    Returns a generator of gender recommendations based on the
    individuals first name, using the genderize.io API. The
    genders returned by the API are 'male' and 'female'.

    Each recommendation contains the uuid of the individual, the
    suggested gender and the accuracy of the prediction.

    When the individual does not have a name set, or the individual
    is not found, it will not be included in the result. By default,
    the name will also need to follow a 'Name LastName' pattern, but
    this validation can be disabled with the 'no_strict_matching' flag.

    :param uuids: list of individual identifiers
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param no_strict_matching: disable name validation
    :returns: a generator of recommendations
    """
    logger.debug(
        f"Generating genders recommendations; "
        f"uuids={uuids}; ..."
    )

    if exclude:
        excluded_terms = set(fetch_recommender_exclusion_list())

    strict = not no_strict_matching
    for uuid in uuids:
        try:
            if exclude and _exclude_uuid(uuid, excluded_terms):
                continue
            individual = find_individual_by_uuid(uuid)
            name = _get_individual_name(individual, strict)
            gender, accuracy = _genderize(name)
        except NotFoundError:
            message = f"Skipping {uuid}: Individual not found"
            logger.warning(message)
            continue
        except InvalidValueError:
            message = f"Skipping {uuid}: No valid name"
            logger.warning(message)
            continue
        except requests.exceptions.RequestException as e:
            message = f"Skipping {uuid} due to a connection error: {str(e)}"
            logger.warning(message)
            continue
        else:
            yield uuid, individual.mk, (gender, accuracy)

    logger.info(f"Gender recommendations generated; uuids='{uuids}'")


def _exclude_uuid(uuid, excluded_terms):
    """If one of username, email, or name are in excluded_terms
    it will return True and False if not.

    :param uuid: Individual UUID
    :excluded_terms: Set of terms (RecommenderExclusionTerm)

    :returns: True | False
    """
    identity = find_identity(uuid)
    identity_set = {identity.username, identity.name, identity.email}
    identity_set.discard(None)

    return not identity_set.isdisjoint(excluded_terms)


def _get_individual_name(individual, strict):
    """Get the first name of an individual from their profile"""

    name_pattern = loose_name_pattern

    if strict:
        name_pattern = strict_name_pattern

    try:
        name_match = name_pattern.match(individual.profile.name)
        first_name = name_match.group(1).lower()
    except Exception as e:
        raise InvalidValueError(msg=str(e))
    else:
        return first_name


@lru_cache(maxsize=128)
def _genderize(name):
    """Fetch gender from genderize.io"""

    from django.conf import settings

    api_key = settings.SORTINGHAT_GENDERIZE_API_KEY
    genderize_api_url = "https://api.genderize.io/"
    total_retries = 10
    max_retries = 5
    sleep_time = 0.25
    status_forcelist = [502]

    params = {
        'name': name
    }

    if api_key:
        params['apikey'] = api_key

    session = requests.Session()

    retries = urllib3.util.Retry(total=total_retries,
                                 connect=max_retries,
                                 status=max_retries,
                                 status_forcelist=status_forcelist,
                                 backoff_factor=sleep_time,
                                 raise_on_status=True)

    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))

    r = session.get(genderize_api_url, params=params)

    result = r.json()

    r.raise_for_status()

    gender = result.get('gender', None)
    prob = result.get('probability', None)
    acc = int(prob * 100) if prob else None

    return gender, acc
