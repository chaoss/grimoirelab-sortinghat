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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import datetime

import dateutil

from django.db.models import (CASCADE,
                              SET_NULL,
                              Model,
                              BooleanField,
                              CharField,
                              DateTimeField,
                              PositiveIntegerField,
                              ForeignKey,
                              OneToOneField)

from django_mysql.models import JSONField

from enum import Enum

from grimoirelab_toolkit.datetime import datetime_utcnow

# Default dates for periods
MIN_PERIOD_DATE = datetime.datetime(1900, 1, 1, 0, 0, 0,
                                    tzinfo=dateutil.tz.tzutc())
MAX_PERIOD_DATE = datetime.datetime(2100, 1, 1, 0, 0, 0,
                                    tzinfo=dateutil.tz.tzutc())

# Innodb and utf8mb4 can only index 191 characters
# For more information regarding this topic see:
# https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-conversion.html
MAX_SIZE_CHAR_INDEX = 191
MAX_SIZE_CHAR_FIELD = 128


class CreationDateTimeField(DateTimeField):
    """Field automatically set to the current date when an object is created."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('default', datetime_utcnow)
        super().__init__(*args, **kwargs)


class LastModificationDateTimeField(DateTimeField):
    """Field automatically set to the current date on each save() call."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('default', datetime_utcnow)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = datetime_utcnow()
        setattr(model_instance, self.attname, value)
        return value


class EntityBase(Model):
    created_at = CreationDateTimeField()
    last_modified = LastModificationDateTimeField()

    class Meta:
        abstract = True


class Transaction(Model):
    tuid = CharField(max_length=MAX_SIZE_CHAR_FIELD,
                     primary_key=True)
    name = CharField(max_length=MAX_SIZE_CHAR_FIELD)
    created_at = DateTimeField()
    closed_at = DateTimeField(null=True)
    is_closed = BooleanField(default=False)
    authored_by = CharField(max_length=MAX_SIZE_CHAR_FIELD,
                            null=True)

    class Meta:
        db_table = 'transactions'
        ordering = ('created_at', 'tuid')

    def __str__(self):
        return '%s - %s' % (self.tuid, self.name)


class Operation(Model):
    class OpType(Enum):
        ADD = 'ADD'
        DELETE = 'DELETE'
        UPDATE = 'UPDATE'

        @classmethod
        def choices(cls):
            return ((item.name, item.value) for item in cls)

        def __str__(self):
            return self.value

    ouid = CharField(max_length=MAX_SIZE_CHAR_FIELD, primary_key=True)
    op_type = CharField(max_length=MAX_SIZE_CHAR_FIELD, choices=OpType.choices())
    entity_type = CharField(max_length=MAX_SIZE_CHAR_FIELD)
    target = CharField(max_length=MAX_SIZE_CHAR_FIELD)
    trx = ForeignKey(Transaction, related_name='operations',
                     on_delete=CASCADE, db_column='tuid')
    timestamp = DateTimeField()
    args = JSONField()

    class Meta:
        db_table = 'operations'
        ordering = ('timestamp', 'ouid', 'trx')

    def __str__(self):
        return '%s - %s - %s - %s - %s' % (self.ouid, self.trx, self.op_type, self.entity_type, self.target)


class Organization(EntityBase):
    name = CharField(max_length=MAX_SIZE_CHAR_INDEX)

    class Meta:
        db_table = 'organizations'
        unique_together = ('name',)

    def __str__(self):
        return self.name


class Domain(EntityBase):
    domain = CharField(max_length=MAX_SIZE_CHAR_FIELD)
    is_top_domain = BooleanField(default=False)
    organization = ForeignKey(Organization, related_name='domains', on_delete=CASCADE)

    class Meta:
        db_table = 'domains_organizations'
        unique_together = ('domain',)
        ordering = ('domain',)

    def __str__(self):
        return self.domain


class Country(EntityBase):
    code = CharField(max_length=2, primary_key=True)
    name = CharField(max_length=MAX_SIZE_CHAR_INDEX)
    alpha3 = CharField(max_length=3)

    class Meta:
        db_table = 'countries'
        unique_together = ('alpha3',)

    def __str__(self):
        return self.name


class UniqueIdentity(EntityBase):
    uuid = CharField(max_length=MAX_SIZE_CHAR_FIELD, primary_key=True)

    class Meta:
        db_table = 'uidentities'

    def __str__(self):
        return self.uuid


class Identity(EntityBase):
    id = CharField(max_length=MAX_SIZE_CHAR_FIELD, primary_key=True)
    name = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    email = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    username = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    source = CharField(max_length=32)
    uidentity = ForeignKey(UniqueIdentity, related_name='identities',
                           on_delete=CASCADE, db_column='uuid')

    class Meta:
        db_table = 'identities'
        unique_together = ('name', 'email', 'username', 'source', )

    def __str__(self):
        return self.id


class Profile(EntityBase):
    uidentity = OneToOneField(UniqueIdentity, related_name='profile',
                              on_delete=CASCADE, db_column='uuid')
    name = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    email = CharField(max_length=MAX_SIZE_CHAR_FIELD, null=True)
    gender = CharField(max_length=32, null=True)
    gender_acc = PositiveIntegerField(null=True)
    is_bot = BooleanField(default=False, null=False)
    country = ForeignKey(Country, null=True, on_delete=SET_NULL, db_column='country_code')

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return self.uidentity.uuid


class Enrollment(EntityBase):
    uidentity = ForeignKey(UniqueIdentity, related_name='enrollments',
                           on_delete=CASCADE, db_column='uuid')
    organization = ForeignKey(Organization, related_name='enrollments',
                              on_delete=CASCADE)
    start = DateTimeField(default=MIN_PERIOD_DATE)
    end = DateTimeField(default=MAX_PERIOD_DATE)

    class Meta:
        db_table = 'enrollments'
        unique_together = ('uidentity', 'organization', 'start', 'end',)
        ordering = ('start', 'end', )

    def __str__(self):
        return '%s - %s' % (self.uidentity.uuid, self.organization.name)


class MatchingBlacklist(EntityBase):
    excluded = CharField(max_length=MAX_SIZE_CHAR_FIELD, primary_key=True)

    class Meta:
        db_table = 'matching_blacklist'
