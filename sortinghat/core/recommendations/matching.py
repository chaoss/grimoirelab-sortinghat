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
#


import logging
import pandas
import numpy

from collections import defaultdict

from django.conf import settings
from django.forms.models import model_to_dict

from ..db import (find_individual_by_uuid)
from ..errors import NotFoundError
from ..models import Identity, MIN_PERIOD_DATE

from .exclusion import fetch_recommender_exclusion_list

logger = logging.getLogger(__name__)

EMAIL_ADDRESS_REGEX = r"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$"
NAME_REGEX = r"^\w+\s\w+"


def recommend_matches(source_uuids, target_uuids,
                      criteria, exclude=True,
                      verbose=False, strict=True,
                      match_source=False,
                      last_modified=MIN_PERIOD_DATE):
    """Recommend identity matches for a list of individuals.

    Returns a generator of identity matches recommendations
    based on a list of criteria composed by email addresses,
    name and/or usernames of the individuals.

    The function checks if any identity from each individual
    matches with a given set of target individuals. First,
    it filters by the fields from the criteria and then it
    groups the matches by identity. Then, these groups are
    turned into sets of matching identities found among all
    the input identities set.

    Each recommendation contains the uuid of the individual
    provided in the input list and a list with the matching
    individuals or the matching identities if the `verbose`
    option is activated.

    When no matching is found for a given individual, an empty
    list is returned.

    When there are no `target_uuids`, the recommendations will
    be returned for each `source_uuids` against all identities
    on the registry.

    :param source_uuids: list of individual keys to find matches for
    :param target_uuids: list of individual keys where to find matches
    :param criteria: list of matching criteria (`email`, `name`, `username`)
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param verbose: if set to `True`, the list of results will include individual
    identities. Otherwise, results will include main keys from individuals
    :param strict: strict matching with well-formed email addresses and names
    :param match_source: only matching for identities with the same source
    :param last_modified: generate recommendations only for individuals modified after
        this date

    :returns: a generator of recommendations
    """

    def _get_identities(uuid):
        """Get the identities from a given Individual based on one of its uuids"""

        try:
            individual = find_individual_by_uuid(uuid)
        except NotFoundError:
            identities = []
        else:
            identities = individual.identities.all()

        return identities

    logger.debug(
        f"Generating matching recommendations; "
        f"source={source_uuids} target={target_uuids} criteria='{criteria}'; ..."
    )

    aliases = defaultdict(list)
    mk_sources = dict()
    input_set = set()
    target_set = set()

    if source_uuids:
        for uuid in source_uuids:
            identities = _get_identities(uuid)
            aliases[uuid] = [identity.uuid for identity in identities]
            mk_sources[uuid] = identities[0].individual.mk if len(identities) > 0 else uuid
            input_set.update(identities)
    else:
        identities = Identity.objects.select_related('individual').filter(individual__last_modified__gte=last_modified)
        input_set.update(identities)
        for identity in identities:
            aliases[identity.individual.mk].append(identity.uuid)
            mk_sources[identity.uuid] = identity.individual.mk
        source_uuids = aliases.keys()

    if target_uuids:
        for uuid in target_uuids:
            identities = _get_identities(uuid)
            target_set.update(identities)
    else:
        identities = Identity.objects.all()
        target_set.update(identities)

    matched = _find_matches(input_set, target_set, criteria, exclude=exclude, verbose=verbose, strict=strict,
                            match_source=match_source)
    # Return filtered results
    for uuid in source_uuids:
        result = set()
        if uuid in matched.keys():
            result = set(matched[uuid])
        else:
            for alias in aliases[uuid]:
                if alias in matched.keys():
                    result = set(matched[alias])
        # Remove input uuid from results if needed
        try:
            result.remove(uuid)
        except KeyError:
            pass
        yield uuid, mk_sources[uuid], sorted(result)

    logger.info(f"Matching recommendations generated; criteria='{criteria}'")


def _find_matches(set_x, set_y, criteria, exclude, verbose, strict, match_source=False):
    """Find identities matches between two sets using Pandas' library.

    This method find matches for the identities in `set_x` looking at
    the identities from `set_y` given a list of criteria.

    The identities sets are transformed into Pandas dataframes and
    they are filtered according to the different criteria, then
    merged and grouped by the identities from `set_x`. The grouped
    results are transformed into sets of results taking into account
    the results from the rest of results to generate complete sets
    of matches per each identity from `set_x`.

    :param set_x: list of individual keys to find matches for
    :param set_y: list of individual keys where to find matches
    :param criteria: list of matching criteria (`email`, `name`, `username`).
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param verbose: if set to `True`, the list of results will include individual
        identities. Otherwise, results will include main keys from individuals.
    :param strict: strict matching with well-formed email addresses and names
    :param match_source: only find matches for the same source

    :returns: a dictionary including the set of matches found for each
        identity from `set_x`.
    """
    def _to_df(data_set):
        """Convert identities set into a Pandas `Dataframe` object"""
        df = pandas.DataFrame(data_set)
        df.replace('', numpy.nan, inplace=True)
        return df.sort_values(['individual'])

    def _apply_recommender_exclusion_list(df):
        """Apply RecommenderExclusionTerm to returns the dataframes that do not match
        `name`, `username`, or `email` with this excluded list"""
        excluded = fetch_recommender_exclusion_list()
        df_excluded = df[~df['username'].isin(excluded) & ~df['email'].isin(excluded) & ~df['name'].isin(excluded)]
        return df_excluded

    def _filter_criteria(df, c, strict=True, match_source=False):
        """Filter dataframe creating a basic subset including a given column"""
        cols = ['uuid', 'individual', c]
        if match_source and c == 'username':
            cols += ['source']
            cdf = df[cols]
            cdf = cdf[cdf['source'].isin(settings.MATCH_TRUSTED_SOURCES)]
        else:
            cdf = df[cols]
        cdf = cdf.dropna(subset=[c])

        if strict and c == 'email':
            cdf = cdf[cdf['email'].str.fullmatch(EMAIL_ADDRESS_REGEX)]
        elif strict and c == 'name':
            cdf = cdf[cdf['name'].str.match(NAME_REGEX)]

        return cdf

    data_x = [model_to_dict(fl) for fl in set_x]
    data_y = [model_to_dict(fl) for fl in set_y]

    if (not data_x) or (not data_y):
        return {}

    df_x = _to_df(data_x)
    df_y = _to_df(data_y)

    if exclude:
        df_x = _apply_recommender_exclusion_list(df_x)
        df_y = _apply_recommender_exclusion_list(df_y)

    cdfs = []

    for c in criteria:
        cdf_x = _filter_criteria(df_x, c, strict, match_source)
        cdf_y = _filter_criteria(df_y, c, strict, match_source)
        if match_source and c == 'username':
            cdf = pandas.merge(cdf_x, cdf_y, on=[c, 'source'], how='inner')
        else:
            cdf = pandas.merge(cdf_x, cdf_y, on=c, how='inner')
        cdf = cdf[['individual_x', 'uuid_x', 'individual_y', 'uuid_y']]
        cdfs.append(cdf)

    result = pandas.concat(cdfs)

    col_y_name = 'uuid_y' if verbose else 'individual_y'
    col_x_name = 'uuid_x' if verbose else 'individual_x'
    result = result[[col_x_name, col_y_name]]

    # Remove duplicated
    result = result[result[col_x_name] != result[col_y_name]]
    result_g = result.groupby(col_x_name, group_keys=False)

    # Convert the dataframe to a dict of sets
    matched = result_g[col_y_name].apply(set).to_dict()

    return matched
