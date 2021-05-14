import logging
import re

import requests
import urllib3.util

from ..db import (find_individual_by_uuid)
from ..errors import NotFoundError


NAME_PATTERN = re.compile(r"(^\w+)\s\w+")


logger = logging.getLogger(__name__)


def recommend_gender(uuids, api_token=None):
    """recommend gender for a list of individuals.

    Returns a generator of gender recommendations
    based on the names or usernames of the individuals.

    :return: a generator of recommendations
    """
    logger.debug(
        f"Generating gender recommendations; "
        f"uuids={uuids}; ..."
    )

    for uuid in uuids:
        try:
            individual = find_individual_by_uuid(uuid)
        except NotFoundError:
            continue
        else:
            yield uuid, _suggest_gender(individual, uuid, api_token)

    logger.info(f"Gender recommendations generated; uuids='{uuids}'")


def _suggest_gender(individual, uuid, api_token=None):
    """Suggest the gender where the individual does not provide"""

    name = _retrieve_individual_name(individual)

    try:
        gender, accuracy = _genderize(name, api_token)
    except (requests.exceptions.RequestException,
            requests.exceptions.RetryError) as e:
        msg = "Skipping '%s' name (%s) due to a connection error."
        msg = msg % (name, uuid, str(e))
        logger.warning(msg)
        return None
    else:
        return gender, accuracy


def _retrieve_individual_name(individual):
    """Return the first name of the name linked to an individual"""

    for profile in individual.profiles.all():
        if profile.gender:
            continue
        if not profile.name:
            continue
        if not NAME_PATTERN.match(profile.name):
            continue

        first_name = NAME_PATTERN.match(profile.name).group(1).lower()

        if first_name:
            return first_name


def _genderize(name, api_token=None):
    """Fetch gender from genderize.io"""

    GENDERIZE_API_URL = "https://api.genderize.io/"
    TOTAL_RETRIES = 10
    MAX_RETRIES = 5
    SLEEP_TIME = 0.25
    STATUS_FORCELIST = [502]

    params = {
        'name': name
    }

    if api_token:
        params['api_key'] = api_token

    session = requests.Session()

    retries = urllib3.util.Retry(total=TOTAL_RETRIES,
                                 connect=MAX_RETRIES,
                                 status=MAX_RETRIES,
                                 status_forcelist=STATUS_FORCELIST,
                                 backoff_factor=SLEEP_TIME,
                                 raise_on_status=True)

    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))

    r = session.get(GENDERIZE_API_URL, params=params)
    result = r.json()

    gender = result['gender']
    prob = result.get('probability', None)

    acc = int(prob * 100) if prob else None

    return gender, acc
