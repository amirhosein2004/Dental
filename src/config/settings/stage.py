"""
Staging settings.

Deliberately production minus the consequences. It runs the same Postgres, the
same Redis, the same gunicorn and the same `DEBUG = False` render path, so a
bug that only appears with real infrastructure appears here first — but every
outbound channel is neutered, because a staging box that can text patients or
charge the SMS panel is worse than no staging box at all.

What differs from `production.py`, and why each one:

* SMS goes to the console. The bulk sender bills per recipient and a staging
  run with a copied production database would text every real patient in it.
* Email goes to a file. Same reasoning, plus it makes OTP codes readable
  without a mailbox.
* Web push is left unconfigured unless the environment supplies keys, so a
  tester cannot fire notifications at whatever phones subscribed in production.
* `noindex` on every page. Staging is reachable and would otherwise compete
  with the real site in search results — and leak draft content.
* Media stays on local disk rather than the shared S3 bucket, so a test upload
  cannot overwrite a real one.
"""
from .production import *  # noqa: F401,F403

# --- Search engines ---------------------------------------------------------
# Appended, not inserted: it only needs to touch the response on the way out,
# and running last means it also stamps responses the other middleware
# short-circuit (a 429 from the rate limiter, a redirect from the SSL one).
MIDDLEWARE = MIDDLEWARE + [  # noqa: F405
    'utils.http.staging.NoIndexMiddleware',
]

# --- Outbound channels: all neutered ---------------------------------------
# `console` only logs, so nothing here can spend panel credit or reach a real
# phone even if the environment accidentally carries production credentials.
SMS_BACKEND = 'console'
KAVENEGAR_API_KEY = ''

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'  # noqa: F405
EMAIL_FILE_PATH.mkdir(exist_ok=True)

# Alerts have nowhere to go unless staging is given its own numbers.
STAFF_ALERT_NUMBERS = os.getenv('STAFF_ALERT_NUMBERS', '')  # noqa: F405

# --- Media stays local ------------------------------------------------------
# Overrides prod.py's S3 default. Two environments writing to one bucket means
# a staging upload can replace a file the live site is serving.
STORAGES = {  # noqa: F405
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # Same hashing as production: staging is where a broken manifest or a
        # missing asset reference should surface.
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

# --- HSTS off ---------------------------------------------------------------
# A year-long HSTS header from a staging host pins that hostname to HTTPS in
# every tester's browser, including after the certificate is gone.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
