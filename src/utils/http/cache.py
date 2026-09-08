"""
Cache helpers.

Views opt into a group by passing ``group=`` to :func:`get_cache_key`; models
trigger invalidation by calling :func:`invalidate_group` (typically from a
signal). The version integer stored per group is prefixed into every derived
key, so bumping it orphans every entry within the group instantly. Orphaned
keys expire naturally within their TTL.

Because Django's built-in Redis backend does not support pattern deletes,
version bumping is the mechanism used for group-scoped invalidation.
"""

from django.core.cache import cache

_VERSION_KEY_TEMPLATE = "cache_group_version:{group}"
_DEFAULT_VERSION_TTL = None  # never expire on its own


def get_group_version(group):
    """Return the current version integer for a cache group (creating it if missing)."""
    key = _VERSION_KEY_TEMPLATE.format(group=group)
    version = cache.get(key)
    if version is None:
        cache.set(key, 1, _DEFAULT_VERSION_TTL)
        return 1
    return version


def invalidate_group(group):
    """Bump the version of a cache group, invalidating every keyed entry within it."""
    key = _VERSION_KEY_TEMPLATE.format(group=group)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, _DEFAULT_VERSION_TTL)


def get_cache_key(request, cache_view, group=None, public=False, vary_on=()):
    """
    Build a cache key for a request.

    ``cache_view`` is required — a missing name collapses every caller into a
    single ``cache_None_...`` bucket and one view silently overwrites another.

    ``group`` embeds the group's current version so :func:`invalidate_group`
    can atomically orphan every derived key.

    ``public=True`` drops the per-user segment so anonymous- and
    doctor-visible-but-identical pages share a single Redis entry instead of
    one entry per visitor. Use it for pages whose response body does not
    depend on ``request.user``.

    ``vary_on`` names the query parameters the response actually depends on —
    normally the view's filter fields. Everything else in the query string is
    ignored.

    That last part is a availability control, not a tidiness one. This used to
    append ``request.GET.urlencode()`` wholesale, so ``/blog/?x=1``,
    ``?x=2``, … each minted a distinct entry held for a day. A few minutes of
    requesting a public page with a counter in the query string would fill
    Redis with entries nobody will ever read again, and the eviction that
    follows takes the real cache with it. Unknown parameters change nothing
    about the response — django-filter ignores them — so they must not change
    the key either.
    """
    if not cache_view:
        raise ValueError("cache_view is required for get_cache_key()")

    version_segment = f"_v{get_group_version(group)}" if group else ""

    if public:
        base_key = f"cache_{cache_view}{version_segment}_public"
    elif request.user.is_authenticated:
        base_key = f"cache_{cache_view}{version_segment}_user_{request.user.id}"
    else:
        base_key = f"cache_{cache_view}{version_segment}_anon"

    if not vary_on:
        return base_key

    # Sorted so ``?a=1&b=2`` and ``?b=2&a=1`` land on one entry, and
    # getlist so a multi-select filter keeps every selected value.
    parts = []
    for name in sorted(vary_on):
        values = request.GET.getlist(name)
        if values:
            parts.append(f"{name}={','.join(sorted(values))}")

    if not parts:
        return base_key
    return f"{base_key}_{'&'.join(parts)}"
