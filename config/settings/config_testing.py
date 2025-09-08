import sys
import logging

import django_rq.queues

from fakeredis import FakeRedis, FakeStrictRedis

# Graphene logs SortingHat exceptions and Django prints them
# to the standard error output. This code prevents Django
# kind of errors are not shown.
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    logging.disable(logging.CRITICAL)


SILENCED_SYSTEM_CHECKS = ["django_mysql.E016"]

SECRET_KEY = 'fake-key'

SORTINGHAT_GENDERIZE_API_KEY = 'fake-key'

MATCH_TRUSTED_SOURCES = ['github', 'gitlab', 'slack']

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'graphene_django',
    'sortinghat.core',
]

SQL_MODE = [
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
        'PASSWORD': 'root',
        'NAME': 'sortinghat_db',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'sql_mode': ','.join(SQL_MODE)
        },
        'TEST': {
            'NAME': 'testhat',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_520_ci',
        },
        'HOST': '127.0.0.1',
        'PORT': 3306
    }
}

TEST_DATABASE_IMAGE = "mariadb:11.4"

TEST_RUNNER = 'tests.runners.SkipMultiTenantTestRunner'

USE_TZ = True

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# This option should be set to True to pass
# authentication tests.
SORTINGHAT_AUTHENTICATION_REQUIRED = True

GRAPHENE = {
    'SCHEMA': 'sortinghat.core.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

SORTINGHAT_API_PAGE_SIZE = 10

MULTI_TENANT = False


# Configuration to pretend there is a Redis service
# available. We need to set up the connection before
# RQ Django reads the settings. Also, the connection
# must be the same because in fakeredis connections
# do not share the state. Therefore, we define a
# singleton object to reuse it.

class FakeRedisConn:
    """Singleton FakeRedis connection."""

    def __init__(self):
        self.conn = None

    def __call__(self, _, strict):
        if not self.conn:
            self.conn = FakeStrictRedis() if strict else FakeRedis()
        return self.conn


django_rq.queues.get_redis_connection = FakeRedisConn()


RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'ASYNC': False,
        'DB': 0
    }
}
