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
#   Quan Zhou <quan@bitergia.com>
#

import logging

import django.db.utils

from grimoirelab_toolkit.datetime import datetime_utcnow

from ..errors import (InvalidValueError,
                      AlreadyExistsError,
                      NotFoundError)
from ..db import _handle_integrity_error
from ..log import TransactionsLog
from ..models import (Operation,
                      RecommenderExclusionTerm)
from ..aux import validate_field


logger = logging.getLogger(__name__)


def add_recommender_exclusion_term(ctx, term):
    """Add a term to the registry.

    This function adds the given term to the registry.

    :param ctx: context from where this method is called
    :param term: name of the term to add

    :raises InvalidValueError: raised when the term is None or an empty string
    :raises AlreadyExistsError: raised when the term is already in the registry
    """
    if term is None:
        raise InvalidValueError(msg="'term' cannot be None")
    if term == '':
        raise InvalidValueError(msg="'term' cannot be an empty string")

    trxl = TransactionsLog.open('add_recommender_exclusion_term', ctx)

    try:
        rel = _add_excluded_term(trxl, term=term)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except AlreadyExistsError as exc:
        raise exc

    trxl.close()
    logger.info(f"Term '{rel.term}' added to the recommender exclusion list")

    return rel


def delete_recommend_exclusion_term(ctx, term):
    """Remove a term from the registry.

    This function removes the given term from the registry.
    It checks first whether the term is already on the registry.
    When it is found, the term is removed. Otherwise,
    it will raise a 'NotFoundError'.

    :param ctx: context from where this method is called
    :param term: name of the term to remove

    :raises InvalidValueError: raised when the term is None or an empty string
    :raises NotFoundError: raised when the term does not exist
        in the registry
    """
    if term is None:
        raise InvalidValueError(msg="'term' cannot be None")
    if term == '':
        raise InvalidValueError(msg="'term' cannot be an empty string")

    trxl = TransactionsLog.open('delete_recommend_exclusion_term', ctx)

    try:
        exclusion = RecommenderExclusionTerm.objects.get(term=term)
        _delete_excluded_term(trxl, term=exclusion)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except NotFoundError as exc:
        raise exc
    except RecommenderExclusionTerm.DoesNotExist:
        logger.debug(f"Term '{term}' does not exist")
        raise NotFoundError(entity=term)

    trxl.close()

    logger.info(f"Term '{term}' deleted from recommender exclusion list")

    return exclusion


def fetch_recommender_exclusion_list():
    """Fetch the list of terms of recommender exclusion term table."""

    exclusion_terms = RecommenderExclusionTerm.objects.all()

    return [exclusion.term for exclusion in exclusion_terms]


def _add_excluded_term(trxl, term):
    """Add a term to the database.

    This function adds a new term to the database,
    using the given term as an identifier. Term cannot be
    empty or `None`.

    It returns a new `RecommenderExclusionTerm` object.

    :param trxl: TransactionsLog object from the method calling this one
    :param term: term

    :returns: a new excluded term
    """
    # Setting operation arguments before they are modified
    op_args = {
        'term': term
    }

    validate_field('term', term)

    excluded = RecommenderExclusionTerm(term=term)

    try:
        excluded.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(RecommenderExclusionTerm, exc)

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='recommender_exclusion_terms',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['term'])

    return excluded


def _delete_excluded_term(trxl, term):
    """Remove a term from the database.

    Function that removes from the database the term
    given in `recommenderExclusionTerm`.

    :param trxl: TransactionsLog object from the method calling this one
    :param term: term to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'term': term.term
    }

    term.delete()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='recommender_exclusion_terms',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['term'])
