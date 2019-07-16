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
import logging
import re

import requests
import urllib3.util

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import NotFoundError, InvalidValueError


AUTOGENDER_COMMAND_USAGE_MSG = """%(prog)s autogender [--api-token] [--all]"""

logger = logging.getLogger(__name__)


class AutoGender(Command):
    """Auto complete gender information.

    This command autocompletes the gender information (stored in
    the profile) of unique identities. Possible vales for auto
    completing the gender data are 'male' or 'female'.

    Only those unique identities with no gender data will be updated
    unless `--all` option is given. When this option is given, gender
    information will be overwritten.

    This command uses http://genderize.io API to guess the gender of
    a name. Registered users should use the option `--api-token` for
    authentication.
    """
    def __init__(self, **kwargs):
        super(AutoGender, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Optional arguments
        self.parser.add_argument('--api-token', dest='api_token', default=None,
                                 help="genderize.io API token used for authentication")
        self.parser.add_argument('--all', dest='genderize_all', action='store_true',
                                 help="overwrite gender data for all the unique identities")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Autocomplete gender information."""

    @property
    def usage(self):
        return AUTOGENDER_COMMAND_USAGE_MSG

    def run(self, *args):
        """Autocomplete gender information."""

        params = self.parser.parse_args(args)
        api_token = params.api_token
        genderize_all = params.genderize_all
        code = self.autogender(api_token=api_token,
                               genderize_all=genderize_all)

        return code

    def autogender(self, api_token=None, genderize_all=False):
        """Autocomplete gender information of unique identities.

        Autocomplete unique identities gender using genderize.io
        API. Only those unique identities without an assigned
        gender will be updated unless `genderize_all` option is given.
        """
        name_cache = {}
        no_gender = not genderize_all
        pattern = re.compile(r"(^\w+)\s\w+")

        profiles = api.search_profiles(self.db, no_gender=no_gender)

        for profile in profiles:
            if not profile.name:
                continue

            name = profile.name.strip()
            m = pattern.match(name)

            if not m:
                continue

            firstname = m.group(1).lower()

            if firstname in name_cache:
                gender_data = name_cache[firstname]
            else:
                try:
                    gender, acc = genderize(firstname, api_token)
                except (requests.exceptions.RequestException,
                        requests.exceptions.RetryError) as e:
                    msg = "Skipping '%s' name (%s) due to a connection error. Error: %s"
                    msg = msg % (firstname, profile.uuid, str(e))
                    self.warning(msg)
                    continue

                gender_data = {
                    'gender': gender,
                    'gender_acc': acc
                }
                name_cache[firstname] = gender_data

            if not gender_data['gender']:
                continue

            try:
                api.edit_profile(self.db, profile.uuid, **gender_data)
                self.display('autogender.tmpl',
                             uuid=profile.uuid, name=profile.name,
                             gender_data=gender_data)
            except (NotFoundError, InvalidValueError) as e:
                self.error(str(e))
                return e.code

        return CMD_SUCCESS


def genderize(name, api_token=None):
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
        params['apikey'] = api_token

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
    r.raise_for_status()
    result = r.json()

    gender = result['gender']
    prob = result.get('probability', None)

    acc = int(prob * 100) if prob else None

    return gender, acc
