from .testing import *  # noqa: F403,F401
from .testing import SQL_MODE, DATABASES


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
    for tenant in ['tenant_1', 'tenant_2']
})

DATABASE_ROUTERS = [
    'sortinghat.core.middleware.TenantDatabaseRouter'
]

TEST_RUNNER = 'tests.runners.OnlyMultiTenantTestRunner'
