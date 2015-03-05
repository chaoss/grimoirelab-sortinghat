# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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

import datetime

from sqlalchemy import Column, Boolean, Integer, String, DateTime,\
    ForeignKey, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base


# Default dates for periods
MIN_PERIOD_DATE = datetime.datetime(1900, 1, 1, 0, 0, 0)
MAX_PERIOD_DATE = datetime.datetime(2100, 1, 1, 0, 0, 0)


ModelBase = declarative_base()


class Organization(ModelBase):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    # One-to-Many relationship
    domains = relationship('Domain', backref='organizations',
                           lazy='joined', cascade="save-update, merge, delete")

    # Enrollment relationships
    enrollments = association_proxy('enrollments', 'uidentities')

    __table_args__ = (UniqueConstraint('name', name='_name_unique'),
                      {'mysql_charset': 'utf8'})

    def to_dict(self):
        return {
                'name'    : self.name,
                'domains' : [d.to_dict() for d in self.domains]
                }


class Domain(ModelBase):
    __tablename__ = 'domains_organizations'

    id = Column(Integer, primary_key=True)
    domain = Column(String(128), nullable=False)
    is_top_domain = Column(Boolean(name='top_domain_check'), default=False)
    organization_id = Column(Integer,
                             ForeignKey('organizations.id', ondelete='CASCADE'),
                             nullable=False)

    # Many-to-One relationship
    organization = relationship("Organization", backref='domains_organizations',
                                lazy='joined')

    __table_args__ = (UniqueConstraint('domain', name='_domain_unique'),
                      {'mysql_charset': 'utf8'})

    def to_dict(self):
        return {
                'domain'       : self.domain,
                'top_domain'   : self.is_top_domain,
                'organization' : self.organization.name
                }

    def __repr__(self):
        return "%s (%s)" % (self.domain, self.organization.name)


class UniqueIdentity(ModelBase):
    __tablename__ = 'uidentities'

    uuid = Column(String(128), primary_key=True)

    # One-to-Many relationship
    identities = relationship('Identity', backref='uidentities',
                              lazy='joined', cascade="save-update, merge, delete")

    # Many-to-many association proxy
    organizations = association_proxy('enrollments', 'organizations')

    __table_args__ = ({'mysql_charset': 'utf8'})

    def __init__(self, uuid=None):
        self.uuid = uuid
        self.enrollments = []

    def to_dict(self):
        return {
                'uuid'       : self.uuid,
                'identities' : [i.to_dict() for i in self.identities]
                }

    def __repr__(self):
        return self.uuid


class Identity(ModelBase):
    __tablename__ = 'identities'

    id = Column(String(128), primary_key=True)
    name = Column(String(128))
    email = Column(String(128))
    username = Column(String(128))
    source = Column(String(32), nullable=False)
    uuid = Column(String(128),
                  ForeignKey('uidentities.uuid', ondelete='CASCADE'))

    # Many-to-One relationship
    uidentity = relationship('UniqueIdentity', backref='uuid_identy',
                             lazy='joined')

    __table_args__ = (UniqueConstraint('name', 'email', 'username', 'source',
                                       name='_identity_unique'),
                      {'mysql_charset': 'utf8'})

    def to_dict(self):
        return {
                'id'       : self.id,
                'name'     : self.name,
                'email'    : self.email,
                'username' : self.username,
                'source'   : self.source,
                'uuid'     : self.uuid
                }


class Enrollment(ModelBase):
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key=True)
    start = Column(DateTime, default=MIN_PERIOD_DATE, nullable=False)
    end = Column(DateTime, default=MAX_PERIOD_DATE, nullable=False)
    uuid = Column(String(128),
                  ForeignKey('uidentities.uuid', ondelete='CASCADE'),
                  nullable=False)
    organization_id = Column(Integer,
                             ForeignKey('organizations.id', ondelete='CASCADE'),
                             nullable=False)

    # Bidirectional attribute/collection of "upeople"/"enrollments"
    uidentity = relationship(UniqueIdentity,
                             backref=backref('enrollments',
                                             cascade="all, delete-orphan"),
                             lazy='joined')

    # Reference to the "Organization" object
    organization = relationship(Organization,
                                backref=backref('enrollments',
                                                cascade="all, delete-orphan"),
                                lazy='joined')

    __table_args__ = (UniqueConstraint('uuid', 'organization_id',
                                       'start', 'end',
                                       name='_period_unique'),
                      {'mysql_charset': 'utf8'})

    def to_dict(self):
        return {
                'start'        : self.start,
                'end'          : self.end,
                'uuid'         : self.uuid,
                'organization' : self.organization.name
                }


class MappedTable(object):

    @classmethod
    def tables(cls):
        raise NotImplementedError

    @classmethod
    def column_prefix(cls):
        raise NotImplementedError


class MetricsGrimoireIdentity(MappedTable):
    """Generic identity to map identities data from Metrics Grimoire databases"""

    IDENTITIES_TABLES = ['people', 'users', 'irclog']

    COLUMN_PREFIX = '_'

    MG_ID_KEYS = ['_nick', '_id', '_email_address']
    NAME_KEYS = ['_name']
    EMAIL_KEYS = ['_email', '_email_address']
    USERNAME_KEYS = ['_username', '_user_id', '_nick', '_login']

    def __init__(self):
        super(MetricsGrimoireIdentity, self).__init__()

    def __eq__(self, other):
        if isinstance(other, MetricsGrimoireIdentity) or\
           isinstance(other, Identity):
            return self.name == other.name \
                   and self.email == other.email \
                   and self.username == other.username
        else:
            return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)

        if result is NotImplemented:
            return result
        return not result

    @property
    def mg_id(self):
        return self.__map_to_attr(self.MG_ID_KEYS)

    @property
    def name(self):
        return self.__map_to_attr(self.NAME_KEYS)

    @property
    def email(self):
        return self.__map_to_attr(self.EMAIL_KEYS)

    @property
    def username(self):
        return self.__map_to_attr(self.USERNAME_KEYS)

    @classmethod
    def tables(cls):
        return cls.IDENTITIES_TABLES

    @classmethod
    def column_prefix(cls):
        return cls.COLUMN_PREFIX

    def to_dict(self):
        return {'name' : self.name,
                'email' : self.email,
                'username' : self.username}

    def __map_to_attr(self, m):
        for k in m:
            try:
                v = self.__getattribute__(k)
                return v if v else None
            except:
                pass
        return None
