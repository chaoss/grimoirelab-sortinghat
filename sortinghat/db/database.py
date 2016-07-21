# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#         Santiago Dueñas <sduenas@bitergia.com>
#

from __future__ import absolute_import
from __future__ import unicode_literals

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.schema import MetaData

from sortinghat.exceptions import DatabaseError
from sortinghat.db.model import ModelBase


class Database(object):

    MYSQL_CREATE_DB = "CREATE DATABASE %(database)s CHARACTER SET utf8 COLLATE utf8_unicode_ci"
    MYSQL_DROP_DB = "DROP DATABASE IF EXISTS %(database)s"


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
        except:
            session.rollback()
            raise
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
        query = Database.MYSQL_CREATE_DB % {'database' : database}
        cls.execute(engine, query)

    @classmethod
    def drop(cls, user, password, database, host='localhost', port='3306'):
        engine = cls.build_engine(user, password, None, host, port)
        query = Database.MYSQL_DROP_DB % {'database' : database}
        cls.execute(engine, query)

    @classmethod
    def execute(cls, engine, query):
        try:
            conn = engine.connect()
            conn.execute(query)
        except (OperationalError, ProgrammingError) as e:
            raise DatabaseError(error=e.orig.args[1], code=e.orig.args[0])

    @classmethod
    def build_engine(cls, user, password, database, host='localhost', port='3306'):
        return create_database_engine(user, password, database,
                                      host, port)

    def __create_schema(self, engine):
        ModelBase.metadata.create_all(engine)


def create_database_engine(user, password, database, host, port):
    """Create a database engine"""

    try:
        import MySQLdb
        driver = 'mysql+mysqldb'
    except ImportError:
        driver = 'mysql+pymysql'

    url = URL(driver, user, password, host, port, database,
              query={'charset' : 'utf8'})
    return create_engine(url, poolclass=QueuePool,
                         pool_size=25, echo=False)


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
