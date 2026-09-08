"""
Development settings.

Fills in `_required_env(...)` values with stable, obviously-insecure defaults so
`base.py` never raises during local development. Do NOT copy these to prod.
"""

import os


def _setdefault(name, value):
    """
    `os.environ.setdefault`, but treating an empty value as absent.

    The real `setdefault` only fills a name that is missing entirely. An env
    file that lists `VAPID_PUBLIC_KEY=` with nothing after it — which every
    example file here does, to show the full shape — sets it to the empty
    string, and the default below then never applies. That produced a suite
    which passed on a machine whose `.env` omitted the key and failed on one
    whose `.env` listed it blank.
    """
    if not os.environ.get(name):
        os.environ[name] = value


# Unconditionally shadow the production-shaped env for local dev. `setdefault`
# is not enough: the project's `.env` typically holds real prod values and
# Django's autoreloader inherits them across restarts, so a raw `setdefault`
# quietly leaves the production admin URL / secret key active. Using dev.py
# is an explicit opt-in, so overriding here is safe.
os.environ['SECRET_KEY'] = 'dev-insecure-secret-key-do-not-use-in-production'
os.environ['OTP_SECRET_KEY'] = 'dev-insecure-otp-key-do-not-use-in-production'
os.environ['SECURE_ADMIN_PANEL'] = 'admin'
# Dev always runs with DEBUG=True: preview URLs, static-file serving, debug
# toolbar, template auto-reload all depend on it. To exercise the DEBUG=False
# render path (custom 404/403/500), use ``production.py`` or the DEBUG=False test
# flow described in the README.
os.environ['DEBUG'] = 'True'
# base.py no longer defaults to '*'; local runs still need a value.
_setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver,[::1]')
# Throwaway VAPID pair so the push endpoints are exercised locally. Generated
# for this repo and published in it — never use these in production.
_setdefault(
    'VAPID_PUBLIC_KEY',
    'BL2oSV1-yFAt5OYMrMopn6QZg7fx0jFJcliRTRFGohyvipRqRWJDR5QP2_7zAB8WACUG9-MZW25XXjpYHTG34es',
)
_setdefault('VAPID_PRIVATE_KEY', '8FAJszyH291PkWxvrv0tINtNj0vyDvISfo34FyR5QX8')
# Notifications: the console back-end only logs, so nothing here can reach a
# real phone or spend panel credit. The alert numbers are placeholders that
# exist so the full send path is exercised in development.
_setdefault('SMS_BACKEND', 'console')
# Same reasoning for email. The project's `.env` usually holds real SMTP
# credentials, and dev runs Celery eagerly with EAGER_PROPAGATES on — so a
# mail server unreachable from a laptop does not just fail to send, it raises
# straight through the request and turns the login step into a 500.
#
# File-based rather than console: the console backend writes to stdout, and on
# Windows that is a legacy code page (cp1256 here), so a Persian subject line
# dies with UnicodeEncodeError — the same 500, one layer further down. Writing
# to a file sidesteps the terminal encoding entirely, and has the nicer
# property that the OTP code is sitting in a file you can open.
os.environ['EMAIL_BACKEND'] = 'django.core.mail.backends.filebased.EmailBackend'
_setdefault('STAFF_ALERT_NUMBERS', '09120000000, 09350000000')

from .base import *  # noqa: E402, F401, F403


# ---------------------------------------------------------------------------
# Two ways to run develop, and they need different infrastructure.
#
#   `python manage.py runserver` on the laptop — no Postgres, no Redis, no
#   broker installed. SQLite and in-memory everything, so a fresh clone runs
#   with nothing to install. This is the default.
#
#   `docker compose -f deploy/base.yml -f deploy/develop.yml up` — the whole
#   point is real Postgres and real Redis. Overriding them here would start
#   both containers and then ignore them, which is worse than not starting
#   them: the stack looks right and tests nothing.
#
# The compose env file sets USE_CONTAINER_SERVICES=1; nothing else does. An
# explicit switch rather than "is DB_HOST set?" because the project's root
# `.env` carries production values for exactly those variables — which is what
# made the unconditional override necessary in the first place.
# ---------------------------------------------------------------------------
USE_CONTAINER_SERVICES = os.getenv('USE_CONTAINER_SERVICES') == '1'

if not USE_CONTAINER_SERVICES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'dental-dev',
        }
    }

    # Tasks run inside the request, so "send OTP" delivers immediately without
    # a worker and a broker running.
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'

# Under compose, base.py's env-driven DATABASES, CACHES and Celery settings are
# already pointing at the `db` and `redis` services — so there is nothing to
# override, and the worker container does real queued work.


# Where the file-based email backend drops messages. Gitignored — these are
# throwaway, and one of them contains a live OTP code.
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
EMAIL_FILE_PATH.mkdir(exist_ok=True)
