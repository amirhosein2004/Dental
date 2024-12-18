from .base import *

# پایگاه داده تست
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

