from .base import *  # تمام تنظیمات عمومی از فایل base وارد می‌شوند
import os

# تنظیمات خاص محیط توسعه
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
