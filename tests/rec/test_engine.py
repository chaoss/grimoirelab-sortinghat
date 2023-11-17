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

from django.test import TestCase

from sortinghat.core.errors import RecommendationEngineError
from sortinghat.core.recommendations.engine import RecommendationEngine


UNKNOWN_TYPE_ERROR = "Unknown '{}' recommendation type"
ENGINE_ERROR = "Engine error"


# Mock recommendations
options = ['A', 'B', 'C']


def generate_recommendations():
    """Generate fake recommendations."""

    for i in range(len(options)):
        yield (i, i, options[0:i])


def generate_error():
    """Generate fake errors."""

    raise RecommendationEngineError(msg=ENGINE_ERROR)


class MockEngine(RecommendationEngine):
    """Mocks RecommendationEngine"""

    RECOMMENDATION_TYPES = {
        'mock': generate_recommendations,
        'error': generate_error
    }


class TestRecommendationEngine(TestCase):
    """Unit tests for RecommendationEngine"""

    def test_recommend(self):
        """Check it the engine produces a list of recommendations"""

        engine = MockEngine()
        recs = [rec for rec in engine.recommend('mock')]

        self.assertEqual(len(recs), 3)

        for i in range(len(options)):
            rec = recs[i]
            self.assertEqual(rec.key, i)
            self.assertEqual(rec.type, 'mock')
            self.assertListEqual(rec.options, options[0:i])

    def test_generator_error(self):
        """Check if an error is raised when recommendations are generated"""

        engine = MockEngine()

        with self.assertRaisesRegex(RecommendationEngineError,
                                    ENGINE_ERROR):
            _ = [rec for rec in engine.recommend('error')]

    def test_unknown_type(self):
        """Check if an error is raised when a recommendation type does not exist"""

        engine = RecommendationEngine()
        error = UNKNOWN_TYPE_ERROR.format('mytype')

        with self.assertRaisesRegex(RecommendationEngineError,
                                    error):
            engine.recommend('mytype')

    def test_types(self):
        """Test the list of supported recommendation types"""

        types = RecommendationEngine.types()
        self.assertListEqual(types, ['affiliation', 'matches', 'gender'])
