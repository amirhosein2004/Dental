"""
Feed the login throttle from Django's own auth signals.

Signals rather than per-view code: ``user_login_failed`` fires from inside
``authenticate()`` and ``user_logged_in`` from inside ``login()``, so the
admin, the doctor login form and anything added later are all counted without
each one having to remember to call the throttle.
"""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from utils.security.login_throttle import clear, record_failure


@receiver(user_login_failed)
def count_failed_login(sender, credentials=None, request=None, **kwargs):
    """
    One miss against this (ip, username) pair and against the IP overall.

    ``credentials`` arrives with the password already masked by Django, so
    nothing sensitive reaches the cache key — only the username does.
    """
    record_failure(request, (credentials or {}).get('username'))


@receiver(user_logged_in)
def reset_failed_logins(sender, request=None, user=None, **kwargs):
    """
    A correct password clears the slate.

    Without this, a doctor who mistypes four times and then gets it right
    would still be one miss from a lockout for the next quarter of an hour.
    """
    if user is not None:
        clear(request, user.get_username())
