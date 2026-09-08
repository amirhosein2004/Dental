"""
Print a fresh VAPID keypair for Web Push.

Run once per deployment and keep the result: the public key is baked into
every subscription the browsers hand back, so rotating it silently
invalidates all of them and every staff device has to opt in again.
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def _b64(raw):
    """URL-safe base64 without padding — the encoding the Push API expects."""
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()


WRITE_TO_ENV = '\nدو خط بالا را در فایل .env قرار دهید.'
ROTATION_WARNING = (
    '\nهشدار: با تغییر این کلیدها تمام دستگاه‌هایی که قبلاً اعلان را فعال کرده‌اند باید دوباره فعال کنند.'
)


class Command(BaseCommand):
    help = 'تولید کلید VAPID برای اعلان مرورگر (Web Push)'

    def handle(self, *args, **options):
        key = ec.generate_private_key(ec.SECP256R1())

        private = _b64(key.private_numbers().private_value.to_bytes(32, 'big'))
        public = _b64(key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        ))

        # The keys go out first, and alone on their lines, because everything
        # else printed here is Persian. A Windows console runs on a legacy
        # code page (cp1256 on a Persian install) and Django's OutputWrapper
        # inherits it, so a Persian line raises UnicodeEncodeError — which
        # used to happen *after* the keypair was generated and *before* it was
        # shown, losing it for good. Same trap as the file-based email backend
        # in settings/develop.py.
        self.stdout.write(f'VAPID_PUBLIC_KEY={public}')
        self.stdout.write(f'VAPID_PRIVATE_KEY={private}')

        self._write_fa(self.style.SUCCESS(WRITE_TO_ENV))
        self._write_fa(ROTATION_WARNING)

    def _write_fa(self, message):
        """Print Persian guidance, or drop it if the console cannot encode it."""
        try:
            self.stdout.write(message)
        except UnicodeEncodeError:
            # Losing the note is acceptable. Losing the keypair above is not.
            pass
