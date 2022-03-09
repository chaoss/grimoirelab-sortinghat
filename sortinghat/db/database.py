# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
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
#         Santiago Dueñas <sduenas@bitergia.com>
#

import re

from contextlib import contextmanager
import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError, InternalError, IntegrityError
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.orm.exc import FlushError
from sqlalchemy.pool import QueuePool
from sqlalchemy.schema import MetaData

from sortinghat.exceptions import DatabaseError, DatabaseExists, AlreadyExistsError
from sortinghat.db.model import ModelBase


logger = logging.getLogger(__name__)


class Database(object):

    MYSQL_CREATE_DB = "CREATE DATABASE %(database)s CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci"
    MYSQL_DROP_DB = "DROP DATABASE IF EXISTS %(database)s"

    # Regular expressions for handling errors
    MYSQL_INSERT_ERROR_REGEX = re.compile(r"INSERT INTO (?P<table>.+) \(.+\) VALUES")
    MYSQL_DUPLICATE_ENTRY_ERROR_REGEX = re.compile(r"Duplicate entry '(?P<value>.+)' for key")
    MYSQL_FLUSH_ERROR_REGEX = re.compile(
        r"New instance <(?P<entity>.+) at .+<class '.+'>, \('(?P<eid>.+)',.+\)\sconflicts")

    def __init__(self, user, password, database, host='localhost', port='3306'):
        self._engine = self.build_engine(user, password, database, host, port)
        self._Session = sessionmaker(bind=self._engine)

        try:
            self.__create_schema(self._engine)
        except OperationalError as e:
            raise DatabaseError(error=e.orig.args[1], code=e.orig.args[0])

    @contextmanager
    def connect(self):
        session = self._Session()

        try:
            yield session
            session.commit()
        except Exception as ex:
            self.handle_database_error(session, ex)
        finally:
            session.close()

    def clear(self):
        session = self._Session()

        for table in reversed(ModelBase.metadata.sorted_tables):
            session.execute(table.delete())
            session.commit()
        session.close()

    @classmethod
    def create(cls, user, password, database, host='localhost', port='3306'):
        engine = cls.build_engine(user, password, None, host, port)
        query = Database.MYSQL_CREATE_DB % {'database': database}
        cls.execute(engine, query)

    @classmethod
    def drop(cls, user, password, database, host='localhost', port='3306'):
        engine = cls.build_engine(user, password, None, host, port)
        query = Database.MYSQL_DROP_DB % {'database': database}
        cls.execute(engine, query)

    @classmethod
    def execute(cls, engine, query):
        try:
            conn = engine.connect()
            conn.execute(query)
        except (OperationalError, ProgrammingError, InternalError) as e:
            code = e.orig.args[0]
            if isinstance(e, ProgrammingError) and code == 1007:
                # Query for creating database failed because it exists
                raise DatabaseExists(error=e.orig.args[1], code=code)
            else:
                raise DatabaseError(error=e.orig.args[1], code=code)

    @classmethod
    def build_engine(cls, user, password, database, host='localhost', port='3306'):
        try:
            return create_database_engine(user, password, database,
                                          host, port)
        except OperationalError as e:
            raise DatabaseError(error=e.orig.args[1], code=e.orig.args[0])

    @classmethod
    def handle_database_error(cls, session, exception):
        """Rollback changes made and handle any type of error raised by the DBMS."""

        session.rollback()

        if isinstance(exception, IntegrityError):
            cls.handle_integrity_error(exception)
        elif isinstance(exception, FlushError):
            cls.handle_flush_error(exception)
        else:
            raise exception

    @classmethod
    def handle_integrity_error(cls, exception):
        """Handle integrity error exceptions."""

        m = re.match(cls.MYSQL_INSERT_ERROR_REGEX,
                     exception.statement)

        if not m:
            raise exception

        model = find_model_by_table_name(m.group('table'))

        if not model:
            raise exception

        m = re.match(cls.MYSQL_DUPLICATE_ENTRY_ERROR_REGEX,
                     exception.orig.args[1])

        if not m:
            raise exception

        entity = model.__name__
        eid = m.group('value')

        raise AlreadyExistsError(entity=entity, eid=eid)

    @classmethod
    def handle_flush_error(cls, exception):
        """Handle flush error exceptions."""

        trace = exception.args[0]
        m = re.match(cls.MYSQL_FLUSH_ERROR_REGEX, trace)

        if not m:
            raise exception

        entity = m.group('entity')
        eid = m.group('eid')

        raise AlreadyExistsError(entity=entity, eid=eid)

    def __create_schema(self, engine):
        ModelBase.metadata.create_all(engine)


def create_database_engine(user, password, database, host, port):
    """Create a database engine"""

    driver = 'mysql+pymysql'
    url = URL(driver, user, password, host, port, database,
              query={'charset': 'utf8mb4'})

    # Generic parameters for the engine.
    #
    # SSL param needs a non-empty dict to be activated in pymsql.
    # That is why a fake parameter 'activate' is given but not
    # used by the library.
    #
    engine_params = {
        'poolclass': QueuePool,
        'pool_size': 25,
        'pool_pre_ping': True,
        'echo': False,
        'connect_args': {
            'ssl': {
                'activate': True
            }
        }
    }

    engine = create_engine(url, **engine_params)

    try:
        engine.connect().close()
    except InternalError:
        # Try non-SSL connection
        engine_params['connect_args'].pop('ssl')
        engine = create_engine(url, **engine_params)
        engine.connect().close()

    return engine


def create_database_session(engine):
    """Connect to the database"""

    try:
        Session = sessionmaker(bind=engine)
        return Session()
    except OperationalError as e:
        raise DatabaseError(error=e.orig.args[1], code=e.orig.args[0])


def close_database_session(session):
    """Close connection with the database"""

    try:
        session.close()
    except OperationalError as e:
        raise DatabaseError(error=e.orig.args[1], code=e.orig.args[0])


def reflect_table(engine, klass):
    """Inspect and reflect objects"""

    try:
        meta = MetaData()
        meta.reflect(bind=engine)
    except OperationalError as e:
        raise DatabaseError(error=e.orig.args[1], code=e.orig.args[0])

    # Try to reflect from any of the supported tables
    table = None

    for tb in klass.tables():
        if tb in meta.tables:
            table = meta.tables[tb]
            break

    if table is None:
        raise DatabaseError(error="Invalid schema. Table not found",
                            code="-1")

    # Map table schema into klass
    mapper(klass, table,
           column_prefix=klass.column_prefix())

    return table


def find_model_by_table_name(name):
    """Find a model reference by its table name"""

    for model in ModelBase._decl_class_registry.values():
        if hasattr(model, '__table__') and model.__table__.fullname == name:
            return model
    return None
