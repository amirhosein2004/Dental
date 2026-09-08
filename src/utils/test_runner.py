"""
Test-time configuration, applied by the runner rather than by a settings file.

There used to be a `Dental/settings/test.py`. It was never a deployment
environment — nothing ever ran on it — but sitting beside `develop.py`,
`stage.py` and `production.py` it read like a fourth one, and every command
had to name it explicitly.

What it held was infrastructure for running tests, and that is what this is.
Setting `TEST_RUNNER` in `base.py` means `manage.py test` picks these up
whichever environment it is pointed at, so the suite behaves the same on a
laptop and in CI.

Four overrides, each load-bearing:

* **Rate limiting off.** A test that calls one view ten times would otherwise
  get a 429 instead of the response under test. The one test that checks the
  limit actually works turns it back on with `override_settings`.
* **MD5 password hashing.** The default PBKDF2 runs 600,000 iterations per
  call; with hundreds of `create_user` fixtures that is most of the suite's
  runtime — about 25 seconds against 8.
* **Local-memory cache.** Otherwise the tests need a live Redis, and one test
  run could evict a developer's real cache.
* **Celery inline.** Otherwise they need a live broker and worker.
* **No HTTPS redirect.** `production.py` sets `SECURE_SSL_REDIRECT`, and the
  test client speaks plain HTTP: run the suite against stage or production
  settings and every request comes back as a 301 to https before the view is
  reached, so 287 of 518 tests failed on an assertion about a page that was
  never rendered. Nothing about a redirect belongs in a unit test; the tests
  that care about it set it themselves.
* **Local file storage, unhashed.** `production.py` points the default storage
  at the S3 bucket, so any test that saves an upload would try to reach Liara
  — slow at best, and writing into a real bucket at worst. Static files drop
  back to plain names for a different reason: `ManifestStaticFilesStorage`
  renames `js/pwa.js` to `js/pwa.3ac137dd4a34.js`, so an assertion about a
  script tag passed under develop and failed under stage over a hash. It also
  needs `staticfiles.json`, which only exists after `collectstatic` — a
  checkout that has never run one could not start the suite at all.

Media goes to a temporary directory that is removed afterwards, rather than
accumulating in `test_media/` the way it used to.
"""
import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


class DentalTestRunner(DiscoverRunner):
    """The project's test runner. Named by `TEST_RUNNER` in base settings."""

    def build_suite(self, test_labels=None, **kwargs):
        """
        Discover from `src/` rather than from the working directory.

        Django starts discovery at `.`, which is right when `manage.py` sits
        beside the apps. Here it does not — the application is under `src/`
        and the repository root holds only deploy, docs and scripts. Run from
        the root, the default finds no tests at all and reports "Ran 0 tests"
        as a success, which is the worst possible way for a test command to
        fail.

        An explicit label (`manage.py test apps.blog`) is left alone.
        """
        if not test_labels:
            test_labels = [str(settings.BASE_DIR)]
        if self.top_level is None:
            self.top_level = str(settings.BASE_DIR)
        return super().build_suite(test_labels, **kwargs)

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)

        # django-ratelimit counts in the cache and does not consult DEBUG, so
        # this is the only switch that turns it off.
        settings.RATELIMIT_ENABLE = False

        settings.PASSWORD_HASHERS = [
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ]

        settings.CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'dental-test',
            }
        }

        # Every environment above develop redirects plain HTTP to HTTPS. The
        # test client is plain HTTP, so with this left on the suite tests the
        # redirect and nothing else.
        settings.SECURE_SSL_REDIRECT = False

        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True
        settings.CELERY_BROKER_URL = 'memory://'
        settings.CELERY_RESULT_BACKEND = 'cache+memory://'

        # Mail must never leave the machine during a test run, whatever the
        # environment's backend is. Django swaps this itself, but only after
        # the runner starts — being explicit means a test that reads
        # `settings.EMAIL_BACKEND` sees the same thing either way.
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        # Uploads land in a directory that is thrown away, instead of piling up
        # in the working tree run after run.
        self._media_root = tempfile.mkdtemp(prefix='dental-test-media-')
        settings.MEDIA_ROOT = self._media_root

        # And the storage backend has to follow it. Production stores uploads
        # in the S3 bucket, where MEDIA_ROOT means nothing — a test that saves
        # a file would go out to the network and, with real credentials
        # present, leave the file there.
        settings.STORAGES = {
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        }

        # `testserver` is what Django's test client sends as the Host header,
        # and ALLOWED_HOSTS is strict in every environment.
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        shutil.rmtree(getattr(self, '_media_root', ''), ignore_errors=True)
