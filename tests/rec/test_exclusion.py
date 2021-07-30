# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Bitergia
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
#     Quan Zhou <quan@bitergia.com>
#


from django.contrib.auth import get_user_model
from django.test import TestCase

import sortinghat.core.errors
from sortinghat.core.context import SortingHatContext
from sortinghat.core.recommendations.exclusion import (add_recommender_exclusion_term,
                                                       delete_recommend_exclusion_term,
                                                       fetch_recommender_exclusion_list)


class TestRecommenderExclusionTerm(TestCase):
    """Unit tests for recommender exclusion"""

    def setUp(self):
        """Initialize"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    def test_add_recommender_exclusion_term(self):
        """Check add a term to recommender exclusion term"""

        # Add terms to RecommenderExclusionTerm
        add_recommender_exclusion_term(self.ctx, "jsmith")
        add_recommender_exclusion_term(self.ctx, "John Smith")

        expected_terms = ["jsmith", "John Smith"]

        # Fetch terms from RecommenderExclusionTerm
        terms = fetch_recommender_exclusion_list()

        self.assertEqual(len(terms), 2)
        self.assertListEqual(terms, expected_terms)

    def test_add_recommender_exclusion_term_not_valid(self):
        """Check add not valid terms to recommender exclusion term"""

        with self.assertRaises(sortinghat.core.errors.InvalidValueError):
            add_recommender_exclusion_term(self.ctx, "")
            add_recommender_exclusion_term(self.ctx, None)

        expected_terms = []

        # Fetch terms from RecommenderExclusionTerm
        terms = fetch_recommender_exclusion_list()

        self.assertEqual(len(terms), 0)
        self.assertListEqual(terms, expected_terms)

    def test_delete_recommender_exclusion_term(self):
        """Check delete a term from recommender exclusion term"""

        # Add terms to RecommenderExclusionTerm
        add_recommender_exclusion_term(self.ctx, "jsmith")
        add_recommender_exclusion_term(self.ctx, "John Smith")

        # Remove term from RecommenderExclusionTerm
        delete_recommend_exclusion_term(self.ctx, "John Smith")

        expected_term = ["jsmith"]

        # Fetch term from RecommenderExclusionTerm
        term = fetch_recommender_exclusion_list()

        self.assertEqual(len(term), 1)
        self.assertListEqual(term, expected_term)

    def test_delete_recommender_exclusion_term_not_valid(self):
        """Check delete not valid terms from recommender exclusion term"""

        with self.assertRaises(sortinghat.core.errors.InvalidValueError):
            delete_recommend_exclusion_term(self.ctx, "")
            delete_recommend_exclusion_term(self.ctx, None)

    def test_delete_recommender_exclusion_empty(self):
        """Check delete a term from recommender exclusion when it is empty"""

        with self.assertRaises(sortinghat.core.errors.NotFoundError):
            delete_recommend_exclusion_term(self.ctx, "John Smith")

        # Fetch term from RecommenderExclusionTerm
        term = fetch_recommender_exclusion_list()

        self.assertEqual(len(term), 0)
        self.assertListEqual(term, [])
