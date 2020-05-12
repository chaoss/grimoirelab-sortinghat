import sys
import logging

import django_rq.queues

from fakeredis import FakeRedis, FakeStrictRedis

# Graphene logs SortingHat exceptions and Django pritns them
# to the standard error output. This code prevents Django
# kind of errors are not shown.
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    logging.disable(logging.CRITICAL)


SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'graphene_django',
    'sortinghat.core',
]

SQL_MODE = [
    'ONLY_FULL_GROUP_BY',
    'NO_ZERO_IN_DATE',
    'NO_ZERO_DATE',
    'ERROR_FOR_DIVISION_BY_ZERO',
    'NO_AUTO_CREATE_USER',
    'NO_ENGINE_SUBSTITUTION',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'root',
        'PASSWORD': '',
        'NAME': 'sortinghat_db',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'sql_mode': ','.join(SQL_MODE)
        },
        'TEST': {
            'NAME': 'testhat',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_520_ci',
        }
    }
}

USE_TZ = True

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# This option should be set to True to pass
# authentication tests.
AUTHENTICATION_REQUIRED = True

GRAPHENE = {
    'SCHEMA': 'sortinghat.core.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

DEFAULT_GRAPHQL_PAGE_SIZE = 10


# Configuration to pretend there is a Redis service
# available. We need to set up the connection before
# RQ Django reads the settings.

def fake_redis_connection(_, strict):
    return FakeStrictRedis() if strict else FakeRedis()


django_rq.queues.get_redis_connection = fake_redis_connection


RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'ASYNC': False,
        'DB': 0
    }
}
