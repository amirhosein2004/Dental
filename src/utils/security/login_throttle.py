"""
Login throttling on the cache.

Replaces django-axes. Axes brought a third-party app, two DB tables, its own
middleware and an authentication backend — and needed all four wired correctly
or it silently recorded failures without refusing a single login. The project
already runs Redis and already throttles every other endpoint through
``RateLimitMixin``; this does the same thing for logins, in one file, with no
migrations and no schema to keep.

Two counters, both fixed-window:

* **(ip, username)** — the pair that a password-guessing run keeps constant.
  Five misses and that pair is refused for fifteen minutes.
* **ip** — catches spraying, where the attacker walks through usernames from
  one address so no single pair ever reaches its limit.

Deliberately *not* keyed on username alone. That is the shape most lockout
bugs take: anyone who knows a staff username could lock them out of their own
account from anywhere, turning the protection into the attack.

Enforcement has two layers because they answer different questions:

* :class:`~utils.security.auth_backends.LoginThrottleBackend` is the hard stop. Every
  login path goes through ``authenticate()`` — the admin, the doctor form, a
  management command — so putting the refusal there means no future view can
  forget it.
* The doctor login form additionally asks :func:`locked_for` up front, so a
  locked-out doctor is told how long is left instead of being handed a generic
  "wrong password".
"""
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Misses allowed for one (ip, username) pair before it is refused.
FAILURE_LIMIT = 5
# Misses allowed from one IP across all usernames — the spraying case.
IP_FAILURE_LIMIT = 20
# How long a counter lives, and therefore how long a lockout lasts.
LOCKOUT_SECONDS = 15 * 60

_PAIR_KEY = 'login-throttle:pair:{ip}:{username}'
_IP_KEY = 'login-throttle:ip:{ip}'


def client_ip(request):
    """
    The caller's address as the proxy reports it.

    Mirrors :func:`utils.http.mixins.client_ip_rate_key`: behind Nginx, REMOTE_ADDR
    is the proxy itself, so every visitor would share one counter and the
    first five failures anywhere would lock out the whole site.
    """
    if request is None:
        return ''
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip.strip()
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _keys(request, username):
    ip = client_ip(request)
    # Username lower-cased so "Doctor" and "doctor" share a counter; an
    # attacker must not get a fresh allowance by changing the capitalisation.
    name = (username or '').strip().lower()
    return (
        _PAIR_KEY.format(ip=ip, username=name),
        _IP_KEY.format(ip=ip),
    )


def _bump(key, timeout=LOCKOUT_SECONDS):
    """
    Increment a fixed-window counter, creating it with a TTL if absent.

    ``add`` then ``incr`` rather than ``set(get() + 1)``: two simultaneous
    failures would both read the same value and write the same number back,
    so a concurrent run would be undercounted. ``incr`` is atomic in Redis.
    """
    cache.add(key, 0, timeout)
    try:
        return cache.incr(key)
    except ValueError:
        # The key expired between the add and the incr. Treat it as the first
        # failure of a new window rather than losing the count.
        cache.set(key, 1, timeout)
        return 1


def record_failure(request, username):
    """Count one failed attempt against both the pair and the IP."""
    pair_key, ip_key = _keys(request, username)
    pair_count = _bump(pair_key)
    ip_count = _bump(ip_key)

    if pair_count == FAILURE_LIMIT or ip_count == IP_FAILURE_LIMIT:
        # Logged once, on the attempt that crosses the line — not on every
        # subsequent refusal, which would let an attacker fill the log.
        logger.warning(
            'Login throttle engaged: ip=%s username=%s pair=%s ip_total=%s',
            client_ip(request), username, pair_count, ip_count,
        )


def clear(request, username):
    """Forget the counters after a successful login."""
    pair_key, ip_key = _keys(request, username)
    cache.delete_many([pair_key, ip_key])


def locked_for(request, username):
    """
    Seconds remaining on a lockout, or 0 when the caller may try again.

    Returns the *window* length rather than the true remaining time: Django's
    cache API exposes no portable TTL read, and over-reporting is the safe
    direction — it never invites an attempt that would be refused anyway.
    """
    pair_key, ip_key = _keys(request, username)
    counts = cache.get_many([pair_key, ip_key])

    if counts.get(pair_key, 0) >= FAILURE_LIMIT:
        return LOCKOUT_SECONDS
    if counts.get(ip_key, 0) >= IP_FAILURE_LIMIT:
        return LOCKOUT_SECONDS
    return 0


def is_locked(request, username):
    return locked_for(request, username) > 0
