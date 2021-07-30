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

from django.forms.models import model_to_dict

from ..db import (find_individual_by_uuid)
from ..errors import NotFoundError
from ..models import Identity

from .exclusion import fetch_recommender_exclusion_list

logger = logging.getLogger(__name__)


def recommend_matches(source_uuids, target_uuids, criteria, exclude=True, verbose=False):
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

    aliases = {}
    input_set = set()
    target_set = set()
    for uuid in source_uuids:
        identities = _get_identities(uuid)
        aliases[uuid] = [identity.uuid for identity in identities]
        input_set.update(identities)

    if target_uuids:
        for uuid in target_uuids:
            identities = _get_identities(uuid)
            target_set.update(identities)
    else:
        identities = Identity.objects.all()
        target_set.update(identities)

    matched = _find_matches(input_set, target_set, criteria, exclude=exclude, verbose=verbose)
    # Return filtered results
    for uuid in source_uuids:
        result = set()
        if uuid in matched.keys():
            result = matched[uuid]
        else:
            for alias in aliases[uuid]:
                if alias in matched.keys():
                    result = matched[alias]
        # Remove input uuid from results if needed
        try:
            result.remove(uuid)
        except KeyError:
            pass
        yield uuid, list(result)

    logger.info(f"Matching recommendations generated; criteria='{criteria}'")


def _find_matches(set_x, set_y, criteria, exclude, verbose):
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

    :returns: a dictionary including the set of matches found for each
        identity from `set_x`.
    """
    def _to_df(data_set):
        """Convert identities set into a Pandas `Dataframe` object"""
        df = pandas.DataFrame(data_set)
        return df.sort_values(['individual'])

    def _apply_recommender_exclusion_list(df):
        """Apply RecommenderExclusionTerm to returns the dataframes that do not match
        `name`, `username`, or `email` with this excluded list"""
        excluded = fetch_recommender_exclusion_list()
        df_excluded = df[~df['username'].isin(excluded) & ~df['email'].isin(excluded) & ~df['name'].isin(excluded)]
        return df_excluded

    def _filter_criteria(df, c):
        """Filter dataframe creating a basic subset including a given column"""
        cols = ['uuid', 'individual', c]
        cdf = df[cols]
        return cdf.dropna(subset=[c])

    def _calculate_matches_groups(grouped_uids, verbose=False):
        """Calculate groups of matching identities from identity groups.

        For instance, given a list of matched unique identities like
        A = {A, B}; B = {B,A,C}, C = {C,} and D = {D,} the output
        for keys A, B and C will be the set {A, B, C}. As D has no matches,
        it won't be included in any group and it won't be returned.

        :param grouped_uids: groups of unique identities
        :param verbose: if true, the grouping will be calculated using
            unique identities (uuids) instead of main keys from individuals.

        :returns: a dictionary including the set of matches for each
            group key.
        """
        matches = {}
        # Group by main keys from Individuals or by uuids from Identities
        col_name = 'uuid_y' if verbose else 'individual_y'

        sorted_keys = sorted(grouped_uids.groups.keys())

        while sorted_keys:
            group_key = sorted_keys.pop(0)
            uuid_set = set()
            for uuid in grouped_uids.get_group(group_key)[col_name]:
                uuid_set.add(uuid)

            for key in matches:
                prev_match = matches[key]
                if prev_match == uuid_set:
                    continue
                elif prev_match.intersection(uuid_set):
                    prev_match.update(uuid_set)
                    uuid_set = prev_match
            matches[group_key] = uuid_set

        return matches

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
        cdf_x = _filter_criteria(df_x, c)
        cdf_y = _filter_criteria(df_y, c)
        cdf = pandas.merge(cdf_x, cdf_y, on=c, how='inner')
        cdf = cdf[['individual_y', 'uuid_x', 'uuid_y']]
        cdfs.append(cdf)

    result = pandas.concat(cdfs)
    result = result.drop_duplicates()

    g_result = result.groupby(by=['uuid_x'],
                              as_index=True, sort=True)

    matched = _calculate_matches_groups(g_result, verbose=verbose)

    return matched
