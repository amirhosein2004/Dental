"""
Signed OTP-session helpers.

The session token expiry is deliberately kept in sync with
:meth:`accounts.models.OTP.is_valid` (2 minutes). Widening it here would
let a user pass the session gate with an already-expired OTP code and hit
a confusing "code expired" error mid-flow.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()

# Single source of truth for OTP-session lifetime. Kept equal to
# ``OTP.is_valid()``'s 2-minute window.
SESSION_EXPIRY = timedelta(minutes=2)


def generate_otp_token(user):
    """Return a HMAC-signed OTP session token for the given user."""
    secret_key = settings.OTP_SECRET_KEY
    random_token = secrets.token_hex(16)
    created_at = timezone.now().isoformat()
    token_data = f"{user.id}|{random_token}|{created_at}"

    signature = hmac.new(
        secret_key.encode(),
        token_data.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{user.id}|{random_token}|{created_at}|{signature}"


def validate_otp_token(request):
    """
    Validate the OTP token stored in ``request.session`` and return
    ``(user, None)`` on success or ``(None, error_message)`` on failure.
    """
    otp_token = request.session.get('otp_token')
    if not otp_token:
        return None, "سشن نامعتبر است"

    try:
        user_id, random_token, created_at, signature = otp_token.split('|')

        expected_signature = hmac.new(
            settings.OTP_SECRET_KEY.encode(),
            f"{user_id}|{random_token}|{created_at}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not secrets.compare_digest(signature, expected_signature):
            return None, "توکن دستکاری شده است"

        created_time = datetime.fromisoformat(created_at)
        if timezone.now() > created_time + SESSION_EXPIRY:
            return None, "جلسه شما منقضی شده است"

        return User.objects.get(id=user_id), None
    except (ValueError, User.DoesNotExist):
        return None, "کاربر یا توکن نامعتبر است"
