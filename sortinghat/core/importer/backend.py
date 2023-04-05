# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import logging

import sortinghat.core.importer.backends
from grimoirelab_toolkit.introspect import inspect_signature_parameters
from .. import api, db
from ..errors import (LoadError,
                      InvalidValueError,
                      AlreadyExistsError,
                      NotFoundError,
                      DuplicateRangeError)
from ..importer.utils import find_backends
from ..models import MIN_PERIOD_DATE, MAX_PERIOD_DATE

logger = logging.getLogger(__name__)


class IdentitiesImporter:
    """Abstract class for identities importers.

    Base class for importers that fetch identities from a URL.

    To avoid a :class:`NotImplementedError`, derived classes have to implement
    or define:
     - :func:`get_individuals`, that returns a list of individuals with
        their identities.
     - :func:`__init__` (optional), with the required arguments that will
        be asked for the user in the UI.
     - :data:`NAME`, to define the name of the backend used for the UI.
    """
    NAME = None

    def __init__(self, ctx, url):
        self.ctx = ctx
        self.url = url

    def get_individuals(self):
        """Fetch individuals.

        The method retrieves individuals from a specific source. It should
        return a list of individuals with their related identities.

        Each backend implements this method.
        """
        raise NotImplementedError

    def import_identities(self):
        """Import individuals information on the registry.

        New individuals, organizations and enrollment data will be added to the
        registry. It checks if the identity already exists on the registry, if not,
        it will create a new one.

        Identities that belongs to the same individual will be merged, but this method
        doesn't run matching algorithms.
        """
        logger.info("Importing individuals")

        individuals = self.get_individuals()

        total = 0
        for individual in individuals:
            uuid, nidentities = self.__load_identities(individual.identities)
            if uuid:
                self.__load_enrollments(individual.enrollments, uuid)
            if uuid and individual.profile:
                # Use the profile defined in the individual
                self.__load_profile(individual.profile, uuid)
            total += nidentities

        logger.info("Individuals loaded")
        return total

    def __load_identities(self, identities):
        """Load identities related with a specific individual.

        This method imports a list of identities that belongs to the
        same individual.

        Those identities that belongs to different individuals will be
        merged. If not exists any of the identities, a new individual and
        profile will be created for all of them.

        :return 'uuid' of the individual and number of identities imported
        """
        uuid = None
        nidentities = 0

        for identity in identities:
            try:
                new_identity = api.add_identity(ctx=self.ctx,
                                                source=identity.source,
                                                email=identity.email,
                                                name=identity.name,
                                                username=identity.username,
                                                uuid=uuid)
                if not uuid:
                    uuid = new_identity.individual.mk
                nidentities += 1
            except InvalidValueError as e:
                logger.warning(str(e))
            except AlreadyExistsError as e:
                stored_identity = db.find_identity(e.eid)
                stored_uuid = stored_identity.individual.mk

                if not uuid:
                    uuid = stored_uuid

                if uuid != stored_uuid:
                    if stored_identity.individual.is_locked:
                        logger.warning(f"Individual {stored_uuid} is locked. Not merging.")
                        continue
                    logger.info(f"Merging {uuid} and {stored_uuid}")
                    api.merge(self.ctx, [uuid], stored_uuid)
                    uuid = stored_uuid

        return uuid, nidentities

    def __load_enrollments(self, enrollments, uuid):
        """Load enrollments for an individual"""

        for enrollment in enrollments:
            organization_name = enrollment.organization.name
            if not organization_name:
                continue

            try:
                api.add_organization(self.ctx, name=organization_name)
            except AlreadyExistsError:
                pass
            except Exception as e:
                logger.error(f"Error adding organization {organization_name}: {e}")
                continue
            if not enrollment.start:
                enrollment.start = MIN_PERIOD_DATE
            if not enrollment.end:
                enrollment.end = MAX_PERIOD_DATE
            from_date = max(MIN_PERIOD_DATE, enrollment.start)
            to_date = min(MAX_PERIOD_DATE, enrollment.end)

            try:
                api.enroll(self.ctx, uuid=uuid, group=organization_name,
                           from_date=from_date, to_date=to_date)
            except AlreadyExistsError:
                pass
            except DuplicateRangeError:
                pass
            except (ValueError, NotFoundError) as e:
                raise LoadError(cause=str(e))

    def __load_profile(self, profile, uuid):
        """Update the profile of the given individual.

        This method updates the profile of the individual using the
        attributes defined in the profile object.

        If any of the attributes is None or empty, it is not updated.
        """
        params = {}
        if profile.name:
            params['name'] = profile.name
        if profile.email:
            params['email'] = profile.email
        if profile.gender:
            params['gender'] = profile.gender
        if profile.gender_acc:
            params['gender_acc'] = profile.gender_acc
        if profile.is_bot:
            params['is_bot'] = profile.is_bot
        if profile.country_code:
            params['country_code'] = profile.country_code

        api.update_profile(self.ctx, uuid, **params)


def find_import_identities_backends():
    """Find backends that implements IdentitiesImporter.

    This function returns a dictionary of the backends that
    implements this function. The key is the name of the backend
    and the value is a dictionary with the class and the arguments
    that accept.
    """
    backends_found = {}
    backends = find_backends(sortinghat.core.importer.backends, IdentitiesImporter)
    for klass in backends.values():
        params = inspect_signature_parameters(klass.__init__, ('self', 'cls', 'ctx'))
        params = [arg.name for arg in params]
        backends_found[klass.NAME] = {
            'class': klass,
            'args': params
        }
    return backends_found
