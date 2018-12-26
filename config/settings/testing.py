SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'graphene_django',
    'sortinghat.core',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'root',
        'PASSWORD': '',
        'NAME': 'sortinghat_db',
        'TEST': {
            'NAME': 'testhat',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_520_ci',
        }
    }
}

USE_TZ = True
