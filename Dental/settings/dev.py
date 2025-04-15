# dev.py (تنظیمات توسعه - Development)
# Importing base settings
from .base import *

# Database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Using SQLite as the database engine
        'NAME': BASE_DIR / 'db.sqlite3',        # Database file location
    }
}
