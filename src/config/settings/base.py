import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


# Load environment variables from a .env file
load_dotenv()

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _env(name, default):
    """
    Return an environment variable, treating empty as absent.

    `os.getenv(name, default)` returns the default only when the name is not
    set at all. An env file that lists a key with no value — which every
    example file in this repository does, to show the full shape — sets it to
    the empty string instead, and the default never applies. For a string
    setting that is a subtle misconfiguration; for `int(...)` it is a
    ValueError at import time.
    """
    value = os.getenv(name)
    return default if value in (None, '') else value


def _required_env(name):
    """
    Return an environment variable or raise ImproperlyConfigured.

    Reason: values like SECRET_KEY, SECURE_ADMIN_PANEL and OTP_SECRET_KEY must
    be stable across restarts. A random fallback silently invalidates every
    existing session, reset link, and OTP token each time the process
    restarts. Failing fast surfaces the missing config
    immediately instead of at 3 AM in production. `develop.py` and `test.py` set
    safe defaults via `os.environ.setdefault(...)` before importing this file.
    """
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(
            f"The {name} environment variable is required. "
            "Set it in the runtime environment or your .env file."
        )
    return value


# General environment variables
SECRET_KEY = _required_env('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Enable/disable debug mode

# Only the hosts named in the environment. The previous default was '*', which
# accepts any Host header — and the header is what Django echoes into the
# absolute URLs it builds, including the link in the password-reset email. An
# attacker who can reach the app directly could request a reset for a known
# address and have the mail arrive pointing at their own domain.
# `develop.py`/`test.py` set localhost defaults before importing this file.
ALLOWED_HOSTS = [
    host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()
]

# Required by django.contrib.sites, which django.contrib.sitemaps depends on.
SITE_ID = 1

# The canonical origin, used for absolute URLs in `<link rel=canonical>`, the
# `og:` tags and the JSON-LD blocks. Those have to be absolute and have to
# agree with each other: two spellings of the same page (with and without
# www, http and https) are two pages as far as a crawler is concerned, and
# the ranking splits between them.
SITE_URL = _env('SITE_URL', 'https://sbdental.ir').rstrip('/')

# Shown in <title> suffixes, the footer and structured data. "مطب" rather
# than "کلینیک" throughout: it is what this practice is, and it is also the
# word patients here actually type when they search.
SITE_NAME = _env('SITE_NAME', 'مطب دندانپزشکی دکتر بابایی و بهمدی')

# Installed apps for the Django project
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # `intcomma` for price formatting
    # `sites` is a dependency of `sitemaps`, not a feature in its own right:
    # Sitemap.get_urls() asks the Site framework for the domain when no
    # request is available. Nothing else in this project reads it.
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # Custom apps
    'apps.home',
    'apps.blog',
    'apps.users',
    'apps.about',
    'apps.core',
    'apps.service',
    'apps.gallery',
    'apps.contact',
    'apps.dashboard',
    # Public CV pages for the doctors. The Doctor model itself stays in
    # `dashboard` (blog.BlogPost points at it); this app is only the public
    # half, kept separate because /dashboard/ is staff-only and noindexed
    # while these pages are the ones most meant to be found.
    'apps.doctors',
    'apps.accounts',
    'apps.pricing',
    'apps.appointments',
    'apps.notifications',

    # Third-party apps
    'django_filters',  # For filtering querysets
    'django_ckeditor_5',  # CKEditor 5 integration for rich text editing
    'storages', # For using cloud storage backends (e.g., AWS S3, Google Cloud Storage)
]

# The debug toolbar is a development tool that reads settings, SQL and request
# internals. It used to be installed unconditionally, so the production image
# carried it too. Its middleware short-circuits when DEBUG is off, but a
# panel is one misconfigured INTERNAL_IPS away from serving the whole settings
# dict, and there is no reason for the code to be there at all.
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    # Must sit as early as possible to time the rest of the stack; the docs
    # put it right after SecurityMiddleware.
    MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Root URL configuration
ROOT_URLCONF = 'config.urls'

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Custom template directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.dashboard.context_processors.clinic_doctors',
                'apps.about.context_processors.about_info',
                'apps.core.context_processors.seo',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'config.wsgi.application'

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),  # Default to SQLite
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
        'CONN_MAX_AGE': 600,  # Persistent connections
    }
}


