"""
`generate_vapid_keys`, which is the first command a deploy runs.

The keypair it prints cannot be recovered once the command exits, so the one
thing worth pinning is that nothing between generating and printing it can
throw. It used to: the Persian guidance was written first, and on a Windows
console — a legacy code page, cp1256 on a Persian install, inherited by
Django's OutputWrapper — that raised UnicodeEncodeError *after* the keys were
generated and before they were shown.
"""
import base64
import io

from django.core.management import call_command
from django.test import SimpleTestCase


def _decode(value):
    """Undo the URL-safe, unpadded base64 the Push API expects."""
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


class GenerateVapidKeysTests(SimpleTestCase):
    def _run(self, stdout):
        call_command('generate_vapid_keys', stdout=stdout)
        pairs = {}
        for line in stdout.getvalue().splitlines():
            if line.startswith('VAPID_'):
                name, _, value = line.partition('=')
                pairs[name] = value
        return pairs

    def test_prints_a_usable_keypair(self):
        pairs = self._run(io.StringIO())

        self.assertIn('VAPID_PUBLIC_KEY', pairs)
        self.assertIn('VAPID_PRIVATE_KEY', pairs)
        # 32-byte private scalar, and an uncompressed P-256 point: the 0x04
        # prefix plus two 32-byte coordinates. A browser rejects a
        # subscription whose applicationServerKey is any other length.
        self.assertEqual(len(_decode(pairs['VAPID_PRIVATE_KEY'])), 32)
        self.assertEqual(len(_decode(pairs['VAPID_PUBLIC_KEY'])), 65)
        self.assertEqual(_decode(pairs['VAPID_PUBLIC_KEY'])[0], 0x04)
        # No padding: `=` in an env value is a second `=` on the line.
        self.assertNotIn('=', pairs['VAPID_PUBLIC_KEY'])
        self.assertNotIn('=', pairs['VAPID_PRIVATE_KEY'])

    def test_keys_survive_a_console_that_cannot_encode_persian(self):
        class Cp1256Stream(io.StringIO):
            """A stdout that rejects anything outside the legacy code page."""

            def write(self, text):
                text.encode('cp1256')  # raises on Persian, like a Windows console
                return super().write(text)

        stdout = Cp1256Stream()
        pairs = self._run(stdout)

        # The keys came out; only the guidance was dropped.
        self.assertIn('VAPID_PUBLIC_KEY', pairs)
        self.assertIn('VAPID_PRIVATE_KEY', pairs)

    def test_each_run_is_a_fresh_keypair(self):
        first = self._run(io.StringIO())
        second = self._run(io.StringIO())
        self.assertNotEqual(first['VAPID_PRIVATE_KEY'], second['VAPID_PRIVATE_KEY'])
