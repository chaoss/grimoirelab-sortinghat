from .testing import *  # noqa: F403,F401
from .testing import SQL_MODE, DATABASES, RQ_QUEUES

tenants_cfg = [
    {'name': 'tenant_1', 'dedicated_queue': True},
    {'name': 'tenant_2', 'dedicated_queue': False},
    {'name': 'error_tenant', 'dedicated_queue': True}
]

MULTI_TENANT = True

TENANTS_NAMES = [t["name"] for t in tenants_cfg]
TENANTS_DEDICATED_QUEUES = [t["name"] for t in tenants_cfg if t["dedicated_queue"]]

DATABASES.update({
    tenant: {
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'root',
        'PASSWORD': 'root',
        'NAME': tenant,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'sql_mode': ','.join(SQL_MODE)
        },
        'TEST': {
            'NAME': tenant,
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_520_ci',
        },
        'HOST': '127.0.0.1',
        'PORT': 3306
    }
    for tenant in [t["name"] for t in tenants_cfg]
})

RQ_QUEUES.update({
    tenant: {
        'HOST': 'localhost',
        'PORT': 6379,
        'ASYNC': False,
        'DB': 0
    }
    for tenant in [
        t["name"] for t in tenants_cfg
        if t["dedicated_queue"] and t["name"] != "error_tenant"
    ]
})

DATABASE_ROUTERS = [
    'sortinghat.core.middleware.TenantDatabaseRouter'
]

TEST_RUNNER = 'tests.runners.OnlyMultiTenantTestRunner'
