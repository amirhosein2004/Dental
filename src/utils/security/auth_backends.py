"""
Authentication backend that enforces :mod:`utils.security.login_throttle`.

Placed first in ``AUTHENTICATION_BACKENDS``. It never authenticates anyone —
it only refuses. Raising ``PermissionDenied`` from a backend makes Django stop
walking the backend list and return ``None``, so a throttled attempt can never
reach ``ModelBackend`` and never succeeds by accident.

Doing it here rather than in each login view is the point: the admin login,
the doctor login form and anything future that calls ``authenticate()`` all
pass through this one place.
"""
from django.core.exceptions import PermissionDenied

from .login_throttle import is_locked


class LoginThrottleBackend:
    """Refuses login attempts from a throttled (ip, username) pair or IP."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # `request` is None when authenticate() is called without one — a
        # management command or a test helper. There is no IP to key on, so
        # there is nothing to throttle; fall through to the real backend.
        if request is None or not username:
            return None

        if is_locked(request, username):
            raise PermissionDenied(
                'تعداد تلاش‌های ناموفق بیش از حد مجاز است. کمی بعد دوباره تلاش کنید'
            )
        return None

    def get_user(self, user_id):
        """Never the backend that loaded the session user."""
        return None
