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

import collections

from ..errors import RecommendationEngineError
from .affiliation import recommend_affiliations
from .matching import recommend_matches
from .gender import recommend_gender


Recommendation = collections.namedtuple(
    'Recommendation',
    ['key', 'type', 'options']
)


class RecommendationEngine:
    """Recommender engine for SortingHat.

    This class implements a basic recommendation system that
    generates a set of suggestions regarding the data stored
    on the registry.
    """
    RECOMMENDATION_TYPES = {
        'affiliation': recommend_affiliations,
        'matches': recommend_matches,
        'gender': recommend_gender
    }

    def recommend(self, name, *args, **kwargs):
        """Generate a list of recommendations.

        Returns a generator of recommendations of type `name`.
        Specific arguments can be passed using positional or
        keyword arguments.

        Recommendations are tuples of the class `Recommendation`,
        that contain a `key` and a `type` to identify it, and
        a list of `options` or suggestions.

        When `name` is not a valid type of recommendation, the
        method will raise a `RecommendationEngineError`
        exception.

        :param name: recommendation type
        :param *args: positional arguments to run the engine
        :param **args: keyword arguments to run the engine

        :returns: a generator of `Recommendation`

        :raises RecommendationEngineError: when any error is
            found in the engine
        """
        try:
            recommender = self.RECOMMENDATION_TYPES[name]
        except KeyError:
            msg = "Unknown '{}' recommendation type".format(name)
            raise RecommendationEngineError(msg=msg)

        return self._generate_recommendations(name,
                                              recommender,
                                              *args,
                                              **kwargs)

    @staticmethod
    def _generate_recommendations(name, recommender, *args, **kwargs):
        """Generator of recommendations."""

        for rec in recommender(*args, **kwargs):
            yield Recommendation(rec[0], name, rec[1])

    @classmethod
    def types(cls):
        """List of supported types of recommendations."""

        return [v for v in cls.RECOMMENDATION_TYPES.keys()]
