# test.py (Testing settings)
# Import base settings
from .base import *

# Configure the database to use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',  # Test database file
    }
}

# Use a faster password hasher for testing purposes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable Axes (security feature) during testing
AXES_ENABLED = False