import os
from pathlib import Path
from dotenv import load_dotenv
import secrets

# بارگذاری فایل .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# متغیرهای محیطی عمومی
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(50))  # مقدار پیش‌فرض برای مواقع تست

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'home',
    'blog',
    'django_jalali',
    'users',
    'about',
    'core',
    'service',
    'gallery',
    'contact',
    'dashboard',
    'accounts',

    # Third-party apps
    'django_filters',
    'captcha',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Dental.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Dental.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#     }
# }

# SESSION_COOKIE_SECURE = True  # فقط HTTPS
# SESSION_COOKIE_HTTPONLY = True  # جلوگیری از دسترسی جاوااسکریپت
# SESSION_COOKIE_SAMESITE = 'Strict'  # جلوگیری از CSRF
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True  # همه درخواست‌ها به HTTPS ریدایرکت بشن

PASSWORD_RESET_TIMEOUT = 1800  # ۳۰ دقیقه (۱۸۰۰ ثانیه)

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = os.getenv('USE_I18N', 'False') == 'True'
USE_TZ = os.getenv('USE_TZ', 'False') == 'True'

MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / os.getenv('STATIC_ROOT', 'static')
 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Google ReCaptcha
RECAPTCHA_PUBLIC_KEY = "6LdwEtsqAAAAADzdwgPOrMVPUbbMkKfkyqMIcr55"
RECAPTCHA_PRIVATE_KEY = "6LdwEtsqAAAAAGmybZkNo-FV-hCmaLsbCc9dpwg3"

# email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'amirhoosenbabai82@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)

OTP_SECRET_KEY = os.getenv('OTP_SECRET_KEY', secrets.token_urlsafe(50))
RESET_PREFIX = os.getenv('RESET_PREFIX', 'amir-amiir-amiiir')