# Caching (Redis by default). Multi-worker Gunicorn setups need a shared
# backend or per-worker caches diverge and signal-driven invalidation only
# affects the worker that handled the write.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Celery — Redis broker + result backend
CELERY_BROKER_URL = os.getenv('REDIS_URL_CELERY', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL_CELERY', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Password reset timeout (30 minutes)
PASSWORD_RESET_TIMEOUT = 1800

# --- SMS / notifications ---------------------------------------------------
# `console` only logs, so a misconfigured environment can never spend real
# credit or text a real patient. Switch to 'kavenegar' in production.
SMS_BACKEND = os.getenv('SMS_BACKEND', 'console')
KAVENEGAR_API_KEY = os.getenv('KAVENEGAR_API_KEY', '')
# Optional: blank means "use the panel's default line".
KAVENEGAR_SENDER = os.getenv('KAVENEGAR_SENDER', '')
# Who gets operational alerts (new contact message, new booking). Comma- or
# space-separated; kept in config because who should be interrupted is a
# business decision, not a property of whoever has a doctor row.
STAFF_ALERT_NUMBERS = os.getenv('STAFF_ALERT_NUMBERS', '')

# --- Web Push --------------------------------------------------------------
# Browser notifications for staff: free, instant, and delivered to the device
# already in their hand — the complement to SMS, which costs per message.
#
# The keypair identifies this server to Google's/Mozilla's/Apple's push
# services. It is not a third-party account; generate one with:
#   python manage.py generate_vapid_keys
# Rotating it invalidates every existing subscription, so treat it like
# SECRET_KEY: set it once, keep it. Blank keys disable push entirely rather
# than erroring, so a fresh checkout runs without configuration.
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
# Contact address the push service uses to report abuse. Must be a mailto: or
# https: URL — push services reject messages signed without one.
VAPID_SUBJECT = os.getenv('VAPID_SUBJECT', 'mailto:info@sbdental.ir')

# Localization settings
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = os.getenv('USE_I18N', 'False') == 'True'
USE_TZ = os.getenv('USE_TZ', 'False') == 'True'

# Static and media file settings
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / os.getenv('STATIC_ROOT', 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Test runner. Holds what used to be a `settings/test.py`: rate limiting off,
# cheap password hashing, in-memory cache and inline Celery. Those are
# properties of *running tests*, not of an environment, so they live with the
# runner and apply whichever settings module the suite is pointed at.
TEST_RUNNER = 'utils.test_runner.DentalTestRunner'

# Email configuration
#
# `_env` and not `os.getenv` throughout: a variable that is *present but
# empty* — `EMAIL_PORT=` in a .env file, an unset value passed through by
# compose, a blank CI variable — returns `''`, and `os.getenv`'s default only
# applies when the name is missing entirely. `int('')` then raises at import
# time and takes the whole project down before a single setting is read.
EMAIL_BACKEND = _env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = _env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(_env('EMAIL_PORT', 587))
EMAIL_USE_TLS = _env('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = _env('EMAIL_HOST_USER', 'amirhoosenbabai82@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD') or None

# OTP HMAC key and obscured URL segments. All required — rotating any of
# these invalidates in-flight reset emails or previously issued OTP tokens.
OTP_SECRET_KEY = _required_env('OTP_SECRET_KEY')
SECURE_ADMIN_PANEL = _required_env('SECURE_ADMIN_PANEL')
# `urls.py` hands this straight to `path()` as a prefix, and admin's own
# patterns start with `''` and `login/`. Without a trailing slash they are
# concatenated: a value of `admin` puts the index at `/admin` and the login
# page at `/adminlogin/`, which resolves and renders and is simply wrong — the
# kind of thing nobody notices until a link is shared. Normalising here rather
# than in every env file means an operator who forgets the slash still gets a
# working admin.
if not SECURE_ADMIN_PANEL.endswith('/'):
    SECURE_ADMIN_PANEL += '/'

# Authentication backends
#
# The throttle backend comes first and never authenticates anyone — it only
# refuses attempts that `utils.security.login_throttle` has locked out. Raising from a
# backend stops Django walking the list, so a throttled attempt can never
# reach ModelBackend. Counters live in the Redis cache configured above;
# the tuning constants are in `utils/login_throttle.py`.
AUTHENTICATION_BACKENDS = [
    'utils.security.auth_backends.LoginThrottleBackend',  # Refuses throttled logins
    'django.contrib.auth.backends.ModelBackend',  # Default authentication backend
]

# CKEditor 5 configuration
CKEDITOR_5_CONFIGS = {
    # A short-text editor: bold, italic, a link, a list. Used for the
    # treatment card blurb, where the point is to be able to emphasise a word
    # — not to build a second body. Headings, images and tables are absent on
    # purpose: the blurb renders inside a card and a <h2> or a table there
    # breaks the layout, and the full body already has its own editor below.
    'simple': {
        'toolbar': [
            'bold', 'italic', 'underline', '|',
            'bulletedList', 'numberedList', '|',
            'link', 'removeFormat', '|', 'undo', 'redo',
        ],
        'language': 'fa',
        'height': '180px',
        'width': '100%',
    },
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'link', 'bulletedList', 
            'numberedList', 'blockQuote', 'imageUpload', 'undo', 'redo',
            'fontColor', 'fontBackgroundColor'  # گزینه‌های رنگ
        ],
        'language': 'fa',  # زبان فارسی
        'height': '300px',
        'width': '100%',
        'image': {  # تنظیمات مربوط به تصاویر
            'toolbar': [
                'imageTextAlternative', '|',  # متن جایگزین تصویر
                'imageStyle:alignLeft', 'imageStyle:alignCenter', 'imageStyle:alignRight'  # جهت‌گیری تصویر
            ],
            'styles': [
                'alignLeft', 'alignCenter', 'alignRight'  # استایل‌های جهت‌گیری
            ]
        }
    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3', '|',
            'bulletedList', 'numberedList', '|',
            'blockQuote',
        ],
        'toolbar': [
            'heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 
            'underline', 'strikethrough', 'code', 'subscript', 'superscript', 
            'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
            'bulletedList', 'numberedList', 'todoList', '|', 'blockQuote', 
            'imageUpload', '|', 'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 
            'mediaEmbed', 'removeFormat', 'insertTable',
        ],
        'image': {  # تنظیمات کامل برای تصاویر
            'toolbar': [
                'imageTextAlternative', '|',  # متن جایگزین
                'imageStyle:alignLeft', 'imageStyle:alignCenter', 'imageStyle:alignRight',  # جهت‌گیری چپ، وسط، راست
                'imageStyle:full', 'imageStyle:side'  # اندازه کامل یا کناری
            ],
            'styles': [
                'full', 'side', 'alignLeft', 'alignCenter', 'alignRight'  # استایل‌های موجود
            ],
            'resizeOptions': [  # گزینه‌های تغییر اندازه تصویر
                {'name': 'resize:original', 'value': None, 'label': 'Original'},
                {'name': 'resize:50', 'value': '50', 'label': '50%'},
                {'name': 'resize:75', 'value': '75', 'label': '75%'},
                {'name': 'resize:100', 'value': '100', 'label': '100%'}
            ]
        },
        'fontColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 0%)', 'label': 'سیاه'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'خاکستری تیره'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'خاکستری'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'خاکستری روشن'},
                {'color': 'hsl(0, 0%, 100%)', 'label': 'سفید'},
                {'color': 'hsl(0, 75%, 60%)', 'label': 'قرمز'},
                {'color': 'hsl(30, 75%, 60%)', 'label': 'نارنجی'},
                {'color': 'hsl(60, 75%, 60%)', 'label': 'زرد'},
                {'color': 'hsl(120, 75%, 60%)', 'label': 'سبز'},
                {'color': 'hsl(180, 75%, 60%)', 'label': 'فیروزه‌ای'},
                {'color': 'hsl(240, 75%, 60%)', 'label': 'آبی'},
                {'color': 'hsl(300, 75%, 60%)', 'label': 'بنفش'}
            ],
            'columns': 5
        },
        'fontBackgroundColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 100%)', 'label': 'سفید'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'خاکستری روشن'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'خاکستری'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'خاکستری تیره'},
                {'color': 'hsl(0, 0%, 0%)', 'label': 'سیاه'},
                {'color': 'hsl(0, 75%, 85%)', 'label': 'قرمز روشن'},
                {'color': 'hsl(30, 75%, 85%)', 'label': 'نارنجی روشن'},
                {'color': 'hsl(60, 75%, 85%)', 'label': 'زرد روشن'},
                {'color': 'hsl(120, 75%, 85%)', 'label': 'سبز روشن'},
                {'color': 'hsl(180, 75%, 85%)', 'label': 'فیروزه‌ای روشن'},
                {'color': 'hsl(240, 75%, 85%)', 'label': 'آبی روشن'},
                {'color': 'hsl(300, 75%, 85%)', 'label': 'بنفش روشن'}
            ],
            'columns': 5
        },
        'language': 'fa',  # زبان فارسی
        'height': '400px',  # ارتفاع ادیتور
        'width': '100%',   # عرض ادیتور
        'htmlSupport': {
            'allow': [
                {'name': 'p'},
                {'name': 'b'},
                {'name': 'i'},
                {'name': 'u'},
                {'name': 'strong'},
                {'name': 'em'},
                {'name': 'h1'},
                {'name': 'h2'},
                {'name': 'h3'},
                {'name': 'ul'},
                {'name': 'ol'},
                {'name': 'li'},
                {'name': 'a', 'attributes': ['href', 'title']},
                {'name': 'img', 'attributes': ['src', 'alt', 'style']},
                {'name': 'table'},
                {'name': 'tr'},
                {'name': 'td', 'attributes': ['colspan', 'rowspan']},
                {'name': 'th'},
                {'name': 'blockquote'},
                {'name': 'code'},
                {'name': 'pre'},
            ],
            'disallow': [
                {'name': 'script'},
                {'name': 'iframe'},
                {'name': 'style'},
                {'name': 'object'},
                {'name': 'embed'},
            ],
        },
        'table': {  # تنظیمات جدول
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells'
            ]
        }
    }
}

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
]