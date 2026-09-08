"""
Repo-wide template hygiene.

Cheap static checks for mistakes that are invisible in code review but very
visible on the rendered page.
"""
import os
import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase

PROJECT_ROOT = Path(settings.BASE_DIR)


def project_templates():
    """Every template in the project, excluding the virtualenv."""
    for path in PROJECT_ROOT.rglob('*.html'):
        if 'venv' in path.parts or 'site-packages' in path.parts:
            continue
        yield path


class TemplateHygieneTests(TestCase):
    def test_no_unterminated_inline_comments(self):
        """
        Django's ``{# ... #}`` comment is single-line only. If the closing
        ``#}`` sits on a later line the tag is never recognised and the comment
        text renders to the visitor as page content. Multi-line notes must use
        ``{% comment %}``.

        This reached the live page three separate times (footer, services page,
        bulk-SMS page), so it is pinned here rather than left to review.
        """
        offenders = []
        for path in project_templates():
            for lineno, line in enumerate(
                path.read_text(encoding='utf-8').splitlines(), start=1
            ):
                if '{#' in line and '#}' not in line:
                    offenders.append(
                        f'{path.relative_to(PROJECT_ROOT).as_posix()}:{lineno}'
                    )

        self.assertEqual(
            offenders, [],
            'Unterminated {# #} comment — use {% comment %} for multi-line '
            'notes, otherwise the text renders on the page:\n  '
            + '\n  '.join(offenders),
        )

    def test_no_raw_confirm_dialogs(self):
        """
        ``window.confirm()`` renders an OS alert: Latin font, LTR layout, and
        no relation to the design. Destructive forms use the shared
        ``data-confirm`` dialog instead.
        """
        pattern = re.compile(r'(onsubmit|onclick)\s*=\s*"[^"]*confirm\s*\(')
        offenders = []
        for path in project_templates():
            for lineno, line in enumerate(
                path.read_text(encoding='utf-8').splitlines(), start=1
            ):
                if pattern.search(line):
                    offenders.append(
                        f'{path.relative_to(PROJECT_ROOT).as_posix()}:{lineno}'
                    )

        self.assertEqual(
            offenders, [],
            'Inline confirm() found — use the shared data-confirm dialog:\n  '
            + '\n  '.join(offenders),
        )

    def test_hidden_attribute_is_enforced_globally(self):
        """
        Several features toggle visibility with the ``hidden`` attribute alone
        (blog and gallery "load more", the pricing search empty state, the
        bulk-SMS counter). The browser's own ``[hidden] { display: none }`` has
        the weakest specificity, so any class rule setting ``display`` beats it
        and the element stays visible.

        Bootstrap's reboot used to carry the !important version. Dropping
        Bootstrap made the "you've seen everything" notes render next to a
        still-usable "load more" button, so the rule is pinned here.
        """
        css = (PROJECT_ROOT / 'static' / 'css' / 'design-system.css').read_text(
            encoding='utf-8'
        )
        self.assertRegex(
            css,
            r'\[hidden\]\s*\{[^}]*display:\s*none\s*!important',
            'design-system.css must force [hidden] to display:none !important — '
            'without it, elements toggled by the hidden attribute stay visible '
            'wherever a class sets display.',
        )

    def test_no_external_assets(self):
        """
        Every stylesheet, script, font and image must come from our own domain.

        Iranian ISPs reach CDNs unreliably, so a linked asset is not a
        performance question — a blocked jsDelivr or unpkg means the page
        renders unstyled or a map never appears, with nothing in the logs to
        say why. Leaflet, Swiper, Vazirmatn and Font Awesome are vendored under
        ``static/``; Bootstrap was dropped entirely.

        Outbound *links* (share buttons, Google Maps directions) are fine —
        this only covers assets the browser must fetch to render the page.
        """
        pattern = re.compile(
            r'(?:src|href)\s*=\s*["\']https?://(?!fonts\.gstatic\.com/dummy)',
            re.IGNORECASE,
        )
        # Anchors and og:/twitter: meta URLs are navigation, not fetched assets.
        asset_tag = re.compile(r'<(link|script|img)\b', re.IGNORECASE)

        offenders = []
        for path in project_templates():
            for lineno, line in enumerate(
                path.read_text(encoding='utf-8').splitlines(), start=1
            ):
                if asset_tag.search(line) and pattern.search(line):
                    offenders.append(
                        f'{path.relative_to(PROJECT_ROOT).as_posix()}:{lineno}'
                    )

        self.assertEqual(
            offenders, [],
            'Asset loaded from an external host — vendor it under static/ '
            'instead, CDNs are not reliably reachable from Iran:\n  '
            + '\n  '.join(offenders),
        )


class SettingsHygieneTests(TestCase):
    """
    Configuration that is silently inert if someone reorders or removes a line.
    """

    def test_login_throttle_backend_is_installed_and_first(self):
        """
        The throttle only refuses; it never authenticates. If ModelBackend ran
        first it would hand back a valid user before the lockout was ever
        consulted, and the whole thing would be decoration.
        """
        backends = settings.AUTHENTICATION_BACKENDS
        self.assertIn('utils.security.auth_backends.LoginThrottleBackend', backends)
        self.assertEqual(
            backends[0], 'utils.security.auth_backends.LoginThrottleBackend',
            'LoginThrottleBackend must come first, or ModelBackend '
            'authenticates the user before the lockout check runs.',
        )

    def test_allowed_hosts_is_never_a_wildcard(self):
        """
        Django echoes the Host header into the absolute URLs it builds — the
        password-reset link among them. '*' accepts any host, so a reset mail
        could arrive pointing at someone else's domain.
        """
        self.assertNotIn('*', settings.ALLOWED_HOSTS)
        self.assertTrue(
            settings.ALLOWED_HOSTS,
            'ALLOWED_HOSTS must be set explicitly for the environment.',
        )

    def test_debug_toolbar_presence_follows_debug(self):
        """
        The toolbar reads settings, SQL and request internals — it belongs in
        development and nowhere else.

        The assertion is the *relationship*, not the absolute: Django forces
        `settings.DEBUG` to False while tests run, but INSTALLED_APPS was built
        at import time from the environment. Reading DEBUG off `settings` here
        would compare against a value that was never used, so the environment
        variable is the honest source.
        """
        debug_at_import = os.environ.get('DEBUG', 'False') == 'True'
        installed = 'debug_toolbar' in settings.INSTALLED_APPS
        in_middleware = any('debug_toolbar' in m for m in settings.MIDDLEWARE)

        self.assertEqual(
            installed, debug_at_import,
            'debug_toolbar must be installed exactly when DEBUG is on',
        )
        self.assertEqual(
            in_middleware, debug_at_import,
            'the toolbar middleware must be loaded exactly when DEBUG is on',
        )
